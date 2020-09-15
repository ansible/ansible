# Copyright: (c) 2018, Pluribus Networks
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.netvisor import pn_vrouter_bgp
from units.modules.utils import set_module_args
from .nvos_module import TestNvosModule


class TestVrouterBGPModule(TestNvosModule):

    module = pn_vrouter_bgp

    def setUp(self):
        self.mock_run_nvos_commands = patch('ansible.modules.network.netvisor.pn_vrouter_bgp.run_cli')
        self.run_nvos_commands = self.mock_run_nvos_commands.start()

        self.mock_run_check_cli = patch('ansible.modules.network.netvisor.pn_vrouter_bgp.check_cli')
        self.run_check_cli = self.mock_run_check_cli.start()

    def tearDown(self):
        self.mock_run_nvos_commands.stop()

    def run_cli_patch(self, module, cli, state_map):
        if state_map['present'] == 'vrouter-bgp-add':
            results = dict(
                changed=True,
                cli_cmd=cli
            )
        elif state_map['absent'] == 'vrouter-bgp-remove':
            results = dict(
                changed=True,
                cli_cmd=cli
            )
        elif state_map['update'] == 'vrouter-bgp-modify':
            results = dict(
                changed=True,
                cli_cmd=cli
            )
        module.exit_json(**results)

    def load_fixtures(self, commands=None, state=None, transport='cli'):
        self.run_nvos_commands.side_effect = self.run_cli_patch
        if state == 'present':
            self.run_check_cli.return_value = True, False
        if state == 'absent':
            self.run_check_cli.return_value = True, True
        if state == 'update':
            self.run_check_cli.return_value = True, True

    def test_vrouter_bgp_add(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_vrouter_name': 'sw01-vrouter',
                         'pn_neighbor': '105.104.104.1', 'pn_remote_as': '65000', 'pn_bfd': True, 'state': 'present'})
        result = self.execute_module(changed=True, state='present')
        expected_cmd = ' switch sw01 vrouter-bgp-add vrouter-name sw01-vrouter neighbor 105.104.104.1  remote-as 65000 bfd '
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_vrouter_bgp_remove(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_vrouter_name': 'sw01-vrouter',
                         'pn_neighbor': '105.104.104.1', 'state': 'absent'})
        result = self.execute_module(changed=True, state='absent')
        expected_cmd = ' switch sw01 vrouter-bgp-remove vrouter-name sw01-vrouter neighbor 105.104.104.1 '
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_vrouter_bgp_modify(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_vrouter_name': 'sw01-vrouter', 'pn_neighbor': '105.104.104.1',
                         'pn_remote_as': '65000', 'pn_bfd': False, 'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 vrouter-bgp-modify vrouter-name sw01-vrouter neighbor 105.104.104.1  remote-as 65000 no-bfd '
        self.assertEqual(result['cli_cmd'], expected_cmd)
