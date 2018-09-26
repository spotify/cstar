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

import socket
import re

from cstar.topology import Topology, Host

_cluster_name_re = re.compile(r"^\s*Name:\s*(.*)$", re.MULTILINE)
_ip_re = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
_token_re = re.compile(r"^\-?\d+$")
_status_re = re.compile(r"^[A-Za-z]+$")
_state_re = re.compile(r"^[A-Za-z]+$")
_keyspace_name_re = re.compile(r"^\s*Keyspace\s*:\s*(.*)$", re.MULTILINE)

def parse_describe_cluster(text):
    return _cluster_name_re.search(text).group(1)


def _parse_node(line):
    words = line.split()
    if len(words) == 8 and re.match(_ip_re, words[0]) and re.match(_status_re, words[2]) and re.match(_state_re, words[3]) and re.match(_token_re, words[7]):
        return words
    else:
        return None


def _parse_datacenter_name_and_nodes(datacenter_section):
    lines = datacenter_section.split("\n")
    name = lines[0]
    nodes = [_parse_node(line) for line in lines[1:]]
    return (name, [node for node in nodes if node is not None])


def parse_nodetool_ring(text, cluster_name, reverse_dns_preheat):
    topology = []
    datacenter_sections = text.split("Datacenter: ")[1:]
    datacenter_names_and_nodes = [_parse_datacenter_name_and_nodes(section) for section in datacenter_sections]
    reverse_dns_preheat([node[0] for (_, nodes) in datacenter_names_and_nodes for node in nodes])
    for (datacenterName, nodes) in datacenter_names_and_nodes:
        for node in nodes:
            fqdn = node[0]
            try:
                fqdn=socket.gethostbyaddr(node[0])[0]
            except socket.herror:
                pass
            topology.append(Host(fqdn=fqdn, ip=node[0], dc=datacenterName, cluster=cluster_name,
                                 is_up=(node[2] == "Up" and node[3] == "Normal"), token=int(node[7])))

    return Topology(topology)


def extract_keyspaces_from_cfstats(text):
    return re.findall(_keyspace_name_re, text)
