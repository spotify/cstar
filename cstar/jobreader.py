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

import datetime
import json
import os

import cstar.jobrunner
import cstar.jobwriter
import cstar.strategy
import cstar.topology
from cstar.exceptions import BadFileFormatVersion, FileTooOld
from cstar.output import debug


def read(job, job_id, stop_after, output_directory=None, max_days=7, endpoint_mapper=None, retry=False):
    output_directory = output_directory or os.path.expanduser("~/.cstar/jobs/" + job_id)
    file = output_directory + "/job.json"

    if not endpoint_mapper:
        endpoint_mapper = job.get_endpoint_mapping

    with open(file) as f:
        return _parse(f.read(), file, output_directory, job, job_id, stop_after, max_days, endpoint_mapper, retry)
    return job


def _parse(input, file, output_directory, job, job_id, stop_after, max_days, endpoint_mapper, retry=False):
    data = json.loads(input)

    if 'version' not in data:
        raise BadFileFormatVersion("Incompatible file format version, wanted %d" %
                                   (cstar.jobwriter.FILE_FORMAT_VERSION,))
    if data['version'] != cstar.jobwriter.FILE_FORMAT_VERSION:
        raise BadFileFormatVersion("Incompatible file format version, wanted %d but %s is of version %d" %
                                   (cstar.jobwriter.FILE_FORMAT_VERSION, file, data['version']))

    creation_time = datetime.datetime.utcfromtimestamp(data["creation_timestamp"])
    age = (datetime.datetime.utcnow() - creation_time).days
    if age > max_days:
        raise FileTooOld(("Job created %d days ago, which is more than the current maximum age of %d. " +
                          "Use --max-job-age %d if you really want to run this job.") % (age, max_days, age + 1))

    state = data['state']
    job.command = data['command']
    job.job_id = job_id
    job.timeout = data['timeout']
    job.env = data['env']
    job.job_runner = getattr(cstar.jobrunner, data["job_runner"])
    job.key_space = data['key_space'] if 'key_space' in data else None
    job.output_directory = output_directory
    job.sleep_on_new_runner = data['sleep_on_new_runner']
    job.ssh_username = data['ssh_username']
    job.ssh_identity_file = data['ssh_identity_file']
    job.ssh_password = data['ssh_password']
    job.ssh_lib = data['ssh_lib']
    job.jmx_username = data['jmx_username']
    job.hosts_variables = data['hosts_variables']

    strategy = cstar.strategy.parse(state['strategy'])
    cluster_parallel = state['cluster_parallel']
    dc_parallel = state['dc_parallel']
    max_concurrency = state['max_concurrency']

    progress = cstar.progress.Progress(
        running=[cstar.topology.Host(*arr) for arr in state['progress']['running']],
        done=[cstar.topology.Host(*arr) for arr in state['progress']['done']],
        failed=[cstar.topology.Host(*arr) for arr in state['progress']['failed']])

    if retry==True:
        progress.failed = set([])
    
    original_topology = cstar.topology.Topology(cstar.topology.Host(*arr) for arr in state['original_topology'])
    current_topology = cstar.topology.Topology(cstar.topology.Host(*arr) for arr in state['current_topology'])

    debug("Run on hosts", original_topology)
    debug("in topology", current_topology)

    if strategy is cstar.strategy.Strategy.TOPOLOGY:
        endpoint_mapping = endpoint_mapper(original_topology)
    else:
        endpoint_mapping = None

    job.state = cstar.state.State(
        original_topology=original_topology,
        strategy=strategy,
        endpoint_mapping=endpoint_mapping,
        cluster_parallel=cluster_parallel,
        dc_parallel=dc_parallel,
        max_concurrency=max_concurrency,
        current_topology=current_topology,
        stop_after=stop_after,
        progress=progress,
        ignore_down_nodes=state['ignore_down_nodes'])
