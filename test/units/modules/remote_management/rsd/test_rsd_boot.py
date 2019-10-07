# -*- coding: utf-8 -*-

#######################################################
# Copyright (c) 2019 Intel Corporation. All rights reserved.
#
# GNU General Public License v3.0+
# (see LICENSE.GPL or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Authors:
#   - Radoslaw Kuschel - <radoslaw.kuschel@intel.com>
#   - Przemyslaw Szczerbik - <przemyslawx.szczerbik@intel.com>
#######################################################

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from units.compat import mock
from units.modules.utils import set_module_args, AnsibleFailJson
import units.modules.remote_management.rsd.utilities as rsd_utils

import pytest


class TestRsdBootModule():

    BOOT_ARGS = {
        'boot_target': 'remote_drive',
        'boot_enable': 'once',
        'boot_mode': 'uefi'
    }

    BOOT_ARGS_MAPPED = {
        'boot_target': 'RemoteDrive',
        'boot_enable': 'Once',
        'boot_mode': 'UEFI'
    }

    def get_rsd_boot_args(self):
        args = rsd_utils.get_rsd_common_args()
        args.update(TestRsdBootModule.BOOT_ARGS)
        return args

    def test_without_required_parameters(self, rsd_mock, rsd_boot):

        with pytest.raises(AnsibleFailJson,
                           match='missing required arguments'):
            set_module_args(rsd_utils.get_rsd_common_args())
            rsd_boot.main()

    def test_params_mappings(self, rsd_mock, rsd_boot):

        set_module_args(self.get_rsd_boot_args())
        module = rsd_boot.RsdNodeBoot()
        call_params_mapping = module._params_mappings(
            TestRsdBootModule.BOOT_ARGS)
        assert call_params_mapping == TestRsdBootModule.BOOT_ARGS_MAPPED

    def test_return_current_boot_options(self, rsd_mock, rsd_boot):

        mock_node_boot_opt = mock.Mock()
        mock_boot = mock.Mock()
        mock_boot.boot_source_override_target = 'RemoteDrive'
        mock_boot.boot_source_override_enabled = 'Once'
        mock_boot.boot_source_override_mode = "UEFI"
        mock_node_boot_opt.boot = mock_boot

        set_module_args(self.get_rsd_boot_args())
        module = rsd_boot.RsdNodeBoot()
        function_return = module._get_current_node_boot_options(
            mock_node_boot_opt)
        assert function_return == TestRsdBootModule.BOOT_ARGS_MAPPED

    def test_check_boot_opt_false(self, rsd_mock, rsd_boot):
        set_module_args(self.get_rsd_boot_args())
        module = rsd_boot.RsdNodeBoot()
        function_return = module._check_boot_opt_diff(
            TestRsdBootModule.BOOT_ARGS, TestRsdBootModule.BOOT_ARGS)
        assert not function_return

    def test_check_boot_opt_True(self, rsd_mock, rsd_boot):

        previous_boot_opt = {
            'boot_target': 'Hdd',
            'boot_enable': 'Once',
            'boot_mode': 'Uefi'
        }
        set_module_args(self.get_rsd_boot_args())
        module = rsd_boot.RsdNodeBoot()
        function_return = module._check_boot_opt_diff(
            TestRsdBootModule.BOOT_ARGS, previous_boot_opt)
        assert function_return

    def test_change_boot_options_diff_true_exception_three_param(
            self, rsd_mock, rsd_boot, get_sample_node, sushy_import_mock):
        mock_node, get_node_mock = get_sample_node('assembled', 'On')

        mock_node.set_node_boot_source.side_effect = \
            sushy_import_mock.exceptions.InvalidParameterValueError

        with pytest.raises(AnsibleFailJson,
                           match='Invalid Parameter:') as result:
            set_module_args({
                'id': {'type': 'identity', 'value': 1},
                'boot_target': 'remote_drive',
                'boot_enable': 'once',
                'boot_mode': 'uefi',
                'podm': {'host': '127.0.0.1'},
                'auth': {'user': 'admin', 'password': 'admin'}
            })
            rsd_boot.main()
        result = result.value.args[0]
        assert result['failed']
