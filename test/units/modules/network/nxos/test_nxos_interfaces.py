# (c) 2019 Red Hat Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from textwrap import dedent
from units.compat.mock import patch
from units.modules.utils import AnsibleFailJson
from ansible.modules.network.nxos import nxos_interfaces
from ansible.module_utils.network.nxos.config.interfaces.interfaces import Interfaces
from ansible.module_utils.network.nxos.facts.interfaces.interfaces import InterfacesFacts
from .nxos_module import TestNxosModule, load_fixture, set_module_args

ignore_provider_arg = True


class TestNxosInterfacesModule(TestNxosModule):

    module = nxos_interfaces

    def setUp(self):
        super(TestNxosInterfacesModule, self).setUp()

        self.mock_FACT_LEGACY_SUBSETS = patch('ansible.module_utils.network.nxos.facts.facts.FACT_LEGACY_SUBSETS')
        self.FACT_LEGACY_SUBSETS = self.mock_FACT_LEGACY_SUBSETS.start()

        self.mock_get_resource_connection_config = patch('ansible.module_utils.network.common.cfg.base.get_resource_connection')
        self.get_resource_connection_config = self.mock_get_resource_connection_config.start()

        self.mock_get_resource_connection_facts = patch('ansible.module_utils.network.common.facts.facts.get_resource_connection')
        self.get_resource_connection_facts = self.mock_get_resource_connection_facts.start()

        self.mock_edit_config = patch('ansible.module_utils.network.nxos.config.interfaces.interfaces.Interfaces.edit_config')
        self.edit_config = self.mock_edit_config.start()
        self.mock__device_info = patch('ansible.module_utils.network.nxos.facts.interfaces.interfaces.InterfacesFacts._device_info')
        self._device_info = self.mock__device_info.start()

    def tearDown(self):
        super(TestNxosInterfacesModule, self).tearDown()
        self.mock_FACT_LEGACY_SUBSETS.stop()
        self.mock_get_resource_connection_config.stop()
        self.mock_get_resource_connection_facts.stop()
        self.mock_edit_config.stop()
        self.mock__device_info.stop()

    def load_fixtures(self, commands=None, device=''):
        self.mock_FACT_LEGACY_SUBSETS.return_value = dict()
        self.get_resource_connection_config.return_value = None
        self.edit_config.return_value = None
        if device == 'legacy':
            # call execute_module() with device='legacy' to use this codepath
            self._device_info.return_value = {'network_os_platform': 'N3K-Cxxx'}
        else:
            self._device_info.return_value = {'network_os_platform': 'N9K-Cxxx'}

    SHOW_RUN_SYSDEF = "show running-config all | incl 'system default switchport'"
    SHOW_RUN_INTF = 'show running-config | section ^interface'

    def test_1(self):
        # Overall general test for each state: merged, deleted, overridden, replaced
        sysdefs = dedent('''\
          !
          ! Interfaces default to L3 !!
          !
          no system default switchport
          no system default switchport shutdown
        ''')
        intf = dedent('''\
          interface mgmt0
            description do not manage mgmt0!
          interface Ethernet1/1
            description foo
          interface Ethernet1/2
            description bar
            speed 1000
            duplex full
            mtu 4096
            ip forward
            fabric forwarding mode anycast-gateway
          interface Ethernet1/3
          interface Ethernet1/4
          interface Ethernet1/5
          interface Ethernet1/6
            no shutdown
          interface loopback0
            description test-loopback
        ''')
        self.get_resource_connection_facts.return_value = {
            self.SHOW_RUN_SYSDEF: sysdefs,
            self.SHOW_RUN_INTF: intf
        }
        playbook = dict(config=[
            dict(name='Ethernet1/1', description='ansible', mode='layer3'),
            dict(name='Ethernet1/2', speed=10000, duplex='auto', mtu=1500,
                 ip_forward=False, fabric_forwarding_anycast_gateway=False),
            dict(name='Ethernet1/3', description='ansible', mode='layer3'),
            dict(name='Ethernet1/3.101', description='test-sub-intf', enabled=False),
            dict(name='Ethernet1/4', mode='layer2'),
            dict(name='Ethernet1/5'),
            dict(name='loopback1', description='test-loopback')
        ])
        merged = [
            # Update existing device states with any differences in the playbook.
            'interface Ethernet1/1', 'description ansible',
            'interface Ethernet1/2', 'speed 10000', 'duplex auto', 'mtu 1500',
            'no ip forward', 'no fabric forwarding mode anycast-gateway',
            'interface Ethernet1/3', 'description ansible',
            'interface Ethernet1/3.101', 'description test-sub-intf',
            'interface Ethernet1/4', 'switchport',
            'interface loopback1', 'description test-loopback'
        ]
        playbook['state'] = 'merged'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=merged)

        deleted = [
            # Reset existing device state to default values. Scope is limited to
            # objects in the play. Ignores any play attrs other than 'name'.
            'interface Ethernet1/1', 'no description',
            'interface Ethernet1/2', 'no description', 'no speed', 'no duplex', 'no mtu',
            'no ip forward', 'no fabric forwarding mode anycast-gateway',
        ]
        playbook['state'] = 'deleted'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=deleted)

        replaced = [
            # Scope is limited to objects in the play. The play is the source of
            # truth for the objects that are explicitly listed.
            'interface Ethernet1/1', 'description ansible',
            'interface Ethernet1/2', 'no description',
            'no ip forward', 'no fabric forwarding mode anycast-gateway',
            'speed 10000', 'duplex auto', 'mtu 1500',
            'interface Ethernet1/3', 'description ansible',
            'interface Ethernet1/3.101', 'description test-sub-intf',
            'interface Ethernet1/4', 'switchport',
            'interface loopback1', 'description test-loopback'
        ]
        playbook['state'] = 'replaced'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=replaced)

        overridden = [
            # The play is the source of truth. Similar to replaced but the scope
            # includes all objects on the device; i.e. it will also reset state
            # on objects not found in the play.
            'interface Ethernet1/1', 'description ansible',
            'interface Ethernet1/2', 'no description',
            'no ip forward', 'no fabric forwarding mode anycast-gateway',
            'speed 10000', 'duplex auto', 'mtu 1500',
            'interface Ethernet1/6', 'shutdown',
            'interface loopback0', 'no description',
            'interface Ethernet1/3', 'description ansible',
            'interface Ethernet1/4', 'switchport',
            'interface Ethernet1/3.101', 'description test-sub-intf',
            'interface loopback1', 'description test-loopback'
        ]
        playbook['state'] = 'overridden'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=overridden)

    def test_2(self):
        # 'enabled'/shutdown behaviors are tricky:
        # - different default states for different interface types for different
        #   platforms, based on 'system default switchport' settings
        # - virtual interfaces may not exist yet
        # - idempotence for interfaces with all default states
        sysdefs = dedent('''\
          !
          ! Interfaces default to L3 !!
          !
          no system default switchport
          no system default switchport shutdown
        ''')
        intf = dedent('''\
          interface mgmt0
          interface Ethernet1/1
          interface Ethernet1/2
            switchport
            shutdown
          interface Ethernet1/3
            switchport
          interface loopback1
          interface loopback2
            shutdown
          interface loopback3
          interface loopback8
          interface loopback9
            shutdown
          interface port-channel2
          interface port-channel3
            shutdown
        ''')
        self.get_resource_connection_facts.return_value = {
            self.SHOW_RUN_SYSDEF: sysdefs,
            self.SHOW_RUN_INTF: intf
        }
        playbook = dict(config=[
            # Set non-default states on existing objs
            dict(name='Ethernet1/1', mode='layer3', enabled=True),
            dict(name='loopback1', enabled=False),
            # Set default states on existing objs
            dict(name='Ethernet1/2', enabled=True),
            dict(name='loopback2', enabled=True),
            # Set explicit default state on existing objs (no chg)
            dict(name='Ethernet1/3', enabled=True),
            dict(name='loopback3', enabled=True),
            dict(name='port-channel3', enabled=True),
            # Set default state on non-existent objs; no state changes but need to create intf
            dict(name='loopback4', enabled=True),
            dict(name='port-channel4', enabled=True),
            dict(name='Ethernet1/4.101')
        ])
        # Testing with newer code version
        merged = [
            'interface Ethernet1/1', 'no shutdown',
            'interface loopback1', 'shutdown',
            'interface Ethernet1/2', 'no shutdown',
            'interface loopback2', 'no shutdown',
            'interface port-channel3', 'no shutdown',
            'interface loopback4',
            'interface port-channel4',
            'interface Ethernet1/4.101'
        ]
        playbook['state'] = 'merged'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=merged)

        deleted = [
            # e1/2 becomes L3 so enable default changes to false
            'interface Ethernet1/2', 'no switchport',
            'interface loopback2', 'no shutdown',
            'interface Ethernet1/3', 'no switchport',
            'interface port-channel3', 'no shutdown'
        ]
        playbook['state'] = 'deleted'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=deleted)

        replaced = [
            'interface Ethernet1/1', 'no shutdown',
            'interface loopback1', 'shutdown',
            'interface Ethernet1/2', 'no switchport', 'no shutdown',
            'interface loopback2', 'no shutdown',
            'interface Ethernet1/3', 'no switchport', 'no shutdown',
            'interface port-channel3', 'no shutdown',
            'interface loopback4',
            'interface port-channel4',
            'interface Ethernet1/4.101'
        ]
        playbook['state'] = 'replaced'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=replaced)

        overridden = [
            'interface Ethernet1/2', 'no switchport', 'no shutdown',
            'interface Ethernet1/3', 'no switchport', 'no shutdown',
            'interface loopback2', 'no shutdown',
            'interface loopback9', 'no shutdown',
            'interface port-channel3', 'no shutdown',
            'interface Ethernet1/1', 'no shutdown',
            'interface loopback1', 'shutdown',
            'interface loopback4',
            'interface port-channel4',
            'interface Ethernet1/4.101'
        ]
        playbook['state'] = 'overridden'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=overridden)

    def test_3(self):
        # Testing 'enabled' with different 'system default' settings.
        # This is the same as test_2 with some minor changes.
        sysdefs = dedent('''\
          !
          ! Interfaces default to L2 !!
          !
          system default switchport
          system default switchport shutdown
        ''')
        intf = dedent('''\
          interface mgmt0
          interface Ethernet1/1
          interface Ethernet1/2
            no switchport
            no shutdown
          interface Ethernet1/3
            no switchport
          interface loopback1
          interface loopback2
            shutdown
          interface loopback3
          interface loopback8
          interface loopback9
            shutdown
          interface port-channel2
          interface port-channel3
            shutdown
        ''')
        self.get_resource_connection_facts.return_value = {
            self.SHOW_RUN_SYSDEF: sysdefs,
            self.SHOW_RUN_INTF: intf
        }
        playbook = dict(config=[
            # Set non-default states on existing objs
            dict(name='Ethernet1/1', mode='layer3', enabled=True),
            dict(name='loopback1', enabled=False),
            # Set default states on existing objs
            dict(name='Ethernet1/2', enabled=False),
            dict(name='loopback2', enabled=True),
            # Set explicit default state on existing objs (no chg)
            dict(name='Ethernet1/3', enabled=False),
            dict(name='loopback3', enabled=True),
            dict(name='port-channel3', enabled=True),
            # Set default state on non-existent objs; no state changes but need to create intf
            dict(name='loopback4', enabled=True),
            dict(name='port-channel4', enabled=True),
            dict(name='Ethernet1/4.101')
        ])
        merged = [
            'interface Ethernet1/1', 'no switchport', 'no shutdown',
            'interface loopback1', 'shutdown',
            'interface Ethernet1/2', 'shutdown',
            'interface loopback2', 'no shutdown',
            'interface port-channel3', 'no shutdown',
            'interface loopback4',
            'interface port-channel4',
            'interface Ethernet1/4.101'
        ]
        playbook['state'] = 'merged'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=merged)

        # Test with an older image version which has different defaults
        merged_legacy = [
            'interface Ethernet1/1', 'no switchport',
            'interface loopback1', 'shutdown',
            'interface Ethernet1/2', 'shutdown',
            'interface loopback2', 'no shutdown',
            'interface Ethernet1/3', 'shutdown',
            'interface port-channel3', 'no shutdown',
            'interface loopback4',
            'interface port-channel4',
            'interface Ethernet1/4.101'
        ]
        self.execute_module(changed=True, commands=merged_legacy, device='legacy')

        deleted = [
            'interface Ethernet1/2', 'switchport', 'shutdown',
            'interface loopback2', 'no shutdown',
            'interface Ethernet1/3', 'switchport',
            'interface port-channel3', 'no shutdown'
        ]
        playbook['state'] = 'deleted'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=deleted)

        replaced = [
            'interface Ethernet1/1', 'no switchport', 'no shutdown',
            'interface loopback1', 'shutdown',
            'interface Ethernet1/2', 'switchport', 'shutdown',
            'interface loopback2', 'no shutdown',
            'interface Ethernet1/3', 'switchport',
            'interface port-channel3', 'no shutdown',
            'interface loopback4',
            'interface port-channel4',
            'interface Ethernet1/4.101'
        ]
        playbook['state'] = 'replaced'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=replaced)

        overridden = [
            'interface Ethernet1/2', 'switchport', 'shutdown',
            'interface Ethernet1/3', 'switchport',
            'interface loopback2', 'no shutdown',
            'interface loopback9', 'no shutdown',
            'interface port-channel3', 'no shutdown',
            'interface Ethernet1/1', 'no switchport', 'no shutdown',
            'interface loopback1', 'shutdown',
            'interface loopback4',
            'interface port-channel4',
            'interface Ethernet1/4.101'
        ]
        playbook['state'] = 'overridden'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=overridden)

    def test_4(self):
        # Basic idempotence test
        sysdefs = dedent('''\
          !
          ! Interfaces default to L3 !!
          !
          no system default switchport
          no system default switchport shutdown
        ''')
        intf = dedent('''\
          interface Ethernet1/1
          interface Ethernet1/2
            switchport
            speed 1000
            shutdown
        ''')
        self.get_resource_connection_facts.return_value = {
            self.SHOW_RUN_SYSDEF: sysdefs,
            self.SHOW_RUN_INTF: intf
        }
        playbook = dict(config=[
            dict(name='Ethernet1/1', mode='layer3'),
            dict(name='Ethernet1/2', mode='layer2', enabled=False)
        ])
        merged = []
        playbook['state'] = 'merged'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=False, commands=merged)

    def test_5(self):
        # 'state: deleted' without 'config'; clean all objects.
        sysdefs = dedent('''\
          !
          ! Interfaces default to L3 !!
          !
          no system default switchport
          no system default switchport shutdown
        ''')
        intf = dedent('''\
          interface Ethernet1/1
            switchport
          interface Ethernet1/2
            speed 1000
            no shutdown
        ''')
        self.get_resource_connection_facts.return_value = {
            self.SHOW_RUN_SYSDEF: sysdefs,
            self.SHOW_RUN_INTF: intf
        }
        playbook = dict()
        deleted = [
            'interface Ethernet1/1', 'no switchport',
            'interface Ethernet1/2', 'no speed', 'shutdown'
        ]
        playbook['state'] = 'deleted'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=deleted)
