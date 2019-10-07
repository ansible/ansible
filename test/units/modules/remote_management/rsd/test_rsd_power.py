# -*- coding: utf-8 -*-

#######################################################
# Copyright (c) 2019 Intel Corporation. All rights reserved.
#
# GNU General Public License v3.0+
# (see LICENSE.GPL or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Authors:
#   - Piotr Mossakowski <piotrx.mossakowski@intel.com>
#######################################################

import pytest

from units.modules.utils import AnsibleExitJson, AnsibleFailJson, \
    set_module_args
import units.modules.remote_management.rsd.utilities as rsd_utils


class TestRsdPower():

    def get_rsd_power_args(self, state='on', force=False):
        args = rsd_utils.get_rsd_common_args()
        args.update(dict(state=state, force=force))
        return args

    def test_fail_without_required_args(self, rsd_mock, rsd_power):
        set_module_args(rsd_utils.get_rsd_common_args())
        with pytest.raises(AnsibleFailJson,
                           match='missing required arguments:'):
            rsd_power.main()

        rsd_mock.assert_not_called()

    def test_fail_with_unknown_state(self, rsd_mock, rsd_power):
        set_module_args(self.get_rsd_power_args('rebooted'))
        with pytest.raises(AnsibleFailJson,
                           match='value of state must be one of: on, off, '
                                 'restarted'):
            rsd_power.main()

    @pytest.mark.parametrize('force, expected_result', [(False, 'On'),
                                                        (True, 'ForceOn')])
    def test_convert_power_param(self, force, expected_result, rsd_mock,
                                 rsd_power):
        set_module_args(self.get_rsd_power_args(force=force))
        actual_result = rsd_power.RsdNodePower()._convert_power_param()
        assert actual_result == expected_result

    @pytest.mark.parametrize(
        'state, force, node_power_state, expected_result',
        [('restarted', False, 'On', 'GracefulRestart'),
         ('off', True, 'On', 'ForceOff'),
         ('on', False, 'Off', 'On')])
    def test_restart_poweroff_poweron_node(self, state, force,
                                           node_power_state, expected_result,
                                           rsd_mock, rsd_power,
                                           get_sample_node):
        mock_node, get_node_mock = get_sample_node('assembled',
                                                   node_power_state)
        set_module_args(self.get_rsd_power_args(state, force))
        with pytest.raises(AnsibleExitJson) as result:
            rsd_power.main()
        result = result.value.args[0]
        assert result['node']['requested_power_action'] in \
            result['node']['supported_power_action']
        assert result['node']['requested_power_action'] == expected_result
        assert result['changed']

    @pytest.mark.parametrize('state, err_regex', [
        ('restarted',
         "Reset action failed. The required transition might not be supported"),
        ('on',
         "This node does not support such power action: 'ForceOn'.")
    ])
    def test_fail_with_unsupported_transitions(self, state, err_regex,
                                               rsd_mock, rsd_power,
                                               get_sample_node,
                                               sushy_import_mock):
        mock_node, get_node_mock = get_sample_node('assembled', 'Off')
        set_module_args(self.get_rsd_power_args(state, force=True))
        mock_node.reset_node.side_effect = \
            sushy_import_mock.exceptions.ServerSideError
        with pytest.raises(AnsibleFailJson, match=err_regex):
            rsd_power.main()
