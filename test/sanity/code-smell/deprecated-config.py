#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) 2018, Matt Martz <matt@sivel.net>
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

import mmap
import os
import re
import sys

from distutils.version import StrictVersion

import yaml

import ansible.config

from ansible.plugins.loader import fragment_loader
from ansible.release import __version__ as ansible_version
from ansible.utils.plugin_docs import get_docstring

DOC_RE = re.compile(b'^DOCUMENTATION', flags=re.M)
ANSIBLE_MAJOR = StrictVersion('.'.join(ansible_version.split('.')[:2]))


def find_deprecations(obj, path=None):
    if not isinstance(obj, (list, dict)):
        return

    try:
        items = obj.items()
    except AttributeError:
        items = enumerate(obj)

    for key, value in items:
        if path is None:
            this_path = []
        else:
            this_path = path[:]

        this_path.append(key)

        if key != 'deprecated':
            for result in find_deprecations(value, path=this_path):
                yield result
        else:
            try:
                version = value['version']
                this_path.append('version')
            except KeyError:
                version = value['removed_in']
                this_path.append('removed_in')
            if StrictVersion(version) <= ANSIBLE_MAJOR:
                yield (this_path, version)


def main():
    plugins = []
    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        with open(path, 'rb') as f:
            try:
                mm_file = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            except ValueError:
                continue
            if DOC_RE.search(mm_file):
                plugins.append(path)
            mm_file.close()

    for plugin in plugins:
        data = {}
        data['doc'], data['examples'], data['return'], data['metadata'] = get_docstring(plugin, fragment_loader)
        for result in find_deprecations(data['doc']):
            print(
                '%s: %s is scheduled for removal in %s' % (plugin, '.'.join(str(i) for i in result[0][:-2]), result[1])
            )

    base = os.path.join(os.path.dirname(ansible.config.__file__), 'base.yml')
    with open(base) as f:
        data = yaml.safe_load(f)

    for result in find_deprecations(data):
        print('%s: %s is scheduled for removal in %s' % (base, '.'.join(str(i) for i in result[0][:-2]), result[1]))


if __name__ == '__main__':
    main()
