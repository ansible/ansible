# -*- coding: utf-8 -*-
# (c) 2016, Toshio Kuratomi <tkuratomi@ansible.com>
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

try:
    import builtins
except ImportError:
    import __builtin__ as builtins

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock
from ansible.module_utils import known_hosts

from units.mock.procenv import ModuleTestCase
from units.mock.generator import add_method

class TestSetModeIfDifferentBase(ModuleTestCase):

    def setUp(self):
        self.mock_stat1 = MagicMock()
        self.mock_stat1.st_mode = 0o444
        self.mock_stat2 = MagicMock()
        self.mock_stat2.st_mode = 0o660

        super(TestSetModeIfDifferentBase, self).setUp()
        from ansible.module_utils import basic
        self.old_ANSIBLE_ARGS = basic._ANSIBLE_ARGS
        basic._ANSIBLE_ARGS = None

        self.am = basic.AnsibleModule(
            argument_spec = dict(),
        )

    def tearDown(self):
        super(TestSetModeIfDifferentBase, self).tearDown()
        from ansible.module_utils import basic
        basic._ANSIBLE_ARGS = self.old_ANSIBLE_ARGS


def _check_no_mode_given_returns_previous_changes(self, previous_changes=True):
    with patch('os.lstat', side_effect=[self.mock_stat1]):
        self.assertEqual(self.am.set_mode_if_different('/path/to/file', None, previous_changes), previous_changes)

def _check_mode_changed_to_0660(self, mode):
    # Note: This is for checking that all the different ways of specifying
    # 0660 mode work.  It cannot be used to check that setting a mode that is
    # not equivalent to 0660 works.
    with patch('os.lstat', side_effect=[self.mock_stat1, self.mock_stat2, self.mock_stat2]) as m_lstat:
        with patch('os.lchmod', return_value=None, create=True) as m_lchmod:
            self.assertEqual(self.am.set_mode_if_different('/path/to/file', mode, False), True)
            m_lchmod.assert_called_with(b'/path/to/file', 0o660)

def _check_mode_unchanged_when_already_0660(self, mode):
    # Note: This is for checking that all the different ways of specifying
    # 0660 mode work.  It cannot be used to check that setting a mode that is
    # not equivalent to 0660 works.
    with patch('os.lstat', side_effect=[self.mock_stat2, self.mock_stat2, self.mock_stat2]) as m_lstat:
        self.assertEqual(self.am.set_mode_if_different('/path/to/file', mode, False), False)


SYNONYMS_0660 = (
    [[0o660]],
    [['0o660']],
    [['660']],
    )

@add_method(_check_no_mode_given_returns_previous_changes,
        [dict(previous_changes=True)],
    [dict(previous_changes=False)],
    )
@add_method(_check_mode_changed_to_0660,
        *SYNONYMS_0660
        )
@add_method(_check_mode_unchanged_when_already_0660,
        *SYNONYMS_0660
        )
class TestSetModeIfDifferent(TestSetModeIfDifferentBase):
    def test_module_utils_basic_ansible_module_set_mode_if_different(self):
        with patch('os.lstat') as m:
            with patch('os.lchmod', return_value=None, create=True) as m_os:
                m.side_effect = [self.mock_stat1, self.mock_stat2, self.mock_stat2]
                self.am._symbolic_mode_to_octal = MagicMock(side_effect=Exception)
                with pytest.raises(SystemExit):
                    self.am.set_mode_if_different('/path/to/file', 'o+w,g+w,a-r', False)

        original_hasattr = hasattr
        def _hasattr(obj, name):
            if obj == os and name == 'lchmod':
                return False
            return original_hasattr(obj, name)

        # FIXME: this isn't working yet
        with patch('os.lstat', side_effect=[self.mock_stat1, self.mock_stat2]):
            with patch.object(builtins, 'hasattr', side_effect=_hasattr):
                with patch('os.path.islink', return_value=False):
                    with patch('os.chmod', return_value=None) as m_chmod:
                        self.assertEqual(self.am.set_mode_if_different('/path/to/file/no_lchmod', 0o660, False), True)
        with patch('os.lstat', side_effect=[self.mock_stat1, self.mock_stat2]):
            with patch.object(builtins, 'hasattr', side_effect=_hasattr):
                with patch('os.path.islink', return_value=True):
                    with patch('os.chmod', return_value=None) as m_chmod:
                        with patch('os.stat', return_value=self.mock_stat2):
                            self.assertEqual(self.am.set_mode_if_different('/path/to/file', 0o660, False), True)


def _check_knows_to_change_to_0660_in_check_mode(self, mode):
    # Note: This is for checking that all the different ways of specifying
    # 0660 mode work.  It cannot be used to check that setting a mode that is
    # not equivalent to 0660 works.
    with patch('os.lstat', side_effect=[self.mock_stat1, self.mock_stat2, self.mock_stat2]) as m_lstat:
        self.assertEqual(self.am.set_mode_if_different('/path/to/file', mode, False), True)

@add_method(_check_no_mode_given_returns_previous_changes,
        [dict(previous_changes=True)],
    [dict(previous_changes=False)],
    )
@add_method(_check_knows_to_change_to_0660_in_check_mode,
        *SYNONYMS_0660
        )
@add_method(_check_mode_unchanged_when_already_0660,
        *SYNONYMS_0660
        )
class TestSetModeIfDifferentWithCheckMode(TestSetModeIfDifferentBase):
    def setUp(self):
        super(TestSetModeIfDifferentWithCheckMode, self).setUp()
        self.am.check_mode = True

    def tearDown(self):
        super(TestSetModeIfDifferentWithCheckMode, self).tearDown()
        self.am.check_mode = False
