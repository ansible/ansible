# Copyright: (c) 2018, Pluribus Networks
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.netvisor import pn_prefix_list_network
from units.modules.utils import set_module_args
from .nvos_module import TestNvosModule


class TestPrefixListNetworkModule(TestNvosModule):

    module = pn_prefix_list_network

    def setUp(self):
        self.mock_run_nvos_commands = patch('ansible.modules.network.netvisor.pn_prefix_list_network.run_cli')
        self.run_nvos_commands = self.mock_run_nvos_commands.start()

        self.mock_run_check_cli = patch('ansible.modules.network.netvisor.pn_prefix_list_network.check_cli')
        self.run_check_cli = self.mock_run_check_cli.start()

    def tearDown(self):
        self.mock_run_nvos_commands.stop()
        self.mock_run_check_cli.stop()

    def run_cli_patch(self, module, cli, state_map):
        if state_map['present'] == 'prefix-list-network-add':
            results = dict(
                changed=True,
                cli_cmd=cli
            )
        elif state_map['absent'] == 'prefix-list-network-remove':
            results = dict(
                changed=True,
                cli_cmd=cli
            )
        module.exit_json(**results)

    def load_fixtures(self, commands=None, state=None, transport='cli'):
        self.run_nvos_commands.side_effect = self.run_cli_patch
        if state == 'present':
            self.run_check_cli.return_value = False
        if state == 'absent':
            self.run_check_cli.return_value = True

    def test_prefix_list_network_add(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_name': 'foo',
                         'pn_network': '172.16.3.1', 'pn_netmask': '24', 'state': 'present'})
        result = self.execute_module(changed=True, state='present')
        expected_cmd = ' switch sw01 prefix-list-network-add  name foo network 172.16.3.1 netmask 24'
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_prefix_list_network_remove(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_name': 'foo',
                         'pn_network': '172.16.3.1', 'pn_netmask': '24', 'state': 'absent'})
        result = self.execute_module(changed=True, state='absent')
        expected_cmd = ' switch sw01 prefix-list-network-remove  name foo network 172.16.3.1 netmask 24'
        self.assertEqual(result['cli_cmd'], expected_cmd)
