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

from enum import Enum
from cstar.exceptions import HostIsDown


class Strategy(Enum):
    """The three concurrency strategies available in cstar"""
    ONE = 1
    TOPOLOGY = 2
    ALL = 3


def parse(text):
    """Convert a strategy string to a strategy object"""
    return {
        "one": Strategy.ONE,
        "topology": Strategy.TOPOLOGY,
        "all": Strategy.ALL
    }[text]


def serialize(s):
    """Convert a strategy object to a strategy string"""
    return {
        Strategy.ONE: "one",
        Strategy.TOPOLOGY: "topology",
        Strategy.ALL: "all"
    }[s]


def find_next_host(strategy, topology, endpoint_mapping, progress, cluster_parallel, dc_parallel, max_concurrency,
                   stop_after, ignore_down_nodes):
    """Entry point for figuring out which host to do things on next."""

    if stop_after and ((len(progress.running) + len(progress.done) + len(progress.failed)) >= stop_after):
        return None

    remaining = topology.without_hosts(progress.done).without_hosts(progress.running).without_hosts(progress.failed)
    if progress.running and not cluster_parallel:
        remaining = remaining.with_cluster(next(iter(progress.running)).cluster)

    if progress.running and not dc_parallel:
        remaining = remaining.with_dc(next(iter(progress.running)).dc)

    if not remaining:
        return None

    if max_concurrency and (len(progress.running) >= max_concurrency):
        return None

    if not ignore_down_nodes:
        for host in remaining:
            if not host.is_up:
                raise HostIsDown(host)

    return _strategy_mapping[strategy](remaining, endpoint_mapping, progress.running)


def _all_find_next_host(remaining, endpoint_mapping, running):
    return remaining.first()


def _one_find_next_host(remaining, endpoint_mapping, running):
    if running:
        return None
    return remaining.first()


def _topology_find_next_host(remaining, endpoint_mapping, running):
    for h in running:
        for next in endpoint_mapping[h]:
            remaining = remaining.without_host(next)
    return remaining.first()


_strategy_mapping = {
    Strategy.ONE: _one_find_next_host,
    Strategy.TOPOLOGY: _topology_find_next_host,
    Strategy.ALL: _all_find_next_host}
