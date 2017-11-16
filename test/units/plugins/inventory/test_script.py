# -*- coding: utf-8 -*-

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

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.plugins.loader import PluginLoader
from ansible.compat.tests import mock
from ansible.compat.tests import unittest
from ansible.module_utils._text import to_bytes, to_native


class TestInventoryModule(unittest.TestCase):

    def setUp(self):

        class Inventory():
            cache = dict()

        class PopenResult():
            returncode = 0
            stdout = b""
            stderr = b""

            def communicate(self):
                return (self.stdout, self.stderr)

        self.popen_result = PopenResult()
        self.inventory = Inventory()
        self.loader = mock.MagicMock()
        self.loader.load = mock.MagicMock()

        inv_loader = PluginLoader('InventoryModule', 'ansible.plugins.inventory', C.DEFAULT_INVENTORY_PLUGIN_PATH, 'inventory_plugins')
        self.inventory_module = inv_loader.get('script')
        self.inventory_module.set_options()

        def register_patch(name):
            patcher = mock.patch(name)
            self.addCleanup(patcher.stop)
            return patcher.start()

        self.popen = register_patch('subprocess.Popen')
        self.popen.return_value = self.popen_result

        self.BaseInventoryPlugin = register_patch('ansible.plugins.inventory.BaseInventoryPlugin')
        self.BaseInventoryPlugin.get_cache_prefix.return_value = 'abc123'

    def test_parse_subprocess_path_not_found_fail(self):
        self.popen.side_effect = OSError("dummy text")

        with pytest.raises(AnsibleError) as e:
            self.inventory_module.parse(self.inventory, self.loader, '/foo/bar/foobar.py')
        assert e.value.message == "problem running /foo/bar/foobar.py --list (dummy text)"

    def test_parse_subprocess_err_code_fail(self):
        self.popen_result.stdout = to_bytes(u"fooébar", errors='surrogate_escape')
        self.popen_result.stderr = to_bytes(u"dummyédata")

        self.popen_result.returncode = 1

        with pytest.raises(AnsibleError) as e:
            self.inventory_module.parse(self.inventory, self.loader, '/foo/bar/foobar.py')
        assert e.value.message == to_native("Inventory script (/foo/bar/foobar.py) had an execution error: "
                                            "dummyédata\n ")

    def test_parse_utf8_fail(self):
        self.popen_result.returncode = 0
        self.popen_result.stderr = to_bytes("dummyédata")
        self.loader.load.side_effect = TypeError('obj must be string')

        with pytest.raises(AnsibleError) as e:
            self.inventory_module.parse(self.inventory, self.loader, '/foo/bar/foobar.py')
        assert e.value.message == to_native("failed to parse executable inventory script results from "
                                            "/foo/bar/foobar.py: obj must be string\ndummyédata\n")

    def test_parse_dict_fail(self):
        self.popen_result.returncode = 0
        self.popen_result.stderr = to_bytes("dummyédata")
        self.loader.load.return_value = 'i am not a dict'

        with pytest.raises(AnsibleError) as e:
            self.inventory_module.parse(self.inventory, self.loader, '/foo/bar/foobar.py')
        assert e.value.message == to_native("failed to parse executable inventory script results from "
                                            "/foo/bar/foobar.py: needs to be a json dict\ndummyédata\n")
