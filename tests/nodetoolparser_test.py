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
import cstar.exceptions

import unittest

BAD_SYNTAX = ("foo(3)", "foo([7)", "foo(3,", "foo(", "foo([1 1])", "foo([a:b])", "foo(bar [])")


class NodetoolParserTest(unittest.TestCase):

    def test_parse_describecluster(self):
        with open("tests/resources/describecluster-2.0.txt", 'r') as f:
            name = cstar.nodetoolparser.parse_describe_cluster(f.read())
            self.assertEqual(name, "c2.0.13")
        with open("tests/resources/describecluster-2.2.txt", 'r') as f:
            name = cstar.nodetoolparser.parse_describe_cluster(f.read())
            self.assertEqual(name, "fnorp")
        with open("tests/resources/describecluster-3.0.txt", 'r') as f:
            name = cstar.nodetoolparser.parse_describe_cluster(f.read())
            self.assertEqual(name, "c3.0.13")
        with open("tests/resources/describecluster-3.11.txt", 'r') as f:
            name = cstar.nodetoolparser.parse_describe_cluster(f.read())
            self.assertEqual(name, "c3111")

    def test_parse_nodetool_ring(self):
        with open("tests/resources/nodetool_ring-2.0.txt", 'r') as f:
            topology = cstar.nodetoolparser.parse_nodetool_ring(f.read(), 'test_cluster', lambda _: None)
            nodes = topology.hosts
            self.assertEqual(3, len(nodes))
            self.assertEqual("127.0.0.1", topology.get_host("127.0.0.1").ip)
            self.assertEqual(False, topology.get_host("127.0.0.3").is_up)
            self.assertEqual(True, topology.get_host("127.0.0.1").is_up)
            self.assertEqual(-9223372036854775808, topology.get_host("127.0.0.1").token)
            self.assertEqual("datacenter1", topology.get_host("127.0.0.1").dc)
        with open("tests/resources/nodetool_ring-2.2.txt", 'r') as f:
            topology = cstar.nodetoolparser.parse_nodetool_ring(f.read(), 'test_cluster', lambda _: None)
            nodes = topology.hosts
            self.assertEqual(9, len(nodes))
            self.assertEqual("1.159.15.53", topology.get_host("1.159.15.53").ip)
            self.assertEqual(False, topology.get_host("1.146.20.131").is_up)
            self.assertEqual(-9223372036854775806, topology.get_host("1.159.15.53").token)
            self.assertEqual("dc1", topology.get_host("1.159.15.53").dc)
            self.assertEqual("dc3", topology.get_host("1.145.23.52").dc)
        with open("tests/resources/nodetool_ring-3.0.txt", 'r') as f:
            topology = cstar.nodetoolparser.parse_nodetool_ring(f.read(), 'test_cluster', lambda _: None)
            nodes = topology.hosts
            self.assertEqual(3, len(nodes))
            self.assertEqual("127.0.0.1", topology.get_host("127.0.0.1").ip)
            self.assertEqual(False, topology.get_host("127.0.0.3").is_up)
            self.assertEqual(True, topology.get_host("127.0.0.1").is_up)
            self.assertEqual(-9223372036854775808, topology.get_host("127.0.0.1").token)
            self.assertEqual("datacenter1", topology.get_host("127.0.0.1").dc)
        with open("tests/resources/nodetool_ring-3.11.txt", 'r') as f:
            topology = cstar.nodetoolparser.parse_nodetool_ring(f.read(), 'test_cluster', lambda _: None)
            nodes = topology.hosts
            self.assertEqual(3, len(nodes))
            self.assertEqual("127.0.0.1", topology.get_host("127.0.0.1").ip)
            self.assertEqual(False, topology.get_host("127.0.0.3").is_up)
            self.assertEqual(True, topology.get_host("127.0.0.1").is_up)
            self.assertEqual(-9223372036854775808, topology.get_host("127.0.0.1").token)
            self.assertEqual("datacenter1", topology.get_host("127.0.0.1").dc)
        with open("tests/resources/ring_state_changes.txt", 'r') as f:
            topology = cstar.nodetoolparser.parse_nodetool_ring(f.read(), 'test_cluster', lambda _: None)
            nodes = topology.hosts
            self.assertEqual(9, len(nodes))
            self.assertEqual("1.159.15.53", topology.get_host("1.159.15.53").ip)
            self.assertEqual(False, topology.get_host("1.159.15.53").is_up)
            self.assertEqual(False, topology.get_host("1.154.15.51").is_up)
            self.assertEqual(False, topology.get_host("1.158.15.54").is_up)
            self.assertEqual(True, topology.get_host("1.133.36.89").is_up)
            self.assertEqual(False, topology.get_host("1.146.20.131").is_up)
            self.assertEqual(-9223372036854775806, topology.get_host("1.159.15.53").token)
            self.assertEqual("dc1", topology.get_host("1.159.15.53").dc)
            self.assertEqual("dc3", topology.get_host("1.145.23.52").dc)
            
    def test_parse_nodetool_ring_with_vnodes(self):
        with open("tests/resources/ring_vnodes.txt", 'r') as f:
            topology = cstar.nodetoolparser.parse_nodetool_ring(f.read(), 'test_cluster', lambda _: None)
            nodes = topology.hosts
            self.assertEqual(6, len(nodes))
            self.assertEqual("127.0.0.1", topology.get_host("127.0.0.1").ip)
            self.assertEqual(True, topology.get_host("127.0.0.3").is_up)
            self.assertEqual(True, topology.get_host("127.0.0.1").is_up)
            self.assertEqual(-9186465342292526055, topology.get_host("127.0.0.1").token)
            self.assertEqual("datacenter1", topology.get_host("127.0.0.1").dc)

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


if __name__ == '__main__':
    unittest.main()