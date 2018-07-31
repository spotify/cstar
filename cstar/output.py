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

import sys
import curses
import traceback

_print_debug = False
_print_info = False
_last_message_was_topology = False
_last_topology_lines = None
_term_setup = False

CURSOR_UP = 'CURSOR_UP'
CLEAR_LINE = 'CLEAR_LINE'
SET_BOLD = 'SET_BOLD'
SET_NORMAL = 'SET_NORMAL'
CODES = {CURSOR_UP: 'cuu1', CLEAR_LINE: 'el', SET_BOLD: 'bold', SET_NORMAL: 'sgr0'}


def get_termstr(action):
    global _term_setup
    if not _term_setup:
        curses.setupterm()
        _term_setup = True
    return curses.tigetstr(CODES[action]).decode('utf-8')


def configure(verbosity):
    global _print_debug, _print_info
    _print_debug = verbosity >= 2
    _print_info = verbosity >= 1


def msg(*args, **kwargs):
    global _last_message_was_topology
    _last_message_was_topology = False
    print(*args, **kwargs)


def print_topology(top):
    global _last_message_was_topology, _last_topology_lines
    if _last_message_was_topology:
        top = (get_termstr(CLEAR_LINE) + get_termstr(CURSOR_UP)) * _last_topology_lines + get_termstr(CLEAR_LINE) + top

    print(top)
    _last_topology_lines = top.count('\n') + 1
    _last_message_was_topology = True


def info(*args, **kwargs):
    global _last_message_was_topology
    if _print_info:
        _last_message_was_topology = False
        print(*args, **kwargs)


def err(*args, **kwargs):
    global _last_message_was_topology
    _last_message_was_topology = False
    print(*args, file=sys.stderr, **kwargs)


def debug(*args, **kwargs):
    global _last_message_was_topology
    if _print_debug:
        _last_message_was_topology = False
        print(*args, file=sys.stderr, **kwargs)


def warn(*args, **kwargs):
    global _last_message_was_topology
    _last_message_was_topology = False
    print(*args, file=sys.stderr, **kwargs)


def emph(msg):
    return get_termstr(SET_BOLD) + msg + get_termstr(SET_NORMAL)


def error(*args, code=1, print_traceback=True):
    if print_traceback:
        traceback.print_exc()
    err(emph("Error:"), *args)
    sys.exit(code)
