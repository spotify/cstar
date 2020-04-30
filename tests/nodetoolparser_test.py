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

import cstar.nodetoolparser
import cstar.nodetoolparser.describering
import cstar.nodetoolparser.status
import cstar.exceptions

import unittest

BAD_SYNTAX = ("foo(3)", "foo([7)", "foo(3,", "foo(", "foo([1 1])", "foo([a:b])", "foo(bar [])")


class NodetoolParserTest(unittest.TestCase):

    def test_parse_describecluster(self):
        with open("tests/resources/describecluster-2.0.txt", 'r') as f:
            nodetool_output = f.read()
            (name, schema_version) = cstar.nodetoolparser.parse_describe_cluster(nodetool_output)
            self.assertEqual(name, "c2.0.13")
            self.assertEqual(schema_version, "08428c1c-086b-322c-ae61-988129270360")
        with open("tests/resources/describecluster-2.2.txt", 'r') as f:
            nodetool_output = f.read()
            (name, schema_version) = cstar.nodetoolparser.parse_describe_cluster(nodetool_output)
            self.assertEqual(name, "fnorp")
            self.assertEqual(schema_version, "48fc7f6b-b59d-3ed8-bc63-6e09b575651a")
        with open("tests/resources/describecluster-3.0.txt", 'r') as f:
            nodetool_output = f.read()
            (name, schema_version) = cstar.nodetoolparser.parse_describe_cluster(nodetool_output)
            self.assertEqual(name, "c3.0.13")
            self.assertEqual(schema_version, "48fc7f6b-b59d-3ed8-bc63-6e09b575651a")
        with open("tests/resources/describecluster-3.11.txt", 'r') as f:
            nodetool_output = f.read()
            (name, schema_version) = cstar.nodetoolparser.parse_describe_cluster(nodetool_output)
            self.assertEqual(name, "c3111")
            self.assertEqual(schema_version, "d8210030-20a4-3f05-b2ef-ea154a6d8ef6")

    def test_tokenize(self):
        with open("tests/resources/describering-2.2.txt", 'r') as f:
            tokens = cstar.nodetoolparser.describering._tokenize(f.read())
            self.assertEqual(243, len(tokens))

    def test_parse_describering(self):
        with open("tests/resources/describering-2.0.txt", 'r') as f:
            ast = cstar.nodetoolparser.parse_nodetool_describering(f.read())
            self.assertEqual(3, len(ast))
            self.assertEqual(ast[0].arguments['end_token'], -3074457345618258603)
            self.assertEqual(ast[1].arguments['endpoints'][1], "127.0.0.1")
            self.assertEqual(ast[1].arguments['endpoint_details'][0].arguments['datacenter'], "datacenter1")
            self.assertEqual(ast[1].arguments['endpoint_details'][0].arguments['rack'], "rack1")
        with open("tests/resources/describering-2.2.txt", 'r') as f:
            ast = cstar.nodetoolparser.parse_nodetool_describering(f.read())
            self.assertEqual(3, len(ast))
            self.assertEqual(ast[0].arguments['end_token'], -3074457345618258603)
            self.assertEqual(ast[1].arguments['endpoints'][1], "3.4.5.6")
            self.assertEqual(ast[1].arguments['endpoint_details'][0].arguments['datacenter'], "gew")
            self.assertEqual(ast[1].arguments['endpoint_details'][0].arguments['rack'], "rac1")
        with open("tests/resources/describering-3.0.txt", 'r') as f:
            ast = cstar.nodetoolparser.parse_nodetool_describering(f.read())
            self.assertEqual(3, len(ast))
            self.assertEqual(ast[0].arguments['end_token'], -3074457345618258603)
            self.assertEqual(ast[1].arguments['endpoints'][1], "127.0.0.1")
            self.assertEqual(ast[1].arguments['endpoint_details'][0].arguments['datacenter'], "datacenter1")
            self.assertEqual(ast[1].arguments['endpoint_details'][0].arguments['rack'], "rack1")
        with open("tests/resources/describering-3.11.txt", 'r') as f:
            ast = cstar.nodetoolparser.parse_nodetool_describering(f.read())
            self.assertEqual(3, len(ast))
            self.assertEqual(ast[0].arguments['end_token'], -3074457345618258603)
            self.assertEqual(ast[1].arguments['endpoints'][1], "127.0.0.1")
            self.assertEqual(ast[1].arguments['endpoint_details'][0].arguments['datacenter'], "datacenter1")
            self.assertEqual(ast[1].arguments['endpoint_details'][0].arguments['rack'], "rack1")

    def test_bad_syntax(self):
        for arg in BAD_SYNTAX:
            with self.assertRaises(cstar.exceptions.ParseException):
                cstar.nodetoolparser.parse_nodetool_describering(arg)
                print(arg)

    def test_parse_keyspaces(self):
        with open("tests/resources/cfstats-2.0.txt", 'r') as f:
            keyspaces = cstar.nodetoolparser.extract_keyspaces_from_cfstats(f.read())
            self.assertEqual(keyspaces, ['reaper_db', 'system_traces', 'system', 'test','users'])
        with open("tests/resources/cfstats-2.2.txt", 'r') as f:
            keyspaces = cstar.nodetoolparser.extract_keyspaces_from_cfstats(f.read())
            self.assertEqual(keyspaces, ['reaper_db', 'system_traces', 'booya', 'system', 'system_distributed', 'system_auth'])
        with open("tests/resources/cfstats-3.0.txt", 'r') as f:
            keyspaces = cstar.nodetoolparser.extract_keyspaces_from_cfstats(f.read())
            self.assertEqual(keyspaces, ['reaper_db', 'system_traces', 'booya', 'system', 'system_distributed', 'system_auth'])
        with open("tests/resources/cfstats-3.11.txt", 'r') as f:
            keyspaces = cstar.nodetoolparser.extract_keyspaces_from_cfstats(f.read())
            self.assertEqual(keyspaces, ['reaper_db', 'system_traces', 'system', 'system_distributed', 'system_schema', 'system_auth'])

    def test_convert_describering_to_json(self):
        with open("tests/resources/describering-2.2.txt", 'r') as f:
            describering = cstar.nodetoolparser.parse_nodetool_describering(f.read())
            range_mapping = cstar.nodetoolparser.convert_describering_to_range_mapping(describering)
            self.assertEqual(3,len(range_mapping))
            self.assertEqual("-9223372036854775808", range_mapping[0]["startToken"])
            self.assertEqual("-9223372036854775808", range_mapping[2]["endToken"])
            self.assertEqual(['1.2.3.4', '2.3.4.5', '3.4.5.6'], range_mapping[0]["endpoints"])
        with open("tests/resources/describering-2.0.txt", 'r') as f:
            describering = cstar.nodetoolparser.parse_nodetool_describering(f.read())
            range_mapping = cstar.nodetoolparser.convert_describering_to_range_mapping(describering)
            self.assertEqual(3,len(range_mapping))
            self.assertEqual("-9223372036854775808", range_mapping[0]["startToken"])
            self.assertEqual("-9223372036854775808", range_mapping[2]["endToken"])
            self.assertEqual(['127.0.0.2', '127.0.0.3', '127.0.0.1'], range_mapping[0]["endpoints"])
        with open("tests/resources/describering-3.0.txt", 'r') as f:
            describering = cstar.nodetoolparser.parse_nodetool_describering(f.read())
            range_mapping = cstar.nodetoolparser.convert_describering_to_range_mapping(describering)
            self.assertEqual(3,len(range_mapping))
            self.assertEqual("-9223372036854775807", range_mapping[0]["startToken"])
            self.assertEqual("-9223372036854775807", range_mapping[2]["endToken"])
            self.assertEqual(['127.0.0.2', '127.0.0.3', '127.0.0.1'], range_mapping[0]["endpoints"])
        with open("tests/resources/describering-3.11.txt", 'r') as f:
            describering = cstar.nodetoolparser.parse_nodetool_describering(f.read())
            range_mapping = cstar.nodetoolparser.convert_describering_to_range_mapping(describering)
            self.assertEqual(3,len(range_mapping))
            self.assertEqual("-9223372036854775806", range_mapping[0]["startToken"])
            self.assertEqual("-9223372036854775806", range_mapping[2]["endToken"])
            self.assertEqual(['127.0.0.2', '127.0.0.3', '127.0.0.1'], range_mapping[0]["endpoints"])

    def test_parse_nodetool_status(self):
        with open("tests/resources/status-2.2.txt", 'r') as f:
            topology = cstar.nodetoolparser.parse_nodetool_status(f.read(), 'test_cluster', lambda _: None)
            nodes = topology.hosts
            self.assertEqual(9, len(nodes))
            self.assertEqual("11.111.111.111", topology.get_host("11.111.111.111").ip)
            self.assertEqual(False, topology.get_host("11.111.111.115").is_up)
            self.assertEqual(True, topology.get_host("11.111.111.116").is_up)
            self.assertEqual("dc1", topology.get_host("11.111.111.112").dc)
            self.assertEqual("a6234243-8abd-435e-b822-838bc4749160", topology.get_host("11.111.111.111").host_id)
            self.assertEqual("rac2", topology.get_host("11.111.111.112").rack)
            self.assertEqual("97123467-7dab-4a9e-bd44-5613ac419961", topology.get_host("11.111.111.119").host_id)
            


if __name__ == '__main__':
    unittest.main()