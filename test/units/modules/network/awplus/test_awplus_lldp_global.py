#
# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.awplus import awplus_lldp_global
from units.modules.utils import set_module_args
from .awplus_module import TestAwplusModule, load_fixture


class TestAwplusLldpGlobalModule(TestAwplusModule):
    module = awplus_lldp_global

    def setUp(self):
        super(TestAwplusLldpGlobalModule, self).setUp()

        self.mock_get_config = patch(
            'ansible.module_utils.network.common.network.Config.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.common.network.Config.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_resource_connection_config = patch(
            'ansible.module_utils.network.common.cfg.base.get_resource_connection')
        self.get_resource_connection_config = self.mock_get_resource_connection_config.start()

        self.mock_get_resource_connection_facts = patch(
            'ansible.module_utils.network.common.facts.facts.get_resource_connection')
        self.get_resource_connection_facts = self.mock_get_resource_connection_facts.start()

        self.mock_edit_config = patch(
            'ansible.module_utils.network.awplus.providers.providers.CliProvider.edit_config')
        self.edit_config = self.mock_edit_config.start()

        self.mock_execute_show_command = patch(
            'ansible.module_utils.network.awplus.facts.lldp_global.lldp_global.Lldp_globalFacts.get_lldp_facts')
        self.execute_show_command = self.mock_execute_show_command.start()

    def tearDown(self):
        super(TestAwplusLldpGlobalModule, self).tearDown()
        self.mock_get_resource_connection_config.stop()
        self.mock_get_resource_connection_facts.stop()
        self.mock_edit_config.stop()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_execute_show_command.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        def load_from_file(*args, **kwargs):
            return load_fixture('awplus_lldp_config.cfg')
        self.execute_show_command.side_effect = load_from_file

    def test_awplus_lldp_default(self):
        set_module_args(dict(
            config=dict(
                enabled=True,
                reinit=3
            )
        ))
        commands = ['lldp run', 'lldp reinit 3']
        self.execute_module(changed=True, commands=commands)

    def test_awplus_lldp_default_idempotent(self):
        set_module_args(dict(
            config=dict(
                enabled=False,
                reinit=2,
                holdtime=4,
                timer=30
            )
        ))
        self.execute_module(changed=False, commands=[])

    def test_awplus_lldp_merged(self):
        set_module_args(dict(
            config=dict(
                holdtime=6,
                timer=36
            ), state='merged'
        ))
        commands = ['lldp holdtime 6', 'lldp timer 36']
        self.execute_module(changed=True, commands=commands)

    def test_awplus_lldp_merged_idempotent(self):
        set_module_args(dict(
            config=dict(
                enabled=False,
                reinit=2,
                holdtime=4,
                timer=30
            ), state='merged'
        ))
        self.execute_module(changed=False, commands=[])

    def test_awplus_lldp_replaced(self):
        set_module_args(dict(
            config=dict(
                enabled=True,
                holdtime=1,
            ), state='replaced'
        ))
        commands = ['lldp run', 'lldp holdtime 1',
                    'no lldp reinit', 'no lldp timer']
        self.execute_module(changed=True, commands=commands)

    def test_awplus_lldp_replaced_idempotent(self):
        set_module_args(dict(
            config=dict(
                enabled=False,
                reinit=2,
                holdtime=4,
                timer=30
            ), state='replaced'
        ))
        self.execute_module(changed=False, commands=[])

    def test_awplus_lldp_deleted(self):
        set_module_args(dict(config=dict(), state='deleted'))
        commands = ['no lldp timer', 'no lldp holdtime', 'no lldp reinit']
        self.execute_module(changed=True, commands=commands)
