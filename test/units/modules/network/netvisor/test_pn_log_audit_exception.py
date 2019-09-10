# Copyright: (c) 2018, Pluribus Networks
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

from units.compat.mock import patch
from ansible.modules.network.netvisor import pn_log_audit_exception
from units.modules.utils import set_module_args
from .nvos_module import TestNvosModule, load_fixture


class TestLogAuditExceptionModule(TestNvosModule):

    module = pn_log_audit_exception

    def setUp(self):
        self.mock_run_nvos_commands = patch('ansible.modules.network.netvisor.pn_log_audit_exception.run_cli')
        self.run_nvos_commands = self.mock_run_nvos_commands.start()

        self.mock_run_check_cli = patch('ansible.modules.network.netvisor.pn_log_audit_exception.check_cli')
        self.run_check_cli = self.mock_run_check_cli.start()

    def tearDown(self):
        self.mock_run_nvos_commands.stop()
        self.mock_run_check_cli.stop()

    def run_cli_patch(self, module, cli, state_map):
        if state_map['present'] == 'log-audit-exception-create':
            results = dict(
                changed=True,
                cli_cmd=cli
            )
        elif state_map['absent'] == 'log-audit-exception-delete':
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

    def test_log_audit_exception_create(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_audit_type': 'cli',
                         'pn_pattern': 'test', 'pn_scope': 'local', 'pn_access': 'any', 'state': 'present'})
        result = self.execute_module(changed=True, state='present')
        expected_cmd = ' switch sw01 log-audit-exception-create cli pattern test any scope local '
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_log_audit_exception_delete(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_audit_type': 'cli',
                         'pn_pattern': 'test', 'pn_access': 'any', 'state': 'absent'})
        result = self.execute_module(changed=True, state='absent')
        expected_cmd = ' switch sw01 log-audit-exception-delete cli pattern test any'
        self.assertEqual(result['cli_cmd'], expected_cmd)
