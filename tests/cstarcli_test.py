# Copyright 2020 Datastax
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

import argparse
import copy
import unittest

import cstar.args
import cstar.cstarcli

# noop stub
def execute_command(args):
    return

# noop stub
def execute_continue(args):
    return

# noop stub
def execute_cleanup(args):
    return

class CstarcliTest(unittest.TestCase):

    DEFAULT_RUN_NAMESPACE_VALUES = {
        'COMMAND': 'echo',
        'cluster_parallel': None,
        'dc_filter': None,
        'dc_parallel': None,
        'enforced_job_id': None,
        'host': None,
        'host_file': None,
        'ignore_down_nodes': False,
        'jmx_username': None,
        'key_space': None,
        'max_concurrency': None,
        'node_done_pause_time': 0.0,
        'output_directory': None,
        'seed_host': None,
        'ssh_identity_file': None,
        'ssh_lib': 'paramiko',
        'ssh_password': None,
        'ssh_pause_time': 0.5,
        'ssh_username': None,
        'stop_after': None,
        'strategy': None,
        'strategy_all': False,
        'strategy_one': False,
        'strategy_one_per_dc': False,
        'strategy_topology': False,
        'strategy_topology_per_dc': False,
        'sub_command': 'run',
        'timeout': None,
        'verbose': 0
    }

    def assert_args(self, args, expected):
        for k in expected:
            self.assertEqual(getattr(args, k), expected[k], f"{k} does not have expected value")

    def test_empty(self):

        parser = argparse.ArgumentParser(prog='cstar', formatter_class=argparse.RawDescriptionHelpFormatter)
        cstar.args.add_cstar_arguments(parser, cstar.cstarcli.get_commands(), execute_command, execute_continue, execute_cleanup)
        namespace = parser.parse_args([])

        self.assertEqual(namespace.sub_command, None)

    def test_cleanup_jobs(self):

        parser = argparse.ArgumentParser(prog='cstar', formatter_class=argparse.RawDescriptionHelpFormatter)
        cstar.args.add_cstar_arguments(parser, cstar.cstarcli.get_commands(), execute_command, execute_continue, execute_cleanup)
        namespace = parser.parse_args(["cleanup-jobs"])

        self.assertEqual(namespace.enforced_job_id, None)
        self.assertEqual(namespace.ignore_down_nodes, False)
        self.assertEqual(namespace.jmx_username, None)
        self.assertEqual(namespace.max_job_age, 7)
        self.assertEqual(namespace.output_directory, None)
        self.assertEqual(namespace.ssh_identity_file, None)
        self.assertEqual(namespace.ssh_username, None)
        self.assertEqual(namespace.ssh_password, None)
        self.assertEqual(namespace.stop_after, None)
        self.assertEqual(namespace.sub_command, 'cleanup-jobs')
        self.assertEqual(namespace.verbose, 0)

    def test_run(self):

        parser = argparse.ArgumentParser(prog='cstar', formatter_class=argparse.RawDescriptionHelpFormatter)
        cstar.args.add_cstar_arguments(parser, cstar.cstarcli.get_commands(), execute_command, execute_continue, execute_cleanup)
        args = parser.parse_args(["run", "--command", "echo"])

        self.assert_args(args, self.DEFAULT_RUN_NAMESPACE_VALUES)
        self.assertEqual(args.command.strategy, 'topology')

    def test_run_strategy_one(self):

        parser = argparse.ArgumentParser(prog='cstar', formatter_class=argparse.RawDescriptionHelpFormatter)
        cstar.args.add_cstar_arguments(parser, cstar.cstarcli.get_commands(), execute_command, execute_continue, execute_cleanup)
        args = parser.parse_args(["run", "--command", "echo", "--strategy=one"])

        expected = self.DEFAULT_RUN_NAMESPACE_VALUES.copy()
        expected.update({'strategy': 'one'})
        self.assert_args(args, expected)
        self.assertEqual(args.command.strategy, 'topology')

        computed_args = cstar.cstarcli.args_from_strategy_shortcut(copy.deepcopy(args))

        self.assert_args(computed_args, expected)

        self.assertEqual(
            cstar.strategy.parse(cstar.cstarcli.fallback(computed_args.strategy, args.strategy, "funk")),
            cstar.strategy.Strategy.ONE)


    def test_run_strategy_one__short(self):

        parser = argparse.ArgumentParser(prog='cstar', formatter_class=argparse.RawDescriptionHelpFormatter)
        cstar.args.add_cstar_arguments(parser, cstar.cstarcli.get_commands(), execute_command, execute_continue, execute_cleanup)
        args = parser.parse_args(["run", "--command", "echo", "--one"])

        expected = self.DEFAULT_RUN_NAMESPACE_VALUES.copy()
        expected.update({'strategy_one': True})
        self.assert_args(args, expected)
        self.assertEqual(args.command.strategy, 'topology')

        computed_args = cstar.cstarcli.args_from_strategy_shortcut(copy.deepcopy(args))

        expected.update({'dc_parallel': False, 'strategy': 'one'})
        self.assert_args(computed_args, expected)

        self.assertEqual(
            cstar.strategy.parse(cstar.cstarcli.fallback(computed_args.strategy, args.strategy, "funk")),
            cstar.strategy.Strategy.ONE)


    def test_run_stratgy_one_per_dc(self):

        parser = argparse.ArgumentParser(prog='cstar', formatter_class=argparse.RawDescriptionHelpFormatter)
        cstar.args.add_cstar_arguments(parser, cstar.cstarcli.get_commands(), execute_command, execute_continue, execute_cleanup)
        args = parser.parse_args(["run", "--command", "echo", "--strategy=one", "--dc-parallel"])

        expected = self.DEFAULT_RUN_NAMESPACE_VALUES.copy()
        expected.update({'dc_parallel': True, 'strategy': 'one'})
        self.assert_args(args, expected)
        self.assertEqual(args.command.strategy, 'topology')

        computed_args = cstar.cstarcli.args_from_strategy_shortcut(copy.deepcopy(args))

        self.assert_args(computed_args, expected)

        self.assertEqual(
            cstar.strategy.parse(cstar.cstarcli.fallback(computed_args.strategy, args.strategy, "funk")),
            cstar.strategy.Strategy.ONE)


    def test_run_stratgy_one_per_dc__short(self):

        parser = argparse.ArgumentParser(prog='cstar', formatter_class=argparse.RawDescriptionHelpFormatter)
        cstar.args.add_cstar_arguments(parser, cstar.cstarcli.get_commands(), execute_command, execute_continue, execute_cleanup)
        args = parser.parse_args(["run", "--command", "echo", "--one-per-dc"])

        expected = self.DEFAULT_RUN_NAMESPACE_VALUES.copy()
        expected.update({'strategy_one_per_dc': True})
        self.assert_args(args, expected)
        self.assertEqual(args.command.strategy, 'topology')

        computed_args = cstar.cstarcli.args_from_strategy_shortcut(copy.deepcopy(args))

        expected.update({'dc_parallel': True, 'strategy': 'one'})
        self.assert_args(computed_args, expected)

        self.assertEqual(
            cstar.strategy.parse(cstar.cstarcli.fallback(computed_args.strategy, args.strategy, "funk")),
            cstar.strategy.Strategy.ONE)


    def test_run_strategy_topology(self):

        parser = argparse.ArgumentParser(prog='cstar', formatter_class=argparse.RawDescriptionHelpFormatter)
        cstar.args.add_cstar_arguments(parser, cstar.cstarcli.get_commands(), execute_command, execute_continue, execute_cleanup)
        args = parser.parse_args(["run", "--command", "echo", "--strategy=topology"])

        expected = self.DEFAULT_RUN_NAMESPACE_VALUES.copy()
        expected.update({'strategy': 'topology'})
        self.assert_args(args, expected)
        self.assertEqual(args.command.strategy, 'topology')

        computed_args = cstar.cstarcli.args_from_strategy_shortcut(copy.deepcopy(args))

        self.assert_args(computed_args, expected)

        self.assertEqual(
            cstar.strategy.parse(cstar.cstarcli.fallback(computed_args.strategy, args.strategy, "funk")),
            cstar.strategy.Strategy.TOPOLOGY)


    def test_run_strategy_topology__short(self):

        parser = argparse.ArgumentParser(prog='cstar', formatter_class=argparse.RawDescriptionHelpFormatter)
        cstar.args.add_cstar_arguments(parser, cstar.cstarcli.get_commands(), execute_command, execute_continue, execute_cleanup)
        args = parser.parse_args(["run", "--command", "echo", "--topology"])

        expected = self.DEFAULT_RUN_NAMESPACE_VALUES.copy()
        expected.update({'strategy_topology': True})
        self.assert_args(args, expected)
        self.assertEqual(args.command.strategy, 'topology')

        computed_args = cstar.cstarcli.args_from_strategy_shortcut(copy.deepcopy(args))

        expected.update({'dc_parallel': False, 'strategy': 'topology'})
        self.assert_args(computed_args, expected)

        self.assertEqual(
            cstar.strategy.parse(cstar.cstarcli.fallback(computed_args.strategy, args.strategy, "funk")),
            cstar.strategy.Strategy.TOPOLOGY)


    def test_run_stratgy_topology_per_dc(self):

        parser = argparse.ArgumentParser(prog='cstar', formatter_class=argparse.RawDescriptionHelpFormatter)
        cstar.args.add_cstar_arguments(parser, cstar.cstarcli.get_commands(), execute_command, execute_continue, execute_cleanup)
        args = parser.parse_args(["run", "--command", "echo", "--strategy=topology", "--dc-parallel"])

        expected = self.DEFAULT_RUN_NAMESPACE_VALUES.copy()
        expected.update({'dc_parallel': True, 'strategy': 'topology'})
        self.assert_args(args, expected)
        self.assertEqual(args.command.strategy, 'topology')

        computed_args = cstar.cstarcli.args_from_strategy_shortcut(copy.deepcopy(args))

        self.assert_args(computed_args, expected)

        self.assertEqual(
            cstar.strategy.parse(cstar.cstarcli.fallback(computed_args.strategy, args.strategy, "funk")),
            cstar.strategy.Strategy.TOPOLOGY)


    def test_run_stratgy_topology_per_dc__short(self):

        parser = argparse.ArgumentParser(prog='cstar', formatter_class=argparse.RawDescriptionHelpFormatter)
        cstar.args.add_cstar_arguments(parser, cstar.cstarcli.get_commands(), execute_command, execute_continue, execute_cleanup)
        args = parser.parse_args(["run", "--command", "echo", "--topology-per-dc"])

        expected = self.DEFAULT_RUN_NAMESPACE_VALUES.copy()
        expected.update({'strategy_topology_per_dc': True})
        self.assert_args(args, expected)
        self.assertEqual(args.command.strategy, 'topology')

        computed_args = cstar.cstarcli.args_from_strategy_shortcut(copy.deepcopy(args))

        expected.update({'dc_parallel': True, 'strategy': 'topology'})
        self.assert_args(computed_args, expected)

        self.assertEqual(
            cstar.strategy.parse(cstar.cstarcli.fallback(computed_args.strategy, args.strategy, "funk")),
            cstar.strategy.Strategy.TOPOLOGY)

    def test_run_strategy_all(self):

        parser = argparse.ArgumentParser(prog='cstar', formatter_class=argparse.RawDescriptionHelpFormatter)
        cstar.args.add_cstar_arguments(parser, cstar.cstarcli.get_commands(), execute_command, execute_continue, execute_cleanup)
        args = parser.parse_args(["run", "--command", "echo", "--strategy=all"])

        expected = self.DEFAULT_RUN_NAMESPACE_VALUES.copy()
        expected.update({'strategy': 'all'})
        self.assert_args(args, expected)
        self.assertEqual(args.command.strategy, 'topology')

        computed_args = cstar.cstarcli.args_from_strategy_shortcut(copy.deepcopy(args))

        self.assert_args(computed_args, expected)

        self.assertEqual(
            cstar.strategy.parse(cstar.cstarcli.fallback(computed_args.strategy, args.strategy, "funk")),
            cstar.strategy.Strategy.ALL)


    def test_run_strategy_all__short(self):

        parser = argparse.ArgumentParser(prog='cstar', formatter_class=argparse.RawDescriptionHelpFormatter)
        cstar.args.add_cstar_arguments(parser, cstar.cstarcli.get_commands(), execute_command, execute_continue, execute_cleanup)
        args = parser.parse_args(["run", "--command", "echo", "--all"])

        expected = self.DEFAULT_RUN_NAMESPACE_VALUES.copy()
        expected.update({'strategy_all': True})
        self.assert_args(args, expected)
        self.assertEqual(args.command.strategy, 'topology')

        computed_args = cstar.cstarcli.args_from_strategy_shortcut(copy.deepcopy(args))

        expected.update({'dc_parallel': True, 'strategy': 'all'})
        self.assert_args(computed_args, expected)

        self.assertEqual(
            cstar.strategy.parse(cstar.cstarcli.fallback(computed_args.strategy, args.strategy, "funk")),
            cstar.strategy.Strategy.ALL)


    def test_run_stratgy_all(self):

        parser = argparse.ArgumentParser(prog='cstar', formatter_class=argparse.RawDescriptionHelpFormatter)
        cstar.args.add_cstar_arguments(parser, cstar.cstarcli.get_commands(), execute_command, execute_continue, execute_cleanup)
        args = parser.parse_args(["run", "--command", "echo", "--strategy=all", "--dc-parallel"])

        expected = self.DEFAULT_RUN_NAMESPACE_VALUES.copy()
        expected.update({'dc_parallel': True, 'strategy': 'all'})
        self.assert_args(args, expected)
        self.assertEqual(args.command.strategy, 'topology')

        computed_args = cstar.cstarcli.args_from_strategy_shortcut(copy.deepcopy(args))

        self.assert_args(computed_args, expected)

        self.assertEqual(
            cstar.strategy.parse(cstar.cstarcli.fallback(computed_args.strategy, args.strategy, "funk")),
            cstar.strategy.Strategy.ALL)



    def test_continue(self):

        parser = argparse.ArgumentParser(prog='cstar', formatter_class=argparse.RawDescriptionHelpFormatter)
        cstar.args.add_cstar_arguments(parser, cstar.cstarcli.get_commands(), execute_command, execute_continue, execute_cleanup)
        namespace = parser.parse_args(["continue", "1"])

        self.assertEqual(namespace.enforced_job_id, None)
        self.assertEqual(namespace.ignore_down_nodes, False)
        self.assertEqual(namespace.jmx_username, None)
        self.assertEqual(namespace.job_id, '1')
        self.assertEqual(namespace.max_job_age, 7)
        self.assertEqual(namespace.output_directory, None)
        self.assertEqual(namespace.ssh_identity_file, None)
        self.assertEqual(namespace.ssh_username, None)
        self.assertEqual(namespace.ssh_password, None)
        self.assertEqual(namespace.stop_after, None)
        self.assertEqual(namespace.sub_command, 'continue')
        self.assertEqual(namespace.verbose, 0)

if __name__ == '__main__':
    unittest.main()
