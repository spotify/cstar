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

_state_re = re.compile(r"^[A-Za-z]{2}$")
_ip_re = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
_load_re = re.compile(r"^(([0-9]+([,.][0-9]+)?)(\s+)([a-zA-Z]{1,2}))$")
_tokens_re = re.compile(r"^\d+$")
_owns_re = re.compile(r"^\d+\.\d+\%$")
_host_id_re = re.compile(r"^[0-9A-Fa-f]{8}(?:-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}$")
_rack_re = re.compile(r"^\w+$")
_keyspace_name_re = re.compile(r"^\s*Keyspace\s*:\s*(.*)$", re.MULTILINE)


def _parse_node(line):
    words = line.split()
    if len(words) == 8 \
        and re.match(_state_re, words[0]) \
        and re.match(_ip_re, words[1]) \
        and re.match(_tokens_re, words[4]) \
        and re.match(_host_id_re, words[6]) \
        and re.match(_rack_re, words[7]):
        return words
    else:
        return None


def _parse_datacenter_name_and_nodes(datacenter_section):
    lines = datacenter_section.split("\n")
    name = lines[0]
    nodes = [_parse_node(line) for line in lines[1:]]
    return (name, [node for node in nodes if node is not None])


def parse_nodetool_status(text, cluster_name, reverse_dns_preheat, resolve_hostnames=False):
    topology = []
    datacenter_sections = text.split("Datacenter: ")[1:]
    datacenter_names_and_nodes = [_parse_datacenter_name_and_nodes(section) for section in datacenter_sections]
    if resolve_hostnames:
        reverse_dns_preheat([node[1] for (_, nodes) in datacenter_names_and_nodes for node in nodes])
    for (datacenter_name, nodes) in datacenter_names_and_nodes:
        for node in nodes:
            fqdn = node[1]
            if resolve_hostnames:
                try:
                    fqdn=socket.gethostbyaddr(node[1])[0]
                except socket.herror:
                    pass
            topology.append(Host(fqdn=fqdn, ip=node[1], dc=datacenter_name, cluster=cluster_name,
                                 is_up=(node[0] == "UN"), rack=node[7], host_id=node[6]))

    return Topology(topology)
