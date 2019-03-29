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

import unittest
import json

import cstar.job
import cstar.jobreader
import cstar.strategy
import cstar.topology
import cstar.jobwriter

from cstar.exceptions import BadFileFormatVersion, FileTooOld


def revise(input, **kwargs):
    data = json.loads(input)
    for key, val in kwargs.items():
        data[key] = val
    return json.dumps(data)


def get_example_file():
    SMALL_EXAMPLE = r"""
{
    "command": "/some/directory/commands/command.sh",
    "creation_timestamp": 1508493330,
    "env": {},
    "errors": [],
    "job_runner": "RemoteJobRunner",
    "key_space": null,
    "sleep_on_new_runner": 0.5,
    "output_directory": "/some/directory/jobs/5ac35f50-5c20-45a2-9d22-1ec2e0b9d959",
    "ssh_username": null,
    "ssh_password": null,
    "ssh_identity_file": null,
    "ssh_lib": "paramiko",
    "state": {
        "cluster_parallel": true,
        "current_topology": [
            [
                "host1",
                "1.2.3.4",
                "dc",
                "cluster",
                3074457345618258602,
                true
            ],
            [
                "host2",
                "1.2.3.5",
                "dc",
                "cluster",
                -3074457345618258603,
                true
            ],
            [
                "host3",
                "1.2.3.6",
                "dc",
                "cluster",
                -9223372036854775808,
                true
            ]
        ],
        "dc_parallel": true,
        "progress" : {
            "running": [],
            "done": [
                [
                    "host1",
                    "1.2.3.4",
                    "dc",
                    "cluster",
                    3074457345618258602,
                    true
                ],
                [
                    "host2",
                    "1.2.3.5",
                    "dc",
                    "cluster",
                    -3074457345618258603,
                    true
                ]
            ],
            "failed": []
        },
        "max_concurrency": null,
        "original_topology": [
            [
                "host1",
                "1.2.3.4",
                "dc",
                "cluster",
                3074457345618258602,
                true
            ],
            [
                "host2",
                "1.2.3.5",
                "dc",
                "cluster",
                -3074457345618258603,
                true
            ],
            [
                "host3",
                "1.2.3.6",
                "dc",
                "cluster",
                -9223372036854775808,
                true
            ]
        ],
        "strategy": "topology",
        "ignore_down_nodes": false
    },
    "timeout": null,
    "jmx_username": null,
    "version": 8
}
"""
    return revise(SMALL_EXAMPLE, version=cstar.jobwriter.FILE_FORMAT_VERSION)


class JobReaderTest(unittest.TestCase):
    def test_normal_job(self):
        job = cstar.job.Job()
        job_id = "1234"
        stop_after = 5
        max_days = 999999
        output_directory = "/som/dir"
        filename = output_directory + "/some_file"

        cstar.jobreader._parse(get_example_file(), filename, output_directory, job, job_id, stop_after, max_days,
                               endpoint_mapper=lambda x: {})

        self.assertEqual(job.output_directory, output_directory)
        self.assertEqual(job.job_id, job_id)
        self.assertEqual(job.state.stop_after, stop_after)
        self.assertEqual(job.command, "/some/directory/commands/command.sh")
        self.assertEqual(job.state.strategy, cstar.strategy.Strategy.TOPOLOGY)
        self.assertEqual(len(job.state.progress.done), 2)
        self.assertEqual(len(job.state.current_topology), 3)
        self.assertEqual(len(job.state.original_topology), 3)
        self.assertEqual(type(job.state.original_topology.first()), cstar.topology.Host)

    def test_old_job(self):
        job = cstar.job.Job()
        revised = revise(get_example_file(), creation_timestamp=5)
        with self.assertRaises(FileTooOld):
            cstar.jobreader._parse(revised, "foo", "/somewhare", job, "1234", 5, 8,
                                   endpoint_mapper=lambda x: {})

    def test_future_version(self):
        job = cstar.job.Job()
        revised = revise(get_example_file(), version=999999)
        with self.assertRaises(BadFileFormatVersion):
            cstar.jobreader._parse(revised, "foo", "/somewhare", job, "1234", 5, 8,
                                   endpoint_mapper=lambda x: {})

    def test_retry_failed_job(self):
        job = cstar.job.Job()
        job_id = "1234"
        stop_after = 5
        max_days = 999999
        output_directory = "/som/dir"
        filename = output_directory + "/some_file"
        with open("tests/resources/failed_job.json", 'r') as f:
            cstar.jobreader._parse(f.read(), "tests/resources/failed_job.json", output_directory, job, job_id, stop_after, max_days,
                               endpoint_mapper=lambda x: {}, retry=False)
            self.assertEqual(len(job.state.progress.failed), 1)
        
    def test_do_not_retry_failed_job(self):
        job = cstar.job.Job()
        job_id = "1234"
        stop_after = 5
        max_days = 999999
        output_directory = "/som/dir"
        filename = output_directory + "/some_file"
        with open("tests/resources/failed_job.json", 'r') as f:
            cstar.jobreader._parse(f.read(), "tests/resources/failed_job.json", output_directory, job, job_id, stop_after, max_days,
                               endpoint_mapper=lambda x: {}, retry=True)
            self.assertEqual(len(job.state.progress.failed), 0)


if __name__ == '__main__':
    unittest.main()
