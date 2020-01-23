#! /usr/bin/env python
# -*- coding: utf-8 -*-
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

from setuptools import setup
from setuptools.command.install import install
import os
import sys

# circleci.py version
VERSION = '0.7.3'

class VerifyVersionCommand(install):
    """Custom command to verify that the git tag matches our version"""
    description = 'verify that the git tag matches our version'

    def run(self):
        tag = os.getenv('CIRCLE_TAG')

        if tag != VERSION:
            info = "Git tag: {0} does not match the version of this app: {1}".format(
                tag, VERSION
            )
            sys.exit(info)

setup(name='cstar',
      version=VERSION,
      author='Spotify',
      author_email='rebase-squad@spotify.com',
      url='https://github.com/spotify/cstar',
      description='Apache Cassandra cluster orchestration tool for the command line',
      license='Apache-2.0',
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: Apache Software License',
          'Programming Language :: Python :: 3.6',
          'Topic :: Database'
      ],
      install_requires=['paramiko==2.3.3'],
      python_requires='>=3',
      packages=('cstar', 'cstar.nodetoolparser', 'cstar.resources'),
      package_data={'cstar.resources': ['commands/*', 'scripts/*']},
      test_suite='tests',
      entry_points={
          'console_scripts': [
              'cstar=cstar.cstarcli:main',
              'cstarpar=cstar.cstarparcli:main',
          ]},
      cmdclass={
          'verify': VerifyVersionCommand,
      }
)
