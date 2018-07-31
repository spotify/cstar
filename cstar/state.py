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
import cstar.strategy
import cstar.progress


class State(object):
    """All the state, all the time.

    This type contains all the different data that is required to find out what node (if any) to run the job on next.

    Somewhat confusingly, the State object needs to keep track of two potentially different topologies of hosts.
    The first topology (original_topology) is the set of hosts that cstar needs to run on. The second topology
    (current_topology) is the current set of nodes in those same clusters. For many cluter operations, those two sets
    will be identical, but cstar needs to be able to support node operations such as spinning down nodes and replacing
    nodes, and in these situations some or all of the nodes towards the end of the execution will be different.

    This type is meant to be used without mutating it."""

    def __init__(
            self, original_topology, strategy, endpoint_mapping, cluster_parallel, dc_parallel,
            max_concurrency=None, progress=None, current_topology=None, stop_after=None,
            ignore_down_nodes=False):
        self.original_topology = original_topology
        self.current_topology = current_topology or original_topology
        self.strategy = strategy
        self.endpoint_mapping = endpoint_mapping
        self.cluster_parallel = cluster_parallel
        self.dc_parallel = dc_parallel
        self.max_concurrency = max_concurrency
        self.progress = progress or cstar.progress.Progress()
        self.stop_after = stop_after
        self.ignore_down_nodes = ignore_down_nodes

    def clone(self):
        return copy.copy(self)

    def with_topology(self, new_topology):
        res = self.clone()
        res.current_topology = new_topology
        return res

    def with_running(self, host):
        return self.with_progress(self.progress.with_running(host))

    def with_done(self, host):
        return self.with_progress(self.progress.with_done(host))

    def with_failed(self, host):
        return self.with_progress(self.progress.with_failed(host))

    def with_progress(self, progress):
        res = self.clone()
        res.progress = progress
        return res

    def find_next_host(self):
        return cstar.strategy.find_next_host(
            topology=self.original_topology, strategy=self.strategy, endpoint_mapping=self.endpoint_mapping,
            max_concurrency=self.max_concurrency, progress=self.progress,
            cluster_parallel=self.cluster_parallel, dc_parallel=self.dc_parallel, stop_after=self.stop_after,
            ignore_down_nodes=self.ignore_down_nodes)

    def is_done(self):
        return (len(self.progress.done) == len(self.original_topology)) or (
            self.stop_after and (len(self.progress.running) + len(self.progress.done) + len(self.progress.failed) >= self.stop_after))

    def is_healthy(self):
        if self.ignore_down_nodes:
            return True
        return len(self.current_topology.without_hosts(self.progress.running).get_down()) == 0

    def get_idle(self):
        return self.current_topology.without_hosts(self.progress.running)

    def __str__(self):
        return """"State(
    original_topology=%s,
    current_topology=%s,
    strategy=%s,
    endpoint_mapping=%s,
    cluster_parallel%s,
    dc_parallel=%s,
    max_concurrency=%s,
    progress=%s)""" % (
            self.original_topology, self.current_topology, self.strategy, self.endpoint_mapping, self.cluster_parallel,
            self.dc_parallel, self.max_concurrency, self.progress)
