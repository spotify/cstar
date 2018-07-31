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

from cstar.jobprinter import print_progress
from cstar.topology import Topology, Host
from cstar.progress import Progress

import unittest


def make_topology(size, has_down_host=False):
    test_topology = []
    for i in range(size):
        test_topology.append(Host("a", "1.2.3.%d" % i, "eu", "cluster1", i * 100, not has_down_host))
        test_topology.append(Host("b", "2.2.3.%d" % i, "us", "cluster1", (i * 100) + 1, True))
        test_topology.append(Host("c", "3.2.3.%d" % i, "eu", "cluster2", (i * 100) + 2, True))
        test_topology.append(Host("d", "4.2.3.%d" % i, "us", "cluster2", (i * 100) + 3, True))
    return Topology(test_topology)


class JobPrinterTest(unittest.TestCase):

    def test_do_nothing(self):
        top = make_topology(2)
        out = ""

        def writer(x):
            nonlocal out
            out = x
        print_progress(top, Progress(), top.get_down(), writer)
        expected = """ +  Done, up      * Executing, up      !  Failed, up      . Waiting, up
 -  Done, down    / Executing, down    X  Failed, down    : Waiting, down
Cluster: cluster1
DC: eu
..
DC: us
..
Cluster: cluster2
DC: eu
..
DC: us
..
0 done, 0 failed, 0 executing"""
        self.assertEqual(out, expected)

    def test_do_with_something(self):
        top = make_topology(2)
        out = ""

        def writer(x):
            nonlocal out
            out = x
        print_progress(top, Progress(running=set((top.first(),))), top.get_down(), writer)
        expected = """ +  Done, up      * Executing, up      !  Failed, up      . Waiting, up
 -  Done, down    / Executing, down    X  Failed, down    : Waiting, down
Cluster: cluster1
DC: eu
*.
DC: us
..
Cluster: cluster2
DC: eu
..
DC: us
..
0 done, 0 failed, 1 executing"""
        self.assertEqual(out, expected)


if __name__ == '__main__':
    unittest.main()
