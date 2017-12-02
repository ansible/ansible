# -*- coding: utf-8 -*-
# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2016 Toshio Kuratomi <tkuratomi@ansible.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import errno
import json
import os
import sys
from io import BytesIO, StringIO

from units.mock.procenv import ModuleTestCase, swap_stdin_and_argv

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock, mock_open, Mock, call
from ansible.module_utils.six.moves import builtins

realimport = builtins.__import__

class TestAtomicMove(ModuleTestCase):
    @patch('tempfile.mkstemp')
    @patch('os.umask')
    @patch('shutil.copyfileobj')
    @patch('shutil.move')
    @patch('shutil.copy2')
    @patch('os.rename')
    @patch('pwd.getpwuid')
    @patch('os.getuid')
    @patch('os.environ')
    @patch('os.getlogin')
    @patch('os.chown')
    @patch('os.chmod')
    @patch('os.stat')
    @patch('os.path.exists')
    @patch('os.close')
    def test_module_utils_basic_ansible_module_atomic_move(
            self,
            _os_close,
            _os_path_exists,
            _os_stat,
            _os_chmod,
            _os_chown,
            _os_getlogin,
            _os_environ,
            _os_getuid,
            _pwd_getpwuid,
            _os_rename,
            _shutil_copy2,
            _shutil_move,
            _shutil_copyfileobj,
            _os_umask,
            _tempfile_mkstemp):

        from ansible.module_utils import basic
        basic._ANSIBLE_ARGS = None

        am = basic.AnsibleModule(
            argument_spec=dict(),
        )

        environ = dict()
        _os_environ.__getitem__ = environ.__getitem__
        _os_environ.__setitem__ = environ.__setitem__

        am.selinux_enabled = MagicMock()
        am.selinux_context = MagicMock()
        am.selinux_default_context = MagicMock()
        am.set_context_if_different = MagicMock()

        # test destination does not exist, no selinux, login name = 'root',
        # no environment, os.rename() succeeds
        _os_path_exists.side_effect = [False, False]
        _os_getlogin.return_value = 'root'
        _os_getuid.return_value = 0
        _pwd_getpwuid.return_value = ('root', '', 0, 0, '', '', '')
        _os_rename.return_value = None
        _os_umask.side_effect = [18, 0]
        am.selinux_enabled.return_value = False
        _os_chmod.reset_mock()
        _os_chown.reset_mock()
        am.set_context_if_different.reset_mock()
        am.atomic_move('/path/to/src', '/path/to/dest')
        _os_rename.assert_called_with(b'/path/to/src', b'/path/to/dest')
        self.assertEqual(_os_chmod.call_args_list, [call(b'/path/to/dest', basic.DEFAULT_PERM & ~18)])

        # same as above, except selinux_enabled
        _os_path_exists.side_effect = [False, False]
        _os_getlogin.return_value = 'root'
        _os_getuid.return_value = 0
        _pwd_getpwuid.return_value = ('root', '', 0, 0, '', '', '')
        _os_rename.return_value = None
        _os_umask.side_effect = [18, 0]
        mock_context = MagicMock()
        am.selinux_default_context.return_value = mock_context
        am.selinux_enabled.return_value = True
        _os_chmod.reset_mock()
        _os_chown.reset_mock()
        am.set_context_if_different.reset_mock()
        am.selinux_default_context.reset_mock()
        am.atomic_move('/path/to/src', '/path/to/dest')
        _os_rename.assert_called_with(b'/path/to/src', b'/path/to/dest')
        self.assertEqual(_os_chmod.call_args_list, [call(b'/path/to/dest', basic.DEFAULT_PERM & ~18)])
        self.assertEqual(am.selinux_default_context.call_args_list, [call('/path/to/dest')])
        self.assertEqual(am.set_context_if_different.call_args_list, [call('/path/to/dest', mock_context, False)])

        # now with dest present, no selinux, also raise OSError when using
        # os.getlogin() to test corner case with no tty
        _os_path_exists.side_effect = [True, True]
        _os_getlogin.side_effect = OSError()
        _os_getuid.return_value = 0
        _pwd_getpwuid.return_value = ('root', '', 0, 0, '', '', '')
        _os_rename.return_value = None
        _os_umask.side_effect = [18, 0]
        environ['LOGNAME'] = 'root'
        stat1 = MagicMock()
        stat1.st_mode = 0o0644
        stat1.st_uid = 0
        stat1.st_gid = 0
        _os_stat.side_effect = [stat1, ]
        am.selinux_enabled.return_value = False
        _os_chmod.reset_mock()
        _os_chown.reset_mock()
        am.set_context_if_different.reset_mock()
        am.atomic_move('/path/to/src', '/path/to/dest')
        _os_rename.assert_called_with(b'/path/to/src', b'/path/to/dest')

        # dest missing, selinux enabled
        _os_path_exists.side_effect = [True, True]
        _os_getlogin.return_value = 'root'
        _os_getuid.return_value = 0
        _pwd_getpwuid.return_value = ('root', '', 0, 0, '', '', '')
        _os_rename.return_value = None
        _os_umask.side_effect = [18, 0]
        stat1 = MagicMock()
        stat1.st_mode = 0o0644
        stat1.st_uid = 0
        stat1.st_gid = 0
        _os_stat.side_effect = [stat1, ]
        mock_context = MagicMock()
        am.selinux_context.return_value = mock_context
        am.selinux_enabled.return_value = True
        _os_chmod.reset_mock()
        _os_chown.reset_mock()
        am.set_context_if_different.reset_mock()
        am.selinux_default_context.reset_mock()
        am.atomic_move('/path/to/src', '/path/to/dest')
        _os_rename.assert_called_with(b'/path/to/src', b'/path/to/dest')
        self.assertEqual(am.selinux_context.call_args_list, [call('/path/to/dest')])
        self.assertEqual(am.set_context_if_different.call_args_list, [call('/path/to/dest', mock_context, False)])

        # now testing with exceptions raised
        # have os.stat raise OSError which is not EPERM
        _os_stat.side_effect = OSError()
        _os_path_exists.side_effect = [True, True]
        _os_getlogin.return_value = 'root'
        _os_getuid.return_value = 0
        _pwd_getpwuid.return_value = ('root', '', 0, 0, '', '', '')
        _os_rename.return_value = None
        _os_umask.side_effect = [18, 0]
        self.assertRaises(OSError, am.atomic_move, '/path/to/src', '/path/to/dest')

        # and now have os.stat return EPERM, which should not fail
        _os_stat.side_effect = OSError(errno.EPERM, 'testing os stat with EPERM')
        _os_path_exists.side_effect = [True, True]
        _os_getlogin.return_value = 'root'
        _os_getuid.return_value = 0
        _pwd_getpwuid.return_value = ('root', '', 0, 0, '', '', '')
        _os_rename.return_value = None
        _os_umask.side_effect = [18, 0]
        # FIXME: we don't assert anything here yet
        am.atomic_move('/path/to/src', '/path/to/dest')

        # now we test os.rename() raising errors...
        # first we test with a bad errno to verify it bombs out
        _os_path_exists.side_effect = [False, False]
        _os_getlogin.return_value = 'root'
        _os_getuid.return_value = 0
        _pwd_getpwuid.return_value = ('root', '', 0, 0, '', '', '')
        _os_umask.side_effect = [18, 0]
        _os_rename.side_effect = OSError(errno.EIO, 'failing with EIO')
        self.assertRaises(SystemExit, am.atomic_move, '/path/to/src', '/path/to/dest')

        # next we test with EPERM so it continues to the alternate code for moving
        # test with mkstemp raising an error first
        _os_path_exists.side_effect = [False, False]
        _os_getlogin.return_value = 'root'
        _os_getuid.return_value = 0
        _os_close.return_value = None
        _pwd_getpwuid.return_value = ('root', '', 0, 0, '', '', '')
        _os_umask.side_effect = [18, 0]
        _os_rename.side_effect = [OSError(errno.EPERM, 'failing with EPERM'), None]
        _tempfile_mkstemp.return_value = None
        _tempfile_mkstemp.side_effect = OSError()
        am.selinux_enabled.return_value = False
        self.assertRaises(SystemExit, am.atomic_move, '/path/to/src', '/path/to/dest')

        # then test with it creating a temp file
        _os_path_exists.side_effect = [False, False, False]
        _os_getlogin.return_value = 'root'
        _os_getuid.return_value = 0
        _pwd_getpwuid.return_value = ('root', '', 0, 0, '', '', '')
        _os_umask.side_effect = [18, 0]
        _os_rename.side_effect = [OSError(errno.EPERM, 'failing with EPERM'), None]
        mock_stat1 = MagicMock()
        mock_stat2 = MagicMock()
        mock_stat3 = MagicMock()
        _os_stat.return_value = [mock_stat1, mock_stat2, mock_stat3]
        _os_stat.side_effect = None
        _tempfile_mkstemp.return_value = (None, '/path/to/tempfile')
        _tempfile_mkstemp.side_effect = None
        am.selinux_enabled.return_value = False
        # FIXME: we don't assert anything here yet
        am.atomic_move('/path/to/src', '/path/to/dest')

        # same as above, but with selinux enabled
        _os_path_exists.side_effect = [False, False, False]
        _os_getlogin.return_value = 'root'
        _os_getuid.return_value = 0
        _pwd_getpwuid.return_value = ('root', '', 0, 0, '', '', '')
        _os_umask.side_effect = [18, 0]
        _os_rename.side_effect = [OSError(errno.EPERM, 'failing with EPERM'), None]
        _tempfile_mkstemp.return_value = (None, None)
        mock_context = MagicMock()
        am.selinux_default_context.return_value = mock_context
        am.selinux_enabled.return_value = True
        am.atomic_move('/path/to/src', '/path/to/dest')
