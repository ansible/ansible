# Copyright: (c) 2018, Pluribus Networks
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

from units.compat.mock import patch
from ansible.modules.network.netvisor import pn_system_settings
from units.modules.utils import set_module_args
from .nvos_module import TestNvosModule, load_fixture


class TestSystemSettingsModule(TestNvosModule):

    module = pn_system_settings

    def setUp(self):
        self.mock_run_nvos_commands = patch('ansible.modules.network.netvisor.pn_system_settings.run_cli')
        self.run_nvos_commands = self.mock_run_nvos_commands.start()

    def tearDown(self):
        self.mock_run_nvos_commands.stop()

    def run_cli_patch(self, module, cli, state_map):
        if state_map['update'] == 'system-settings-modify':
            results = dict(
                changed=True,
                cli_cmd=cli
            )
        module.exit_json(**results)

    def load_fixtures(self, commands=None, state=None, transport='cli'):
        self.run_nvos_commands.side_effect = self.run_cli_patch

    def test_system_settings_modify_t1(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_cliusername': 'foo',
                         'pn_clipassword': 'foo123', 'pn_auto_trunk': False, 'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = '/usr/bin/cli --quiet -e --no-login-prompt --user "foo":"foo123"  switch sw01 system-settings-modify  no-auto-trunk '
        self.assertEqual(result['cli_cmd'], expected_cmd)

    def test_system_settings_modify_t2(self):
        set_module_args({'pn_cliswitch': 'sw01', 'pn_cliusername': 'foo',
                         'pn_clipassword': 'foo123', 'pn_optimize_arps': True, 'state': 'update'})
        result = self.execute_module(changed=True, state='update')
        expected_cmd = '/usr/bin/cli --quiet -e --no-login-prompt --user "foo":"foo123"  switch sw01 system-settings-modify  optimize-arps '
        self.assertEqual(result['cli_cmd'], expected_cmd)
