# Copyright: (c) 2018, Pluribus Networks
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.netvisor import pn_port_cos_bw
from units.modules.utils import set_module_args
from .nvos_module import TestNvosModule


class TestAdminServiceModule(TestNvosModule):

    module = pn_port_cos_bw

    def setUp(self):
        self.mock_run_nvos_commands = patch('ansible.modules.network.netvisor.pn_port_cos_bw.run_cli')
        self.run_nvos_commands = self.mock_run_nvos_commands.start()

    def tearDown(self):
        self.mock_run_nvos_commands.stop()

    def run_cli_patch(self, module, cli, state_map):
        if state_map['update'] == 'port-cos-bw-modify':
            results = dict(
                changed=True,
                cli_cmd=cli
            )
        module.exit_json(**results)

    def load_fixtures(self, commands=None, state=None, transport='cli'):
        self.run_nvos_commands.side_effect = self.run_cli_patch

    def test_pn_port_cos_bw_modify_t1(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_port': '1',
                         'pn_cos': '0', 'pn_min_bw_guarantee': '60', 'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 port-cos-bw-modify  cos 0 port 1 min-bw-guarantee 60'
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_pn_port_cos_bw_modify_t2(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_port': 'all',
                         'pn_cos': '1', 'pn_weight': 'priority', 'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 port-cos-bw-modify  cos 1 port all weight priority'
        self.assertEqual(result['cli_cmd'], expected_cmd)
