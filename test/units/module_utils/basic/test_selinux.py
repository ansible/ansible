# -*- coding: utf-8 -*-
# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2016 Toshio Kuratomi <tkuratomi@ansible.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import errno
import json

from units.mock.procenv import ModuleTestCase, swap_stdin_and_argv

from ansible.compat.tests.mock import patch, MagicMock, mock_open, Mock
from ansible.module_utils.six.moves import builtins

realimport = builtins.__import__


class TestSELinux(ModuleTestCase):
    def test_module_utils_basic_ansible_module_selinux_mls_enabled(self):
        from ansible.module_utils import basic
        basic._ANSIBLE_ARGS = None

        am = basic.AnsibleModule(
            argument_spec=dict(),
        )

        basic.HAVE_SELINUX = False
        self.assertEqual(am.selinux_mls_enabled(), False)

        basic.HAVE_SELINUX = True
        basic.selinux = Mock()
        with patch.dict('sys.modules', {'selinux': basic.selinux}):
            with patch('selinux.is_selinux_mls_enabled', return_value=0):
                self.assertEqual(am.selinux_mls_enabled(), False)
            with patch('selinux.is_selinux_mls_enabled', return_value=1):
                self.assertEqual(am.selinux_mls_enabled(), True)
        delattr(basic, 'selinux')

    def test_module_utils_basic_ansible_module_selinux_initial_context(self):
        from ansible.module_utils import basic
        basic._ANSIBLE_ARGS = None

        am = basic.AnsibleModule(
            argument_spec=dict(),
        )

        am.selinux_mls_enabled = MagicMock()
        am.selinux_mls_enabled.return_value = False
        self.assertEqual(am.selinux_initial_context(), [None, None, None])
        am.selinux_mls_enabled.return_value = True
        self.assertEqual(am.selinux_initial_context(), [None, None, None, None])

    def test_module_utils_basic_ansible_module_selinux_enabled(self):
        from ansible.module_utils import basic
        basic._ANSIBLE_ARGS = None

        am = basic.AnsibleModule(
            argument_spec=dict(),
        )

        # we first test the cases where the python selinux lib is
        # not installed, which has two paths: one in which the system
        # does have selinux installed (and the selinuxenabled command
        # is present and returns 0 when run), or selinux is not installed
        basic.HAVE_SELINUX = False
        am.get_bin_path = MagicMock()
        am.get_bin_path.return_value = '/path/to/selinuxenabled'
        am.run_command = MagicMock()
        am.run_command.return_value = (0, '', '')
        self.assertRaises(SystemExit, am.selinux_enabled)
        am.get_bin_path.return_value = None
        self.assertEqual(am.selinux_enabled(), False)

        # finally we test the case where the python selinux lib is installed,
        # and both possibilities there (enabled vs. disabled)
        basic.HAVE_SELINUX = True
        basic.selinux = Mock()
        with patch.dict('sys.modules', {'selinux': basic.selinux}):
            with patch('selinux.is_selinux_enabled', return_value=0):
                self.assertEqual(am.selinux_enabled(), False)
            with patch('selinux.is_selinux_enabled', return_value=1):
                self.assertEqual(am.selinux_enabled(), True)
        delattr(basic, 'selinux')

    def test_module_utils_basic_ansible_module_selinux_default_context(self):
        from ansible.module_utils import basic
        basic._ANSIBLE_ARGS = None

        am = basic.AnsibleModule(
            argument_spec=dict(),
        )

        am.selinux_initial_context = MagicMock(return_value=[None, None, None, None])
        am.selinux_enabled = MagicMock(return_value=True)

        # we first test the cases where the python selinux lib is not installed
        basic.HAVE_SELINUX = False
        self.assertEqual(am.selinux_default_context(path='/foo/bar'), [None, None, None, None])

        # all following tests assume the python selinux bindings are installed
        basic.HAVE_SELINUX = True

        basic.selinux = Mock()

        with patch.dict('sys.modules', {'selinux': basic.selinux}):
            # next, we test with a mocked implementation of selinux.matchpathcon to simulate
            # an actual context being found
            with patch('selinux.matchpathcon', return_value=[0, 'unconfined_u:object_r:default_t:s0']):
                self.assertEqual(am.selinux_default_context(path='/foo/bar'), ['unconfined_u', 'object_r', 'default_t', 's0'])

            # we also test the case where matchpathcon returned a failure
            with patch('selinux.matchpathcon', return_value=[-1, '']):
                self.assertEqual(am.selinux_default_context(path='/foo/bar'), [None, None, None, None])

            # finally, we test where an OSError occurred during matchpathcon's call
            with patch('selinux.matchpathcon', side_effect=OSError):
                self.assertEqual(am.selinux_default_context(path='/foo/bar'), [None, None, None, None])

        delattr(basic, 'selinux')

    def test_module_utils_basic_ansible_module_selinux_context(self):
        from ansible.module_utils import basic
        basic._ANSIBLE_ARGS = None

        am = basic.AnsibleModule(
            argument_spec=dict(),
        )

        am.selinux_initial_context = MagicMock(return_value=[None, None, None, None])
        am.selinux_enabled = MagicMock(return_value=True)

        # we first test the cases where the python selinux lib is not installed
        basic.HAVE_SELINUX = False
        self.assertEqual(am.selinux_context(path='/foo/bar'), [None, None, None, None])

        # all following tests assume the python selinux bindings are installed
        basic.HAVE_SELINUX = True

        basic.selinux = Mock()

        with patch.dict('sys.modules', {'selinux': basic.selinux}):
            # next, we test with a mocked implementation of selinux.lgetfilecon_raw to simulate
            # an actual context being found
            with patch('selinux.lgetfilecon_raw', return_value=[0, 'unconfined_u:object_r:default_t:s0']):
                self.assertEqual(am.selinux_context(path='/foo/bar'), ['unconfined_u', 'object_r', 'default_t', 's0'])

            # we also test the case where matchpathcon returned a failure
            with patch('selinux.lgetfilecon_raw', return_value=[-1, '']):
                self.assertEqual(am.selinux_context(path='/foo/bar'), [None, None, None, None])

            # finally, we test where an OSError occurred during matchpathcon's call
            e = OSError()
            e.errno = errno.ENOENT
            with patch('selinux.lgetfilecon_raw', side_effect=e):
                self.assertRaises(SystemExit, am.selinux_context, path='/foo/bar')

            e = OSError()
            with patch('selinux.lgetfilecon_raw', side_effect=e):
                self.assertRaises(SystemExit, am.selinux_context, path='/foo/bar')

        delattr(basic, 'selinux')

    def test_module_utils_basic_ansible_module_is_special_selinux_path(self):
        from ansible.module_utils import basic

        args = json.dumps(dict(ANSIBLE_MODULE_ARGS={'_ansible_selinux_special_fs': "nfs,nfsd,foos",
                                                    '_ansible_remote_tmp': "/tmp",
                                                    '_ansible_keep_remote_files': False}))

        with swap_stdin_and_argv(stdin_data=args):
            basic._ANSIBLE_ARGS = None
            am = basic.AnsibleModule(
                argument_spec=dict(),
            )

            def _mock_find_mount_point(path):
                if path.startswith('/some/path'):
                    return '/some/path'
                elif path.startswith('/weird/random/fstype'):
                    return '/weird/random/fstype'
                return '/'

            am.find_mount_point = MagicMock(side_effect=_mock_find_mount_point)
            am.selinux_context = MagicMock(return_value=['foo_u', 'foo_r', 'foo_t', 's0'])

            m = mock_open()
            m.side_effect = OSError

            with patch.object(builtins, 'open', m, create=True):
                self.assertEqual(am.is_special_selinux_path('/some/path/that/should/be/nfs'), (False, None))

            mount_data = [
                '/dev/disk1 / ext4 rw,seclabel,relatime,data=ordered 0 0\n',
                '1.1.1.1:/path/to/nfs /some/path nfs ro 0 0\n',
                'whatever /weird/random/fstype foos rw 0 0\n',
            ]

            # mock_open has a broken readlines() implementation apparently...
            # this should work by default but doesn't, so we fix it
            m = mock_open(read_data=''.join(mount_data))
            m.return_value.readlines.return_value = mount_data

            with patch.object(builtins, 'open', m, create=True):
                self.assertEqual(am.is_special_selinux_path('/some/random/path'), (False, None))
                self.assertEqual(am.is_special_selinux_path('/some/path/that/should/be/nfs'), (True, ['foo_u', 'foo_r', 'foo_t', 's0']))
                self.assertEqual(am.is_special_selinux_path('/weird/random/fstype/path'), (True, ['foo_u', 'foo_r', 'foo_t', 's0']))

    def test_module_utils_basic_ansible_module_set_context_if_different(self):
        from ansible.module_utils import basic
        basic._ANSIBLE_ARGS = None

        am = basic.AnsibleModule(
            argument_spec=dict(),
        )

        basic.HAVE_SELINUX = False

        am.selinux_enabled = MagicMock(return_value=False)
        self.assertEqual(am.set_context_if_different('/path/to/file', ['foo_u', 'foo_r', 'foo_t', 's0'], True), True)
        self.assertEqual(am.set_context_if_different('/path/to/file', ['foo_u', 'foo_r', 'foo_t', 's0'], False), False)

        basic.HAVE_SELINUX = True

        am.selinux_enabled = MagicMock(return_value=True)
        am.selinux_context = MagicMock(return_value=['bar_u', 'bar_r', None, None])
        am.is_special_selinux_path = MagicMock(return_value=(False, None))

        basic.selinux = Mock()
        with patch.dict('sys.modules', {'selinux': basic.selinux}):
            with patch('selinux.lsetfilecon', return_value=0) as m:
                self.assertEqual(am.set_context_if_different('/path/to/file', ['foo_u', 'foo_r', 'foo_t', 's0'], False), True)
                m.assert_called_with('/path/to/file', 'foo_u:foo_r:foo_t:s0')
                m.reset_mock()
                am.check_mode = True
                self.assertEqual(am.set_context_if_different('/path/to/file', ['foo_u', 'foo_r', 'foo_t', 's0'], False), True)
                self.assertEqual(m.called, False)
                am.check_mode = False

            with patch('selinux.lsetfilecon', return_value=1) as m:
                self.assertRaises(SystemExit, am.set_context_if_different, '/path/to/file', ['foo_u', 'foo_r', 'foo_t', 's0'], True)

            with patch('selinux.lsetfilecon', side_effect=OSError) as m:
                self.assertRaises(SystemExit, am.set_context_if_different, '/path/to/file', ['foo_u', 'foo_r', 'foo_t', 's0'], True)

            am.is_special_selinux_path = MagicMock(return_value=(True, ['sp_u', 'sp_r', 'sp_t', 's0']))

            with patch('selinux.lsetfilecon', return_value=0) as m:
                self.assertEqual(am.set_context_if_different('/path/to/file', ['foo_u', 'foo_r', 'foo_t', 's0'], False), True)
                m.assert_called_with('/path/to/file', 'sp_u:sp_r:sp_t:s0')

        delattr(basic, 'selinux')
