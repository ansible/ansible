# Copyright: (c) 2018, Pluribus Networks
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

from units.compat.mock import patch
from ansible.modules.network.netvisor import pn_port_config
from units.modules.utils import set_module_args
from .nvos_module import TestNvosModule, load_fixture


class TestPortConfigModule(TestNvosModule):

    module = pn_port_config

    def setUp(self):
        self.mock_run_nvos_commands = patch('ansible.modules.network.netvisor.pn_port_config.run_cli')
        self.run_nvos_commands = self.mock_run_nvos_commands.start()

    def tearDown(self):
        self.mock_run_nvos_commands.stop()

    def run_cli_patch(self, module, cli, state_map):
        if state_map['update'] == 'port-config-modify':
            results = dict(
                changed=True,
                cli_cmd=cli
            )
        module.exit_json(**results)

    def load_fixtures(self, commands=None, state=None, transport='cli'):
        self.run_nvos_commands.side_effect = self.run_cli_patch

    def test_pn_port_config_modify_t1(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_port': '1,2',
                         'pn_speed': '10g', 'pn_jumbo': True, 'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 port-config-modify  speed 10g port 1,2 jumbo '
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_pn_port_config_modify_t2(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_port': 'all',
                         'pn_host_enable': True, 'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 port-config-modify  port all host-enable '
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_pn_port_config_modify_t3(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_port': '5',
                         'pn_crc_check_enable': True, 'pn_vxlan_termination': False, 'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 port-config-modify  port 5 crc-check-enable  no-vxlan-termination '
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_pn_port_config_modify_t4(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_port': '10,11,12',
                         'pn_pause': False, 'pn_enable': True, 'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 port-config-modify  port 10,11,12 no-pause  enable '
        self.assertEqual(result['cli_cmd'], expected_cmd)
