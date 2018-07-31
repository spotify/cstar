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
from cstar.state import State
from cstar.progress import Progress

import unittest


def make_topology(size, has_down_host=False):
    test_topology = []
    for i in range(size):
        test_topology.append(Host("a%d" % i, "1.2.3.%d" % i, "eu", "cluster1", i * 100, not has_down_host))
        test_topology.append(Host("b%d" % i, "2.2.3.%d" % i, "us", "cluster1", (i * 100) + 1, True))
        test_topology.append(Host("c%d" % i, "3.2.3.%d" % i, "eu", "cluster2", i * 100, True))
        test_topology.append(Host("d%d" % i, "4.2.3.%d" % i, "us", "cluster2", (i * 100) + 1, True))
    return Topology(test_topology)


class TopologyTest(unittest.TestCase):
    def test_is_healthy_true(self):
        top = make_topology(3, False)
        state = State(top, None, {}, True, True)
        self.assertEqual(state.is_healthy(), True)

    def test_is_healthy_is_true_when_running_jobs_take_down_host(self):
        top = make_topology(3, True)
        state = State(top, None, {}, True, True, progress=Progress(running=set(top.get_down())))
        self.assertEqual(state.is_healthy(), True)

    def test_is_healthy_false(self):
        top = make_topology(3, True)
        state = State(top, None, {}, True, True)
        self.assertEqual(state.is_healthy(), False)

    def test_get_idle_host(self):
        top = make_topology(1)
        state = State(top, None, {}, True, True)

        self.assertEqual(set(state.get_idle()), set(state.original_topology))
        state.progress.running = set(state.original_topology)
        self.assertEqual(set(state.get_idle()), set())

    def test_down_host(self):
        top = make_topology(2, True)
        state = State(top, None, {}, True, True)
        self.assertEqual(
            state.current_topology.get_down(),
            Topology((Host("a0", "1.2.3.0", "eu", "cluster1", 0, False),
                     Host("a1", "1.2.3.1", "eu", "cluster1", 100, False))))

    def test_unhealthy_cluster(self):
        top = make_topology(2, True)
        state = State(top, None, {}, True, True)
        self.assertEqual(
            state.is_healthy(), False)

    def test_healthy_cluster(self):
        top = make_topology(2, True)
        down = set(top.get_down())
        state = State(top, None, {}, True, True, progress=Progress(running=down))
        self.assertEqual(
            state.is_healthy(), True)


if __name__ == '__main__':
    unittest.main()
