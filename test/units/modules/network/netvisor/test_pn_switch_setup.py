# Copyright: (c) 2018, Pluribus Networks
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

from units.compat.mock import patch
from ansible.modules.network.netvisor import pn_switch_setup
from units.modules.utils import set_module_args
from .nvos_module import TestNvosModule, load_fixture


class TestSwitchSetupModule(TestNvosModule):

    module = pn_switch_setup

    def setUp(self):
        self.mock_run_nvos_commands = patch('ansible.modules.network.netvisor.pn_switch_setup.run_cli')
        self.run_nvos_commands = self.mock_run_nvos_commands.start()

    def tearDown(self):
        self.mock_run_nvos_commands.stop()

    def run_cli_patch(self, module, cli, state_map):
        if state_map['update'] == 'switch-setup-modify':
            results = dict(
                changed=True,
                cli_cmd=cli
            )
        module.exit_json(**results)

    def load_fixtures(self, commands=None, state=None, transport='cli'):
        self.run_nvos_commands.side_effect = self.run_cli_patch

    def test_pn_switch_setup_modify_t1(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_timezone': 'America/New_York',
                         'pn_in_band_ip': '20.20.1.1', 'pn_in_band_netmask': '24', 'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 switch-setup-modify  timezone America/New_York '
        expected_cmd += 'in-band-netmask 24 in-band-ip 20.20.1.1'
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_pn_switch_setup_modify_t2(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_in_band_ip6': '2001:0db8:85a3::8a2e:0370:7334',
                         'pn_in_band_netmask_ip6': '127', 'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 switch-setup-modify  in-band-ip6 2001:0db8:85a3::8a2e:0370:7334 '
        expected_cmd += 'in-band-netmask-ip6 127'
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_pn_switch_setup_modify_t3(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_date': '2019-01-11',
                         'pn_loopback_ip': '10.10.10.1', 'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 switch-setup-modify  date 2019-01-11 loopback-ip 10.10.10.1'
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_pn_switch_setup_modify_t4(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_dns_ip': '172.16.5.5',
                         'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 switch-setup-modify  dns-ip 172.16.5.5'
        self.assertEqual(result['cli_cmd'], expected_cmd)
