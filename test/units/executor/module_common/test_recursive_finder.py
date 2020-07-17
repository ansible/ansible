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

import os
import pytest
import zipfile

from collections import namedtuple
from io import BytesIO

import ansible.errors

from ansible.executor.module_common import recursive_finder
from ansible.module_utils.six import PY2


# These are the modules that are brought in by module_utils/basic.py  This may need to be updated
# when basic.py gains new imports
# We will remove these when we modify AnsiBallZ to store its args in a separate file instead of in
# basic.py

MODULE_UTILS_BASIC_FILES = frozenset(('ansible/__init__.py',
                                      'ansible/module_utils/__init__.py',
                                      'ansible/module_utils/_text.py',
                                      'ansible/module_utils/basic.py',
                                      'ansible/module_utils/six/__init__.py',
                                      'ansible/module_utils/_text.py',
                                      'ansible/module_utils/common/_collections_compat.py',
                                      'ansible/module_utils/common/_json_compat.py',
                                      'ansible/module_utils/common/collections.py',
                                      'ansible/module_utils/common/parameters.py',
                                      'ansible/module_utils/common/warnings.py',
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
                                      'ansible/module_utils/compat/__init__.py',
                                      'ansible/module_utils/compat/_selectors2.py',
                                      'ansible/module_utils/compat/selectors.py',
                                      'ansible/module_utils/distro/__init__.py',
                                      'ansible/module_utils/distro/_distro.py',
                                      'ansible/module_utils/parsing/__init__.py',
                                      'ansible/module_utils/parsing/convert_bool.py',
                                      'ansible/module_utils/pycompat24.py',
                                      'ansible/module_utils/six/__init__.py',
                                      ))

ONLY_BASIC_FILE = frozenset(('ansible/module_utils/basic.py',))

ANSIBLE_LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'lib', 'ansible')


@pytest.fixture
def finder_containers():
    FinderContainers = namedtuple('FinderContainers', ['zf'])

    zipoutput = BytesIO()
    zf = zipfile.ZipFile(zipoutput, mode='w', compression=zipfile.ZIP_STORED)

    return FinderContainers(zf)


class TestRecursiveFinder(object):
    def test_no_module_utils(self, finder_containers):
        name = 'ping'
        data = b'#!/usr/bin/python\nreturn \'{\"changed\": false}\''
        recursive_finder(name, os.path.join(ANSIBLE_LIB, 'modules', 'system', 'ping.py'), data, *finder_containers)
        assert frozenset(finder_containers.zf.namelist()) == MODULE_UTILS_BASIC_FILES

    def test_module_utils_with_syntax_error(self, finder_containers):
        name = 'fake_module'
        data = b'#!/usr/bin/python\ndef something(:\n   pass\n'
        with pytest.raises(ansible.errors.AnsibleError) as exec_info:
            recursive_finder(name, os.path.join(ANSIBLE_LIB, 'modules', 'system', 'fake_module.py'), data, *finder_containers)
        assert 'Unable to import fake_module due to invalid syntax' in str(exec_info.value)

    def test_module_utils_with_identation_error(self, finder_containers):
        name = 'fake_module'
        data = b'#!/usr/bin/python\n    def something():\n    pass\n'
        with pytest.raises(ansible.errors.AnsibleError) as exec_info:
            recursive_finder(name, os.path.join(ANSIBLE_LIB, 'modules', 'system', 'fake_module.py'), data, *finder_containers)
        assert 'Unable to import fake_module due to unexpected indent' in str(exec_info.value)

    #
    # Test importing six with many permutations because it is not a normal module
    #
    def test_from_import_six(self, finder_containers):
        name = 'ping'
        data = b'#!/usr/bin/python\nfrom ansible.module_utils import six'
        recursive_finder(name, os.path.join(ANSIBLE_LIB, 'modules', 'system', 'ping.py'), data, *finder_containers)
        assert frozenset(finder_containers.zf.namelist()) == frozenset(('ansible/module_utils/six/__init__.py', )).union(MODULE_UTILS_BASIC_FILES)

    def test_import_six(self, finder_containers):
        name = 'ping'
        data = b'#!/usr/bin/python\nimport ansible.module_utils.six'
        recursive_finder(name, os.path.join(ANSIBLE_LIB, 'modules', 'system', 'ping.py'), data, *finder_containers)
        assert frozenset(finder_containers.zf.namelist()) == frozenset(('ansible/module_utils/six/__init__.py', )).union(MODULE_UTILS_BASIC_FILES)

    def test_import_six_from_many_submodules(self, finder_containers):
        name = 'ping'
        data = b'#!/usr/bin/python\nfrom ansible.module_utils.six.moves.urllib.parse import urlparse'
        recursive_finder(name, os.path.join(ANSIBLE_LIB, 'modules', 'system', 'ping.py'), data, *finder_containers)
        assert frozenset(finder_containers.zf.namelist()) == frozenset(('ansible/module_utils/six/__init__.py',)).union(MODULE_UTILS_BASIC_FILES)
