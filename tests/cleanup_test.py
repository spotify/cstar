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

import unittest
import os.path

import cstar.cleanup


class CleanupTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.deleted = []

    def setUp(self):
        self.deleted.clear()

    def delete(self, name):
        self.deleted.append(name)

    def raise_exc(selfself):
        raise FileNotFoundError()

    def test_nothing_is_to_be_done(self):
        cstar.cleanup.cleanup(7, listdir=lambda x: ['12345'], jobread=lambda *args, **kwargs: args[0], delete=self.delete)
        self.assertEqual(self.deleted, [])

    def test_delete_a_directory(self):
        cstar.cleanup.cleanup(7, listdir=lambda x: ['12345'], jobread=self.raise_exc, delete=self.delete)
        self.assertEqual(self.deleted, [os.path.join(os.path.expanduser('~/.cstar/jobs'), '12345')])
