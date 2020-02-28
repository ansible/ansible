#
# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.ios import ios_acl_interfaces
from units.modules.utils import set_module_args
from .ios_module import TestIosModule, load_fixture


class TestIosAclInterfacesModule(TestIosModule):
    module = ios_acl_interfaces

    def setUp(self):
        super(TestIosAclInterfacesModule, self).setUp()

        self.mock_get_config = patch('ansible.module_utils.network.common.network.Config.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.module_utils.network.common.network.Config.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_resource_connection_config = patch('ansible.module_utils.network.common.cfg.base.'
                                                         'get_resource_connection')
        self.get_resource_connection_config = self.mock_get_resource_connection_config.start()

        self.mock_get_resource_connection_facts = patch('ansible.module_utils.network.common.facts.facts.'
                                                        'get_resource_connection')
        self.get_resource_connection_facts = self.mock_get_resource_connection_facts.start()

        self.mock_edit_config = patch('ansible.module_utils.network.ios.providers.providers.CliProvider.edit_config')
        self.edit_config = self.mock_edit_config.start()

        self.mock_execute_show_command = patch('ansible.module_utils.network.ios.facts.acl_interfaces.acl_interfaces.'
                                               'Acl_InterfacesFacts.get_acl_interfaces_data')
        self.execute_show_command = self.mock_execute_show_command.start()

    def tearDown(self):
        super(TestIosAclInterfacesModule, self).tearDown()
        self.mock_get_resource_connection_config.stop()
        self.mock_get_resource_connection_facts.stop()
        self.mock_edit_config.stop()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_execute_show_command.stop()

    def load_fixtures(self, commands=None):

        def load_from_file(*args, **kwargs):
            return load_fixture('ios_acl_interfaces.cfg')
        self.execute_show_command.side_effect = load_from_file

    def test_ios_acl_interfaces_merged(self):
        set_module_args(
            dict(config=[
                dict(name="GigabitEthernet0/1",
                     access_groups=[
                         dict(afi="ipv4",
                              acls=[
                                  dict(name="merge_110",
                                       direction="in"),
                                  dict(name="merge_123",
                                       direction="out")
                              ]),
                         dict(afi="ipv6",
                              acls=[
                                  dict(name="merge_temp_v6",
                                       direction="in"),
                                  dict(name="merge_test_v6",
                                       direction="out")
                              ])
                     ]),
                dict(name="GigabitEthernet0/2",
                     access_groups=[
                         dict(afi="ipv4",
                              acls=[
                                  dict(name="merge_110",
                                       direction="in"),
                                  dict(name="merge_123",
                                       direction="out")
                              ])
                     ])
            ], state="merged"))
        commands = ['interface GigabitEthernet0/1',
                    'ip access-group merge_110 in',
                    'ip access-group merge_123 out',
                    'ipv6 traffic-filter merge_temp_v6 in',
                    'ipv6 traffic-filter merge_test_v6 out',
                    'interface GigabitEthernet0/2',
                    'ip access-group merge_110 in',
                    'ip access-group merge_123 out'
                    ]
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], commands)

    def test_ios_acl_interfaces_merged_idempotent(self):
        set_module_args(dict(
            config=[dict(
                name="GigabitEthernet0/1",
                access_groups=[dict(
                    afi="ipv4",
                    acls=[dict(
                        name="110",
                        direction="in"
                    ), dict(
                        name="123",
                        direction="out"
                    )]
                ), dict(
                    afi="ipv6",
                    acls=[dict(
                        name="test_v6",
                        direction="out"
                    ), dict(
                        name="temp_v6",
                        direction="in"
                    )]
                )]
            ), dict(
                name="GigabitEthernet0/2",
                access_groups=[dict(
                    afi="ipv4",
                    acls=[dict(
                        name="110",
                        direction="in"
                    ), dict(
                        name="123",
                        direction="out"
                    )]
                )]
            )], state="merged"
        ))
        self.execute_module(changed=False, commands=[])

    def test_ios_acl_interfaces_replaced(self):
        set_module_args(dict(
            config=[dict(
                name="GigabitEthernet0/1",
                access_groups=[dict(
                    afi="ipv4",
                    acls=[dict(
                        name="replace_100",
                        direction="out"
                    ), dict(
                        name="110",
                        direction="in"
                    )]
                )]
            )], state="replaced"
        ))
        commands = ['interface GigabitEthernet0/1',
                    'no ip access-group 123 out',
                    'no ipv6 traffic-filter temp_v6 in',
                    'no ipv6 traffic-filter test_v6 out',
                    'ip access-group replace_100 out'
                    ]
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], commands)

    def test_ios_acl_interfaces_replaced_idempotent(self):
        set_module_args(dict(
            config=[dict(
                name="GigabitEthernet0/1",
                access_groups=[dict(
                    afi="ipv4",
                    acls=[dict(
                        name="110",
                        direction="in"
                    ), dict(
                        name="123",
                        direction="out"
                    )]
                ), dict(
                    afi="ipv6",
                    acls=[dict(
                        name="test_v6",
                        direction="out"
                    ), dict(
                        name="temp_v6",
                        direction="in"
                    )]
                )]
            )], state="replaced"
        ))
        self.execute_module(changed=False, commands=[])

    def test_ios_acl_interfaces_overridden(self):
        set_module_args(dict(
            config=[dict(
                name="GigabitEthernet0/1",
                access_groups=[dict(
                    afi="ipv4",
                    acls=[dict(
                        name="100",
                        direction="out"
                    ), dict(
                        name="110",
                        direction="in"
                    )]
                )]
            )], state="overridden"
        ))

        commands = [
            'interface GigabitEthernet0/1',
            'no ip access-group 123 out',
            'no ipv6 traffic-filter test_v6 out',
            'no ipv6 traffic-filter temp_v6 in',
            'ip access-group 100 out',
            'interface GigabitEthernet0/2',
            'no ip access-group 110 in',
            'no ip access-group 123 out'
        ]
        self.execute_module(changed=True, commands=commands)

    def test_ios_acl_interfaces_overridden_idempotent(self):
        set_module_args(dict(
            config=[dict(
                name="GigabitEthernet0/1",
                access_groups=[dict(
                    afi="ipv4",
                    acls=[dict(
                        name="110",
                        direction="in"
                    ), dict(
                        name="123",
                        direction="out"
                    )]
                ), dict(
                    afi="ipv6",
                    acls=[dict(
                        name="test_v6",
                        direction="out"
                    ), dict(
                        name="temp_v6",
                        direction="in"
                    )]
                )]
            ), dict(
                name="GigabitEthernet0/2",
                access_groups=[dict(
                    afi="ipv4",
                    acls=[dict(
                        name="110",
                        direction="in"
                    ), dict(
                        name="123",
                        direction="out"
                    )]
                )]
            )], state="overridden"
        ))
        self.execute_module(changed=False, commands=[])

    def test_ios_acl_interfaces_deleted_interface(self):
        set_module_args(
            dict(config=[
                dict(name="GigabitEthernet0/1")
            ], state="deleted"))
        commands = ['interface GigabitEthernet0/1',
                    'no ip access-group 110 in',
                    'no ip access-group 123 out',
                    'no ipv6 traffic-filter test_v6 out',
                    'no ipv6 traffic-filter temp_v6 in',
                    ]
        self.execute_module(changed=True, commands=commands)

    def test_ios_acl_interfaces_deleted_afi(self):
        set_module_args(
            dict(config=[
                dict(name="GigabitEthernet0/1",
                     access_groups=[
                         dict(afi="ipv6")])
            ], state="deleted"))
        commands = ['interface GigabitEthernet0/1',
                    'no ipv6 traffic-filter test_v6 out',
                    'no ipv6 traffic-filter temp_v6 in',
                    ]
        self.execute_module(changed=True, commands=commands)

    def test_ios_acl_interfaces_parsed(self):
        set_module_args(
            dict(
                running_config="interface GigabitEthernet0/1\nip access-group 110 in\nipv6 traffic-filter test_v6 out",
                state="parsed"
            )
        )
        result = self.execute_module(changed=False)
        parsed_list = [
            {'access_groups':
                [
                    {'acls':
                        [
                            {'direction': 'in', 'name': '110'}
                        ], 'afi': 'ipv4'},
                    {'acls':
                        [
                            {'direction': 'out', 'name': 'test_v6'}
                        ],
                        'afi': 'ipv6'}
                ],
                'name': 'GigabitEthernet0/1'}]
        self.assertEqual(parsed_list, result['parsed'])

    def test_ios_acl_interfaces_rendered(self):
        set_module_args(
            dict(config=[
                dict(name="GigabitEthernet0/1",
                     access_groups=[
                         dict(afi="ipv4",
                              acls=[
                                  dict(name="110",
                                       direction="in"),
                                  dict(name="123",
                                       direction="out")
                              ]),
                         dict(afi="ipv6",
                              acls=[
                                  dict(name="temp_v6", direction="in"),
                                  dict(name="test_v6", direction="out")
                              ])
                     ])
            ], state="rendered"))
        commands = ['interface GigabitEthernet0/1',
                    'ip access-group 110 in',
                    'ip access-group 123 out',
                    'ipv6 traffic-filter temp_v6 in',
                    'ipv6 traffic-filter test_v6 out'
                    ]
        result = self.execute_module(changed=False)
        self.assertEqual(sorted(result['rendered']), commands)
