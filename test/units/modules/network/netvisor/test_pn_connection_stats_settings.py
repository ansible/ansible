# Copyright: (c) 2018, Pluribus Networks
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.netvisor import pn_connection_stats_settings
from units.modules.utils import set_module_args
from .nvos_module import TestNvosModule


class TestAdminServiceModule(TestNvosModule):

    module = pn_connection_stats_settings

    def setUp(self):
        self.mock_run_nvos_commands = patch('ansible.modules.network.netvisor.pn_connection_stats_settings.run_cli')
        self.run_nvos_commands = self.mock_run_nvos_commands.start()

    def tearDown(self):
        self.mock_run_nvos_commands.stop()

    def run_cli_patch(self, module, cli, state_map):
        if state_map['update'] == 'connection-stats-settings-modify':
            results = dict(
                changed=True,
                cli_cmd=cli
            )
        module.exit_json(**results)

    def load_fixtures(self, commands=None, state=None, transport='cli'):
        self.run_nvos_commands.side_effect = self.run_cli_patch

    def test_connection_stats_settings_modify_t1(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_enable': False,
                         'pn_fabric_connection_max_memory': '1000', 'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 connection-stats-settings-modify  disable  fabric-connection-max-memory 1000'
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_connection_stats_settings_modify_t2(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_enable': True,
                         'pn_connection_stats_log_enable': False, 'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 connection-stats-settings-modify  enable  connection-stats-log-disable '
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_connection_stats_settings_modify_t3(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_client_server_stats_max_memory': '60M',
                         'pn_client_server_stats_log_disk_space': '40M', 'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 connection-stats-settings-modify  client-server-stats-max-memory '
        expected_cmd += '60M client-server-stats-log-disk-space 40M'
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_connection_stats_settings_modify_t4(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_connection_stats_max_memory': '45M',
                         'pn_fabric_connection_backup_enable': False, 'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 connection-stats-settings-modify '
        expected_cmd += ' fabric-connection-backup-disable  connection-stats-max-memory 45M'
        self.assertEqual(result['cli_cmd'], expected_cmd)
