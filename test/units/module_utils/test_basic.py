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

import __builtin__

from nose.tools import timed

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock

class TestModuleUtilsBasic(unittest.TestCase):
 
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_module_utils_basic_imports(self):
        realimport = __builtin__.__import__

        def _mock_import(name, *args, **kwargs):
            if name == 'json':
                raise ImportError()
            realimport(name, *args, **kwargs)

        with patch.object(__builtin__, '__import__', _mock_import, create=True) as m:
            m('ansible.module_utils.basic')
            __builtin__.__import__('ansible.module_utils.basic')

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
                    self.assertEqual(get_distribution(), "Amazon")

                def _dist(distname='', version='', id='', supported_dists=(), full_distribution_name=1):
                    if supported_dists != ():
                        return ("Bar", "2", "Two")
                    else:
                        return ("", "", "")
                
                with patch('platform.linux_distribution', side_effect=_dist):
                    self.assertEqual(get_distribution(), "OtherLinux")
                
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

    def test_module_utils_basic_get_module_path(self):
        from ansible.module_utils.basic import get_module_path
        with patch('os.path.realpath', return_value='/path/to/foo/'):
            self.assertEqual(get_module_path(), '/path/to/foo')

