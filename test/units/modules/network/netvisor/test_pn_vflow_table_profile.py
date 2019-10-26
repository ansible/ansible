# Copyright: (c) 2018, Pluribus Networks
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.netvisor import pn_vflow_table_profile
from units.modules.utils import set_module_args
from .nvos_module import TestNvosModule


class TestVflowTableProfileModule(TestNvosModule):

    module = pn_vflow_table_profile

    def setUp(self):
        self.mock_run_nvos_commands = patch('ansible.modules.network.netvisor.pn_vflow_table_profile.run_cli')
        self.run_nvos_commands = self.mock_run_nvos_commands.start()

    def tearDown(self):
        self.mock_run_nvos_commands.stop()

    def run_cli_patch(self, module, cli, state_map):
        if state_map['update'] == 'vflow-table-profile-modify':
            results = dict(
                changed=True,
                cli_cmd=cli
            )
        module.exit_json(**results)

    def load_fixtures(self, commands=None, state=None, transport='cli'):
        self.run_nvos_commands.side_effect = self.run_cli_patch

    def test_vflow_table_profile_modify_t1(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_profile': 'ipv6',
                         'pn_hw_tbl': 'switch-main', 'pn_enable': True, 'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 vflow-table-profile-modify  profile ipv6 hw-tbl switch-main enable '
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_vflow_table_profile_modify_t2(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_profile': 'qos',
                         'pn_hw_tbl': 'switch-main', 'pn_enable': False, 'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 vflow-table-profile-modify  profile qos hw-tbl switch-main disable '
        self.assertEqual(result['cli_cmd'], expected_cmd)
