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
"""
This test checks whether the libraries we're bundling are out of date and need to be synced with
a newer upstream release.
"""


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import fnmatch
import json
import re
import sys
from distutils.version import LooseVersion

import packaging.specifiers

from ansible.module_utils.urls import open_url


BUNDLED_RE = re.compile(b'\\b_BUNDLED_METADATA\\b')


def get_bundled_libs(paths):
    """
    Return the set of known bundled libraries

    :arg paths: The paths which the test has been instructed to check
    :returns: The list of all files which we know to contain bundled libraries.  If a bundled
        library consists of multiple files, this should be the file which has metadata included.
    """
    bundled_libs = set()
    for filename in fnmatch.filter(paths, 'lib/ansible/compat/*/__init__.py'):
        bundled_libs.add(filename)

    bundled_libs.add('lib/ansible/module_utils/compat/selectors.py')
    bundled_libs.add('lib/ansible/module_utils/distro/__init__.py')
    bundled_libs.add('lib/ansible/module_utils/six/__init__.py')
    # backports.ssl_match_hostname should be moved to its own file in the future
    bundled_libs.add('lib/ansible/module_utils/urls.py')

    return bundled_libs


def get_files_with_bundled_metadata(paths):
    """
    Search for any files which have bundled metadata inside of them

    :arg paths: Iterable of filenames to search for metadata inside of
    :returns: A set of pathnames which contained metadata
    """

    with_metadata = set()
    for path in paths:
        with open(path, 'rb') as f:
            body = f.read()

        if BUNDLED_RE.search(body):
            with_metadata.add(path)

    return with_metadata


def get_bundled_metadata(filename):
    """
    Retrieve the metadata about a bundled library from a python file

    :arg filename: The filename to look inside for the metadata
    :raises ValueError: If we're unable to extract metadata from the file
    :returns: The metadata from the python file
    """
    with open(filename, 'r') as module:
        for line in module:
            if line.strip().startswith('# NOT_BUNDLED'):
                return None

            if line.strip().startswith('# CANT_UPDATE'):
                print(
                    '{0} marked as CANT_UPDATE, so skipping. Manual '
                    'check for CVEs required.'.format(filename))
                return None

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
    """Get the latest pypi version of the package that we allow

    :arg pypi_data: Pypi information about the data as returned by
        ``https://pypi.org/pypi/{pkg_name}/json``
    :kwarg constraints: version constraints on what we're allowed to use as specified by
        the bundled metadata
    :returns: The most recent version on pypi that are allowed by ``constraints``
    """
    latest_version = "0"
    if constraints:
        version_specification = packaging.specifiers.SpecifierSet(constraints)
        for version in pypi_data['releases']:
            if version in version_specification:
                if LooseVersion(version) > LooseVersion(latest_version):
                    latest_version = version
    else:
        latest_version = pypi_data['info']['version']

    return latest_version


def main():
    """Entrypoint to the script"""

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

        if metadata is None:
            continue

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


if __name__ == '__main__':
    main()
