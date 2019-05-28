# Copyright: (c) 2018, Pluribus Networks
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

from units.compat.mock import patch
from ansible.modules.network.netvisor import pn_vrouter_pim_config
from units.modules.utils import set_module_args
from .nvos_module import TestNvosModule, load_fixture


class TestVrouterPimConfigModule(TestNvosModule):

    module = pn_vrouter_pim_config

    def setUp(self):
        self.mock_run_nvos_commands = patch('ansible.modules.network.netvisor.pn_vrouter_pim_config.run_cli')
        self.run_nvos_commands = self.mock_run_nvos_commands.start()

        self.mock_run_check_cli = patch('ansible.modules.network.netvisor.pn_vrouter_pim_config.check_cli')
        self.run_check_cli = self.mock_run_check_cli.start()

    def tearDown(self):
        self.mock_run_nvos_commands.stop()
        self.mock_run_check_cli.stop()

    def run_cli_patch(self, module, cli, state_map):
        if state_map['update'] == 'vrouter-pim-config-modify':
            results = dict(
                changed=True,
                cli_cmd=cli
            )
        module.exit_json(**results)

    def load_fixtures(self, commands=None, state=None, transport='cli'):
        self.run_nvos_commands.side_effect = self.run_cli_patch
        if state == 'update':
            self.run_check_cli.return_value = True

    def test_vrouter_pim_config_t1(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_query_interval': '10',
                         'pn_querier_timeout': '30', 'pn_vrouter_name': 'foo-vrouter', 'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 vrouter-pim-config-modify vrouter-name foo-vrouter  '
        expected_cmd += 'querier-timeout 30 query-interval 10'
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_vrouter_pim_config_t2(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_query_interval': '30',
                         'pn_hello_interval': '120', 'pn_vrouter_name': 'foo-vrouter', 'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 vrouter-pim-config-modify vrouter-name foo-vrouter  '
        expected_cmd += 'hello-interval 120 query-interval 30'
        self.assertEqual(result['cli_cmd'], expected_cmd)
