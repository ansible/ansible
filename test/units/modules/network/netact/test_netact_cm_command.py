"""
netact_cm_command unit tests
"""

# -*- coding: utf-8 -*-


# (c) 2017, Nokia
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

import json

from ansible.compat.tests import unittest
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible.modules.network.netact import netact_cm_command
from ansible.compat.tests.mock import patch

from units.modules.utils import set_module_args as _set_module_args, \
    AnsibleExitJson, AnsibleFailJson, ModuleTestCase


def set_module_args(args):
    """prepare arguments so that they will be picked up during module creation"""
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)


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
    if arg.endswith('netact_cm_command'):
        return '/usr/bin/my_command'
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
            netact_cm_command.main()
            self.assertTrue(False)

    def test_ensure_command_called(self):
        """
        Testing that command is executed with correct args
        :return:
        """
        set_module_args({
            'operation': "Upload",
            'opsName': 'Uploading_testi',
            'DN': "PLMN-PLMN/MRBTS-746",
        })

        with patch.object(basic.AnsibleModule, 'run_command') as mock_run_command:
            stdout = 'configuration updated'
            stderr = ''
            return_code = 0
            mock_run_command.return_value = return_code, stdout, stderr  # successful execution

            with self.assertRaises(AnsibleExitJson) as result:
                netact_cm_command.main()
            print(result.exception.args)
            self.assertTrue(result.exception.args[0]['changed'])  # ensure result is changed

        mock_run_command.assert_called_once_with(
            ['/opt/oss/bin/racclimx.sh', '-op', 'Upload', '-opsName', 'Uploading_testi',
             '-DN', 'PLMN-PLMN/MRBTS-746'],
            check_rc=True)

    def test_ensure_backupPlanName_outputs_correctly(self):
        """
        Testing that command is executed with correct args
        :return:
        """
        set_module_args({
            'operation': "Provision",
            'opsName': 'Provision_test',
            'WS': "PLMN-PLMN/MRBTS-746",
            'createBackupPlan': "Yes",
            'backupPlanName': "backupPlanName"
        })

        with patch.object(basic.AnsibleModule, 'run_command') as mock_run_command:
            stdout = 'configuration updated'
            stderr = ''
            return_code = 0
            mock_run_command.return_value = return_code, stdout, stderr  # successful execution

            with self.assertRaises(AnsibleExitJson) as result:
                netact_cm_command.main()
            print(result.exception.args)
            self.assertTrue(result.exception.args[0]['changed'])  # ensure result is changed

        mock_run_command.assert_called_once_with(
            ['/opt/oss/bin/racclimx.sh', '-op', 'Provision', '-opsName', 'Provision_test',
             '-WS', 'PLMN-PLMN/MRBTS-746', '-createBackupPlan', 'true', '-backupPlanName', 'backupPlanName'],
            check_rc=True)

    def test_withwrongargs(self):
        """
        Testing that wrong attribute causing error
        :return:
        """
        set_module_args({
            'operation': "Upload",
            'opsName': 'Uploading_testi',
            'MR': "PLMN-PLMN/MRBTS-746",
            'abc': 'abc'
        })

        with self.assertRaises(AnsibleFailJson):
            with patch.object(basic.AnsibleModule, 'run_command') as mock_run_command:
                stdout = 'configuration updated'
                stderr = ''
                return_code = 0
                mock_run_command.return_value = return_code, stdout, stderr  # successful execution

                with self.assertRaises(AnsibleExitJson) as result:
                    netact_cm_command.main()
                self.assertTrue(result.exception.args[0]['changed'])  # ensure result is changed

            self.assertFalse(True)  # ensure result is changed
