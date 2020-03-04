# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.eos import eos_lacp
from units.modules.utils import set_module_args
from .eos_module import TestEosModule, load_fixture


class TestEosLacpInterfacesModule(TestEosModule):
    module = eos_lacp

    def setUp(self):
        super(TestEosLacpInterfacesModule, self).setUp()

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

        self.mock_execute_show_command = patch('ansible.module_utils.network.eos.facts.lacp.lacp.LacpFacts.get_device_data')
        self.execute_show_command = self.mock_execute_show_command.start()

    def tearDown(self):
        super(TestEosLacpInterfacesModule, self).tearDown()
        self.mock_get_resource_connection_config.stop()
        self.mock_get_resource_connection_facts.stop()
        self.mock_edit_config.stop()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_execute_show_command.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        def load_from_file(*args, **kwargs):
            return load_fixture('eos_lacp_config.cfg')
        self.execute_show_command.side_effect = load_from_file

    def test_eos_lacp_default(self):
        set_module_args(dict(
            config=dict(
                system=dict(priority=50)
            )
        ))
        commands = ['lacp system-priority 50']
        self.execute_module(changed=True, commands=commands)

    def test_eos_lacp_default_idempotent(self):
        set_module_args(dict(
            config=dict(
                system=dict(priority=10)
            )
        ))
        self.execute_module(changed=False, commands=[])

    def test_eos_lacp_merged(self):
        set_module_args(dict(
            config=dict(
                system=dict(priority=50)
            ), state="merged"
        ))
        commands = ['lacp system-priority 50']
        self.execute_module(changed=True, commands=commands)

    def test_eos_lacp_merged_idempotent(self):
        set_module_args(dict(
            config=dict(
                system=dict(priority=10)
            ), state="merged"
        ))
        self.execute_module(changed=False, commands=[])

    def test_eos_l3_interfaces_replaced(self):
        set_module_args(dict(
            config=dict(
                system=dict(priority=20)
            ), state="replaced"
        ))
        commands = ['lacp system-priority 20']
        self.execute_module(changed=True, commands=commands)

    def test_eos_l3_interfaces_replaced_idempotent(self):
        set_module_args(dict(
            config=dict(
                system=dict(priority=10)
            ), state="replaced"
        ))
        self.execute_module(changed=False, commands=[])

    def test_eos_l3_interfaces_deleted(self):
        set_module_args(dict(state="deleted"))
        commands = ['no lacp system-priority']
        self.execute_module(changed=True, commands=commands)
