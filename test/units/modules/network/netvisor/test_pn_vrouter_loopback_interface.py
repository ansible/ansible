# Copyright: (c) 2018, Pluribus Networks
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.netvisor import pn_vrouter_loopback_interface
from units.modules.utils import set_module_args
from .nvos_module import TestNvosModule


class TestVrouterLoopbackInterfaceModule(TestNvosModule):

    module = pn_vrouter_loopback_interface

    def setUp(self):
        self.mock_run_nvos_commands = patch('ansible.modules.network.netvisor.pn_vrouter_loopback_interface.run_cli')
        self.run_nvos_commands = self.mock_run_nvos_commands.start()

        self.mock_run_check_cli = patch('ansible.modules.network.netvisor.pn_vrouter_loopback_interface.check_cli')
        self.run_check_cli = self.mock_run_check_cli.start()

    def tearDown(self):
        self.mock_run_nvos_commands.stop()
        self.mock_run_check_cli.stop()

    def run_cli_patch(self, module, cli, state_map):
        if state_map['present'] == 'vrouter-loopback-interface-add':
            results = dict(
                changed=True,
                cli_cmd=cli
            )
        elif state_map['absent'] == 'vrouter-loopback-remove':
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

    def test_vrouter_loopback_interface_add(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_vrouter_name': 'foo-vrouter',
                         'pn_ip': '192.168.10.1', 'state': 'present'})
        result = self.execute_module(changed=True, state='present')
        expected_cmd = ' switch sw01 vrouter-loopback-interface-add vrouter-name foo-vrouter  ip 192.168.10.1'
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_vrouter_loopback_interface_remove(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_vrouter_name': 'foo-vrouter',
                         'pn_ip': '192.168.10.1', 'pn_index': '1', 'state': 'absent'})
        result = self.execute_module(changed=True, state='absent')
        expected_cmd = ' switch sw01 vrouter-loopback-interface-remove vrouter-name foo-vrouter  index 1'
        self.assertEqual(result['cli_cmd'], expected_cmd)
