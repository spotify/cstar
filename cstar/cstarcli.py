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

"""Argument parsing and related plumbing for the cstar command"""

import argparse
import copy
import getpass
import sys
import uuid

import cstar.args
import cstar.cleanup
import cstar.command
import cstar.job
import cstar.jobreader
import cstar.jobrunner
import cstar.output
import cstar.signalhandler
import cstar.strategy
from cstar.exceptions import BadArgument
from cstar.exceptions import BadFileFormatVersion, FileTooOld
from cstar.output import msg, error, emph


def fallback(*args):
    for arg in args:
        if arg is not None:
            return arg


def get_commands():
    result = {}
    names = cstar.command.list()
    for name in sorted(names):
        sub = cstar.command.load(name)
        result[name] = sub
    return result


def execute_continue(args):
    msg("Retry : ", args.retry_failed)
    with cstar.job.Job() as job:
        try:
            cstar.jobreader.read(job, args.job_id, args.stop_after, max_days=args.max_job_age,
                                 output_directory=args.output_directory, retry=args.retry_failed)
        except (FileTooOld, BadFileFormatVersion) as e:
            error(e)
        msg("Resuming job", job.job_id)

        if job.jmx_username:
            job.jmx_password = getpass.getpass(prompt="JMX Password ")

        msg("Running ", job.command)

        cstar.signalhandler.print_message_and_save_on_sigint(job, job.job_id)

        job.resume()


def execute_cleanup(args):
    msg('Cleaning up old jobs')
    cstar.cleanup.cleanup(args.max_job_age)


def execute_command(args):
    cstar.output.debug(args)
    command = args.command
    if bool(args.seed_host) + bool(args.host) + bool(args.host_file) != 1:
        error("Exactly one of --seed-host, --host and --host-file must be used", print_traceback=False)

    computed_args = args_from_strategy_shortcut(copy.deepcopy(args))

    hosts = None

    if args.host_file:
        with open(args.host_file) as f:
            hosts = f.read().splitlines()

    if args.host:
        hosts = args.host

    with cstar.job.Job() as job:
        env = dict((arg.name, getattr(args, arg.name)) for arg in command.arguments)
        if bool(args.enforced_job_id) == 1:
            job_id = args.enforced_job_id
            if not(validate_uuid4(job_id)):
                raise BadArgument("Job id is not a valid UUID v4 value.")
        else:
            job_id = str(uuid.uuid4())
        msg("Job id is", emph(job_id))
        msg("Running", command.file)

        cstar.signalhandler.print_message_and_save_on_sigint(job, job_id)

        job.setup(
            hosts=hosts,
            seeds=args.seed_host,
            command=command.file,
            job_id=job_id,
            strategy=cstar.strategy.parse(fallback(computed_args.strategy, args.strategy, command.strategy, "topology")),
            cluster_parallel=fallback(args.cluster_parallel, command.cluster_parallel, False),
            dc_parallel=fallback(computed_args.dc_parallel, args.dc_parallel, command.dc_parallel, False),
            max_concurrency=args.max_concurrency,
            timeout=args.timeout,
            env=env,
            stop_after=args.stop_after,
            job_runner=cstar.jobrunner.RemoteJobRunner,
            key_space=args.key_space,
            output_directory=args.output_directory,
            ignore_down_nodes=args.ignore_down_nodes,
            dc_filter=args.dc_filter,
            sleep_on_new_runner=args.ssh_pause_time,
            sleep_after_done=args.node_done_pause_time,
            ssh_username=args.ssh_username,
            ssh_password=args.ssh_password,
            ssh_identity_file=args.ssh_identity_file,
            ssh_lib=args.ssh_lib,
            jmx_username=args.jmx_username,
            jmx_password=args.jmx_password,
            resolve_hostnames=args.resolve_hostnames)
        job.run()

def validate_uuid4(uuid_string):
    try:
        val = uuid.UUID(uuid_string)
    except ValueError:
        return False

    return str(val) == uuid_string

def args_from_strategy_shortcut(args):
    """Returns args
    Takes command options and a strategy shortcut in:
    {--one, --one-per-dc, --topology, --topology-per-dc, --all}
    Returns options (args) with --strategy and --dc-parallel set accordingly
    """

    strategy_shortcuts = {
                            "--one": int(args.strategy_one),
                            "--one-per-dc": int(args.strategy_one_per_dc),
                            "--topology": int(args.strategy_topology),
                            "--topology-per-dc": int(args.strategy_topology_per_dc),
                            "--all": int(args.strategy_all)}

    total_shortcuts_used = sum(strategy_shortcuts.values())

    if total_shortcuts_used > 1:
        error("Exactly one of {} must be used".format(', '.join(strategy_shortcuts.keys())), print_traceback=False)

    if total_shortcuts_used == 1:
        if args.strategy is not None:
            error("--strategy option is not compatible with {} options that "
                  "defines the stratgy already".format(', '.join(strategy_shortcuts.keys())), print_traceback=False)
        elif args.dc_parallel is not None:
            error("--dc-parallel option is not compatible with {} options "
                  "that defines the stratgy already".format(', '.join(strategy_shortcuts.keys())), print_traceback=False)
        else:
            # Identify the strategy_?* option used
            for (k, v) in strategy_shortcuts.items():
                if v == 1:
                    # Set corresponding option
                    if k == "--one":
                        args.strategy = "one"
                        args.dc_parallel = False
                    elif k == "--one-per-dc":
                        args.strategy = "one"
                        args.dc_parallel = True
                    elif k == "--topology":
                        args.strategy = "topology"
                        args.dc_parallel = False
                    elif k == "--topology-per-dc":
                        args.strategy = "topology"
                        args.dc_parallel = True
                    elif k == "--all":
                        args.strategy = "all"
                        args.dc_parallel = True
                    else:
                        error("Unknown shortcut option: {}".format(k))

    return args



def main():
    parser = argparse.ArgumentParser(
        description='cstar', prog='cstar', formatter_class=argparse.RawDescriptionHelpFormatter, epilog="(*): Special built-in cstar job management action")
    cstar.args.add_cstar_arguments(parser, get_commands(), execute_command, execute_continue, execute_cleanup)

    #no input
    if len(sys.argv) <= 1:
        parser.print_help(sys.stdout)
        return

    namespace = parser.parse_args(sys.argv[1:])

    if namespace.jmx_username:
        namespace.jmx_password = getpass.getpass(prompt="JMX Password ")
    else:
        namespace.jmx_password = None

    cstar.output.configure(namespace.verbose)
    namespace.func(namespace)


if __name__ == '__main__':
    main()
