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

from units.compat.mock import patch
from ansible.modules.network.vyos import vyos_firewall_global
from units.modules.utils import set_module_args
from .vyos_module import TestVyosModule, load_fixture


class TestVyosFirewallRulesModule(TestVyosModule):

    module = vyos_firewall_global

    def setUp(self):
        super(TestVyosFirewallRulesModule, self).setUp()
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
            'ansible.module_utils.network.vyos.facts.firewall_global.firewall_global.Firewall_globalFacts.get_device_data'
        )

        self.execute_show_command = self.mock_execute_show_command.start()

    def tearDown(self):
        super(TestVyosFirewallRulesModule, self).tearDown()
        self.mock_get_resource_connection_config.stop()
        self.mock_get_resource_connection_facts.stop()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_execute_show_command.stop()

    def load_fixtures(self, commands=None):
        def load_from_file(*args, **kwargs):
            return load_fixture('vyos_firewall_global_config.cfg')

        self.execute_show_command.side_effect = load_from_file

    def test_vyos_firewall_global_set_01_merged(self):
        set_module_args(
            dict(config=dict(
                validation='strict',
                config_trap=True,
                log_martians=True,
                syn_cookies=True,
                twa_hazards_protection=True,
                ping=dict(all=True, broadcast=True),
                state_policy=[
                    dict(
                        connection_type='established',
                        action='accept',
                        log=True,
                    ),
                    dict(connection_type='invalid', action='reject')
                ],
                route_redirects=[
                    dict(afi='ipv4',
                         ip_src_route=True,
                         icmp_redirects=dict(send=True, receive=False))
                ],
                group=dict(
                    address_group=[
                        dict(
                            name='MGMT-HOSTS',
                            description='This group has the Management hosts address lists',
                            members=[
                                dict(address='192.0.1.1'),
                                dict(address='192.0.1.3'),
                                dict(address='192.0.1.5')
                            ])
                    ],
                    network_group=[
                        dict(name='MGMT',
                             description='This group has the Management network addresses',
                             members=[dict(address='192.0.1.0/24')])
                    ])),
                state="merged"))
        commands = [
            "set firewall group address-group MGMT-HOSTS address 192.0.1.1",
            "set firewall group address-group MGMT-HOSTS address 192.0.1.3",
            "set firewall group address-group MGMT-HOSTS address 192.0.1.5",
            "set firewall group address-group MGMT-HOSTS description 'This group has the Management hosts address lists'",
            "set firewall group address-group MGMT-HOSTS",
            "set firewall group network-group MGMT network 192.0.1.0/24",
            "set firewall group network-group MGMT description 'This group has the Management network addresses'",
            "set firewall group network-group MGMT",
            "set firewall ip-src-route 'enable'",
            "set firewall receive-redirects 'disable'",
            "set firewall send-redirects 'enable'",
            "set firewall config-trap 'enable'",
            "set firewall state-policy established action 'accept'",
            "set firewall state-policy established log 'enable'",
            "set firewall state-policy invalid action 'reject'",
            "set firewall broadcast-ping 'enable'",
            "set firewall all-ping 'enable'",
            "set firewall log-martians 'enable'",
            "set firewall twa-hazards-protection 'enable'",
            "set firewall syn-cookies 'enable'",
            "set firewall source-validation 'strict'"
        ]
        self.execute_module(changed=True, commands=commands)

    def test_vyos_firewall_global_set_01_merged_idem(self):
        set_module_args(
            dict(config=dict(group=dict(
                address_group=[
                    dict(name='RND-HOSTS',
                         description='This group has the Management hosts address lists',
                         members=[
                             dict(address='192.0.2.1'),
                             dict(address='192.0.2.3'),
                             dict(address='192.0.2.5')
                         ])
                ],
                network_group=[
                    dict(name='RND',
                         description='This group has the Management network addresses',
                         members=[dict(address='192.0.2.0/24')])
                ])),
                state="merged"))
        self.execute_module(changed=False, commands=[])

    def test_vyos_firewall_global_set_01_replaced(self):
        set_module_args(
            dict(config=dict(group=dict(
                address_group=[
                    dict(name='RND-HOSTS',
                         description='This group has the Management hosts address lists',
                         members=[
                             dict(address='192.0.2.1'),
                             dict(address='192.0.2.7'),
                             dict(address='192.0.2.9')
                         ])
                ],
                network_group=[
                    dict(name='RND',
                         description='This group has the Management network addresses',
                         members=[dict(address='192.0.2.0/24')])
                ])),
                state="replaced"))
        commands = [
            "delete firewall group address-group RND-HOSTS address 192.0.2.3",
            "delete firewall group address-group RND-HOSTS address 192.0.2.5",
            "set firewall group address-group RND-HOSTS address 192.0.2.7",
            "set firewall group address-group RND-HOSTS address 192.0.2.9"
        ]
        self.execute_module(changed=True, commands=commands)

    def test_vyos_firewall_global_set_01_replaced_idem(self):
        set_module_args(
            dict(config=dict(group=dict(
                address_group=[
                    dict(name='RND-HOSTS',
                         description='This group has the Management hosts address lists',
                         members=[
                             dict(address='192.0.2.1'),
                             dict(address='192.0.2.3'),
                             dict(address='192.0.2.5')
                         ])
                ],
                network_group=[
                    dict(name='RND',
                         description='This group has the Management network addresses',
                         members=[dict(address='192.0.2.0/24')])
                ])),
                state="replaced"))
        self.execute_module(changed=False, commands=[])

    def test_vyos_firewall_global_set_01_deleted(self):
        set_module_args(dict(config=dict(), state="deleted"))
        commands = ["delete firewall "]
        self.execute_module(changed=True, commands=commands)
