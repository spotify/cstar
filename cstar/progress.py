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

import copy


class Progress(object):
    """The progress of a job.
    Progress is expressed in terms of what state each node is in.
    This type is meant to be used without mutating it."""

    def __init__(self, done=None, running=None, failed=None):
        self.done = set(done or [])
        self.running = set(running or [])
        self.failed = set(failed or [])

    def clone(self):
        return copy.copy(self)

    def with_running(self, host):
        res = self.clone()
        res.running.add(host)
        return res

    def with_done(self, host):
        res = self.clone()
        res.done.add(host)
        if host in res.running:
            res.running.remove(host)
        return res

    def with_failed(self, host):
        res = self.clone()
        res.failed.add(host)
        if host in res.running:
            res.running.remove(host)
        return res

    def __str__(self):
        return """"Progress(
    done=%s,
    running=%s,
    failed=%s)""" % (self.done, self.running, self.failed)
