#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_ptp_interface
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxPtpInterface(TestOnyxModule):

    module = onyx_ptp_interface
    enabled = False
    interfaces = {'Eth1/1': ('ethernet', '1/1'), 'Vlan 1': ('vlan', '1')}

    def setUp(self):
        self.enabled = False
        super(TestOnyxPtpInterface, self).setUp()
        self.mock_get_config = patch.object(
            onyx_ptp_interface.OnyxPtpInterfaceModule, "_show_ptp_interface_config")
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestOnyxPtpInterface, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        config_file = 'onyx_show_ptp_interface.cfg'
        data = None
        if self.enabled:
            data = load_fixture(config_file)

        self.get_config.return_value = data
        self.load_config.return_value = None

    def test_ptp_disabled_no_change(self):
        for interface in self.interfaces:
            set_module_args(dict(state='disabled', name=interface))
            self.execute_module(changed=False)

    def test_ptp_disabled_with_change(self):
        self.enabled = True
        for interface in self.interfaces:
            set_module_args(dict(state='disabled', name=interface))
            interface_type, interface_id = self.interfaces.get(interface)
            commands = ['no interface %s %s ptp enable' % (interface_type, interface_id)]
            self.execute_module(changed=True, commands=commands)

    def test_ptp_enabled_no_change(self):
        self.enabled = True
        for interface in self.interfaces:
            set_module_args(dict(state='enabled', name=interface))
            self.execute_module(changed=False)

    def test_ptp_enabled_with_change(self):
        for interface in self.interfaces:
            set_module_args(dict(state='disabled', name=interface))
            interface_type, interface_id = self.interfaces.get(interface)
            set_module_args(dict(state='enabled', name=interface))
            commands = ['interface %s %s ptp enable' % (interface_type, interface_id)]
            self.execute_module(changed=True, commands=commands)

    def test_ptp_attributs_no_change(self):
        self.enabled = True
        for interface in self.interfaces:
            set_module_args(dict(state='enabled', name=interface, delay_request=0,
                                 announce_interval=-2, announce_timeout=3,
                                 sync_interval=-3))
        self.execute_module(changed=False)

    def test_ptp_attributs_with_change(self):
        self.enabled = True
        for interface in self.interfaces:
            set_module_args(dict(state='enabled', name=interface, delay_request=2,
                                 announce_interval=-1, announce_timeout=5, sync_interval=-1))
            interface_type, interface_id = self.interfaces.get(interface)
            commands = ['interface %s %s ptp delay-req interval 2' % (interface_type, interface_id),
                        'interface %s %s ptp announce interval -1' % (interface_type, interface_id),
                        'interface %s %s ptp announce timeout 5' % (interface_type, interface_id),
                        'interface %s %s ptp sync interval -1' % (interface_type, interface_id)]
        self.execute_module(changed=True, commands=commands)
