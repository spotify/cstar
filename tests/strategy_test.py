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

import unittest

from cstar.state import State
from cstar.progress import Progress
from cstar.topology import Topology, Host
from cstar.strategy import Strategy, find_next_host, HostIsDown


def make_topology(size, has_down_host=False):
    test_topology = []
    for i in range(size):
        test_topology.append(Host("a", "1.2.3.%d" % i, "eu", "cluster1", i * 100, not has_down_host))
        test_topology.append(Host("b", "2.2.3.%d" % i, "us", "cluster1", (i * 100) + 1, True))
        test_topology.append(Host("c", "3.2.3.%d" % i, "eu", "cluster2", i * 100, True))
        test_topology.append(Host("d", "4.2.3.%d" % i, "us", "cluster2", (i * 100) + 1, True))
    return Topology(test_topology)


def make_mapping(topology):
    size = len(topology) // 4
    mapping = {}
    for i in range(size):
        for j in [(i + 1) % size, (i + 2) % size, (i + size - 2) % size, (i + size - 1) % size]:
            for k in (1, 2, 3, 4):
                a = topology.get_host("%d.2.3.%d" % (k, i))
                b = topology.get_host("%d.2.3.%d" % (k, j))

                mapping.setdefault(a, set())
                mapping[a].add(b)
    return mapping


class StrategyTest(unittest.TestCase):

    def test_all(self):
        top = make_topology(size=3)
        done = []
        running = []
        failed = []

        while True:
            h = find_next_host(Strategy.ALL, top, None, Progress(done=done, running=running, failed=failed), True, True, None, None, False)
            if not h:
                break
            running.append(h)
        self.assertEqual(len(running), 12)

    def test_fail_if_down(self):
        top = make_topology(size=3, has_down_host=True)
        done = []
        running = []
        failed = []
        with self.assertRaises(HostIsDown):
            find_next_host(Strategy.ALL, top, None, Progress(done=done, running=running, failed=failed), True, True, None, None, False)

    def test_succeed_if_down_with_ignore_down_nodes(self):
        top = make_topology(size=3, has_down_host=True)
        done = []
        running = []
        failed = []

        while True:
            h = find_next_host(Strategy.ALL, top, None, Progress(done=done, running=running, failed=failed), True, True, None, None, True)
            if not h:
                break
            running.append(h)
        self.assertEqual(len(running), 12)

    def test_max_concurrency(self):
        top = make_topology(size=3)
        state = State(top, Strategy.ALL, None, True, True, 10)
        state = add_work(state)
        self.assertEqual(len(state.progress.running), 10)

    def test_all_per_dc(self):
        top = make_topology(size=3)
        state = State(top, Strategy.ALL, None, True, False)

        state = add_work(state)
        self.assertEqual(len(state.progress.running), 6)
        state = finish_work(state)

        state = add_work(state)
        self.assertEqual(len(state.progress.running), 6)

    def test_all_per_cluster(self):
        top = make_topology(size=3)
        state = State(top, Strategy.ALL, None, False, True)

        state = add_work(state)
        self.assertEqual(len(state.progress.running), 6)
        state = finish_work(state)

        state = add_work(state)
        self.assertEqual(len(state.progress.running), 6)

    def test_one(self):
        top = make_topology(size=3)
        state = State(top, Strategy.ONE, None, True, True)

        state = add_work(state)
        self.assertEqual(len(state.progress.running), 1)
        state = finish_work(state)

        state = add_work(state)
        self.assertEqual(len(state.progress.running), 1)

    def test_topology_parallel(self):
        top = make_topology(size=12)
        mapping = make_mapping(top)

        state = State(top, Strategy.TOPOLOGY, mapping, True, True)

        laps = 0
        while True:
            state = add_work(state)
            if len(state.progress.running) == 0:
                break
            laps = laps + 1
            self.assertEqual(len(state.progress.running), 16)
            state = finish_work(state)
        self.assertEqual(3, laps)

    def test_topology_serial(self):
        top = make_topology(size=12)
        mapping = make_mapping(top)

        state = State(top, Strategy.TOPOLOGY, mapping, False, False)

        laps = 0
        while True:
            state = add_work(state)
            if len(state.progress.running) == 0:
                break
            laps = laps + 1
            self.assertEqual(len(state.progress.running), 4)
            state = finish_work(state)
        self.assertEqual(12, laps)


def add_work(state):
    """Add more nodes to running until no more nodes can be added"""
    while True:
        h = state.find_next_host()
        if not h:
            break
        state = state.with_running(h)
    return state


def finish_work(state):
    """Move all running nodes to done"""
    state.progress.done = state.progress.done | state.progress.running
    state.progress.running = set()
    return state


if __name__ == '__main__':
    unittest.main()
