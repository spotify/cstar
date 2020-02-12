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
_schema_version_re = re.compile(r"([0-9A-Fa-f]{8}(?:-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}): ", re.MULTILINE)
_keyspace_name_re = re.compile(r"^\s*Keyspace\s*:\s*(.*)$", re.MULTILINE)

def parse_describe_cluster(text):
    return (_cluster_name_re.search(text).group(1), _schema_version_re.search(text).group(1))


def extract_keyspaces_from_cfstats(text):
    return re.findall(_keyspace_name_re, text)
