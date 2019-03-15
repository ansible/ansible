# Copyright: (c) 2018, Pluribus Networks
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

from units.compat.mock import patch
from ansible.modules.network.netvisor import pn_cpu_mgmt_class
from units.modules.utils import set_module_args
from .nvos_module import TestNvosModule, load_fixture


class TestCpuMgmtClassModule(TestNvosModule):

    module = pn_cpu_mgmt_class

    def setUp(self):
        self.mock_run_nvos_commands = patch('ansible.modules.network.netvisor.pn_cpu_mgmt_class.run_cli')
        self.run_nvos_commands = self.mock_run_nvos_commands.start()

    def tearDown(self):
        self.mock_run_nvos_commands.stop()

    def run_cli_patch(self, module, cli, state_map):
        if state_map['update'] == 'cpu-mgmt-class-modify':
            results = dict(
                changed=True,
                cli_cmd=cli
            )
        module.exit_json(**results)

    def load_fixtures(self, commands=None, state=None, transport='cli'):
        self.run_nvos_commands.side_effect = self.run_cli_patch

    def test_cpu_mgmt_class_modify_t1(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_name': 'icmp',
                         'pn_rate_limit': '10000', 'pn_burst_size': '14000', 'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 cpu-mgmt-class-modify name icmp  burst-size 14000 rate-limit 10000'
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_cpu_mgmt_class_modify_t2(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_name': 'ssh',
                         'pn_rate_limit': '10000', 'pn_burst_size': '100000', 'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 cpu-mgmt-class-modify name ssh  burst-size 100000 rate-limit 10000'
        self.assertEqual(result['cli_cmd'], expected_cmd)
