# Copyright 2017 Chris Meyers <cmeyers@ansible.com>
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

import pytest

from ansible.errors import AnsibleError
from ansible.compat.tests import mock
from ansible.compat.tests import unittest

from ansible.plugins.inventory.script import InventoryModule


class TestInventoryModule(unittest.TestCase):

    def setUp(self):
        class Inventory():
            cache = dict()

        class PopenResult():
            returncode = 0
            stdout = u""
            stderr = u""
            def communicate(self):
                return (self.stdout, self.stderr)

        self.popen_result = PopenResult()
        self.inventory = Inventory()
        self.loader = mock.MagicMock()
        self.loader.load = mock.MagicMock()

        def register_patch(name):
            patcher = mock.patch(name)
            self.addCleanup(patcher.stop)
            return patcher.start()

        self.popen = register_patch('subprocess.Popen')
        self.popen.return_value = self.popen_result

        self.BaseInventoryPlugin= register_patch('ansible.plugins.inventory.BaseInventoryPlugin')
        self.BaseInventoryPlugin.get_cache_prefix.return_value = 'abc123'

    def test_parse_subprocess_path_not_found_fail(self):
        self.popen.side_effect = OSError("dummy text")
        
        inventory_module = InventoryModule()
        with pytest.raises(AnsibleError) as e:
            inventory_module.parse(self.inventory, self.loader, '/foo/bar/foobar.py')
        assert e.value.message == "problem running /foo/bar/foobar.py --list (dummy text)"

    def test_parse_subprocess_err_code_fail(self):
        self.popen_result.stdout = u"foo\xe9bar"
        self.popen_result.stderr = u"dummy\xe9data"

        self.popen_result.returncode = 1
        
        inventory_module = InventoryModule()
        with pytest.raises(AnsibleError) as e:
            inventory_module.parse(self.inventory, self.loader, '/foo/bar/foobar.py')
        assert e.value.message == "Inventory script (/foo/bar/foobar.py) had an execution error: " \
                                  "dummy\xc3\xa9data\n "

    def test_parse_utf8_fail(self):
        self.popen_result.returncode = 0
        self.popen_result.stderr = u"dummy\xe9data"
        self.loader.load.side_effect = TypeError('obj must be string')
        
        inventory_module = InventoryModule()
        with pytest.raises(AnsibleError) as e:
            inventory_module.parse(self.inventory, self.loader, '/foo/bar/foobar.py')
        assert e.value.message == "failed to parse executable inventory script results from " \
                                  "/foo/bar/foobar.py: obj must be string\ndummy\xc3\xa9data\n"

    def test_parse_dict_fail(self):
        self.popen_result.returncode = 0
        self.popen_result.stderr = u"dummy\xe9data"
        self.loader.load.return_value = 'i am not a dict'
        
        inventory_module = InventoryModule()
        with pytest.raises(AnsibleError) as e:
            inventory_module.parse(self.inventory, self.loader, '/foo/bar/foobar.py')
        assert e.value.message == "failed to parse executable inventory script results from " \
                                  "/foo/bar/foobar.py: needs to be a json dict\ndummy\xc3\xa9data\n"

