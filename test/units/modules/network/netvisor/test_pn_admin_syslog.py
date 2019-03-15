# Copyright: (c) 2018, Pluribus Networks
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

from units.compat.mock import patch
from ansible.modules.network.netvisor import pn_admin_syslog
from units.modules.utils import set_module_args
from .nvos_module import TestNvosModule, load_fixture


class TestAdminSyslogModule(TestNvosModule):

    module = pn_admin_syslog

    def setUp(self):
        self.mock_run_nvos_commands = patch('ansible.modules.network.netvisor.pn_admin_syslog.run_cli')
        self.run_nvos_commands = self.mock_run_nvos_commands.start()

        self.mock_run_check_cli = patch('ansible.modules.network.netvisor.pn_admin_syslog.check_cli')
        self.run_check_cli = self.mock_run_check_cli.start()

    def tearDown(self):
        self.mock_run_nvos_commands.stop()

    def run_cli_patch(self, module, cli, state_map):
        if state_map['present'] == 'admin-syslog-create':
            results = dict(
                changed=True,
                cli_cmd=cli
            )
        elif state_map['absent'] == 'admin-syslog-delete':
            results = dict(
                changed=True,
                cli_cmd=cli
            )
        elif state_map['update'] == 'admin-syslog-modify':
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

    def test_admin_syslog_create(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_name': 'foo',
                         'pn_scope': 'local', 'pn_host': '166.68.224.46', 'pn_message_format': 'structured', 'state': 'present'})
        result = self.execute_module(changed=True, state='present')
        expected_cmd = ' switch sw01 admin-syslog-create name foo  scope local host 166.68.224.46 '
        expected_cmd += 'transport udp message-format structured'
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_admin_syslog_delete(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_name': 'foo',
                         'state': 'absent'})
        result = self.execute_module(changed=True, state='absent')
        expected_cmd = ' switch sw01 admin-syslog-delete name foo '
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_admin_syslog_update(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_name': 'foo',
                         'state': 'update'})
        result = self.execute_module(changed=True, state='absent')
        expected_cmd = ' switch sw01 admin-syslog-modify name foo  transport udp'
        self.assertEqual(result['cli_cmd'], expected_cmd)
