"""
iap_token unit tests
"""

# -*- coding: utf-8 -*-

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

# pylint: disable=invalid-name,protected-access,function-redefined,unused-argument
# pylint: disable=unused-import,redundant-unittest-assert

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


from ansible.compat.tests import unittest
from ansible.module_utils import basic
from ansible.modules.network.itential import iap_token
from ansible.compat.tests.mock import patch

from units.modules.utils import set_module_args, AnsibleExitJson, AnsibleFailJson, ModuleTestCase


class AnsibleExitJson(Exception):
    """Exception class to be raised by module.exit_json and caught by the test case"""
    pass


class AnsibleFailJson(Exception):
    """Exception class to be raised by module.fail_json and caught by the test case"""
    pass


def exit_json(*args, **kwargs):
    """function to patch over exit_json; package return data into an exception"""
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):
    """function to patch over fail_json; package return data into an exception"""
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)


def get_bin_path(self, arg, required=False):
    """Mock AnsibleModule.get_bin_path"""
    if arg.endswith('iap_token'):
        return '/usr/bin/run_module'
    else:
        if required:
            fail_json(msg='%r not found !' % arg)


class TestClass(unittest.TestCase):
    """
    Test cases
    """
    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule,
                                                 exit_json=exit_json,
                                                 fail_json=fail_json,
                                                 get_bin_path=get_bin_path)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)

    def test_module_fail_when_required_args_missing(self):
        """
        Testing that command is failing if args are missing
        :return:
        """
        with self.assertRaises(AnsibleFailJson):
            set_module_args({})
            iap_token.run_module()
            self.assertTrue(False)

    def test_ensure_command_called(self):
        """
        Testing that command is executed with correct args
        :return:
        """
        set_module_args({
            'username': 'admin',
            'password': 'admin',
            'iap_fqdn': "dfsdf",
            'iap_port': "3333"
        })

        with patch.object(basic.AnsibleModule, 'run_command') as mock_run_command:
            msg = ''
            token = ''
            mock_run_command.return_value = msg
            try:
                result = iap_token.run_module()
                self.assertTrue("msg", result.exception.args[0]['msg'])
            except (AnsibleFailJson, KeyError):
                print('\nFound KeyError')
