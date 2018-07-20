# Copyright 2018 Spotify AB
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

from cstar.exceptions import FileTooOld, BadFileFormatVersion
import cstar.job
from cstar.output import msg, error


def execute_continue(args):
    with cstar.job.Job() as job:
        try:
            cstar.jobreader.read(job, args.job_id, args.stop_after, max_days=args.max_job_age,
                                 output_directory=args.output_directory)
        except (FileTooOld, BadFileFormatVersion) as e:
            error(e)
        msg("Resuming job", job.job_id)
        msg("Running ", job.command)

        cstar.signalhandler.print_message_and_save_on_sigint(job, job.job_id)

        job.resume()


def add_continue_subparser(subparsers, add_common_arguments, add_cstar_arguments_without_command):
    continue_parser = subparsers.add_parser('continue', help='Continue a previously created job (*)')
    continue_parser.set_defaults(func=execute_continue)
    continue_parser.add_argument('job_id')
    add_common_arguments(continue_parser)
    add_cstar_arguments_without_command(continue_parser)
