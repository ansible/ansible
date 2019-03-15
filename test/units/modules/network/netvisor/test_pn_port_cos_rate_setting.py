# Copyright: (c) 2018, Pluribus Networks
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

from units.compat.mock import patch
from ansible.modules.network.netvisor import pn_port_cos_rate_setting
from units.modules.utils import set_module_args
from .nvos_module import TestNvosModule, load_fixture


class TestPortCosRateSettingModule(TestNvosModule):

    module = pn_port_cos_rate_setting

    def setUp(self):
        self.mock_run_nvos_commands = patch('ansible.modules.network.netvisor.pn_port_cos_rate_setting.run_cli')
        self.run_nvos_commands = self.mock_run_nvos_commands.start()

    def tearDown(self):
        self.mock_run_nvos_commands.stop()

    def run_cli_patch(self, module, cli, state_map):
        if state_map['update'] == 'port-cos-rate-setting-modify':
            results = dict(
                changed=True,
                cli_cmd=cli
            )
        module.exit_json(**results)

    def load_fixtures(self, commands=None, state=None, transport='cli'):
        self.run_nvos_commands.side_effect = self.run_cli_patch

    def test_pn_port_cos_rate_setting_modify_t1(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_port': 'control-port',
                         'pn_cos1_rate': '4000', 'pn_cos2_rate': '4000', 'pn_cos3_rate': '4000', 'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 port-cos-rate-setting-modify  cos1-rate 4000 cos2-rate 4000 '
        expected_cmd += 'cos3-rate 4000 port control-port'
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_pn_port_cos_rate_setting_modify_t2(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_port': 'data-port',
                         'pn_cos1_rate': '2000', 'pn_cos5_rate': '3000', 'pn_cos2_rate': '4000', 'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 port-cos-rate-setting-modify  cos1-rate 2000 cos5-rate 3000 '
        expected_cmd += 'cos2-rate 4000 port data-port'
        self.assertEqual(result['cli_cmd'], expected_cmd)
