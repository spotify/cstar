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

import sys

import cstar.args
import cstar.command
import cstar.output


def main():
    parser = cstar.args.get_cstar_parser(cstar.command.get_commands())

    #no input
    if len(sys.argv) <= 1:
        parser.print_help(sys.stdout)
        return

    namespace = parser.parse_args(sys.argv[1:])
    cstar.output.configure(namespace.verbose)
    namespace.func(namespace)


if __name__ == '__main__':
    main()
