# Copyright: (c) 2018, Pluribus Networks
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

from units.compat.mock import patch
from ansible.modules.network.netvisor import pn_igmp_snooping
from units.modules.utils import set_module_args
from .nvos_module import TestNvosModule, load_fixture


class TestAdminServiceModule(TestNvosModule):

    module = pn_igmp_snooping

    def setUp(self):
        self.mock_run_nvos_commands = patch('ansible.modules.network.netvisor.pn_igmp_snooping.run_cli')
        self.run_nvos_commands = self.mock_run_nvos_commands.start()

    def tearDown(self):
        self.mock_run_nvos_commands.stop()

    def run_cli_patch(self, module, cli, state_map):
        if state_map['update'] == 'igmp-snooping-modify':
            results = dict(
                changed=True,
                cli_cmd=cli
            )
        module.exit_json(**results)

    def load_fixtures(self, commands=None, state=None, transport='cli'):
        self.run_nvos_commands.side_effect = self.run_cli_patch

    def test_igmp_snooping_modify_t1(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_vxlan': True,
                         'pn_enable_vlans': '1-399,401-4092', 'pn_no_snoop_linklocal_vlans': 'none', 'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 igmp-snooping-modify  vxlan  enable-vlans '
        expected_cmd += '1-399,401-4092 no-snoop-linklocal-vlans none'
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_igmp_snooping_modify_t2(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_scope': 'local',
                         'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 igmp-snooping-modify  scope local'
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_igmp_snooping_modify_t3(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_vxlan': False,
                         'pn_enable_vlans': '1-399', 'pn_igmpv3_vlans': '1-399', 'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = ' switch sw01 igmp-snooping-modify  no-vxlan  igmpv3-vlans 1-399 enable-vlans 1-399'
        self.assertEqual(result['cli_cmd'], expected_cmd)
