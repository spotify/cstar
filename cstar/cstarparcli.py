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

"""Argument parsing and related plumbing for the cstarpar command"""

import argparse
import sys
import uuid

import cstar.args
import cstar.command
import cstar.strategy
import cstar.job
import cstar.remote
from cstar.output import msg, error, emph
import cstar.output
import cstar.signalhandler
from cstar.exceptions import NoHostsSpecified


def fallback(*args):
    for arg in args:
        if arg is not None:
            return arg


def parse_job_mode():
    desc = '''cstarpar - A shell tool for executing jobs in parallel. Unlike cstar, cstarpar does not run commands
    remotely, it executes a script locally once for each Cassandra host.'''
    parser = argparse.ArgumentParser(description=desc,
                                     prog="cstarpar")

    cstar.args.add_cstarpar_arguments(parser)
    return parser.parse_args()


def main():
    namespace = parse_job_mode()

    if bool(namespace.seed_host) + bool(namespace.host) + bool(namespace.host_file) != 1:
        error("Exactly one of --seed-host, --host and --host-file must be used", print_traceback=False)

    hosts = None

    if namespace.host_file:
        with open(namespace.host_file) as f:
            hosts = f.readlines()

    if namespace.host:
        hosts = namespace.host

    cstar.output.configure(namespace.verbose)

    with cstar.job.Job() as job:
        env = {}
        job_id = str(uuid.uuid4())
        msg("Job id is", emph(job_id))

        cstar.signalhandler.print_message_and_save_on_sigint(job, job_id)

        job.setup(
            hosts=hosts,
            seeds=namespace.seed_host,
            command=namespace.command,
            job_id=job_id,
            strategy=cstar.strategy.parse(fallback(namespace.strategy, "topology")),
            cluster_parallel=fallback(namespace.cluster_parallel, False),
            dc_parallel=fallback(namespace.dc_parallel, False),
            max_concurrency=namespace.max_concurrency,
            timeout=namespace.timeout,
            env=env,
            stop_after=namespace.stop_after,
            job_runner=cstar.jobrunner.LocalJobRunner,
            key_space=namespace.key_space,
            output_directory=namespace.output_directory,
            ignore_down_nodes=False,
            dc_filter=namespace.dc_filter,
            sleep_on_new_runner=namespace.ssh_pause_time,
            sleep_after_done=namespace.node_done_pause_time,
            ssh_username = namespace.ssh_username,
            ssh_password = namespace.ssh_password,
            ssh_identity_file = namespace.ssh_identity_file,
            ssh_lib=namespace.ssh_lib)
        job.run()



if __name__ == '__main__':
    main()
