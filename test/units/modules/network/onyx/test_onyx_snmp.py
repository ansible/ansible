#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_snmp
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxSNMPModule(TestOnyxModule):

    module = onyx_snmp
    enabled = False

    def setUp(self):
        self.enabled = False
        super(TestOnyxSNMPModule, self).setUp()
        self.mock_get_config = patch.object(
            onyx_snmp.OnyxSNMPModule, "_show_snmp_config")
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestOnyxSNMPModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        config_file = 'onyx_snmp_show.cfg'
        data = load_fixture(config_file)
        self.get_config.return_value = data
        self.load_config.return_value = None

    def test_snmp_state_no_change(self):
        set_module_args(dict(state_enabled=True))
        self.execute_module(changed=False)

    def test_snmp_state_with_change(self):
        set_module_args(dict(state_enabled=False))
        commands = ['no snmp-server enable']
        self.execute_module(changed=True, commands=commands)

    def test_snmp_contact_no_change(self):
        set_module_args(dict(contact_name='sara'))
        self.execute_module(changed=False)

    def test_snmp_contact_with_change(self):
        set_module_args(dict(contact_name='Omar'))
        commands = ['snmp-server contact Omar']
        self.execute_module(changed=True, commands=commands)

    def test_snmp_location_no_change(self):
        set_module_args(dict(location='Jordan'))
        self.execute_module(changed=False)

    def test_snmp_location_with_change(self):
        set_module_args(dict(location='London'))
        commands = ['snmp-server location London']
        self.execute_module(changed=True, commands=commands)

    def test_snmp_communities_state_no_change(self):
        set_module_args(dict(communities_enabled=True))
        self.execute_module(changed=False)

    def test_snmp_communities_state_with_change(self):
        set_module_args(dict(communities_enabled=False))
        commands = ['no snmp-server enable communities']
        self.execute_module(changed=True, commands=commands)

    def test_snmp_multi_communities_state_with_no_change(self):
        set_module_args(dict(multi_communities_enabled=True))
        self.execute_module(changed=False)

    def test_snmp_multi_communities_state_with_change(self):
        set_module_args(dict(multi_communities_enabled=False))
        commands = ['no snmp-server enable mult-communities']
        self.execute_module(changed=True, commands=commands)

    def test_snmp_communities_no_change(self):
        set_module_args(dict(snmp_communities=[dict(community_name='community_2',
                                                    community_type='read-write')]))
        self.execute_module(changed=False)

    def test_snmp_communities_with_change(self):
        set_module_args(dict(snmp_communities=[dict(community_name='community_2',
                                                    community_type='read-only')]))
        commands = ['snmp-server community community_2 ro']
        self.execute_module(changed=True, commands=commands)

    def test_snmp_communities_delete_with_change(self):
        set_module_args(dict(snmp_communities=[dict(community_name='community_1',
                                                    state='absent')]))
        commands = ['no snmp-server community community_1']
        self.execute_module(changed=True, commands=commands)

    def test_snmp_notify_state_no_change(self):
        set_module_args(dict(notify_enabled=True))
        self.execute_module(changed=False)

    def test_snmp_notify_state_with_change(self):
        set_module_args(dict(notify_enabled=False))
        commands = ['no snmp-server enable notify']
        self.execute_module(changed=True, commands=commands)

    def test_snmp_notify_port_no_change(self):
        set_module_args(dict(notify_port='1'))
        self.execute_module(changed=False)

    def test_snmp_notify_port_with_change(self):
        set_module_args(dict(notify_port='2'))
        commands = ['snmp-server notify port 2']
        self.execute_module(changed=True, commands=commands)

    def test_snmp_notify_community_no_change(self):
        set_module_args(dict(notify_community='community_1'))
        self.execute_module(changed=False)

    def test_snmp_notify_community_with_change(self):
        set_module_args(dict(notify_community='community_2'))
        commands = ['snmp-server notify community community_2']
        self.execute_module(changed=True, commands=commands)

    def test_snmp_notify_send_test_with_change(self):
        set_module_args(dict(notify_send_test='yes'))
        commands = ['snmp-server notify send-test']
        self.execute_module(changed=True, commands=commands)

    def test_snmp_notify_event_with_change(self):
        set_module_args(dict(notify_event='interface-up'))
        commands = ['snmp-server notify event interface-up']
        self.execute_module(changed=True, commands=commands)

    def test_snmp_permissions_with_change(self):
        set_module_args(dict(snmp_permissions=[dict(state_enabled=True,
                                                    permission_type='RFC1213-MIB')]))
        commands = ['snmp-server enable set-permission RFC1213-MIB']
        self.execute_module(changed=True, commands=commands)

    def test_snmp_engine_id_reset_with_change(self):
        set_module_args(dict(engine_id_reset='yes'))
        commands = ['snmp-server engineID reset']
        self.execute_module(changed=True, commands=commands)
