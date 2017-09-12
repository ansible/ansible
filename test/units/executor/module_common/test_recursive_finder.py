# (c) 2017, Toshio Kuratomi <tkuratomi@ansible.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import imp
import pytest
import zipfile

from collections import namedtuple
from functools import partial
from io import BytesIO, StringIO

import ansible.errors

from ansible.executor.module_common import recursive_finder
from ansible.module_utils.six import PY2
from ansible.module_utils.six.moves import builtins


original_find_module = imp.find_module


@pytest.fixture
def finder_containers():
    FinderContainers = namedtuple('FinderContainers', ['py_module_names', 'py_module_cache', 'zf'])

    py_module_names = set()
    # py_module_cache = {('__init__',): b''}
    py_module_cache = {}

    zipoutput = BytesIO()
    zf = zipfile.ZipFile(zipoutput, mode='w', compression=zipfile.ZIP_STORED)
    # zf.writestr('ansible/__init__.py', b'')

    return FinderContainers(py_module_names, py_module_cache, zf)


def find_module_foo(module_utils_data, *args, **kwargs):
    if args[0] == 'foo':
        return (module_utils_data, '/usr/lib/python2.7/site-packages/ansible/module_utils/foo.py', ('.py', 'r', imp.PY_SOURCE))
    return original_find_module(*args, **kwargs)


def find_package_foo(module_utils_data, *args, **kwargs):
    if args[0] == 'foo':
        return (module_utils_data, '/usr/lib/python2.7/site-packages/ansible/module_utils/foo', ('', '', imp.PKG_DIRECTORY))
    return original_find_module(*args, **kwargs)


class TestRecursiveFinder(object):
    def test_no_module_utils(self, finder_containers):
        name = 'ping'
        data = b'#!/usr/bin/python\nreturn \'{\"changed\": false}\''
        recursive_finder(name, data, *finder_containers)
        assert finder_containers.py_module_names == set(())
        assert finder_containers.py_module_cache == {}
        assert frozenset(finder_containers.zf.namelist()) == frozenset()

    def test_from_import_toplevel_package(self, finder_containers, mocker):
        if PY2:
            module_utils_data = BytesIO(b'# License\ndef do_something():\n    pass\n')
        else:
            module_utils_data = StringIO(u'# License\ndef do_something():\n    pass\n')
        mocker.patch('imp.find_module', side_effect=partial(find_package_foo, module_utils_data))
        mocker.patch('ansible.executor.module_common._slurp', side_effect=lambda x: b'# License\ndef do_something():\n    pass\n')

        name = 'ping'
        data = b'#!/usr/bin/python\nfrom ansible.module_utils import foo'
        recursive_finder(name, data, *finder_containers)
        mocker.stopall()

        assert finder_containers.py_module_names == set((('foo', '__init__'),))
        assert finder_containers.py_module_cache == {}
        assert frozenset(finder_containers.zf.namelist()) == frozenset(('ansible/module_utils/foo/__init__.py',))

    def test_from_import_toplevel_module(self, finder_containers, mocker):
        if PY2:
            module_utils_data = BytesIO(b'# License\ndef do_something():\n    pass\n')
        else:
            module_utils_data = StringIO(u'# License\ndef do_something():\n    pass\n')
        mocker.patch('imp.find_module', side_effect=partial(find_module_foo, module_utils_data))

        name = 'ping'
        data = b'#!/usr/bin/python\nfrom ansible.module_utils import foo'
        recursive_finder(name, data, *finder_containers)
        mocker.stopall()

        assert finder_containers.py_module_names == set((('foo',),))
        assert finder_containers.py_module_cache == {}
        assert frozenset(finder_containers.zf.namelist()) == frozenset(('ansible/module_utils/foo.py',))

    #
    # Test importing six with many permutations because it is not a normal module
    #
    def test_from_import_six(self, finder_containers):
        name = 'ping'
        data = b'#!/usr/bin/python\nfrom ansible.module_utils import six'
        recursive_finder(name, data, *finder_containers)
        assert finder_containers.py_module_names == set((('six', '__init__'),))
        assert finder_containers.py_module_cache == {}
        assert frozenset(finder_containers.zf.namelist()) == frozenset(('ansible/module_utils/six/__init__.py', ))

    def test_import_six(self, finder_containers):
        name = 'ping'
        data = b'#!/usr/bin/python\nimport ansible.module_utils.six'
        recursive_finder(name, data, *finder_containers)
        assert finder_containers.py_module_names == set((('six', '__init__'),))
        assert finder_containers.py_module_cache == {}
        assert frozenset(finder_containers.zf.namelist()) == frozenset(('ansible/module_utils/six/__init__.py', ))

    def test_import_six_from_many_submodules(self, finder_containers):
        name = 'ping'
        data = b'#!/usr/bin/python\nfrom ansible.module_utils.six.moves.urllib.parse import urlparse'
        recursive_finder(name, data, *finder_containers)
        assert finder_containers.py_module_names == set((('six', '__init__'),))
        assert finder_containers.py_module_cache == {}
        assert frozenset(finder_containers.zf.namelist()) == frozenset(('ansible/module_utils/six/__init__.py',))
