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

from ssh2.session import Session
from ssh2.sftp import LIBSSH2_FXF_CREAT, LIBSSH2_FXF_WRITE, LIBSSH2_FXF_READ, \
    LIBSSH2_SFTP_S_IRUSR, LIBSSH2_SFTP_S_IRGRP, LIBSSH2_SFTP_S_IWUSR, \
    LIBSSH2_SFTP_S_IROTH
import os, socket, sys
import re, tempfile
from pkg_resources import resource_string

from cstar.output import err, debug, msg
from cstar.exceptions import BadSSHHost, BadEnvironmentVariable, NoHostsSpecified
from cstar.executionresult import ExecutionResult

SFTP_MODE = LIBSSH2_SFTP_S_IRUSR | LIBSSH2_SFTP_S_IWUSR | LIBSSH2_SFTP_S_IRGRP | LIBSSH2_SFTP_S_IROTH
SFTP_FLAGS = LIBSSH2_FXF_CREAT | LIBSSH2_FXF_WRITE
PING_COMMAND = "echo ping"

_alnum_re = re.compile(r"[^a-zA-Z0-9\|_]")


class RemoteSsh2(object):
    def __init__(self, hostname, ssh_username=None, ssh_password=None, ssh_identity_file=None, host_variables=dict()):
        if hasattr(hostname, "ip"):
            self.hostname = hostname.ip
        else:
            self.hostname = hostname
        if not self.hostname:
            raise NoHostsSpecified("No SSH host specified")
        self.ssh_username = ssh_username
        self.ssh_password = ssh_password
        self.ssh_identity_file = ssh_identity_file
        self.channel = None
        self.session = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()

    def _connect(self):
        try:
            if self.session == None:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self.hostname, 22))
                self.session = Session()
                self.session.handshake(sock)
                if self.ssh_identity_file != None:
                    self.session.userauth_publickey_fromfile(self.ssh_username, self.ssh_identity_file, '', None)
                elif self.ssh_password != None:
                    self.session.userauth_password(self.ssh_username, self.ssh_password)
                elif self.ssh_username == None:
                    user = os.getlogin()
                    self.session.agent_auth(user)
                else:
                    self.session.agent_auth(self.ssh_username)
            self.channel = self.session.open_session()
        except:
            self.channel = None
            self.session = None
            raise BadSSHHost("Could not establish an SSH connection to host %s" % (self.hostname,))

    def run_job(self, file, jobid, timeout=None, env={}):
        try:
            jobs_dir = ".cstar/remote-jobs/" + jobid
            self.run(("mkdir", "-p", jobs_dir))
            self.put_command(file, "%s/job" % (jobs_dir,))

            # Manually insert environment into script, since passing env into exec_command leads to it being
            # ignored on most ssh servers. :-(

            for key in env:
                if _alnum_re.search(key):
                    raise BadEnvironmentVariable(key)

            env_str = self._substitute_host_variables(" ".join(key + "=" + self.escape(value) for key, value in env.items()))
            remote_script = resource_string('cstar.resources', 'scripts/remote_job.sh')
            wrapper = remote_script.decode("utf-8") % (env_str,)
            self.write_command(wrapper, "%s/wrapper" % (jobs_dir,))
            cmd_cd = "cd %s" % (self.escape(jobs_dir),)
            cmd_wrapper = "nohup ./wrapper"
            self.exec_command(cmd_cd + ";" + cmd_wrapper)
            out, err_output, status = self.read_channel()
            real_output = self.read_file(jobs_dir + "/stdout")
            real_error = self.read_file(jobs_dir + "/stderr")
            real_status = int(self.read_file(jobs_dir + "/status"))
            return ExecutionResult(cmd_wrapper, real_status, real_output, real_error)
        except:
            err("Command failed : ", sys.exc_info()[0])
            raise BadSSHHost("SSH connection to host %s was reset" % (self.hostname,))

    def _substitute_host_variables(self, env_str):
        env_str_substituted = env_str
        for key, value in self.host_variables.items():
            env_str_substituted = env_str_substituted.replace("{{" + key + "}}", value)
        
        return env_str_substituted

    def get_job_status(self, jobid):
        pass

    def exec_command(self, command):
        self._connect()
        self.channel.execute(command)

    def run(self, argv):
        try:
            cmd = " ".join(self.escape(s) for s in argv)
            self.exec_command(cmd)
            out, error, status = self.read_channel()
            if status != 0:
                err("Command %s failed with status %d on host %s" % (cmd, status, self.hostname))
            else:
                debug("Command %s succeeded on host %s, output was %s and %s" %
                      (cmd, self.hostname, out, error))
            return ExecutionResult(cmd, status, out, error)
        except:
            self.client = None
            raise BadSSHHost("SSH connection to host %s was reset" % (self.hostname,))

    # read stderr, stdout and exit code from the ssh2 channel object
    def read_channel(self):
        stdout = []
        stderr = []

        # read stdout
        size, stdout_part = self.channel.read()
        stdout.append(stdout_part.decode())
        while size > 0:
            size, stdout_part = self.channel.read()
            stdout.append(stdout_part.decode())

        # read stderr
        size, stderr_part = self.channel.read()
        stderr.append(stderr_part.decode())
        while size > 0:
            size, stderr_part = self.channel.read()
            stderr.append(stdout_part.decode())
         
        status = self.channel.get_exit_status()

        return "".join(stdout), "".join(stderr), status

    @staticmethod
    def escape(input):
        if _alnum_re.search(input):
            return "'" + input.replace("'", r"'\''") + "'"
        return input

    def read_file(self, remotepath):
        self._connect()
        debug("Retrieving %s through SCP"% (remotepath))
        channel, info = self.session.scp_recv(remotepath)
        if info.st_size == 0:
            return ""
        size, content = channel.read(info.st_size-1)
        channel.close()
        return content.decode("utf-8")

    def put_file(self, localpath, remotepath):
        self._connect()
        fileinfo = os.stat(localpath)
        chan = self.session.scp_send64(remotepath, fileinfo.st_mode & 755, fileinfo.st_size,
                        fileinfo.st_mtime, fileinfo.st_atime)
        debug("Starting SCP of local file %s to remote %s:%s" % (
            localpath, self.hostname, remotepath))
        with open(localpath, 'rb') as local_fh:
            for data in local_fh:
                chan.write(data)

    def put_command(self, localpath, remotepath):
        self.put_file(localpath, remotepath)
        self.run(("chmod", "755", remotepath))

    def write_command(self, definition, remotepath):
        self._connect()
        with tempfile.NamedTemporaryFile() as fp:
            fp.write(str.encode(definition))
            fp.flush()
            self.put_file(fp.name, remotepath)
        self.run(("chmod", "755", remotepath))

    def mkdir(self, path):
        self.run(("mkdir", path))

    def close(self):
        if self.channel:
            self.channel.close()
        self.channel = None
        self.session = None
