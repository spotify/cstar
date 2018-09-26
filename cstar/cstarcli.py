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
import sys
import uuid

import cstar.args
import cstar.command
import cstar.strategy
import cstar.job
import cstar.remote
import cstar.jobreader
from cstar.output import msg, error, emph
import cstar.output
from cstar.exceptions import BadFileFormatVersion, FileTooOld,NoHostsSpecified
import cstar.signalhandler
import cstar.jobrunner
import cstar.cleanup


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

    hosts = None

    if args.host_file:
        with open(args.host_file) as f:
            hosts = f.readlines()

    if args.host:
        hosts = args.host

    with cstar.job.Job() as job:
        env = dict((arg.name, getattr(args, arg.name)) for arg in command.arguments)
        job_id = str(uuid.uuid4())
        msg("Job id is", emph(job_id))
        msg("Running", command.file)

        cstar.signalhandler.print_message_and_save_on_sigint(job, job_id)

        job.setup(
            hosts=hosts,
            seeds=args.seed_host,
            command=command.file,
            job_id=job_id,
            strategy=cstar.strategy.parse(fallback(args.strategy, command.strategy, "topology")),
            cluster_parallel=fallback(args.cluster_parallel, command.cluster_parallel, False),
            dc_parallel=fallback(args.dc_parallel, command.dc_parallel, False),
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
            ssh_username = args.ssh_username,
            ssh_password = args.ssh_password,
            ssh_identity_file = args.ssh_identity_file,
            ssh_lib=args.ssh_lib)
        job.run()


def main():
    parser = argparse.ArgumentParser(
        description='cstar', prog='cstar', formatter_class=argparse.RawDescriptionHelpFormatter, epilog="(*): Special built-in cstar job management action")
    cstar.args.add_cstar_arguments(parser, get_commands(), execute_command, execute_continue, execute_cleanup)

    #no input
    if len(sys.argv) <= 1:
        parser.print_help(sys.stdout)
        return

    namespace = parser.parse_args(sys.argv[1:])
    cstar.output.configure(namespace.verbose)
    namespace.func(namespace)


if __name__ == '__main__':
    main()
