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

"""Parses the output of 'nodetool describering' and returns a simple AST

Standard parser implemented in two phases (tokenization and parsing).
The parser is a rather simple recursive descent affair.

BNF grammar:

root_expressions ::= root_expression '\n' root_expressions | root_expression

root_expression ::= identifiers ':' identifiers_or_block

identifiers_or_block ::= identifiers | BEGIN expressions END

identifiers ::= identifier identifiers | identifier

expressions ::= expression '\n' expressions | expression

expression ::= call | list | identifier

call ::= identifier '(' opt_arguments ')'

opt_arguments ::= | arguments

arguments ::= argument ',' arguments | argument

argument ::= identifier ':' expression

list ::= '[' opt_expressions ']'

opt_expressions ::= | expressions

expressions ::= expression ',' expressions | expression
"""

from collections import namedtuple
from cstar.exceptions import ParseException
import re

Call = namedtuple("Call", "name arguments")


class Symbol(object):
    def __init__(self, s, pos):
        self.val = s
        self.offset = pos


class Identifier(object):
    def __init__(self, s, pos):
        self.val = s
        self.offset = pos


def parse(text):
    lines = list(filter(lambda x: x, [_parse_line(line) for line in text.split('\n')]))
    return lines


def _parse_line(line):
    tokens = list(reversed(_tokenize(line)))
    if not tokens:
        return None

    if len(tokens) >= 2 and type(tokens[-1]) is Identifier and tokens[-2].val == '(':
        return _parse_call(line, tokens)

    return None


def _parse_call(line, tokens):
    name = tokens.pop()
    res = {}

    if not type(name) is Identifier:
        raise ParseException(line, name.offset, "Bad identifier")

    paran = tokens.pop()
    if paran.val != '(':
        raise ParseException(line, paran.offset, "Expected '('")

    while True:
        _parse_argument(line, tokens, res)
        if tokens[-1].val == ',':
            tokens.pop()
        else:
            break
    if tokens[-1].val != ')':
        raise ParseException(line, tokens[-1].offset, "Expected a ')'")
    tokens.pop()
    return Call(name.val, res)


def _parse_argument(line, tokens, res):
    if not tokens:
        raise ParseException(line, len(line), "Premature end of line")

    name = tokens.pop()
    if not type(name) is Identifier:
        raise ParseException(line, name.offset, "Expected an identifier, not a symbol")

    sym = tokens.pop()
    if sym.val != ':':
        raise ParseException(line, sym.offset, "Expected ':'")

    value = _parse_expression(line, tokens)
    res[name.val] = value


def _parse_expression(line, tokens):
    if tokens[-1].val == '[':
        return _parse_describe_line_list(line, tokens)

    if type(tokens[-1]) is Identifier:
        if (len(tokens) >= 2) and (tokens[-2].val == '('):
            return _parse_call(line, tokens)
        else:
            return tokens.pop().val
    raise ParseException(line, tokens[-1].offset, "Expected identifier, call or list, got '%s'")


def _parse_describe_line_list(line, tokens):
    tokens.pop()
    res = []
    if tokens[-1].val != ']':
        while True:
            res.append(_parse_expression(line, tokens))
            if tokens[-1].val == ',':
                tokens.pop()
            elif tokens[-1].val == ']':
                break
            else:
                raise ParseException(line, tokens[-1].offset, "Expected ',' or ']', got '%s' in line %s")

    tokens.pop()
    return res


def _tokenize(original_line, offset=0):
    line = original_line.lstrip()
    offset += len(original_line) - len(line)
    if not line:
        return ()
    if line[0] in {'(', ')', '[', ']', ',', ':'}:
        return (Symbol(line[0], offset),) + _tokenize(line[1:], offset + 1)
    if line[0].isalnum() or line[0] in {'-'}:
        tok = ""
        while True:
            tok += line[0]
            line = line[1:]
            if not line:
                break
            if not (line[0].isalnum() or line[0] in {'.', '_', '-'}):
                break

        if tok.isnumeric() or (tok[0] == '-' and tok[1:].isnumeric()):
            identifier = Identifier(int(tok), offset)
        else:
            identifier = Identifier(tok, offset)
        return (identifier,) + _tokenize(line, offset + len(tok))
    raise ParseException(line, offset, "Could not parse string")

def convert_describering_to_range_mapping(tokens):
    range_mapping = []
    for token in tokens:
        range = {}
        range["startToken"] = str(token.arguments['start_token'])
        range["endToken"] = str(token.arguments['end_token'])
        range["endpoints"] = token.arguments['endpoints']
        range_mapping.append(range)
    
    return range_mapping
