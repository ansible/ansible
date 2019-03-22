# Copyright: (c) 2018, Pluribus Networks
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

from units.compat.mock import patch
from ansible.modules.network.netvisor import pn_snmp_trap_sink
from units.modules.utils import set_module_args
from .nvos_module import TestNvosModule, load_fixture


class TestSnmpTrapSinkModule(TestNvosModule):

    module = pn_snmp_trap_sink

    def setUp(self):
        self.mock_run_nvos_commands = patch('ansible.modules.network.netvisor.pn_snmp_trap_sink.run_cli')
        self.run_nvos_commands = self.mock_run_nvos_commands.start()

        self.mock_run_check_cli = patch('ansible.modules.network.netvisor.pn_snmp_trap_sink.check_cli')
        self.run_check_cli = self.mock_run_check_cli.start()

    def tearDown(self):
        self.mock_run_nvos_commands.stop()
        self.run_check_cli.stop()

    def run_cli_patch(self, module, cli, state_map):
        if state_map['present'] == 'snmp-trap-sink-create':
            results = dict(
                changed=True,
                cli_cmd=cli
            )
        elif state_map['absent'] == 'snmp-trap-sink-delete':
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

    def test_snmp_trap_sink_create(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_community': 'foo',
                         'pn_dest_host': '192.168.67.8', 'pn_type': 'TRAP_TYPE_V2_INFORM', 'state': 'present'})
        result = self.execute_module(changed=True, state='present')
        expected_cmd = ' switch sw01 snmp-trap-sink-create  type TRAP_TYPE_V2_INFORM dest-host 192.168.67.8 '
        expected_cmd += 'community foo dest-port 162'
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_snmp_trap_sink_delete(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_community': 'foo',
                         'pn_dest_host': '192.168.67.8', 'pn_type': 'TRAP_TYPE_V2_INFORM', 'state': 'absent'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 snmp-trap-sink-delete  community foo dest-host 192.168.67.8 dest-port 162'
        self.assertEqual(result['cli_cmd'], expected_cmd)
