# -*- coding: utf-8 -*-
# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2016 Toshio Kuratomi <tkuratomi@ansible.com>
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
import json
import os
import sys
from io import BytesIO, StringIO

from units.mock.procenv import ModuleTestCase, swap_stdin_and_argv

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock, mock_open, Mock, call
from ansible.module_utils.six.moves import builtins

realimport = builtins.__import__


class TestModuleUtilsBasic(ModuleTestCase):

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
        def _mock_import(name, *args, **kwargs):
            if name == 'selinux':
                raise ImportError
            return realimport(name, *args, **kwargs)

        try:
            self.clear_modules(['selinux', 'ansible.module_utils.basic'])
            mod = builtins.__import__('ansible.module_utils.basic')
            self.assertTrue(mod.module_utils.basic.HAVE_SELINUX)
        except ImportError:
            # no selinux on test system, so skip
            pass

        self.clear_modules(['selinux', 'ansible.module_utils.basic'])
        mock_import.side_effect = _mock_import
        mod = builtins.__import__('ansible.module_utils.basic')
        self.assertFalse(mod.module_utils.basic.HAVE_SELINUX)

    @patch.object(builtins, '__import__')
    def test_module_utils_basic_import_json(self, mock_import):
        def _mock_import(name, *args, **kwargs):
            if name == 'json':
                raise ImportError
            elif name == 'simplejson':
                return MagicMock()
            return realimport(name, *args, **kwargs)

        self.clear_modules(['json', 'ansible.module_utils.basic'])
        mod = builtins.__import__('ansible.module_utils.basic')

        self.clear_modules(['json', 'ansible.module_utils.basic'])
        mock_import.side_effect = _mock_import
        mod = builtins.__import__('ansible.module_utils.basic')

    # FIXME: doesn't work yet
    # @patch.object(builtins, 'bytes')
    # def test_module_utils_basic_bytes(self, mock_bytes):
    #     mock_bytes.side_effect = NameError()
    #     from ansible.module_utils import basic

    @patch.object(builtins, '__import__')
    @unittest.skipIf(sys.version_info[0] >= 3, "literal_eval is available in every version of Python3")
    def test_module_utils_basic_import_literal_eval(self, mock_import):
        def _mock_import(name, *args, **kwargs):
            try:
                fromlist = kwargs.get('fromlist', args[2])
            except IndexError:
                fromlist = []
            if name == 'ast' and 'literal_eval' in fromlist:
                raise ImportError
            return realimport(name, *args, **kwargs)

        mock_import.side_effect = _mock_import
        self.clear_modules(['ast', 'ansible.module_utils.basic'])
        mod = builtins.__import__('ansible.module_utils.basic')
        self.assertEqual(mod.module_utils.basic.literal_eval("'1'"), "1")
        self.assertEqual(mod.module_utils.basic.literal_eval("1"), 1)
        self.assertEqual(mod.module_utils.basic.literal_eval("-1"), -1)
        self.assertEqual(mod.module_utils.basic.literal_eval("(1,2,3)"), (1, 2, 3))
        self.assertEqual(mod.module_utils.basic.literal_eval("[1]"), [1])
        self.assertEqual(mod.module_utils.basic.literal_eval("True"), True)
        self.assertEqual(mod.module_utils.basic.literal_eval("False"), False)
        self.assertEqual(mod.module_utils.basic.literal_eval("None"), None)
        # self.assertEqual(mod.module_utils.basic.literal_eval('{"a": 1}'), dict(a=1))
        self.assertRaises(ValueError, mod.module_utils.basic.literal_eval, "asdfasdfasdf")

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

    def test_module_utils_basic_get_platform(self):
        with patch('platform.system', return_value='foo'):
            from ansible.module_utils.basic import get_platform
            self.assertEqual(get_platform(), 'foo')

    def test_module_utils_basic_get_distribution(self):
        from ansible.module_utils.basic import get_distribution

        with patch('platform.system', return_value='Foo'):
            self.assertEqual(get_distribution(), None)

        with patch('platform.system', return_value='Linux'):
            with patch('platform.linux_distribution', return_value=["foo"]):
                self.assertEqual(get_distribution(), "Foo")

            with patch('os.path.isfile', return_value=True):
                with patch('platform.linux_distribution', side_effect=[("AmazonFooBar", )]):
                    self.assertEqual(get_distribution(), "Amazonfoobar")

                with patch('platform.linux_distribution', side_effect=(("", ), ("AmazonFooBam",))):
                    self.assertEqual(get_distribution(), "Amazon")

                with patch('platform.linux_distribution', side_effect=[("", ), ("", )]):
                    self.assertEqual(get_distribution(), "OtherLinux")

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
            item1=u"Fóo",
            item2=[u"Bár", u"Bam"],
            item3=dict(sub1=u"Súb"),
            item4=(u"föo", u"bär", u"©"),
            item5=42,
        )
        res = json_dict_unicode_to_bytes(test_data)
        res2 = json_dict_bytes_to_unicode(res)

        self.assertEqual(test_data, res2)

    def test_module_utils_basic_get_module_path(self):
        from ansible.module_utils.basic import get_module_path
        with patch('os.path.realpath', return_value='/path/to/foo/'):
            self.assertEqual(get_module_path(), '/path/to/foo')

    def test_module_utils_basic_ansible_module_creation(self):
        from ansible.module_utils import basic

        am = basic.AnsibleModule(
            argument_spec=dict(),
        )

        arg_spec = dict(
            foo=dict(required=True),
            bar=dict(),
            bam=dict(),
            baz=dict(),
        )
        mut_ex = (('bar', 'bam'),)
        req_to = (('bam', 'baz'),)

        # should test ok
        args = json.dumps(dict(ANSIBLE_MODULE_ARGS={"foo": "hello"}))

        with swap_stdin_and_argv(stdin_data=args):
            basic._ANSIBLE_ARGS = None
            am = basic.AnsibleModule(
                argument_spec=arg_spec,
                mutually_exclusive=mut_ex,
                required_together=req_to,
                no_log=True,
                check_invalid_arguments=False,
                add_file_common_args=True,
                supports_check_mode=True,
            )

        # FIXME: add asserts here to verify the basic config

        # fail, because a required param was not specified
        args = json.dumps(dict(ANSIBLE_MODULE_ARGS={}))

        with swap_stdin_and_argv(stdin_data=args):
            basic._ANSIBLE_ARGS = None
            self.assertRaises(
                SystemExit,
                basic.AnsibleModule,
                argument_spec=arg_spec,
                mutually_exclusive=mut_ex,
                required_together=req_to,
                no_log=True,
                check_invalid_arguments=False,
                add_file_common_args=True,
                supports_check_mode=True,
            )

        # fail because of mutually exclusive parameters
        args = json.dumps(dict(ANSIBLE_MODULE_ARGS={"foo": "hello", "bar": "bad", "bam": "bad"}))

        with swap_stdin_and_argv(stdin_data=args):
            basic._ANSIBLE_ARGS = None
            self.assertRaises(
                SystemExit,
                basic.AnsibleModule,
                argument_spec=arg_spec,
                mutually_exclusive=mut_ex,
                required_together=req_to,
                no_log=True,
                check_invalid_arguments=False,
                add_file_common_args=True,
                supports_check_mode=True,
            )

        # fail because a param required due to another param was not specified
        args = json.dumps(dict(ANSIBLE_MODULE_ARGS={"bam": "bad"}))

        with swap_stdin_and_argv(stdin_data=args):
            basic._ANSIBLE_ARGS = None
            self.assertRaises(
                SystemExit,
                basic.AnsibleModule,
                argument_spec=arg_spec,
                mutually_exclusive=mut_ex,
                required_together=req_to,
                no_log=True,
                check_invalid_arguments=False,
                add_file_common_args=True,
                supports_check_mode=True,
            )

    def test_module_utils_basic_ansible_module_with_options_creation(self):
        from ansible.module_utils import basic

        options_spec = dict(
            foo=dict(required=True, aliases=['dup']),
            bar=dict(),
            bam=dict(),
            baz=dict(),
            bam1=dict(),
            bam2=dict(default='test')
        )
        arg_spec = dict(
            foobar=dict(
                type='list',
                elements='dict',
                options=options_spec,
                mutually_exclusive=[
                    ['bam', 'bam1']
                ],
                required_if=[
                    ['foo', 'hello', ['bam']],
                    ['foo', 'bam2', ['bam2']]
                ],
                required_one_of=[
                    ['bar', 'bam']
                ],
                required_together=[
                    ['bam1', 'baz']
                ]
            )
        )

        # should test ok, tests basic foo requirement and required_if
        args = json.dumps(dict(ANSIBLE_MODULE_ARGS={'foobar': [{"foo": "hello", "bam": "good"}, {"foo": "test", "bar": "good"}]}))
        with swap_stdin_and_argv(stdin_data=args):
            basic._ANSIBLE_ARGS = None
            am = basic.AnsibleModule(
                argument_spec=arg_spec,
                no_log=True,
                check_invalid_arguments=False,
                add_file_common_args=True,
                supports_check_mode=True
            )

        # should test ok, handles aliases
        args = json.dumps(dict(ANSIBLE_MODULE_ARGS={'foobar': [{"dup": "test", "bar": "good"}]}))
        with swap_stdin_and_argv(stdin_data=args):
            basic._ANSIBLE_ARGS = None
            am = basic.AnsibleModule(
                argument_spec=arg_spec,
                no_log=True,
                check_invalid_arguments=False,
                add_file_common_args=True,
                supports_check_mode=True
            )

        # fail, because a required param was not specified
        args = json.dumps(dict(ANSIBLE_MODULE_ARGS={'foobar': [{}]}))
        with swap_stdin_and_argv(stdin_data=args):
            basic._ANSIBLE_ARGS = None
            self.assertRaises(
                SystemExit,
                basic.AnsibleModule,
                argument_spec=arg_spec,
                no_log=True,
                check_invalid_arguments=False,
                add_file_common_args=True,
                supports_check_mode=True
            )

        # fail because of mutually exclusive parameters (mutually_exclusive, baz is added as it is required_together with bam1)
        args = json.dumps(dict(ANSIBLE_MODULE_ARGS={'foobar': [{"foo": "test", "bam": "bad", "bam1": "bad", "baz": "req_to"}]}))
        with swap_stdin_and_argv(stdin_data=args):
            basic._ANSIBLE_ARGS = None
            self.assertRaises(
                SystemExit,
                basic.AnsibleModule,
                argument_spec=arg_spec,
                no_log=True,
                check_invalid_arguments=False,
                add_file_common_args=True,
                supports_check_mode=True
            )

        # fail because a param required if for foo=hello is missing (required_if)
        args = json.dumps(dict(ANSIBLE_MODULE_ARGS={'foobar': [{"foo": "hello", "bar": "bad"}]}))
        with swap_stdin_and_argv(stdin_data=args):
            basic._ANSIBLE_ARGS = None
            self.assertRaises(
                SystemExit,
                basic.AnsibleModule,
                argument_spec=arg_spec,
                no_log=True,
                check_invalid_arguments=False,
                add_file_common_args=True,
                supports_check_mode=True
            )

        # fail because one of param is required (required_one_of)
        args = json.dumps(dict(ANSIBLE_MODULE_ARGS={'foobar': [{"foo": "test"}]}))
        with swap_stdin_and_argv(stdin_data=args):
            basic._ANSIBLE_ARGS = None
            self.assertRaises(
                SystemExit,
                basic.AnsibleModule,
                argument_spec=arg_spec,
                no_log=True,
                check_invalid_arguments=False,
                add_file_common_args=True,
                supports_check_mode=True
            )

        # fail because one parameter requires another (required_together, bar is added for the required_one_of field)
        args = json.dumps(dict(ANSIBLE_MODULE_ARGS={'foobar': [{"foo": "test", "bar": "required_one_of", "bam1": "bad"}]}))
        with swap_stdin_and_argv(stdin_data=args):
            basic._ANSIBLE_ARGS = None
            self.assertRaises(
                SystemExit,
                basic.AnsibleModule,
                argument_spec=arg_spec,
                no_log=True,
                check_invalid_arguments=False,
                add_file_common_args=True,
                supports_check_mode=True
            )

        # should test ok, the required param is set by default from spec (required_if together with default value, bar added for required_one_of
        args = json.dumps(dict(ANSIBLE_MODULE_ARGS={'foobar': [{"foo": "bam2", "bar": "required_one_of"}]}))
        with swap_stdin_and_argv(stdin_data=args):
            basic._ANSIBLE_ARGS = None
            am = basic.AnsibleModule(
                argument_spec=arg_spec,
                no_log=True,
                check_invalid_arguments=False,
                add_file_common_args=True,
                supports_check_mode=True
            )

        # should test ok, for options in dict format.
        arg_spec = dict(foobar=dict(type='dict', options=options_spec))

        # should test ok
        args = json.dumps(dict(ANSIBLE_MODULE_ARGS={'foobar': {"foo": "hello"}}))
        with swap_stdin_and_argv(stdin_data=args):
            basic._ANSIBLE_ARGS = None
            am = basic.AnsibleModule(
                argument_spec=arg_spec,
                no_log=True,
                check_invalid_arguments=False,
                add_file_common_args=True,
                supports_check_mode=True
            )

        # should fail, check for invalid agrument
        args = json.dumps(dict(ANSIBLE_MODULE_ARGS={'foobar': {"foo1": "hello"}}))
        with swap_stdin_and_argv(stdin_data=args):
            basic._ANSIBLE_ARGS = None
            self.assertRaises(
                SystemExit,
                basic.AnsibleModule,
                argument_spec=arg_spec,
                no_log=True,
                check_invalid_arguments=True,
                add_file_common_args=True,
                supports_check_mode=True
            )

    def test_module_utils_basic_ansible_module_type_check(self):
        from ansible.module_utils import basic

        arg_spec = dict(
            foo=dict(type='float'),
            foo2=dict(type='float'),
            foo3=dict(type='float'),
            bar=dict(type='int'),
            bar2=dict(type='int'),
        )

        # should test ok
        args = json.dumps(dict(ANSIBLE_MODULE_ARGS={
            "foo": 123.0,  # float
            "foo2": 123,  # int
            "foo3": "123",  # string
            "bar": 123,  # int
            "bar2": "123",  # string
        }))

        with swap_stdin_and_argv(stdin_data=args):
            basic._ANSIBLE_ARGS = None
            am = basic.AnsibleModule(
                argument_spec=arg_spec,
                no_log=True,
                check_invalid_arguments=False,
                add_file_common_args=True,
                supports_check_mode=True,
            )

        # fail, because bar does not accept floating point numbers
        args = json.dumps(dict(ANSIBLE_MODULE_ARGS={"bar": 123.0}))

        with swap_stdin_and_argv(stdin_data=args):
            basic._ANSIBLE_ARGS = None
            self.assertRaises(
                SystemExit,
                basic.AnsibleModule,
                argument_spec=arg_spec,
                no_log=True,
                check_invalid_arguments=False,
                add_file_common_args=True,
                supports_check_mode=True,
            )

    def test_module_utils_basic_ansible_module_options_type_check(self):
        from ansible.module_utils import basic

        options_spec = dict(
            foo=dict(type='float'),
            foo2=dict(type='float'),
            foo3=dict(type='float'),
            bar=dict(type='int'),
            bar2=dict(type='int'),
        )

        arg_spec = dict(foobar=dict(type='list', elements='dict', options=options_spec))
        # should test ok
        args = json.dumps(dict(ANSIBLE_MODULE_ARGS={'foobar': [{
            "foo": 123.0,  # float
            "foo2": 123,  # int
            "foo3": "123",  # string
            "bar": 123,  # int
            "bar2": "123",  # string
        }]}))

        with swap_stdin_and_argv(stdin_data=args):
            basic._ANSIBLE_ARGS = None
            am = basic.AnsibleModule(
                argument_spec=arg_spec,
                no_log=True,
                check_invalid_arguments=False,
                add_file_common_args=True,
                supports_check_mode=True,
            )

        # fail, because bar does not accept floating point numbers
        args = json.dumps(dict(ANSIBLE_MODULE_ARGS={'foobar': [{"bar": 123.0}]}))

        with swap_stdin_and_argv(stdin_data=args):
            basic._ANSIBLE_ARGS = None
            self.assertRaises(
                SystemExit,
                basic.AnsibleModule,
                argument_spec=arg_spec,
                no_log=True,
                check_invalid_arguments=False,
                add_file_common_args=True,
                supports_check_mode=True,
            )

    def test_module_utils_basic_ansible_module_load_file_common_arguments(self):
        from ansible.module_utils import basic
        basic._ANSIBLE_ARGS = None

        am = basic.AnsibleModule(
            argument_spec=dict(),
        )

        am.selinux_mls_enabled = MagicMock()
        am.selinux_mls_enabled.return_value = True
        am.selinux_default_context = MagicMock()
        am.selinux_default_context.return_value = 'unconfined_u:object_r:default_t:s0'.split(':', 3)

        # with no params, the result should be an empty dict
        res = am.load_file_common_arguments(params=dict())
        self.assertEqual(res, dict())

        base_params = dict(
            path='/path/to/file',
            mode=0o600,
            owner='root',
            group='root',
            seuser='_default',
            serole='_default',
            setype='_default',
            selevel='_default',
        )

        extended_params = base_params.copy()
        extended_params.update(dict(
            follow=True,
            foo='bar',
        ))

        final_params = base_params.copy()
        final_params.update(dict(
            path='/path/to/real_file',
            secontext=['unconfined_u', 'object_r', 'default_t', 's0'],
            attributes=None,
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

        args = json.dumps(dict(ANSIBLE_MODULE_ARGS={'_ansible_selinux_special_fs': "nfs,nfsd,foos"}))

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
            if path == b'/':
                return True
            return False

        with patch('os.path.ismount', side_effect=_mock_ismount):
            self.assertEqual(am.find_mount_point('/subdir/mount/path/to/whatever'), '/subdir/mount')

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

    def test_module_utils_basic_ansible_module_set_owner_if_different(self):
        from ansible.module_utils import basic
        basic._ANSIBLE_ARGS = None

        am = basic.AnsibleModule(
            argument_spec=dict(),
        )

        self.assertEqual(am.set_owner_if_different('/path/to/file', None, True), True)
        self.assertEqual(am.set_owner_if_different('/path/to/file', None, False), False)

        am.user_and_group = MagicMock(return_value=(500, 500))

        with patch('os.lchown', return_value=None) as m:
            self.assertEqual(am.set_owner_if_different('/path/to/file', 0, False), True)
            m.assert_called_with(b'/path/to/file', 0, -1)

            def _mock_getpwnam(*args, **kwargs):
                mock_pw = MagicMock()
                mock_pw.pw_uid = 0
                return mock_pw

            m.reset_mock()
            with patch('pwd.getpwnam', side_effect=_mock_getpwnam):
                self.assertEqual(am.set_owner_if_different('/path/to/file', 'root', False), True)
                m.assert_called_with(b'/path/to/file', 0, -1)

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
        basic._ANSIBLE_ARGS = None

        am = basic.AnsibleModule(
            argument_spec=dict(),
        )

        self.assertEqual(am.set_group_if_different('/path/to/file', None, True), True)
        self.assertEqual(am.set_group_if_different('/path/to/file', None, False), False)

        am.user_and_group = MagicMock(return_value=(500, 500))

        with patch('os.lchown', return_value=None) as m:
            self.assertEqual(am.set_group_if_different('/path/to/file', 0, False), True)
            m.assert_called_with(b'/path/to/file', -1, 0)

            def _mock_getgrnam(*args, **kwargs):
                mock_gr = MagicMock()
                mock_gr.gr_gid = 0
                return mock_gr

            m.reset_mock()
            with patch('grp.getgrnam', side_effect=_mock_getgrnam):
                self.assertEqual(am.set_group_if_different('/path/to/file', 'root', False), True)
                m.assert_called_with(b'/path/to/file', -1, 0)

            with patch('grp.getgrnam', side_effect=KeyError):
                self.assertRaises(SystemExit, am.set_group_if_different, '/path/to/file', 'root', False)

            m.reset_mock()
            am.check_mode = True
            self.assertEqual(am.set_group_if_different('/path/to/file', 0, False), True)
            self.assertEqual(m.called, False)
            am.check_mode = False

        with patch('os.lchown', side_effect=OSError) as m:
            self.assertRaises(SystemExit, am.set_group_if_different, '/path/to/file', 'root', False)

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
