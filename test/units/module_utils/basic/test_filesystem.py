# -*- coding: utf-8 -*-
# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2016 Toshio Kuratomi <tkuratomi@ansible.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from units.mock.procenv import ModuleTestCase

from unittest.mock import patch, MagicMock
import builtins

realimport = builtins.__import__


class TestOtherFilesystem(ModuleTestCase):
    def test_module_utils_basic_ansible_module_user_and_group(self):
        from ansible.module_utils import basic
        basic._ANSIBLE_ARGS = None

        am = basic.AnsibleModule(
            argument_spec=dict(),
        )

        mock_stat = MagicMock()
        mock_stat.st_uid = 0
        mock_stat.st_gid = 0

        with patch('os.lstat', return_value=mock_stat):
            self.assertEqual(am.user_and_group('/path/to/file'), (0, 0))

    def test_module_utils_basic_ansible_module_find_mount_point(self):
        from ansible.module_utils import basic
        basic._ANSIBLE_ARGS = None

        am = basic.AnsibleModule(
            argument_spec=dict(),
        )

        def _mock_ismount(path):
            if path == b'/':
                return True
            return False

        with patch('os.path.ismount', side_effect=_mock_ismount):
            self.assertEqual(am.find_mount_point('/root/fs/../mounted/path/to/whatever'), '/')

        def _mock_ismount(path):
            if path == b'/subdir/mount':
                return True
            return False

        with patch('os.path.ismount', side_effect=_mock_ismount):
            self.assertEqual(am.find_mount_point('/subdir/mount/path/to/whatever'), '/subdir/mount')

    def test_module_utils_basic_ansible_module_set_owner_if_different(self):
        from ansible.module_utils import basic
        basic._ANSIBLE_ARGS = None

        am = basic.AnsibleModule(
            argument_spec=dict(),
        )

        assert am.set_owner_if_different('/path/to/file', None, True)
        assert not am.set_owner_if_different('/path/to/file', None, False)

        am.user_and_group = MagicMock(return_value=(500, 500))

        with patch('os.lchown', return_value=None) as m:
            assert am.set_owner_if_different('/path/to/file', 0, False)
            m.assert_called_with(b'/path/to/file', 0, -1)

            def _mock_getpwnam(*args, **kwargs):
                mock_pw = MagicMock()
                mock_pw.pw_uid = 0
                return mock_pw

            m.reset_mock()
            with patch('pwd.getpwnam', side_effect=_mock_getpwnam):
                assert am.set_owner_if_different('/path/to/file', 'root', False)
                m.assert_called_with(b'/path/to/file', 0, -1)

            with patch('pwd.getpwnam', side_effect=KeyError):
                self.assertRaises(SystemExit, am.set_owner_if_different, '/path/to/file', 'root', False)

            m.reset_mock()
            am.check_mode = True
            assert am.set_owner_if_different('/path/to/file', 0, False)
            assert not m.called
            am.check_mode = False

        with patch('os.lchown', side_effect=OSError) as m:
            self.assertRaises(SystemExit, am.set_owner_if_different, '/path/to/file', 'root', False)

    def test_module_utils_basic_ansible_module_set_group_if_different(self):
        from ansible.module_utils import basic
        basic._ANSIBLE_ARGS = None

        am = basic.AnsibleModule(
            argument_spec=dict(),
        )

        assert am.set_group_if_different('/path/to/file', None, True)
        assert not am.set_group_if_different('/path/to/file', None, False)

        am.user_and_group = MagicMock(return_value=(500, 500))

        with patch('os.lchown', return_value=None) as m:
            assert am.set_group_if_different('/path/to/file', 0, False)
            m.assert_called_with(b'/path/to/file', -1, 0)

            def _mock_getgrnam(*args, **kwargs):
                mock_gr = MagicMock()
                mock_gr.gr_gid = 0
                return mock_gr

            m.reset_mock()
            with patch('grp.getgrnam', side_effect=_mock_getgrnam):
                assert am.set_group_if_different('/path/to/file', 'root', False)
                m.assert_called_with(b'/path/to/file', -1, 0)

            with patch('grp.getgrnam', side_effect=KeyError):
                self.assertRaises(SystemExit, am.set_group_if_different, '/path/to/file', 'root', False)

            m.reset_mock()
            am.check_mode = True
            assert am.set_group_if_different('/path/to/file', 0, False)
            assert not m.called
            am.check_mode = False

        with patch('os.lchown', side_effect=OSError) as m:
            self.assertRaises(SystemExit, am.set_group_if_different, '/path/to/file', 'root', False)

    def test_module_utils_basic_ansible_module_set_directory_attributes_if_different(self):
        from ansible.module_utils import basic
        basic._ANSIBLE_ARGS = None

        am = basic.AnsibleModule(
            argument_spec=dict(),
        )

        am.selinux_enabled = lambda: False

        file_args = {
            'path': '/path/to/file',
            'mode': None,
            'owner': None,
            'group': None,
            'seuser': None,
            'serole': None,
            'setype': None,
            'selevel': None,
            'secontext': [None, None, None],
            'attributes': None,
        }

        assert am.set_directory_attributes_if_different(file_args, True)
        assert not am.set_directory_attributes_if_different(file_args, False)
