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

"""Parse the output of the converted nodetool describering output"""

import socket

import collections


def parse(range_mapping, topology, lookup=socket.gethostbyname):
    return _topology_map(_dns_map(_parse_range_mapping(range_mapping), lookup), topology)


def merge(mappings):
    res = collections.defaultdict(lambda: set())
    for mapping in mappings:
        for host, friends in mapping.items():
            res[host] = res[host] | friends
    return res


def _parse_range_mapping(ranges):
    mapping = {}
    for range in ranges:
        for host1 in range.get("endpoints"):
            for host2 in range.get("endpoints"):
                if host1 != host2:
                    mapping.setdefault(host1, set()).add(host2)
    return mapping


def _dns_map(mapping, lookup=socket.gethostbyname):
    return dict(
        (lookup(raw_host), set(lookup(raw_friend) for raw_friend in raw_friends))
        for raw_host, raw_friends in mapping.items())


def _topology_map(mapping, topology):
    res = {}
    # Fallback for case with no overlap
    for host in topology:
        res[host] = set()
    for raw_host, raw_friends in mapping.items():
        friends = (topology.get_host(raw_friend) for raw_friend in raw_friends)
        host = topology.get_host(raw_host)
        filtered_friends = set(friend for friend in friends if friend.dc == host.dc)
        res[host] = filtered_friends
    return res
