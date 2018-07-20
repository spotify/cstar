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

"""Locate and parse cstar commands"""

import json
import os
import re
import functools
from collections import namedtuple
from stat import S_ISREG
from pkg_resources import resource_filename
import uuid

from cstar.exceptions import BadEnvironmentVariable
import cstar.job
import cstar.jobrunner
from cstar.output import msg, error, emph, warn
import cstar.signalhandler
import cstar.strategy

_property_re = re.compile(r"^# C\*\s*([^\s:]+)\s*:\s*(.*)\s*$", re.MULTILINE)
_env_re = re.compile("[^a-zA-Z0-9_]")

Command = namedtuple("Command", "name file strategy cluster_parallel dc_parallel arguments description")


class Argument(object):
    """Represents an argument for a command"""

    def __init__(self, name, option, description, required=False, default=None):
        for name, val in locals().items():
            if name != "self":
                self.__setattr__(name, val)
        if _env_re.search(self.name):
            raise BadEnvironmentVariable(self.name)


def load(command_name):
    """Loads a command"""
    file = _search(command_name)
    with open(file) as f:
        return _parse(command_name, file, f.read())


def _parse(command_name, filename, definition):
    """Parses a command"""
    cluster_parallel = None
    dc_parallel = None
    description = None
    strategy = "topology"
    arguments = []

    truth_lookup = {"true": True, "false": False}

    for line in definition.split('\n'):

        if not line or line[0] != "#":
            break

        match = _property_re.match(line)
        if match:
            name = match.group(1)
            value = match.group(2)
            if name == "cluster-parallel":
                cluster_parallel = truth_lookup[value.lower()]
            elif name == "dc-parallel":
                dc_parallel = truth_lookup[value.lower()]
            elif name == "description":
                description = value
            elif name == "strategy":
                strategy = value
            elif name == "argument":
                arguments.append(Argument(**json.loads(value)))
            else:
                warn("Ignoring unknown property %s while parsing %s" % (name, filename))

    return Command(name=command_name, file=filename,
                   cluster_parallel=cluster_parallel,
                   dc_parallel=dc_parallel,
                   description=description,
                   strategy=strategy,
                   arguments=arguments)


def _search_path():
    return os.path.expanduser('~/.cstar/commands'), '/etc/cstar/commands', resource_filename('cstar.resources', 'commands')


def _stat_is_reg(stat_output):
    return S_ISREG(stat_output.st_mode)


def _search(name, listdir=os.listdir, stat=os.stat, check_is_file=_stat_is_reg):
    """Returns a the filename for a given command"""
    if "/" not in name:
        listing = _list(listdir, stat, check_is_file)
        if name in listing:
            return listing[name]
    if check_is_file(stat(name)):
        return name
    raise FileNotFoundError("Failed to find definition for command %s" % (name,))


def list(listdir=os.listdir, stat=os.stat, check_is_file=_stat_is_reg):
    return _list(listdir, stat, check_is_file).keys()


def get_commands():
    result = {}
    names = list()
    for name in sorted(names):
        sub = load(name)
        result[name] = sub
    return result


def fallback(*args):
    for arg in args:
        if arg is not None:
            return arg


def execute_command(args):
    print(args)
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
            sleep_after_done=args.node_done_pause_time)
        job.run()


@functools.lru_cache(None)
def _list(listdir, stat, check_is_file):
    """Returns a list of the names of all available commands"""
    res = {}
    for dir in _search_path():
        try:
            for filename in listdir(dir):
                full_name = os.path.join(dir, filename)
                try:
                    if not check_is_file(stat(full_name)):
                        continue
                except FileNotFoundError:
                    continue
                if filename.endswith("~") or filename.startswith("#"):
                    continue

                if "." in filename:
                    prefix = re.sub(r"\..*", "", filename)
                else:
                    prefix = filename
                if prefix not in res:
                    res[prefix] = full_name
        except FileNotFoundError:
            pass
    return res
