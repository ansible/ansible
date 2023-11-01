# -*- coding: utf-8 -*-
# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2016 Toshio Kuratomi <tkuratomi@ansible.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import sys

from units.mock.procenv import ModuleTestCase

from unittest.mock import patch
import builtins

realimport = builtins.__import__


class TestImports(ModuleTestCase):

    def clear_modules(self, mods):
        for mod in mods:
            if mod in sys.modules:
                del sys.modules[mod]

    @patch.object(builtins, '__import__')
    def test_module_utils_basic_import_syslog(self, mock_import):
        def _mock_import(name, *args, **kwargs):
            if name == 'syslog':
                raise ImportError
            return realimport(name, *args, **kwargs)

        self.clear_modules(['syslog', 'ansible.module_utils.basic'])
        mod = builtins.__import__('ansible.module_utils.basic')
        self.assertTrue(mod.module_utils.basic.HAS_SYSLOG)

        self.clear_modules(['syslog', 'ansible.module_utils.basic'])
        mock_import.side_effect = _mock_import
        mod = builtins.__import__('ansible.module_utils.basic')
        self.assertFalse(mod.module_utils.basic.HAS_SYSLOG)

    @patch.object(builtins, '__import__')
    def test_module_utils_basic_import_selinux(self, mock_import):
        def _mock_import(name, globals=None, locals=None, fromlist=tuple(), level=0, **kwargs):
            if name == 'ansible.module_utils.compat' and fromlist == ('selinux',):
                raise ImportError
            return realimport(name, globals=globals, locals=locals, fromlist=fromlist, level=level, **kwargs)

        try:
            self.clear_modules(['ansible.module_utils.compat.selinux', 'ansible.module_utils.basic'])
            mod = builtins.__import__('ansible.module_utils.basic')
            self.assertTrue(mod.module_utils.basic.HAVE_SELINUX)
        except ImportError:
            # no selinux on test system, so skip
            pass

        self.clear_modules(['ansible.module_utils.compat.selinux', 'ansible.module_utils.basic'])
        mock_import.side_effect = _mock_import
        mod = builtins.__import__('ansible.module_utils.basic')
        self.assertFalse(mod.module_utils.basic.HAVE_SELINUX)

    # FIXME: doesn't work yet
    # @patch.object(builtins, 'bytes')
    # def test_module_utils_basic_bytes(self, mock_bytes):
    #     mock_bytes.side_effect = NameError()
    #     from ansible.module_utils import basic

    @patch.object(builtins, '__import__')
    def test_module_utils_basic_import_systemd_journal(self, mock_import):
        def _mock_import(name, *args, **kwargs):
            try:
                fromlist = kwargs.get('fromlist', args[2])
            except IndexError:
                fromlist = []
            if name == 'systemd' and 'journal' in fromlist:
                raise ImportError
            return realimport(name, *args, **kwargs)

        self.clear_modules(['systemd', 'ansible.module_utils.basic'])
        mod = builtins.__import__('ansible.module_utils.basic')
        self.assertTrue(mod.module_utils.basic.has_journal)

        self.clear_modules(['systemd', 'ansible.module_utils.basic'])
        mock_import.side_effect = _mock_import
        mod = builtins.__import__('ansible.module_utils.basic')
        self.assertFalse(mod.module_utils.basic.has_journal)
