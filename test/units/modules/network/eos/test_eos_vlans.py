#
# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.eos import eos_vlans
from units.modules.utils import set_module_args
from .eos_module import TestEosModule, load_fixture


class TestEosVlansModule(TestEosModule):
    module = eos_vlans

    def setUp(self):
        super(TestEosVlansModule, self).setUp()

        self.mock_get_config = patch('ansible.module_utils.network.common.network.Config.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.module_utils.network.common.network.Config.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_resource_connection_config = patch('ansible.module_utils.network.common.cfg.base.get_resource_connection')
        self.get_resource_connection_config = self.mock_get_resource_connection_config.start()

        self.mock_get_resource_connection_facts = patch('ansible.module_utils.network.common.facts.facts.get_resource_connection')
        self.get_resource_connection_facts = self.mock_get_resource_connection_facts.start()

        self.mock_edit_config = patch('ansible.module_utils.network.eos.providers.providers.CliProvider.edit_config')
        self.edit_config = self.mock_edit_config.start()

        self.mock_execute_show_command = patch('ansible.module_utils.network.eos.config.vlans.vlans.Vlans.get_vlans_facts')
        self.execute_show_command = self.mock_execute_show_command.start()

    def tearDown(self):
        super(TestEosVlansModule, self).tearDown()
        self.mock_get_resource_connection_config.stop()
        self.mock_get_resource_connection_facts.stop()
        self.mock_edit_config.stop()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_execute_show_command.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        file_cmd = load_fixture('eos_vlan_config.cfg').split()
        file_cmd_dict = {}
        for i in range(0, len(file_cmd), 2):
            if file_cmd[i] == 'vlan_id':
                y = int(file_cmd[i + 1])
            else:
                y = file_cmd[i + 1]
            file_cmd_dict.update({file_cmd[i]: y})
        self.execute_show_command.return_value = [file_cmd_dict]

    def test_eos_vlan_default(self):
        self.execute_show_command.return_value = []
        set_module_args(dict(
            config=[dict(
                vlan_id=30,
                name="thirty"
            )]
        ))
        commands = ['vlan 30', 'name thirty']
        self.execute_module(changed=True, commands=commands)

    def test_eos_vlan_default_idempotent(self):
        self.execute_show_command.return_value = load_fixture('eos_vlan_config.cfg')
        set_module_args(dict(
            config=[dict(
                vlan_id=10,
                name="ten"
            )]
        ))
        self.execute_module(changed=False, commands=[])

    def test_eos_vlan_merged(self):
        self.execute_show_command.return_value = []
        set_module_args(dict(
            config=[dict(
                vlan_id=30,
                name="thirty"
            )], state="merged"
        ))
        commands = ['vlan 30', 'name thirty']
        self.execute_module(changed=True, commands=commands)

    def test_eos_vlan_merged_idempotent(self):
        self.execute_show_command.return_value = load_fixture('eos_vlan_config.cfg')
        set_module_args(dict(
            config=[dict(
                vlan_id=10,
                name="ten"
            )], state="merged"
        ))
        self.execute_module(changed=False, commands=[])

    def test_eos_vlan_replaced(self):
        self.execute_show_command.return_value = []
        set_module_args(dict(
            config=[dict(
                vlan_id=10,
                name="tenreplaced",
                state="suspend"
            )], state="replaced"
        ))
        commands = ['vlan 10', 'name tenreplaced', 'state suspend']
        self.execute_module(changed=True, commands=commands)

    def test_eos_vlan_replaced_idempotent(self):
        self.execute_show_command.return_value = load_fixture('eos_vlan_config.cfg')
        set_module_args(dict(
            config=[dict(
                vlan_id=10,
                name="ten"
            )], state="replaced"
        ))
        self.execute_module(changed=False, commands=[])

    def test_eos_vlan_overridden(self):
        self.execute_show_command.return_value = []
        set_module_args(dict(
            config=[dict(
                vlan_id=30,
                name="thirty",
                state="suspend"
            )], state="overridden"
        ))
        commands = ['no vlan 10', 'vlan 30', 'name thirty', 'state suspend']
        self.execute_module(changed=True, commands=commands)

    def test_eos_vlan_overridden_idempotent(self):
        self.execute_show_command.return_value = load_fixture('eos_vlan_config.cfg')
        set_module_args(dict(
            config=[dict(
                vlan_id=10,
                name="ten"
            )], state="overridden"
        ))
        self.execute_module(changed=False, commands=[])

    def test_eos_vlan_deleted(self):
        set_module_args(dict(
            config=[dict(
                vlan_id=10,
                name="ten",
            )], state="deleted"
        ))
        commands = ['no vlan 10']
        self.execute_module(changed=True, commands=commands)

    def test_eos_vlan_id_datatype(self):
        set_module_args(dict(
            config=[dict(
                vlan_id="thirty"
            )]
        ))
        result = self.execute_module(failed=True)
        self.assertIn("we were unable to convert to int", result['msg'])

    def test_eos_vlan_state_datatype(self):
        set_module_args(dict(
            config=[dict(
                vlan_id=30,
                state=10
            )]
        ))
        result = self.execute_module(failed=True)
        self.assertIn("value of state must be one of: active, suspend", result['msg'])
