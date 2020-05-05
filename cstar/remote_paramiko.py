# Copyright 2017 Spotify AB
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import paramiko.client
import re
import select

from cstar.output import err, debug, msg
from cstar.exceptions import BadSSHHost, BadEnvironmentVariable, NoHostsSpecified
from cstar.executionresult import ExecutionResult
from pkg_resources import resource_string

PING_COMMAND = "echo ping"

_alnum_re = re.compile(r"[^a-zA-Z0-9\|_]")


class RemoteParamiko(object):
    def __init__(self, hostname, ssh_username=None, ssh_password=None, ssh_identity_file=None):
        if hasattr(hostname, "ip"):
            self.hostname = hostname.ip
        else:
            self.hostname = hostname
        if not self.hostname:
            raise NoHostsSpecified("No SSH host specified")
        self.ssh_username = ssh_username
        self.ssh_password = ssh_password
        self.ssh_identity_file = ssh_identity_file
        self.client = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()

    def _connect(self):
        if self.client:
            # Ensure underlying client is still a valid open connection
            try:
                stdin, stdout, stderr = self.client.exec_command(PING_COMMAND)
            except (ConnectionResetError, paramiko.ssh_exception.SSHException):
                # ConnectionResetError is raised when a connection was established but then broken
                # paramiko.ssh_exception.SSHException is raised if the connection was known to be broken
                self.client = None

        if not self.client:
            try:
                self.client = paramiko.client.SSHClient()
                pkey = None
                if self.ssh_identity_file != None:
                    pkey = paramiko.RSAKey.from_private_key_file(self.ssh_identity_file, None)
                debug("Username : ", self.ssh_username)
                debug("Id file: ", self.ssh_identity_file)
                self.client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
                self.client.connect(self.hostname, compress=True, username=self.ssh_username, password=self.ssh_password, pkey=pkey)

                # Enable keepalive to improve connection stability when running commands that return no output for
                # long periods of time.
                transport = self.client.get_transport()
                transport.set_keepalive(5)
            except:
                self.client = None
                raise BadSSHHost("Could not establish an SSH connection to host %s" % (self.hostname,))

    def run_job(self, file, jobid, timeout=None, env={}):
        try:
            self._connect()

            transport = self.client.get_transport()
            session = transport.open_session()
            paramiko.agent.AgentRequestHandler(session)

            dir = ".cstar/remote-jobs/" + jobid

            self.run(("mkdir", "-p", dir))

            self.put_command(file, "%s/job" % (dir,))

            # Manually insert environment into script, since passing env into exec_command leads to it being
            # ignored on most ssh servers. :-(

            for key in env:
                if _alnum_re.search(key):
                    raise BadEnvironmentVariable(key)

            env_str = " ".join(key + "=" + self.escape(value) for key, value in env.items())
            remote_script = resource_string('cstar.resources', 'scripts/remote_job.sh')
            wrapper = remote_script.decode("utf-8") % (env_str,)
            self.write_command(wrapper, "%s/wrapper" % (dir,))

            cmd = """
                cd %s
                nohup ./wrapper
                """ % (self.escape(dir),)

            stdin, stdout, stderr = self.client.exec_command(cmd, timeout=timeout)
            _, _, _ = self._read_results(stdin, stdout, stderr, timeout)

            real_output = self.read_file(dir + "/stdout")
            real_error = self.read_file(dir + "/stderr")
            real_status = int(self.read_file(dir + "/status"))
            return ExecutionResult(cmd, real_status, real_output, real_error)
        except (ConnectionResetError, paramiko.ssh_exception.SSHException):
            raise BadSSHHost("SSH connection to host %s was reset" % (self.hostname,))

    def get_job_status(self, jobid):
        pass

    def run(self, argv):
        try:
            self._connect()
            cmd = " ".join(self.escape(s) for s in argv)
            stdin, stdout, stderr = self.client.exec_command(cmd)
            status, stdout_chunks, stderr_chunks = self._read_results(stdin, stdout, stderr)
            out = b''.join(stdout_chunks)
            error = b''.join(stderr_chunks)
            
            if status != 0:
                err("Command %s failed with status %d on host %s" % (cmd, status, self.hostname))
            else:
                debug("Command %s succeeded on host %s, output was %s and %s" %
                      (cmd, self.hostname, str(out, 'utf-8'), str(error, 'utf-8')))
            return ExecutionResult(cmd, status, str(out, 'utf-8'), str(error, 'utf-8'))
        except (ConnectionResetError, paramiko.ssh_exception.SSHException):
            self.client = None
            raise BadSSHHost("SSH connection to host %s was reset" % (self.hostname,))

    def _read_results(self, stdin, stdout, stderr, timeout=30):

        # get the shared channel for stdout/stderr/stdin
        channel = stdout.channel

        stdin.close()
        # indicate that we're not going to write to that channel anymore
        channel.shutdown_write()

        # read stdout/stderr in order to prevent read block hangs
        stdout_chunks, stderr_chunks = [], []
        stdout_chunks.append(stdout.channel.recv(len(stdout.channel.in_buffer)))
        # chunked read to prevent stalls
        while not channel.closed or channel.recv_ready() or channel.recv_stderr_ready():
            # stop if channel was closed prematurely, and there is no data in the buffers.
            got_chunk = False
            readq, _, _ = select.select([stdout.channel], [], [], timeout)
            for c in readq:
                if c.recv_ready():
                    stdout_chunks.append(stdout.channel.recv(len(c.in_buffer)))
                    got_chunk = True
                if c.recv_stderr_ready():
                    # make sure to read stderr to prevent stall
                    stderr_chunks.append(stderr.channel.recv_stderr(len(c.in_stderr_buffer)))
                    got_chunk = True
            '''
            1) make sure that there are at least 2 cycles with no data in the input buffers in order to not exit too early (i.e. cat on a >200k file).
            2) if no data arrived in the last loop, check if we already received the exit code
            3) check if input buffers are empty
            4) exit the loop
            '''
            if not got_chunk \
                    and stdout.channel.exit_status_ready() \
                    and not stderr.channel.recv_stderr_ready() \
                    and not stdout.channel.recv_ready():
                # indicate that we're not going to read from this channel anymore
                stdout.channel.shutdown_read()
                # close the channel
                stdout.channel.close()
                break    # exit as remote side is finished and our bufferes are empty

        # close all the pseudofiles
        stdout.close()
        stderr.close()

        status = stdout.channel.recv_exit_status()
        return status, stdout_chunks, stderr_chunks

    @staticmethod
    def escape(input):
        if _alnum_re.search(input):
            return "'" + input.replace("'", r"'\''") + "'"
        return input

    def read_file(self, remotepath):
        self._connect()
        with self.client.open_sftp() as ftp_client:
            with ftp_client.file(remotepath, 'r') as f:
                return str(f.read(), 'utf-8')

    def put_file(self, localpath, remotepath):
        self._connect()
        with self.client.open_sftp() as ftp_client:
            ftp_client.put(localpath, remotepath)

    def put_command(self, localpath, remotepath):
        self._connect()
        with self.client.open_sftp() as ftp_client:
            ftp_client.put(localpath, remotepath)
            ftp_client.chmod(remotepath, 0o755)

    def write_command(self, definition, remotepath):
        self._connect()
        with self.client.open_sftp() as ftp_client:
            with ftp_client.open(remotepath, 'w') as f:
                f.write(definition)
            ftp_client.chmod(remotepath, 0o755)

    def mkdir(self, path):
        self.run("mkdir " + path)

    def close(self):
        if self.client:
            self.client.close()
        self.client = None
