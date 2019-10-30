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

import cstar.remote
import cstar.jobwriter
import subprocess
import shlex
import os
import time

from cstar.executionresult import ExecutionResult


def save_output(job, host, result):
    output_directory = job.output_directory + "/" + host.fqdn
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    with open(output_directory + "/out", 'w') as f:
        f.write(result.out)
    with open(output_directory + "/err", 'w') as f:
        f.write(result.err)
    with open(output_directory + "/status", 'w') as f:
        f.write(str(result.status))


class RemoteJobRunner(object):
    """Job runners are responsible for running a command to completion for a specific host and reporting back the
     status.

    This is where network outage handling logic will eventually go.

    When a RemoteJobRunner is rerun twice for the same host in the same job, the command will still only be executed
    once.

    This JobRunner is used by cstar
    """

    def __init__(self, job, host, ssh_username, ssh_password, ssh_identity_file, ssh_lib, host_variables):
        self.job = job
        self.host = host
        self.ssh_username = ssh_username
        self.ssh_password = ssh_password
        self.ssh_identity_file = ssh_identity_file
        self.ssh_lib = ssh_lib
        self.host_variables = host_variables

    def __call__(self):
        with cstar.remote.Remote(self.host, self.ssh_username, self.ssh_password, self.ssh_identity_file, self.ssh_lib, self.host_variables) as conn:
            result = conn.run_job(self.job.command, self.job.job_id, self.job.timeout, self.job.env)
            self.job.results.put((self.host, result))  # This signals the main thread that the job completed.
            save_output(self.job, self.host, result)
            # We have to make sure that the local job file is updated before the remote
            # job data is deleted. We need to syncronize with the main thread.
            while self.host not in self.job.handled_finished_jobs:
                time.sleep(1)
            conn.run(("rm", "-rf", ".cstar/remote-jobs/" + self.job.job_id))
        return result


class LocalJobRunner(object):
    """Job runners are responsible for running a command to completion for a specific host and reporting back the
     status. This one executes the command locally.

    When a LocalJobRunner is rerun twice for the same host in the same job, the command will be executed twice.

     This JobRunner is used by cstarpar
    """

    def __init__(self, job, host, ssh_username, ssh_password, ssh_identity_file, ssh_lib, host_variables):
        self.job = job
        self.host = host

    def __call__(self):
        replaced = self.job.command.replace("{}", self.host.ip)

        # Use subprocess.Popen because subprocess.run is not available in Python 3.4 used by Ubuntu Trusty
        proc = subprocess.Popen(shlex.split(replaced), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            outs, errs = proc.communicate()
        except subprocess.TimeoutExpired:
            # The child process is not killed in case of timeout
            proc.kill()
            outs, errs = proc.communicate()
        result = ExecutionResult(replaced, proc.returncode, str(outs, 'utf-8'), str(errs, 'utf-8'))

        save_output(self.job, self.host, result)
        self.job.results.put((self.host, result))
        return result
