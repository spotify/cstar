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

import cstar.endpoint_mapping
from cstar.nodetoolparser import parse_nodetool_ring

import json
import socket
import unittest

SMALL_EXAMPLE = """
[
    {
        "endpoints": ["a","b","c"]
    },
    {
        "endpoints": ["b","c","d"]
    },
    {
        "endpoints": ["c","d","e"]
    },
    {
        "endpoints": ["d","e","f"]
    },
    {
        "endpoints": ["e","f","g"]
    },
    {
        "endpoints": ["f","g","a"]
    },
    {
        "endpoints": ["g","a","b"]
    }
]
"""


class TopologyTest(unittest.TestCase):

    def ip_lookup(self, name):
        return name

    def test_lookup(self):
        parsed = cstar.endpoint_mapping._parse_range_mapping(json.loads(SMALL_EXAMPLE))

        def lookup(x):
            return x.upper()

        transformed = cstar.endpoint_mapping._dns_map(parsed, lookup)
        self.assertEqual(transformed["A"], set(("F", "G", "B", "C")))

    def test_bigly(self):
        with open("tests/resources/topology.json", 'r') as f:
            parsed = cstar.endpoint_mapping._parse_range_mapping(json.load(f))
        expected = {'cassandra-node-a6233.example.com', 'cassandra-node-a-cdr6.example.com',
                    'cassandra-node-a-rzmz.example.com', 'cassandra-node-a4992.example.com',
                    'cassandra-node-a-7q9q.example.com', 'cassandra-node-a2772.example.com',
                    'cassandra-node-a-243r.example.com', 'cassandra-node-a-4k79.example.com',
                    'cassandra-node-a-0wx3.example.com', 'cassandra-node-a1629.example.com',
                    'cassandra-node-a6906.example.com', 'cassandra-node-a-r3r4.example.com',
                    'cassandra-node-a-mqvb.example.com', 'cassandra-node-a3577.example.com'}

        self.assertEqual(parsed["cassandra-node-a-qz36.example.com"], expected)

    def test_small(self):
        parsed = cstar.endpoint_mapping._parse_range_mapping(json.loads(SMALL_EXAMPLE))
        self.assertEqual(parsed["a"], set(("f", "g", "b", "c")))

        for host in parsed:
            self.assertEqual(len(parsed[host]), 4)

    def test_merge_with_overlap(self):
        tree1 = {"a": set("b"), "b": set("c"), "c": set("a")}
        tree2 = {"a": set(("b", "c")), "b": set(("c", "a")), "c": set(("a", "b"))}
        merged = cstar.endpoint_mapping.merge((tree1, tree2))
        self.assertEqual(merged, tree2)

    def test_merge_without_overlap(self):
        tree1 = {"a": set("b"), "b": set("c"), "c": set("a")}
        tree2 = {"a": set("c"), "b": set("a"), "c": set("b")}
        expected = {"a": set(("b", "c")), "b": set(("c", "a")), "c": set(("a", "b"))}
        merged = cstar.endpoint_mapping.merge((tree1, tree2))
        self.assertEqual(merged, expected)


    def test_endpoint_mapping_vnodes(self):
        with open("tests/resources/ring_vnodes.txt", 'r') as f1:
            topology = parse_nodetool_ring(f1.read(), 'test_cluster', lambda _: None)
        with open("tests/resources/describering-vnodes.txt", 'r') as f2:
            describering = cstar.nodetoolparser.parse_nodetool_describering(f2.read())
            range_mapping = cstar.nodetoolparser.convert_describering_to_range_mapping(describering)
            mapping = cstar.endpoint_mapping.parse(range_mapping, topology, lookup=self.ip_lookup)
            for key in mapping:
                # since we have no racks and we have vnodes, let's check that all nodes are friends
                self.assertEqual(5, len(mapping.get(key)))

    def test_endpoint_mapping_vnodes_and_racks(self):
        with open("tests/resources/ring-vnodes-racks.txt", 'r') as f1:
            topology = parse_nodetool_ring(f1.read(), 'test_cluster', lambda _: None)
        with open("tests/resources/describering-vnodes-racks.txt", 'r') as f2:
            describering = cstar.nodetoolparser.parse_nodetool_describering(f2.read())
            range_mapping = cstar.nodetoolparser.convert_describering_to_range_mapping(describering)
            mapping = cstar.endpoint_mapping.parse(range_mapping, topology, lookup=self.ip_lookup)
            for key in mapping:
                # since we have no racks and we have vnodes, let's check that all nodes are friends
                self.assertEqual(4, len(mapping.get(key)))


if __name__ == '__main__':
    unittest.main()
