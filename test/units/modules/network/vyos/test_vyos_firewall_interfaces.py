# (c) 2016 Red Hat Inc.
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

from units.compat.mock import patch, MagicMock
from ansible.modules.network.vyos import vyos_firewall_interfaces
from units.modules.utils import set_module_args
from .vyos_module import TestVyosModule, load_fixture


class TestVyosFirewallInterfacesModule(TestVyosModule):

    module = vyos_firewall_interfaces

    def setUp(self):
        super(TestVyosFirewallInterfacesModule, self).setUp()
        self.mock_get_config = patch(
            'ansible.module_utils.network.common.network.Config.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.common.network.Config.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_resource_connection_config = patch(
            'ansible.module_utils.network.common.cfg.base.get_resource_connection'
        )
        self.get_resource_connection_config = self.mock_get_resource_connection_config.start(
        )

        self.mock_get_resource_connection_facts = patch(
            'ansible.module_utils.network.common.facts.facts.get_resource_connection'
        )
        self.get_resource_connection_facts = self.mock_get_resource_connection_facts.start(
        )

        self.mock_execute_show_command = patch(
            'ansible.module_utils.network.vyos.facts.firewall_interfaces.firewall_interfaces.Firewall_interfacesFacts.get_device_data'
        )
        self.execute_show_command = self.mock_execute_show_command.start()

    def tearDown(self):
        super(TestVyosFirewallInterfacesModule, self).tearDown()
        self.mock_get_resource_connection_config.stop()
        self.mock_get_resource_connection_facts.stop()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_execute_show_command.stop()

    def load_fixtures(self, commands=None):
        def load_from_file(*args, **kwargs):
            return load_fixture('vyos_firewall_interfaces_config.cfg')

        self.execute_show_command.side_effect = load_from_file

    def test_vyos_firewall_rule_set_01_merged(self):
        set_module_args(
            dict(config=[
                dict(name='eth1',
                     access_rules=[
                         dict(afi='ipv4',
                              rules=[
                                  dict(name='INBOUND', direction='in'),
                                  dict(name='OUTBOUND', direction='out'),
                                  dict(name='LOCAL', direction='local')
                              ]),
                         dict(afi='ipv6',
                              rules=[dict(name='V6-LOCAL', direction='local')])
                     ]),
                dict(name='eth3',
                     access_rules=[
                         dict(afi='ipv4',
                              rules=[
                                  dict(name='INBOUND', direction='in'),
                                  dict(name='OUTBOUND', direction='out'),
                                  dict(name='LOCAL', direction='local')
                              ]),
                         dict(afi='ipv6',
                              rules=[dict(name='V6-LOCAL', direction='local')])
                     ])
            ],
                state="merged"))
        commands = [
            "set interfaces ethernet eth1 firewall in name 'INBOUND'",
            "set interfaces ethernet eth1 firewall out name 'OUTBOUND'",
            "set interfaces ethernet eth1 firewall local name 'LOCAL'",
            "set interfaces ethernet eth1 firewall local ipv6-name 'V6-LOCAL'",
            "set interfaces ethernet eth3 firewall in name 'INBOUND'",
            "set interfaces ethernet eth3 firewall out name 'OUTBOUND'",
            "set interfaces ethernet eth3 firewall local name 'LOCAL'",
            "set interfaces ethernet eth3 firewall local ipv6-name 'V6-LOCAL'"
        ]
        self.execute_module(changed=True, commands=commands)

    def test_vyos_firewall_rule_set_02_merged_idem(self):
        set_module_args(
            dict(config=[
                dict(name='eth0',
                     access_rules=[
                         dict(afi='ipv4',
                              rules=[
                                  dict(name='INBOUND', direction='in'),
                                  dict(name='OUTBOUND', direction='out'),
                                  dict(name='LOCAL', direction='local')
                              ]),
                         dict(afi='ipv6',
                              rules=[dict(name='V6-LOCAL', direction='local')])
                     ]),
                dict(name='eth2',
                     access_rules=[
                         dict(afi='ipv4',
                              rules=[
                                  dict(name='INBOUND', direction='in'),
                                  dict(name='OUTBOUND', direction='out'),
                                  dict(name='LOCAL', direction='local')
                              ]),
                         dict(afi='ipv6',
                              rules=[dict(name='V6-LOCAL', direction='local')])
                     ])
            ],
                state="merged"))
        self.execute_module(changed=False, commands=[])

    def test_vyos_firewall_rule_set_01_deleted_per_afi(self):
        set_module_args(
            dict(config=[
                dict(name='eth0',
                     access_rules=[dict(afi='ipv4'),
                                   dict(afi='ipv6')])
            ],
                state="deleted"))
        commands = [
            "delete interfaces ethernet eth0 firewall in name",
            "delete interfaces ethernet eth0 firewall local name",
            "delete interfaces ethernet eth0 firewall out name",
            "delete interfaces ethernet eth0 firewall local ipv6-name"
        ]
        self.execute_module(changed=True, commands=commands)

    def test_vyos_firewall_rule_set_03_deleted_per_interface(self):
        set_module_args(
            dict(config=[dict(name='eth0'),
                         dict(name='eth2')],
                 state="deleted"))
        commands = [
            "delete interfaces ethernet eth0 firewall",
            "delete interfaces ethernet eth2 firewall"
        ]
        self.execute_module(changed=True, commands=commands)

    def test_vyos_firewall_rule_set_03_deleted_all(self):
        set_module_args(dict(config=[], state="deleted"))
        commands = [
            "delete interfaces ethernet eth0 firewall",
            "delete interfaces ethernet eth2 firewall"
        ]
        self.execute_module(changed=True, commands=commands)

    def test_vyos_firewall_rule_set_03_deleted(self):
        set_module_args(
            dict(config=[dict(name='eth0'),
                         dict(name='eth2')],
                 state="deleted"))
        commands = [
            "delete interfaces ethernet eth0 firewall",
            "delete interfaces ethernet eth2 firewall"
        ]
        self.execute_module(changed=True, commands=commands)

    def test_vyos_firewall_rule_set_04_deleted_interface_idem(self):
        set_module_args(
            dict(config=[dict(name='eth1'),
                         dict(name='eth3')],
                 state="deleted"))
        self.execute_module(changed=False, commands=[])

    def test_vyos_firewall_rule_set_02_replaced_idem(self):
        set_module_args(
            dict(config=[
                dict(name='eth0',
                     access_rules=[
                         dict(afi='ipv4',
                              rules=[
                                  dict(name='INBOUND', direction='in'),
                                  dict(name='OUTBOUND', direction='out'),
                                  dict(name='LOCAL', direction='local')
                              ]),
                         dict(afi='ipv6',
                              rules=[dict(name='V6-LOCAL', direction='local')])
                     ]),
                dict(name='eth2',
                     access_rules=[
                         dict(afi='ipv4',
                              rules=[
                                  dict(name='INBOUND', direction='in'),
                                  dict(name='OUTBOUND', direction='out'),
                                  dict(name='LOCAL', direction='local')
                              ]),
                         dict(afi='ipv6',
                              rules=[dict(name='V6-LOCAL', direction='local')])
                     ])
            ],
                state="replaced"))
        self.execute_module(changed=False, commands=[])

    def test_vyos_firewall_rule_set_01_replaced(self):
        set_module_args(
            dict(config=[
                dict(name='eth0',
                     access_rules=[
                         dict(afi='ipv4',
                              rules=[
                                  dict(name='INBOUND', direction='in'),
                              ]),
                         dict(afi='ipv6',
                              rules=[dict(name='V6-LOCAL', direction='local')])
                     ]),
                dict(name='eth2',
                     access_rules=[
                         dict(afi='ipv4',
                              rules=[dict(name='LOCAL', direction='local')]),
                         dict(afi='ipv6',
                              rules=[dict(name='V6-LOCAL', direction='local')])
                     ]),
                dict(name='eth3',
                     access_rules=[
                         dict(afi='ipv4',
                              rules=[dict(name='LOCAL', direction='local')]),
                         dict(afi='ipv6',
                              rules=[dict(name='V6-LOCAL', direction='local')])
                     ])
            ],
                state="replaced"))
        commands = [
            "delete interfaces ethernet eth0 firewall out name",
            "delete interfaces ethernet eth0 firewall local name",
            "delete interfaces ethernet eth2 firewall in name",
            "delete interfaces ethernet eth2 firewall out name",
            "set interfaces ethernet eth3 firewall local name 'LOCAL'",
            "set interfaces ethernet eth3 firewall local ipv6-name 'V6-LOCAL'"
        ]
        self.execute_module(changed=True, commands=commands)

    def test_vyos_firewall_rule_set_01_overridden(self):
        set_module_args(
            dict(config=[
                dict(name='eth1',
                     access_rules=[
                         dict(afi='ipv4',
                              rules=[dict(name='INBOUND', direction='in')])
                     ])
            ],
                state="overridden"))
        commands = [
            "delete interfaces ethernet eth0 firewall",
            "delete interfaces ethernet eth2 firewall",
            "set interfaces ethernet eth1 firewall in name 'INBOUND'"
        ]
        self.execute_module(changed=True, commands=commands)

    def test_vyos_firewall_rule_set_02_overridden_idem(self):
        set_module_args(
            dict(config=[
                dict(name='eth0',
                     access_rules=[
                         dict(afi='ipv4',
                              rules=[
                                  dict(name='INBOUND', direction='in'),
                                  dict(name='OUTBOUND', direction='out'),
                                  dict(name='LOCAL', direction='local')
                              ]),
                         dict(afi='ipv6',
                              rules=[dict(name='V6-LOCAL', direction='local')])
                     ]),
                dict(name='eth2',
                     access_rules=[
                         dict(afi='ipv4',
                              rules=[
                                  dict(name='INBOUND', direction='in'),
                                  dict(name='OUTBOUND', direction='out'),
                                  dict(name='LOCAL', direction='local')
                              ]),
                         dict(afi='ipv6',
                              rules=[dict(name='V6-LOCAL', direction='local')])
                     ])
            ],
                state="overridden"))
        self.execute_module(changed=False, commands=[])
