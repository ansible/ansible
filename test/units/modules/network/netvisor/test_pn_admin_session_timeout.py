# Copyright: (c) 2018, Pluribus Networks
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.netvisor import pn_admin_session_timeout
from units.modules.utils import set_module_args
from .nvos_module import TestNvosModule


class TestAdminServiceModule(TestNvosModule):

    module = pn_admin_session_timeout

    def setUp(self):
        self.mock_run_nvos_commands = patch('ansible.modules.network.netvisor.pn_admin_session_timeout.run_cli')
        self.run_nvos_commands = self.mock_run_nvos_commands.start()

    def tearDown(self):
        self.mock_run_nvos_commands.stop()

    def run_cli_patch(self, module, cli, state_map):
        if state_map['update'] == 'admin-session-timeout-modify':
            results = dict(
                changed=True,
                cli_cmd=cli
            )
        module.exit_json(**results)

    def load_fixtures(self, commands=None, state=None, transport='cli'):
        self.run_nvos_commands.side_effect = self.run_cli_patch

    def test_admin_session_timeout_modify_t1(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_timeout': '61s',
                         'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 admin-session-timeout-modify  timeout 61s'
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_admin_session_timeout_modify_t2(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_timeout': '1d',
                         'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 admin-session-timeout-modify  timeout 1d'
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_admin_session_timeout_modify_t3(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_timeout': '10d20m3h15s',
                         'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 admin-session-timeout-modify  timeout 10d20m3h15s'
        self.assertEqual(result['cli_cmd'], expected_cmd)
