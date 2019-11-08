# Copyright: (c) 2018, Pluribus Networks
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.netvisor import pn_cpu_class
from units.modules.utils import set_module_args
from .nvos_module import TestNvosModule


class TestCpuClassModule(TestNvosModule):

    module = pn_cpu_class

    def setUp(self):
        self.mock_run_nvos_commands = patch('ansible.modules.network.netvisor.pn_cpu_class.run_cli')
        self.run_nvos_commands = self.mock_run_nvos_commands.start()

        self.mock_run_check_cli = patch('ansible.modules.network.netvisor.pn_cpu_class.check_cli')
        self.run_check_cli = self.mock_run_check_cli.start()

    def tearDown(self):
        self.mock_run_nvos_commands.stop()

    def run_cli_patch(self, module, cli, state_map):
        if state_map['present'] == 'cpu-class-create':
            results = dict(
                changed=True,
                cli_cmd=cli
            )
        elif state_map['absent'] == 'cpu-class-delete':
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

    def test_cpu_class_create(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_name': 'icmp',
                         'pn_scope': 'local', 'pn_rate_limit': '1000', 'state': 'present'})
        result = self.execute_module(changed=True, state='present')
        expected_cmd = ' switch sw01 cpu-class-create name icmp  scope local  rate-limit 1000 '
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_cpu_class_delete(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_name': 'icmp',
                         'state': 'absent'})
        result = self.execute_module(changed=True, state='absent')
        expected_cmd = ' switch sw01 cpu-class-delete name icmp '
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_cpu_class_update(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_name': 'icmp',
                         'pn_rate_limit': '2000', 'state': 'update'})
        result = self.execute_module(changed=True, state='absent')
        expected_cmd = ' switch sw01 cpu-class-modify name icmp  rate-limit 2000 '
        self.assertEqual(result['cli_cmd'], expected_cmd)
