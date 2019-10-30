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

"""Argument parsing"""


def _add_common_arguments(parser):
    parser.add_argument('--stop-after', type=int, help='Stop the job after specified number of hosts')
    parser.add_argument('--verbose', '-v', action="count", default=0, help='Increase command output verbosity')
    parser.add_argument('--output-directory', help='Output location for job log')
    parser.add_argument('--ignore-down-nodes', action="store_true", default=False,
                        help='Run the command even if there are down nodes in the cluster')
    parser.add_argument('--enforced-job-id', help='Force the job id value to ease external tracking')


def _add_destination_arguments(parser):
    parser.add_argument('--seed-host', nargs='*',
                        help='One or more hosts to use as seeds for the cluster topology')

    parser.add_argument('--host', nargs='*', help='One or more hosts to run the script on')

    parser.add_argument('--host-file',
                        help='A file containing one or more hosts to run the script on (newline separated)')
    # The amount of time in seconds to sleep after spinning up a new runner.
    # Spinning up too many things at once seems to cause timeouts. Not sure
    #  if it's paramiko being slow or what, but this seems to help.
    parser.add_argument('--ssh-pause-time', type=float, default=0.5,
                        help='The amount of time to pause between establishing new ssh connections to avoid timeouts')
    parser.add_argument('--node-done-pause-time', type=float, default=0.0,
                        help='The amount of time (in seconds) to pause between a node has finished and the next node starting')
    parser.add_argument('--ssh-lib', type=str, default="paramiko",
                        help='SSH library to use for remote connections')
    parser.add_argument('--hosts-variables',
                        help='A JSON file containing host specific variables in the form: {"host1": {"var1": "host1_var1", "var2": "host1_var2"}, "host2": {"var1": "host2_var1", "var2": "host2_var2"}}')


def _add_strategy_arguments(parser):
    parser.add_argument('--max-concurrency', '-j', type=int,
                        help='Maximum number of hosts to run the job on concurrently')

    parser.add_argument('--timeout', type=int, default=None,
                        help='Maximum number of seconds to run on one host before considering the job failed')

    parser.add_argument('--strategy', choices=("one", "topology", "all"), default=None,
                        help='Maximum number of seconds to run on one host before considering the job failed')

    parser.add_argument('--cluster-parallel', action="store_true", default=None, help='Run on all clusters in parallel')
    parser.add_argument('--cluster-serial', dest='cluster_parallel', action="store_false",
                        help='Run on all clusters in serial')
    parser.add_argument('--dc-parallel', action="store_true", default=None,
                        help='Run on all data centers of a cluster in parallel')
    parser.add_argument('--dc-serial', dest='dc_parallel', action="store_false",
                        help='Run on all data centers of a cluster in serial')
    parser.add_argument('--dc-filter', type=str, default=None,
                        help='Only run in hosts belonging to the specified data center')
    parser.add_argument('--key-space', '--keyspace',
                        help='The keyspace to use for endpoint mapping calculation. Uses all keypsaces by default.')


def _add_cstar_arguments_without_command(parser):
    """Argument parsing for case when cstar is called without specifying a command to run"""
    parser.add_argument('--max-job-age', default=7, type=int, help='Maximum age in days of a job to resume')


def add_cstar_arguments(parser, commands, execute_command, execute_continue, execute_cleanup):
    """Argument parsing for case when cstar is called specifying a command to run"""
    subparsers = parser.add_subparsers(dest='sub_command')

    continue_parser = subparsers.add_parser('continue', help='Continue a previously created job (*)')
    continue_parser.set_defaults(func=execute_continue)
    continue_parser.add_argument('job_id')
    continue_parser.add_argument('--retry-failed', action="store_true", default=False,
                        help='Retry failed nodes.')
    _add_common_arguments(continue_parser)
    _add_cstar_arguments_without_command(continue_parser)
    _add_ssh_arguments(continue_parser)
    _add_jmx_auth_arguments(continue_parser)

    cleanup_parser = subparsers.add_parser('cleanup-jobs', help='Cleanup old finished jobs and exit (*)')
    cleanup_parser.set_defaults(func=execute_cleanup)
    _add_common_arguments(cleanup_parser)
    _add_cstar_arguments_without_command(cleanup_parser)
    _add_ssh_arguments(cleanup_parser)
    _add_jmx_auth_arguments(cleanup_parser)

    for (name, command) in commands.items():
        command_parser = subparsers.add_parser(name, help=command.description)
        for arg in command.arguments:
            command_parser.add_argument(arg.option, dest=arg.name, help=arg.description, required=arg.required, default=arg.default)
        _add_destination_arguments(command_parser)
        _add_strategy_arguments(command_parser)
        _add_common_arguments(command_parser)
        _add_ssh_arguments(command_parser)
        _add_jmx_auth_arguments(command_parser)
        command_parser.set_defaults(func=lambda args: execute_command(args), command=command)


def add_cstarpar_arguments(parser):
    """Argument parsing for cstarpar"""
    _add_destination_arguments(parser)
    _add_common_arguments(parser)
    _add_strategy_arguments(parser)
    _add_ssh_arguments(parser)
    _add_jmx_auth_arguments(parser)
    parser.add_argument('command', help='Command to run once for each Cassandra host')

def _add_ssh_arguments(parser):
    parser.add_argument('--ssh-username', help='Username for ssh connection', default=None)
    parser.add_argument('--ssh-password', help='Password for ssh connection', default=None)
    parser.add_argument('--ssh-identity-file', help='Identity file for ssh connection', default=None)

def _add_jmx_auth_arguments(parser):
    parser.add_argument('--jmx-username', help='JMX username', default=None)
