# Copyright: (c) 2018, Pluribus Networks
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.netvisor import pn_vrouter_packet_relay
from units.modules.utils import set_module_args
from .nvos_module import TestNvosModule


class TestVrouterPacketRelayModule(TestNvosModule):

    module = pn_vrouter_packet_relay

    def setUp(self):
        self.mock_run_nvos_commands = patch('ansible.modules.network.netvisor.pn_vrouter_packet_relay.run_cli')
        self.run_nvos_commands = self.mock_run_nvos_commands.start()

        self.mock_run_check_cli = patch('ansible.modules.network.netvisor.pn_vrouter_packet_relay.check_cli')
        self.run_check_cli = self.mock_run_check_cli.start()

    def tearDown(self):
        self.mock_run_nvos_commands.stop()
        self.mock_run_check_cli.stop()

    def run_cli_patch(self, module, cli, state_map):
        if state_map['present'] == 'vrouter-packet-relay-add':
            results = dict(
                changed=True,
                cli_cmd=cli
            )
        elif state_map['absent'] == 'vrouter-packet-relay-remove':
            results = dict(
                changed=True,
                cli_cmd=cli
            )
        module.exit_json(**results)

    def load_fixtures(self, commands=None, state=None, transport='cli'):
        self.run_nvos_commands.side_effect = self.run_cli_patch
        if state == 'present':
            self.run_check_cli.return_value = True, True
        if state == 'absent':
            self.run_check_cli.return_value = True, True

    def test_vrouter_packet_relay_add(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_vrouter_name': 'foo-vrouter',
                         'pn_forward_ip': '192.168.1.10', 'pn_nic': 'eth0.4092', 'state': 'present'})
        result = self.execute_module(changed=True, state='present')
        expected_cmd = ' switch sw01 vrouter-packet-relay-add vrouter-name foo-vrouter nic eth0.4092 forward-proto dhcp forward-ip 192.168.1.10'
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_vrouter_packet_relay_remove(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_vrouter_name': 'foo-vrouter',
                         'pn_forward_ip': '192.168.1.10', 'pn_nic': 'eth0.4092', 'state': 'absent'})
        result = self.execute_module(changed=True, state='absent')
        expected_cmd = ' switch sw01 vrouter-packet-relay-remove vrouter-name foo-vrouter nic eth0.4092 forward-proto dhcp forward-ip 192.168.1.10'
        self.assertEqual(result['cli_cmd'], expected_cmd)
