# -*- coding: utf-8 -*-
# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2016 Toshio Kuratomi <tkuratomi@ansible.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import builtins
import sys
import unittest

from unittest.mock import patch

realimport = builtins.__import__


class TestImports(unittest.TestCase):

    def clear_modules(self, mods):
        for mod in mods:
            if mod in sys.modules:
                del sys.modules[mod]

    def test_module_utils_basic_import_syslog(self):
        present = True

        def _mock_import(name, *args, **kwargs):
            if name == 'syslog':
                if present:
                    return unittest.mock.MagicMock()
                raise ImportError
            return realimport(name, *args, **kwargs)

        with patch.object(builtins, '__import__', _mock_import):
            self.clear_modules(['syslog', 'ansible.module_utils.basic'])
            mod = builtins.__import__('ansible.module_utils.basic')
            self.assertTrue(mod.module_utils.basic.HAS_SYSLOG)

            present = False

            self.clear_modules(['syslog', 'ansible.module_utils.basic'])
            mod = builtins.__import__('ansible.module_utils.basic')
            self.assertFalse(mod.module_utils.basic.HAS_SYSLOG)

            self.clear_modules(['syslog', 'ansible.module_utils.basic'])

    def test_module_utils_basic_import_selinux(self):
        present = True

        def _mock_import(name, globals=None, locals=None, fromlist=tuple(), level=0, **kwargs):
            if name == 'ansible.module_utils.compat' and fromlist == ('selinux',):
                if present:
                    return unittest.mock.MagicMock()
                raise ImportError
            return realimport(name, globals=globals, locals=locals, fromlist=fromlist, level=level, **kwargs)

        with patch.object(builtins, '__import__', _mock_import):
            self.clear_modules(['ansible.module_utils.compat.selinux', 'ansible.module_utils.basic'])
            mod = builtins.__import__('ansible.module_utils.basic')
            self.assertTrue(mod.module_utils.basic.HAVE_SELINUX)

            present = False

            self.clear_modules(['ansible.module_utils.compat.selinux', 'ansible.module_utils.basic'])
            mod = builtins.__import__('ansible.module_utils.basic')
            self.assertFalse(mod.module_utils.basic.HAVE_SELINUX)

            self.clear_modules(['ansible.module_utils.compat.selinux', 'ansible.module_utils.basic'])

    # FIXME: doesn't work yet
    # @patch.object(builtins, 'bytes')
    # def test_module_utils_basic_bytes(self, mock_bytes):
    #     mock_bytes.side_effect = NameError()
    #     from ansible.module_utils import basic

    def test_module_utils_basic_import_systemd_journal(self):
        present = True

        def _mock_import(name, *args, **kwargs):
            try:
                fromlist = kwargs.get('fromlist', args[2])
            except IndexError:
                fromlist = []
            if name == 'systemd' and 'journal' in fromlist:
                if present:
                    return unittest.mock.MagicMock()
                raise ImportError
            return realimport(name, *args, **kwargs)

        with patch.object(builtins, '__import__', _mock_import):
            self.clear_modules(['systemd', 'ansible.module_utils.basic'])
            mod = builtins.__import__('ansible.module_utils.basic')
            self.assertTrue(mod.module_utils.basic.has_journal)

            present = False

            self.clear_modules(['systemd', 'ansible.module_utils.basic'])
            mod = builtins.__import__('ansible.module_utils.basic')
            self.assertFalse(mod.module_utils.basic.has_journal)

            self.clear_modules(['systemd', 'ansible.module_utils.basic'])
