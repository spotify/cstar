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

import signal
import sys

import cstar.jobwriter
from cstar.output import emph

_msg = None
_job = None


def _handler(signum, frame):
    if cstar.jobwriter.write(_job):
        print("\n" + _msg)
    sys.exit(1)


def print_message_and_save_on_sigint(job, job_id):
    global _msg, _job
    _msg = "Shutting down gracefully. Hit ^C again to shut down gracelessly.\n\nTo resume, type %s" % (
        emph("cstar continue " + job_id),)

    _job = job
    signal.signal(signal.SIGINT, _handler)
