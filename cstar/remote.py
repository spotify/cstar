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

from cstar.remote_paramiko import RemoteParamiko
from cstar.output import debug
from cstar.exceptions import BadArgument

class Remote(object):
    def __init__(self, hostname, ssh_username, ssh_password, ssh_identity_file, ssh_lib):
        debug("Using ssh lib : ", ssh_lib)
        self.remote = RemoteParamiko(hostname, ssh_username, ssh_password, ssh_identity_file)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.remote.close()

    def run_job(self, file, jobid, timeout=None, env={}):
        return self.remote.run_job(file, jobid, timeout, env)

    def get_job_status(self, jobid):
        pass

    def run(self, argv):
        return self.remote.run(argv)

    def close(self):
        self.remote.close()
