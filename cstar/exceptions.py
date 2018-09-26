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


class BadSSHHost(Exception):
    pass


class FailedExecution(Exception):
    pass


class BadEnvironmentVariable(Exception):
    pass

class BadArgument(Exception):
    pass

class NoHostsSpecified(Exception):
    pass


class HostIsDown(Exception):
    pass


class UnknownHost(Exception):
    def __str__(self):
        return "Unknown host: {}".format(self.args[0])


class BadFileFormatVersion(Exception):
    pass


class FileTooOld(Exception):
    pass


class NoDefaultKeyspace(Exception):
    pass


class ParseException(Exception):
    def __init__(self, line, offset, error):
        msg = line + "\n" + (" " * offset) + "^" + "\n" + error
        super(ParseException, self).__init__(msg)
