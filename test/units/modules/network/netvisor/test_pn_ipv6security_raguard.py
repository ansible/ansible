# Copyright: (c) 2018, Pluribus Networks
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.netvisor import pn_ipv6security_raguard
from units.modules.utils import set_module_args
from .nvos_module import TestNvosModule


class TestIPV6SecurityRaguardModule(TestNvosModule):

    module = pn_ipv6security_raguard

    def setUp(self):
        self.mock_run_nvos_commands = patch('ansible.modules.network.netvisor.pn_ipv6security_raguard.run_cli')
        self.run_nvos_commands = self.mock_run_nvos_commands.start()

        self.mock_run_check_cli = patch('ansible.modules.network.netvisor.pn_ipv6security_raguard.check_cli')
        self.run_check_cli = self.mock_run_check_cli.start()

    def tearDown(self):
        self.mock_run_nvos_commands.stop()

    def run_cli_patch(self, module, cli, state_map):
        if state_map['present'] == 'ipv6security-raguard-create':
            results = dict(
                changed=True,
                cli_cmd=cli
            )
        elif state_map['absent'] == 'ipv6security-raguard-delete':
            results = dict(
                changed=True,
                cli_cmd=cli
            )
        elif state_map['update'] == 'ipv6security-raguard-modify':
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
        if state == 'update':
            self.run_check_cli.return_value = True

    def test_ipv6security_raguard_create(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_name': 'foo',
                         'pn_device': 'host'})
        result = self.execute_module(changed=True, state='present')
        expected_cmd = ' switch sw01 ipv6security-raguard-create name foo  device host'
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_ipv6security_raguard_delete(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_name': 'foo',
                         'state': 'absent'})
        result = self.execute_module(changed=True, state='absent')
        expected_cmd = ' switch sw01 ipv6security-raguard-delete name foo '
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_ipv6security_raguard_modify(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_name': 'foo',
                         'pn_device': 'router', 'pn_router_priority': 'medium', 'state': 'update'})
        result = self.execute_module(changed=True, state='absent')
        expected_cmd = ' switch sw01 ipv6security-raguard-modify name foo  device router router-priority medium'
        self.assertEqual(result['cli_cmd'], expected_cmd)
