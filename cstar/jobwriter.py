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

import json
import datetime

import cstar.strategy
import cstar.job
import cstar.state
import cstar.progress
import cstar.topology

FILE_FORMAT_VERSION = 7


def _to_dict(child):
    if type(child) is set:
        return list(child)
    if type(child) is cstar.topology.Topology:
        return list(child)
    if type(child) is cstar.strategy.Strategy:
        return cstar.strategy.serialize(child)
    if type(child) is cstar.state.State:
        return _state_to_dict(child)
    if type(child) is cstar.progress.Progress:
        return _progress_to_dict(child)
    if type(child) is cstar.job.Job:
        return _job_to_dict(child)
    return child


def _state_to_dict(self):
    skip = {"endpoint_mapping", "stop_after"}
    data = dict((key, _to_dict(val)) for key, val in self.__dict__.items() if
                not key.startswith('_') and key not in skip)
    return data


def _progress_to_dict(self):
    skip = {}
    data = dict((key, _to_dict(val)) for key, val in self.__dict__.items() if
                not key.startswith('_') and key not in skip)
    return data


def _job_to_dict(self):
    skip = {"results", "handled_finished_jobs", "do_loop", "job_id", "job_runner"}
    data = dict((key, _to_dict(val)) for key, val in self.__dict__.items() if key[0] != '_' and key not in skip)
    data["version"] = FILE_FORMAT_VERSION
    data["job_runner"] = self.job_runner.__name__
    data["creation_timestamp"] = int(datetime.datetime.utcnow().timestamp())
    return data


def _job_to_json(job):
    return json.dumps(_to_dict(job), sort_keys=True, indent=4)


def write(job):
    if not job.state:
        return False
    with open(job.output_directory + "/job.json", 'w') as f:
        f.write(_job_to_json(job) + "\n")
    return True
