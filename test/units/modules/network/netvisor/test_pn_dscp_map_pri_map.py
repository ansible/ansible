# Copyright: (c) 2018, Pluribus Networks
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.netvisor import pn_dscp_map_pri_map
from units.modules.utils import set_module_args
from .nvos_module import TestNvosModule


class TestCpuClassModule(TestNvosModule):

    module = pn_dscp_map_pri_map

    def setUp(self):
        self.mock_run_nvos_commands = patch('ansible.modules.network.netvisor.pn_dscp_map_pri_map.run_cli')
        self.run_nvos_commands = self.mock_run_nvos_commands.start()

        self.mock_run_check_cli = patch('ansible.modules.network.netvisor.pn_dscp_map_pri_map.check_cli')
        self.run_check_cli = self.mock_run_check_cli.start()

    def tearDown(self):
        self.mock_run_nvos_commands.stop()
        self.mock_run_check_cli.stop()

    def run_cli_patch(self, module, cli, state_map):
        if state_map['update'] == 'dscp-map-pri-map-modify':
            results = dict(
                changed=True,
                cli_cmd=cli
            )
        module.exit_json(**results)

    def load_fixtures(self, commands=None, state=None, transport='cli'):
        self.run_nvos_commands.side_effect = self.run_cli_patch
        if state == 'update':
            self.run_check_cli.return_value = True

    def test_dscp_map_pri_map_t1(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_name': 'foo',
                         'pn_pri': '0', 'pn_dsmap': '40', 'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 dscp-map-pri-map-modify  pri 0 name foo dsmap 40'
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_dscp_map_pri_map_t2(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_name': 'foo',
                         'pn_pri': '1', 'pn_dsmap': '8,10,12,14', 'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 dscp-map-pri-map-modify  pri 1 name foo dsmap 8,10,12,14'
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_dscp_map_pri_map_t3(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_name': 'foo',
                         'pn_pri': '2', 'pn_dsmap': '25', 'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 dscp-map-pri-map-modify  pri 2 name foo dsmap 25'
        self.assertEqual(result['cli_cmd'], expected_cmd)
