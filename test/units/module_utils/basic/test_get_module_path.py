# -*- coding: utf-8 -*-
# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2016 Toshio Kuratomi <tkuratomi@ansible.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from units.mock.procenv import ModuleTestCase

from unittest.mock import patch
import builtins

realimport = builtins.__import__


class TestGetModulePath(ModuleTestCase):
    def test_module_utils_basic_get_module_path(self):
        from ansible.module_utils.basic import get_module_path
        with patch('os.path.realpath', return_value='/path/to/foo/'):
            self.assertEqual(get_module_path(), '/path/to/foo')
