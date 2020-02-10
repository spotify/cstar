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

from cstar.topology import Topology, Host
import json

import unittest


IP1 = "1.2.3.4"
IP2 = "2.3.4.5"
IP3 = "2.3.4.6"
IP4 = "2.3.4.7"
IP5 = "2.3.4.8"

test_topology = Topology((Host("a", IP1, "eu", "cluster1", 0, True, 'host1'), Host("b", IP2, "eu", "cluster1", 10, True, 'host2'),
                          Host("c", IP3, "us", "cluster1", 1, True, 'host3'), Host("d", IP4, "us", "cluster1", 11, True, 'host4'),
                          Host("e", IP5, "us", "cluster2", 0, True, 'host5')))

test_topology_a = Topology((Host("a", IP1, "eu", "cluster1", 0, True, 'host1'), Host("b", IP2, "eu", "cluster1", 10, True, 'host2'),
                          Host("c", IP3, "us", "cluster1", 1, True, 'host3'), Host("d", IP4, "us", "cluster1", 11, True, 'host4')))

test_topology_b = Topology((Host("a", IP1, "eu", "cluster1", 10, True, 'host1'), Host("b", IP2, "eu", "cluster1", 12, True, 'host2'),
                          Host("c", IP3, "us", "cluster1", 11, True, 'host3'), Host("d", IP4, "us", "cluster1", 14, True, 'host4')))

test_topology_c = Topology((Host("a", IP1, "eu", "cluster1", 10, True, 'host1'), Host("b", IP2, "eu", "cluster1", 12, True, 'host6'),
                          Host("c", IP3, "us", "cluster1", 11, True, 'host3'), Host("d", IP4, "us", "cluster1", 14, True, 'host4')))

class TopologyTest(unittest.TestCase):

    def test_with_dc(self):
        sub = test_topology.with_dc("cluster1", "us")
        self.assertEqual(len(sub), 2)
        [self.assertEqual(host.dc, "us") for host in sub]
        [self.assertEqual(host.cluster, "cluster1") for host in sub]

    def test_with_cluster(self):
        sub = test_topology.with_cluster("cluster1")
        self.assertEqual(len(sub), 4)
        [self.assertEqual(host.cluster, "cluster1") for host in sub]
        self.assertEqual(len(test_topology.hosts_by_ip.keys()), 5)

    def test_without_host(self):
        sub = test_topology.without_host(Host("a", IP1, "eu", "cluster1", 0, True, 'host1'))
        self.assertEqual(len(sub), 4)

    def test_without_hosts(self):
        sub = test_topology.without_hosts(
            (Host("a", IP1, "eu", "cluster1", 0, True, 'host1'), Host("b", IP2, "eu", "cluster1", 10, True, 'host2')))
        self.assertEqual(len(sub), 3)
    
    def test_cluster_hash_match(self):
        self.assertEqual(test_topology_a.get_hash(), test_topology_b.get_hash())
        self.assertEqual(test_topology_a.get_hash(), test_topology_a.get_hash())

    def test_cluster_hash_no_match(self):
        self.assertNotEqual(test_topology.get_hash(), test_topology_a.get_hash())
        self.assertNotEqual(test_topology_b.get_hash(), test_topology_c.get_hash())

    def test_dump_topology_to_json(self):
        topology_a_json = json.dumps(list(test_topology_a))
        topology_b_json = json.dumps(list(test_topology_b))
        topology_a_json_parsed = json.loads(topology_a_json)
        parsed_topology_a = Topology(Host(*arr) for arr in topology_a_json_parsed)
        topology_b_json_parsed = json.loads(topology_b_json)
        parsed_topology_b = Topology(Host(*arr) for arr in topology_b_json_parsed)
        self.assertEqual(parsed_topology_a.get_hash(), parsed_topology_b.get_hash())
        self.assertEqual(parsed_topology_a.get_hash(), test_topology_a.get_hash())



if __name__ == '__main__':
    unittest.main()
