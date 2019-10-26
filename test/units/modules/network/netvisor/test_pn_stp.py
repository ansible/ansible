# Copyright: (c) 2018, Pluribus Networks
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.netvisor import pn_stp
from units.modules.utils import set_module_args
from .nvos_module import TestNvosModule


class TestStpModule(TestNvosModule):

    module = pn_stp

    def setUp(self):
        self.mock_run_nvos_commands = patch('ansible.modules.network.netvisor.pn_stp.run_cli')
        self.run_nvos_commands = self.mock_run_nvos_commands.start()

    def tearDown(self):
        self.mock_run_nvos_commands.stop()

    def run_cli_patch(self, module, cli, state_map):
        if state_map['update'] == 'stp-modify':
            results = dict(
                changed=True,
                cli_cmd=cli
            )
        module.exit_json(**results)

    def load_fixtures(self, commands=None, state=None, transport='cli'):
        self.run_nvos_commands.side_effect = self.run_cli_patch

    def test_stp_modify_t1(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_hello_time': '3',
                         'pn_stp_mode': 'rstp', 'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 stp-modify  hello-time 3 root-guard-wait-time 20 mst-max-hops 20 max-age 20 '
        expected_cmd += 'stp-mode rstp forwarding-delay 15 bridge-priority 32768'
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_stp_modify_t2(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_root_guard_wait_time': '50',
                         'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 stp-modify  hello-time 2 root-guard-wait-time 50 mst-max-hops 20 '
        expected_cmd += 'max-age 20 forwarding-delay 15 bridge-priority 32768'
        self.assertEqual(result['cli_cmd'], expected_cmd)
