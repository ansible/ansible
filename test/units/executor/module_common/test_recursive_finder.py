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

# These are the modules that are brought in by module_utils/basic.py  This may need to be updated
# when basic.py gains new imports
# We will remove these when we modify AnsiBallZ to store its args in a separate file instead of in
# basic.py
MODULE_UTILS_BASIC_IMPORTS = frozenset((('_text',),
                                        ('basic',),
                                        ('common', '__init__'),
                                        ('common', '_collections_compat'),
                                        ('common', '_json_compat'),
                                        ('common', 'collections'),
                                        ('common', 'file'),
                                        ('common', 'parameters'),
                                        ('common', 'process'),
                                        ('common', 'sys_info'),
                                        ('common', 'text', '__init__'),
                                        ('common', 'text', 'converters'),
                                        ('common', 'text', 'formatters'),
                                        ('common', 'validation'),
                                        ('common', '_utils'),
                                        ('distro', '__init__'),
                                        ('distro', '_distro'),
                                        ('parsing', '__init__'),
                                        ('parsing', 'convert_bool'),
                                        ('pycompat24',),
                                        ('six', '__init__'),
                                        ))

MODULE_UTILS_BASIC_FILES = frozenset(('ansible/module_utils/_text.py',
                                      'ansible/module_utils/basic.py',
                                      'ansible/module_utils/six/__init__.py',
                                      'ansible/module_utils/_text.py',
                                      'ansible/module_utils/common/_collections_compat.py',
                                      'ansible/module_utils/common/_json_compat.py',
                                      'ansible/module_utils/common/collections.py',
                                      'ansible/module_utils/common/parameters.py',
                                      'ansible/module_utils/parsing/convert_bool.py',
                                      'ansible/module_utils/common/__init__.py',
                                      'ansible/module_utils/common/file.py',
                                      'ansible/module_utils/common/process.py',
                                      'ansible/module_utils/common/sys_info.py',
                                      'ansible/module_utils/common/text/__init__.py',
                                      'ansible/module_utils/common/text/converters.py',
                                      'ansible/module_utils/common/text/formatters.py',
                                      'ansible/module_utils/common/validation.py',
                                      'ansible/module_utils/common/_utils.py',
                                      'ansible/module_utils/distro/__init__.py',
                                      'ansible/module_utils/distro/_distro.py',
                                      'ansible/module_utils/parsing/__init__.py',
                                      'ansible/module_utils/parsing/convert_bool.py',
                                      'ansible/module_utils/pycompat24.py',
                                      'ansible/module_utils/six/__init__.py',
                                      ))

ONLY_BASIC_IMPORT = frozenset((('basic',),))
ONLY_BASIC_FILE = frozenset(('ansible/module_utils/basic.py',))


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
        assert finder_containers.py_module_names == set(()).union(MODULE_UTILS_BASIC_IMPORTS)
        assert finder_containers.py_module_cache == {}
        assert frozenset(finder_containers.zf.namelist()) == MODULE_UTILS_BASIC_FILES

    def test_module_utils_with_syntax_error(self, finder_containers):
        name = 'fake_module'
        data = b'#!/usr/bin/python\ndef something(:\n   pass\n'
        with pytest.raises(ansible.errors.AnsibleError) as exec_info:
            recursive_finder(name, data, *finder_containers)
        assert 'Unable to import fake_module due to invalid syntax' in str(exec_info.value)

    def test_module_utils_with_identation_error(self, finder_containers):
        name = 'fake_module'
        data = b'#!/usr/bin/python\n    def something():\n    pass\n'
        with pytest.raises(ansible.errors.AnsibleError) as exec_info:
            recursive_finder(name, data, *finder_containers)
        assert 'Unable to import fake_module due to unexpected indent' in str(exec_info.value)

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

        assert finder_containers.py_module_names == set((('foo', '__init__'),)).union(ONLY_BASIC_IMPORT)
        assert finder_containers.py_module_cache == {}
        assert frozenset(finder_containers.zf.namelist()) == frozenset(('ansible/module_utils/foo/__init__.py',)).union(ONLY_BASIC_FILE)

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

        assert finder_containers.py_module_names == set((('foo',),)).union(MODULE_UTILS_BASIC_IMPORTS)
        assert finder_containers.py_module_cache == {}
        assert frozenset(finder_containers.zf.namelist()) == frozenset(('ansible/module_utils/foo.py',)).union(MODULE_UTILS_BASIC_FILES)

    #
    # Test importing six with many permutations because it is not a normal module
    #
    def test_from_import_six(self, finder_containers):
        name = 'ping'
        data = b'#!/usr/bin/python\nfrom ansible.module_utils import six'
        recursive_finder(name, data, *finder_containers)
        assert finder_containers.py_module_names == set((('six', '__init__'),)).union(MODULE_UTILS_BASIC_IMPORTS)
        assert finder_containers.py_module_cache == {}
        assert frozenset(finder_containers.zf.namelist()) == frozenset(('ansible/module_utils/six/__init__.py', )).union(MODULE_UTILS_BASIC_FILES)

    def test_import_six(self, finder_containers):
        name = 'ping'
        data = b'#!/usr/bin/python\nimport ansible.module_utils.six'
        recursive_finder(name, data, *finder_containers)
        assert finder_containers.py_module_names == set((('six', '__init__'),)).union(MODULE_UTILS_BASIC_IMPORTS)
        assert finder_containers.py_module_cache == {}
        assert frozenset(finder_containers.zf.namelist()) == frozenset(('ansible/module_utils/six/__init__.py', )).union(MODULE_UTILS_BASIC_FILES)

    def test_import_six_from_many_submodules(self, finder_containers):
        name = 'ping'
        data = b'#!/usr/bin/python\nfrom ansible.module_utils.six.moves.urllib.parse import urlparse'
        recursive_finder(name, data, *finder_containers)
        assert finder_containers.py_module_names == set((('six', '__init__'),)).union(MODULE_UTILS_BASIC_IMPORTS)
        assert finder_containers.py_module_cache == {}
        assert frozenset(finder_containers.zf.namelist()) == frozenset(('ansible/module_utils/six/__init__.py',)).union(MODULE_UTILS_BASIC_FILES)
