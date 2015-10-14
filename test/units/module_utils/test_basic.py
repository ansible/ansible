# -*- coding: utf-8 -*-
# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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
from __future__ import (absolute_import, division)
__metaclass__ = type

import errno
import sys

from six.moves import builtins

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock, mock_open, Mock

class TestModuleUtilsBasic(unittest.TestCase):
 
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_module_utils_basic_imports(self):
        realimport = builtins.__import__

        def _mock_import(name, *args, **kwargs):
            if name == 'json':
                raise ImportError()
            realimport(name, *args, **kwargs)

        with patch.object(builtins, '__import__', _mock_import, create=True) as m:
            m('ansible.module_utils.basic')
            builtins.__import__('ansible.module_utils.basic')

    def test_module_utils_basic_get_platform(self):
        with patch('platform.system', return_value='foo'):
            from ansible.module_utils.basic import get_platform
            self.assertEqual(get_platform(), 'foo')

    def test_module_utils_basic_get_distribution(self):
        from ansible.module_utils.basic import get_distribution

        with patch('platform.system', return_value='Foo'):
            self.assertEqual(get_distribution(), None)

        with patch('platform.system', return_value='Linux'):
            with patch('platform.linux_distribution', return_value=("foo", "1", "One")):
                self.assertEqual(get_distribution(), "Foo")

            with patch('os.path.isfile', return_value=True):
                def _dist(distname='', version='', id='', supported_dists=(), full_distribution_name=1):
                    if supported_dists != ():
                        return ("AmazonFooBar", "", "")
                    else:
                        return ("", "", "")
                 
                with patch('platform.linux_distribution', side_effect=_dist):
                    self.assertEqual(get_distribution(), "Amazonfoobar")

                def _dist(distname='', version='', id='', supported_dists=(), full_distribution_name=1):
                    if supported_dists != ():
                        return ("Bar", "2", "Two")
                    else:
                        return ("", "", "")
                
                with patch('platform.linux_distribution', side_effect=_dist):
                    self.assertEqual(get_distribution(), "Bar")
                
            with patch('platform.linux_distribution', side_effect=Exception("boo")):
                with patch('platform.dist', return_value=("bar", "2", "Two")):
                    self.assertEqual(get_distribution(), "Bar")

    def test_module_utils_basic_get_distribution_version(self):
        from ansible.module_utils.basic import get_distribution_version

        with patch('platform.system', return_value='Foo'):
            self.assertEqual(get_distribution_version(), None)

        with patch('platform.system', return_value='Linux'):
            with patch('platform.linux_distribution', return_value=("foo", "1", "One")):
                self.assertEqual(get_distribution_version(), "1")

            with patch('os.path.isfile', return_value=True):
                def _dist(distname='', version='', id='', supported_dists=(), full_distribution_name=1):
                    if supported_dists != ():
                        return ("AmazonFooBar", "2", "")
                    else:
                        return ("", "", "")

                with patch('platform.linux_distribution', side_effect=_dist):
                    self.assertEqual(get_distribution_version(), "2")

            with patch('platform.linux_distribution', side_effect=Exception("boo")):
                with patch('platform.dist', return_value=("bar", "3", "Three")):
                    self.assertEqual(get_distribution_version(), "3")

    def test_module_utils_basic_load_platform_subclass(self):
        class LinuxTest:
            pass

        class Foo(LinuxTest):
            platform = "Linux"
            distribution = None

        class Bar(LinuxTest):
            platform = "Linux"
            distribution = "Bar"

        from ansible.module_utils.basic import load_platform_subclass

        # match just the platform class, not a specific distribution
        with patch('ansible.module_utils.basic.get_platform', return_value="Linux"):
            with patch('ansible.module_utils.basic.get_distribution', return_value=None):
                self.assertIs(type(load_platform_subclass(LinuxTest)), Foo)

        # match both the distribution and platform class
        with patch('ansible.module_utils.basic.get_platform', return_value="Linux"):
            with patch('ansible.module_utils.basic.get_distribution', return_value="Bar"):
                self.assertIs(type(load_platform_subclass(LinuxTest)), Bar)

        # if neither match, the fallback should be the top-level class
        with patch('ansible.module_utils.basic.get_platform', return_value="Foo"):
            with patch('ansible.module_utils.basic.get_distribution', return_value=None):
                self.assertIs(type(load_platform_subclass(LinuxTest)), LinuxTest)

    def test_module_utils_basic_json_dict_converters(self):
        from ansible.module_utils.basic import json_dict_unicode_to_bytes, json_dict_bytes_to_unicode

        test_data = dict(
            item1 = u"Fóo",
            item2 = [u"Bár", u"Bam"],
            item3 = dict(sub1=u"Súb"),
            item4 = (u"föo", u"bär", u"©"),
            item5 = 42,
        )
        res = json_dict_unicode_to_bytes(test_data)
        res2 = json_dict_bytes_to_unicode(res)

        self.assertEqual(test_data, res2)

    def test_module_utils_basic_heuristic_log_sanitize(self):
        from ansible.module_utils.basic import heuristic_log_sanitize

        URL_SECRET = 'http://username:pas:word@foo.com/data'
        SSH_SECRET = 'username:pas:word@foo.com/data'

        def _gen_data(records, per_rec, top_level, secret_text):
            hostvars = {'hostvars': {}}
            for i in range(1, records, 1):
                host_facts = {'host%s' % i:
                                {'pstack':
                                    {'running': '875.1',
                                     'symlinked': '880.0',
                                     'tars': [],
                                     'versions': ['885.0']},
                             }}
                if per_rec:
                    host_facts['host%s' % i]['secret'] = secret_text
                hostvars['hostvars'].update(host_facts)
            if top_level:
                hostvars['secret'] = secret_text
            return hostvars

        url_data = repr(_gen_data(3, True, True, URL_SECRET))
        ssh_data = repr(_gen_data(3, True, True, SSH_SECRET))

        url_output = heuristic_log_sanitize(url_data)
        ssh_output = heuristic_log_sanitize(ssh_data)

        # Basic functionality: Successfully hid the password
        try:
            self.assertNotIn('pas:word', url_output)
            self.assertNotIn('pas:word', ssh_output)

            # Slightly more advanced, we hid all of the password despite the ":"
            self.assertNotIn('pas', url_output)
            self.assertNotIn('pas', ssh_output)
        except AttributeError:
            # python2.6 or less's unittest
            self.assertFalse('pas:word' in url_output, '%s is present in %s' % ('"pas:word"', url_output))
            self.assertFalse('pas:word' in ssh_output, '%s is present in %s' % ('"pas:word"', ssh_output))

            self.assertFalse('pas' in url_output, '%s is present in %s' % ('"pas"', url_output))
            self.assertFalse('pas' in ssh_output, '%s is present in %s' % ('"pas"', ssh_output))

        # In this implementation we replace the password with 8 "*" which is
        # also the length of our password.  The url fields should be able to
        # accurately detect where the password ends so the length should be
        # the same:
        self.assertEqual(len(url_output), len(url_data))

        # ssh checking is harder as the heuristic is overzealous in many
        # cases.  Since the input will have at least one ":" present before
        # the password we can tell some things about the beginning and end of
        # the data, though:
        self.assertTrue(ssh_output.startswith("{'"))
        self.assertTrue(ssh_output.endswith("}"))
        try:
            self.assertIn(":********@foo.com/data'", ssh_output)
        except AttributeError:
            # python2.6 or less's unittest
            self.assertTrue(":********@foo.com/data'" in ssh_output, '%s is not present in %s' % (":********@foo.com/data'", ssh_output))

    def test_module_utils_basic_get_module_path(self):
        from ansible.module_utils.basic import get_module_path
        with patch('os.path.realpath', return_value='/path/to/foo/'):
            self.assertEqual(get_module_path(), '/path/to/foo')

    @unittest.skipIf(sys.version_info[0] >= 3, "Python 3 is not supported on targets (yet)")
    def test_module_utils_basic_ansible_module_creation(self):
        from ansible.module_utils import basic

        basic.MODULE_COMPLEX_ARGS = '{}'
        am = basic.AnsibleModule(
            argument_spec=dict(),
        )

        arg_spec = dict(
            foo = dict(required=True),
            bar = dict(),
            bam = dict(),
            baz = dict(),
        )
        mut_ex = (('bar', 'bam'),)
        req_to = (('bam', 'baz'),)

        # should test ok
        basic.MODULE_COMPLEX_ARGS = '{"foo":"hello"}'
        am = basic.AnsibleModule(
            argument_spec = arg_spec,
            mutually_exclusive = mut_ex,
            required_together = req_to,
            no_log=True, 
            check_invalid_arguments=False, 
            add_file_common_args=True, 
            supports_check_mode=True,
        )

        # FIXME: add asserts here to verify the basic config

        # fail, because a required param was not specified
        basic.MODULE_COMPLEX_ARGS = '{}'
        self.assertRaises(
            SystemExit,
            basic.AnsibleModule,
            argument_spec = arg_spec,
            mutually_exclusive = mut_ex,
            required_together = req_to,
            no_log=True,
            check_invalid_arguments=False,
            add_file_common_args=True,
            supports_check_mode=True,
        )

        # fail because of mutually exclusive parameters
        basic.MODULE_COMPLEX_ARGS = '{"foo":"hello", "bar": "bad", "bam": "bad"}'
        self.assertRaises(
            SystemExit, 
            basic.AnsibleModule,
            argument_spec = arg_spec,
            mutually_exclusive = mut_ex,
            required_together = req_to,
            no_log=True, 
            check_invalid_arguments=False, 
            add_file_common_args=True, 
            supports_check_mode=True,
        )

        # fail because a param required due to another param was not specified
        basic.MODULE_COMPLEX_ARGS = '{"bam":"bad"}'
        self.assertRaises(
            SystemExit,
            basic.AnsibleModule,
            argument_spec = arg_spec,
            mutually_exclusive = mut_ex,
            required_together = req_to,
            no_log=True,
            check_invalid_arguments=False,
            add_file_common_args=True,
            supports_check_mode=True,
        )

    def test_module_utils_basic_ansible_module_load_file_common_arguments(self):
        from ansible.module_utils import basic

        basic.MODULE_COMPLEX_ARGS = '{}'
        am = basic.AnsibleModule(
            argument_spec = dict(),
        )

        am.selinux_mls_enabled = MagicMock()
        am.selinux_mls_enabled.return_value = True
        am.selinux_default_context = MagicMock()
        am.selinux_default_context.return_value = 'unconfined_u:object_r:default_t:s0'.split(':', 3)

        # with no params, the result should be an empty dict
        res = am.load_file_common_arguments(params=dict())
        self.assertEqual(res, dict())

        base_params = dict(
            path = '/path/to/file',
            mode = 0o600,
            owner = 'root',
            group = 'root',
            seuser = '_default',
            serole = '_default',
            setype = '_default',
            selevel = '_default',
        )

        extended_params = base_params.copy()
        extended_params.update(dict(
            follow = True,
            foo = 'bar',
        ))

        final_params = base_params.copy()
        final_params.update(dict(
            path = '/path/to/real_file',
            secontext=['unconfined_u', 'object_r', 'default_t', 's0'],
        ))

        # with the proper params specified, the returned dictionary should represent
        # only those params which have something to do with the file arguments, excluding
        # other params and updated as required with proper values which may have been
        # massaged by the method
        with patch('os.path.islink', return_value=True):
            with patch('os.path.realpath', return_value='/path/to/real_file'):
                res = am.load_file_common_arguments(params=extended_params)
                self.assertEqual(res, final_params)

    def test_module_utils_basic_ansible_module_selinux_mls_enabled(self):
        from ansible.module_utils import basic

        basic.MODULE_COMPLEX_ARGS = '{}'
        am = basic.AnsibleModule(
            argument_spec = dict(),
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

        basic.MODULE_COMPLEX_ARGS = '{}'
        am = basic.AnsibleModule(
            argument_spec = dict(),
        )

        am.selinux_mls_enabled = MagicMock()
        am.selinux_mls_enabled.return_value = False
        self.assertEqual(am.selinux_initial_context(), [None, None, None])
        am.selinux_mls_enabled.return_value = True
        self.assertEqual(am.selinux_initial_context(), [None, None, None, None])

    def test_module_utils_basic_ansible_module_selinux_enabled(self):
        from ansible.module_utils import basic

        basic.MODULE_COMPLEX_ARGS = '{}'
        am = basic.AnsibleModule(
            argument_spec = dict(),
        )

        # we first test the cases where the python selinux lib is
        # not installed, which has two paths: one in which the system
        # does have selinux installed (and the selinuxenabled command
        # is present and returns 0 when run), or selinux is not installed
        basic.HAVE_SELINUX = False
        am.get_bin_path = MagicMock()
        am.get_bin_path.return_value = '/path/to/selinuxenabled'
        am.run_command = MagicMock()
        am.run_command.return_value=(0, '', '')
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

        basic.MODULE_COMPLEX_ARGS = '{}'
        am = basic.AnsibleModule(
            argument_spec = dict(),
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

        basic.MODULE_COMPLEX_ARGS = '{}'
        am = basic.AnsibleModule(
            argument_spec = dict(),
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

        basic.MODULE_COMPLEX_ARGS = '{}'
        basic.SELINUX_SPECIAL_FS = 'nfs,nfsd,foos'
        am = basic.AnsibleModule(
            argument_spec = dict(),
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

    def test_module_utils_basic_ansible_module_to_filesystem_str(self):
        from ansible.module_utils import basic

        basic.MODULE_COMPLEX_ARGS = '{}'
        am = basic.AnsibleModule(
            argument_spec = dict(),
        )

        self.assertEqual(am._to_filesystem_str(u'foo'), b'foo')
        self.assertEqual(am._to_filesystem_str(u'föö'), b'f\xc3\xb6\xc3\xb6')
        
    def test_module_utils_basic_ansible_module_user_and_group(self):
        from ansible.module_utils import basic

        basic.MODULE_COMPLEX_ARGS = '{}'
        am = basic.AnsibleModule(
            argument_spec = dict(),
        )

        mock_stat = MagicMock()
        mock_stat.st_uid = 0
        mock_stat.st_gid = 0

        with patch('os.lstat', return_value=mock_stat):
            self.assertEqual(am.user_and_group('/path/to/file'), (0, 0))

    def test_module_utils_basic_ansible_module_find_mount_point(self):
        from ansible.module_utils import basic

        basic.MODULE_COMPLEX_ARGS = '{}'
        am = basic.AnsibleModule(
            argument_spec = dict(),
        )

        def _mock_ismount(path):
            if path == '/':
                return True
            return False

        with patch('os.path.ismount', side_effect=_mock_ismount):
            self.assertEqual(am.find_mount_point('/root/fs/../mounted/path/to/whatever'), '/')

        def _mock_ismount(path):
            if path == '/subdir/mount':
                return True
            return False

        with patch('os.path.ismount', side_effect=_mock_ismount):
            self.assertEqual(am.find_mount_point('/subdir/mount/path/to/whatever'), '/subdir/mount')

    def test_module_utils_basic_ansible_module_set_context_if_different(self):
        from ansible.module_utils import basic

        basic.MODULE_COMPLEX_ARGS = '{}'
        am = basic.AnsibleModule(
            argument_spec = dict(),
        )

        basic.HAS_SELINUX = False

        am.selinux_enabled = MagicMock(return_value=False)
        self.assertEqual(am.set_context_if_different('/path/to/file', ['foo_u', 'foo_r', 'foo_t', 's0'], True), True)
        self.assertEqual(am.set_context_if_different('/path/to/file', ['foo_u', 'foo_r', 'foo_t', 's0'], False), False)

        basic.HAS_SELINUX = True

        am.selinux_enabled = MagicMock(return_value=True)
        am.selinux_context = MagicMock(return_value=['bar_u', 'bar_r', None, None])
        am.is_special_selinux_path = MagicMock(return_value=(False, None))

        basic.selinux = Mock()
        with patch.dict('sys.modules', {'selinux': basic.selinux}):
            with patch('selinux.lsetfilecon', return_value=0) as m:
                self.assertEqual(am.set_context_if_different('/path/to/file', ['foo_u', 'foo_r', 'foo_t', 's0'], False), True)
                m.assert_called_with(b'/path/to/file', 'foo_u:foo_r:foo_t:s0')
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
                m.assert_called_with(b'/path/to/file', 'sp_u:sp_r:sp_t:s0')

        delattr(basic, 'selinux')

    def test_module_utils_basic_ansible_module_set_owner_if_different(self):
        from ansible.module_utils import basic

        basic.MODULE_COMPLEX_ARGS = '{}'
        am = basic.AnsibleModule(
            argument_spec = dict(),
        )

        self.assertEqual(am.set_owner_if_different('/path/to/file', None, True), True)
        self.assertEqual(am.set_owner_if_different('/path/to/file', None, False), False)

        am.user_and_group = MagicMock(return_value=(500, 500))

        with patch('os.lchown', return_value=None) as m:
            self.assertEqual(am.set_owner_if_different('/path/to/file', 0, False), True)
            m.assert_called_with('/path/to/file', 0, -1)

            def _mock_getpwnam(*args, **kwargs):
                mock_pw = MagicMock()
                mock_pw.pw_uid = 0
                return mock_pw

            m.reset_mock()
            with patch('pwd.getpwnam', side_effect=_mock_getpwnam):
                self.assertEqual(am.set_owner_if_different('/path/to/file', 'root', False), True)
                m.assert_called_with('/path/to/file', 0, -1)

            with patch('pwd.getpwnam', side_effect=KeyError):
                self.assertRaises(SystemExit, am.set_owner_if_different, '/path/to/file', 'root', False)

            m.reset_mock()
            am.check_mode = True
            self.assertEqual(am.set_owner_if_different('/path/to/file', 0, False), True)
            self.assertEqual(m.called, False)
            am.check_mode = False

        with patch('os.lchown', side_effect=OSError) as m:
            self.assertRaises(SystemExit, am.set_owner_if_different, '/path/to/file', 'root', False)

    def test_module_utils_basic_ansible_module_set_group_if_different(self):
        from ansible.module_utils import basic

        basic.MODULE_COMPLEX_ARGS = '{}'
        am = basic.AnsibleModule(
            argument_spec = dict(),
        )

        self.assertEqual(am.set_group_if_different('/path/to/file', None, True), True)
        self.assertEqual(am.set_group_if_different('/path/to/file', None, False), False)

        am.user_and_group = MagicMock(return_value=(500, 500))

        with patch('os.lchown', return_value=None) as m:
            self.assertEqual(am.set_group_if_different('/path/to/file', 0, False), True)
            m.assert_called_with('/path/to/file', -1, 0)

            def _mock_getgrnam(*args, **kwargs):
                mock_gr = MagicMock()
                mock_gr.gr_gid = 0
                return mock_gr

            m.reset_mock()
            with patch('grp.getgrnam', side_effect=_mock_getgrnam):
                self.assertEqual(am.set_group_if_different('/path/to/file', 'root', False), True)
                m.assert_called_with('/path/to/file', -1, 0)

            with patch('grp.getgrnam', side_effect=KeyError):
                self.assertRaises(SystemExit, am.set_group_if_different, '/path/to/file', 'root', False)

            m.reset_mock()
            am.check_mode = True
            self.assertEqual(am.set_group_if_different('/path/to/file', 0, False), True)
            self.assertEqual(m.called, False)
            am.check_mode = False

        with patch('os.lchown', side_effect=OSError) as m:
            self.assertRaises(SystemExit, am.set_group_if_different, '/path/to/file', 'root', False)

    def test_module_utils_basic_ansible_module_set_mode_if_different(self):
        from ansible.module_utils import basic

        basic.MODULE_COMPLEX_ARGS = '{}'
        am = basic.AnsibleModule(
            argument_spec = dict(),
        )

        mock_stat1 = MagicMock()
        mock_stat1.st_mode = 0o444
        mock_stat2 = MagicMock()
        mock_stat2.st_mode = 0o660

        with patch('os.lstat', side_effect=[mock_stat1]):
            self.assertEqual(am.set_mode_if_different('/path/to/file', None, True), True)
        with patch('os.lstat', side_effect=[mock_stat1]):
            self.assertEqual(am.set_mode_if_different('/path/to/file', None, False), False)

        with patch('os.lstat') as m:
            with patch('os.lchmod', return_value=None, create=True) as m_os:
                m.side_effect = [mock_stat1, mock_stat2, mock_stat2]
                self.assertEqual(am.set_mode_if_different('/path/to/file', 0o660, False), True)
                m_os.assert_called_with('/path/to/file', 0o660)

                m.side_effect = [mock_stat1, mock_stat2, mock_stat2]
                am._symbolic_mode_to_octal = MagicMock(return_value=0o660)
                self.assertEqual(am.set_mode_if_different('/path/to/file', 'o+w,g+w,a-r', False), True)
                m_os.assert_called_with('/path/to/file', 0o660)

                m.side_effect = [mock_stat1, mock_stat2, mock_stat2]
                am._symbolic_mode_to_octal = MagicMock(side_effect=Exception)
                self.assertRaises(SystemExit, am.set_mode_if_different, '/path/to/file', 'o+w,g+w,a-r', False)

                m.side_effect = [mock_stat1, mock_stat2, mock_stat2]
                am.check_mode = True
                self.assertEqual(am.set_mode_if_different('/path/to/file', 0o660, False), True)
                am.check_mode = False

        # FIXME: this isn't working yet
        #with patch('os.lstat', side_effect=[mock_stat1, mock_stat2]):
        #    with patch('os.lchmod', return_value=None) as m_os:
        #        del m_os.lchmod
        #        with patch('os.path.islink', return_value=False):
        #            with patch('os.chmod', return_value=None) as m_chmod:
        #                self.assertEqual(am.set_mode_if_different('/path/to/file/no_lchmod', 0o660, False), True)
        #                m_chmod.assert_called_with('/path/to/file', 0o660)
        #        with patch('os.path.islink', return_value=True):
        #            with patch('os.chmod', return_value=None) as m_chmod:
        #                with patch('os.stat', return_value=mock_stat2):
        #                    self.assertEqual(am.set_mode_if_different('/path/to/file', 0o660, False), True)
        #                    m_chmod.assert_called_with('/path/to/file', 0o660)

