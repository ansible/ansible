#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) 2018, Ansible Project
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import fnmatch
import json
import os
import os.path
import re
import sys
from distutils.version import LooseVersion

import packaging.specifiers

from ansible.module_utils.urls import open_url


BUNDLED_RE = re.compile(b'\\b_BUNDLED_METADATA\\b')


def get_bundled_libs(paths):
    bundled_libs = set()
    for filename in fnmatch.filter(paths, 'lib/ansible/compat/*/__init__.py'):
        bundled_libs.add(filename)

    bundled_libs.add('lib/ansible/module_utils/distro/__init__.py')
    bundled_libs.add('lib/ansible/module_utils/six/__init__.py')
    bundled_libs.add('lib/ansible/module_utils/compat/ipaddress.py')
    # backports.ssl_match_hostname should be moved to its own file in the future
    bundled_libs.add('lib/ansible/module_utils/urls.py')

    return bundled_libs


def get_files_with_bundled_metadata(paths):
    with_metadata = set()
    for path in paths:
        if path == 'test/sanity/code-smell/update-bundled.py':
            continue

        with open(path, 'rb') as f:
            body = f.read()

        if BUNDLED_RE.search(body):
            with_metadata.add(path)

    return with_metadata


def get_bundled_metadata(filename):
    with open(filename, 'r') as module:
        for line in module:
            if line.strip().startswith('_BUNDLED_METADATA'):
                data = line[line.index('{'):].strip()
                break
        else:
            raise ValueError('Unable to check bundled library for update.  Please add'
                             ' _BUNDLED_METADATA dictionary to the library file with'
                             ' information on pypi name and bundled version.')
        metadata = json.loads(data)
    return metadata


def get_latest_applicable_version(pypi_data, constraints=None):
    latest_version = "0"
    if 'version_constraints' in metadata:
        version_specification = packaging.specifiers.SpecifierSet(metadata['version_constraints'])
        for version in pypi_data['releases']:
            if version in version_specification:
                if LooseVersion(version) > LooseVersion(latest_version):
                    latest_version = version
    else:
        latest_version = pypi_data['info']['version']

    return latest_version


if __name__ == '__main__':
    paths = sys.argv[1:] or sys.stdin.read().splitlines()

    bundled_libs = get_bundled_libs(paths)
    files_with_bundled_metadata = get_files_with_bundled_metadata(paths)

    for filename in files_with_bundled_metadata.difference(bundled_libs):
        print('{0}: ERROR: File contains _BUNDLED_METADATA but needs to be added to'
              ' test/sanity/code-smell/update-bundled.py'.format(filename))

    for filename in bundled_libs:
        try:
            metadata = get_bundled_metadata(filename)
        except ValueError as e:
            print('{0}: ERROR: {1}'.format(filename, e))
            continue
        except (IOError, OSError) as e:
            if e.errno == 2:
                print('{0}: ERROR: {1}.  Perhaps the bundled library has been removed'
                      ' or moved and the bundled library test needs to be modified as'
                      ' well?'.format(filename, e))

        pypi_fh = open_url('https://pypi.org/pypi/{0}/json'.format(metadata['pypi_name']))
        pypi_data = json.loads(pypi_fh.read().decode('utf-8'))

        constraints = metadata.get('version_constraints', None)
        latest_version = get_latest_applicable_version(pypi_data, constraints)

        if LooseVersion(metadata['version']) < LooseVersion(latest_version):
            print('{0}: UPDATE {1} from {2} to {3} {4}'.format(
                filename,
                metadata['pypi_name'],
                metadata['version'],
                latest_version,
                'https://pypi.org/pypi/{0}/json'.format(metadata['pypi_name'])))
