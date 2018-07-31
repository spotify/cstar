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

import unittest


IP1 = "1.2.3.4"
IP2 = "2.3.4.5"
IP3 = "2.3.4.6"
IP4 = "2.3.4.7"
IP5 = "2.3.4.8"

test_topology = Topology((Host("a", IP1, "eu", "cluster1", 0, True), Host("b", IP2, "eu", "cluster1", 10, True),
                          Host("c", IP3, "us", "cluster1", 1, True), Host("d", IP4, "us", "cluster1", 11, True),
                          Host("e", IP5, "us", "cluster2", 0, True)))


class TopologyTest(unittest.TestCase):

    def test_with_dc(self):
        sub = test_topology.with_dc("us")
        self.assertEqual(len(sub), 3)
        [self.assertEqual(host.dc, "us") for host in sub]

    def test_with_cluster(self):
        sub = test_topology.with_cluster("cluster1")
        self.assertEqual(len(sub), 4)
        [self.assertEqual(host.cluster, "cluster1") for host in sub]

    def test_without_host(self):
        sub = test_topology.without_host(Host("a", IP1, "eu", "cluster1", 0, True))
        self.assertEqual(len(sub), 4)

    def test_without_hosts(self):
        sub = test_topology.without_hosts(
            (Host("a", IP1, "eu", "cluster1", 0, True), Host("b", IP2, "eu", "cluster1", 10, True)))
        self.assertEqual(len(sub), 3)

if __name__ == '__main__':
    unittest.main()
