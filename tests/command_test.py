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

import os
import unittest
from pkg_resources import resource_filename

import cstar.command

example_dir_data = {
    os.path.expanduser("~/.cstar/commands"): ["foo.py", "bar.txt", "qux.sh~"],
    "/etc/cstar/commands": ["bar.sh", "baz.sh", "qux.sh"],
    resource_filename('cstar.resources', 'commands'): []}

example_job = """#! /bin/bash
# C* cluster-parallel: false
# C* dc-parallel: true
# C* strategy: topology
# C* description: Upgrade one or more clusters by switching to a different puppet branch
# C* argument: {"option":"--snapshot-name", "name":"SNAPSHOT_NAME", "description":"Name of pre-upgrade snapshot", "default":"preupgrade"}
# C* argument: {"option":"--puppet-branch", "name":"PUPPET_BRANCH", "description":"Name of puppet branch to switch to", "required":true}
#C* argument: {"option":"--bork", "name":"BORK", "description":"Bork bork bork"}
# argument: {"option":"--bork2", "name":"BORK2", "description":"Bork bork bork"}
# C argument: {"option":"--bork3", "name":"BORK3", "description":"Bork bork bork"}
# C** argument: {"option":"--bork4", "name":"BORK4", "description":"Bork bork bork"}

echo hopp $SNAPSHOT_NAME
"""


class CommandTest(unittest.TestCase):

    def test_list_dedup(self):
        res = cstar.command.list(listdir=lambda x: example_dir_data[x], stat=lambda x: 0, check_is_file=lambda x: True)
        self.assertEqual(sorted(res), sorted(("foo", "bar", "baz", "qux")))

    def test_search_correct_order(self):
        res = cstar.command._search("bar", listdir=lambda x: example_dir_data[x], stat=lambda x: 0, check_is_file=lambda x: True)
        self.assertEqual(res, os.path.expanduser("~/.cstar/commands/bar.txt"))

    def test_search_skips_backups(self):
        res = cstar.command._search("qux", listdir=lambda x: example_dir_data[x], stat=lambda x: 0, check_is_file=lambda x: True)
        self.assertEqual(res, "/etc/cstar/commands/qux.sh")

    def test_parse(self):
        command = cstar.command._parse("test", "foo/test.foo", example_job)

        self.assertEqual(command.name, "test")
        self.assertEqual(command.file, "foo/test.foo")
        self.assertEqual(command.strategy, "topology")
        self.assertEqual(command.dc_parallel, True)
        self.assertEqual(command.cluster_parallel, False)

        self.assertEqual(len(command.arguments), 2)
        self.assertEqual(command.arguments[0].option, "--snapshot-name")
        self.assertEqual(command.arguments[0].name, "SNAPSHOT_NAME")
        self.assertEqual(command.arguments[0].default, "preupgrade")
        self.assertEqual(command.arguments[0].required, False)


if __name__ == '__main__':
    unittest.main()
