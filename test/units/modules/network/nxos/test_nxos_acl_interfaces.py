#
# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.modules.network.nxos import nxos_acl_interfaces
from units.compat.mock import patch, MagicMock
from units.modules.utils import set_module_args
from .nxos_module import TestNxosModule, load_fixture


class TestNxosAclInterfacesModule(TestNxosModule):

    module = nxos_acl_interfaces

    def setUp(self):
        super(TestNxosAclInterfacesModule, self).setUp()

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
        self.get_resource_connection_facts = self.mock_get_resource_connection_facts.start()

        self.mock_edit_config = patch(
            'ansible.module_utils.network.nxos.config.acl_interfaces.acl_interfaces.Acl_interfaces.edit_config'
        )
        self.edit_config = self.mock_edit_config.start()

        self.mock_execute_show_command = patch(
            'ansible.module_utils.network.nxos.facts.acl_interfaces.acl_interfaces.Acl_interfacesFacts.get_device_data'
        )
        self.execute_show_command = self.mock_execute_show_command.start()

    def tearDown(self):
        super(TestNxosAclInterfacesModule, self).tearDown()
        self.mock_get_resource_connection_config.stop()
        self.mock_get_resource_connection_facts.stop()
        self.mock_edit_config.stop()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_execute_show_command.stop()

    def load_fixtures(self, commands=None, device=''):
        def load_from_file(*args, **kwargs):
            output = '''interface Ethernet1/2\n  ip access-group ACL1v4 out\n interface Ethernet1/4\n ipv6 port traffic-filter ACL2v6 in\n'''
            return output

        self.execute_show_command.side_effect = load_from_file

    def test_nxos_acl_interfaces_merged(self):
        set_module_args(
            dict(config=[
                dict(name="Ethernet1/3",
                     access_groups=[
                         dict(afi="ipv4",
                              acls=[
                                  dict(
                                      name="ACL1v4",
                                      direction="in",
                                  )
                              ]
                              )
                     ]
                     )
            ], state="merged"))
        commands = ['interface Ethernet1/3',
                    'ip access-group ACL1v4 in']
        self.execute_module(changed=True, commands=commands)

    def test_nxos_acl_interfaces_merged_idempotent(self):
        set_module_args(
            dict(config=[
                dict(name="Ethernet1/2",
                     access_groups=[
                         dict(afi="ipv4",
                              acls=[
                                  dict(
                                      name="ACL1v4",
                                      direction="out",
                                  )
                              ]
                              )
                     ]
                     ),
                dict(name="Ethernet1/4",
                     access_groups=[
                         dict(afi="ipv6",
                              acls=[
                                  dict(
                                      name="ACL2v6",
                                      direction="in",
                                      port=True
                                  )
                              ]
                              )
                     ]
                     ),

            ], state="merged"))
        self.execute_module(changed=False, commands=[])

    def test_nxos_acl_interfaces_replaced(self):
        set_module_args(
            dict(config=[
                dict(name="Ethernet1/2",
                     access_groups=[
                          dict(afi="ipv6",
                               acls=[
                                   dict(
                                       name="ACL1v6",
                                       direction="in",
                                       port=True
                                   )
                               ]
                               )
                     ]
                     ),
                dict(name="Ethernet1/5",
                     access_groups=[
                         dict(afi="ipv4",
                              acls=[
                                  dict(
                                      name="ACL2v4",
                                      direction="in",
                                      port=True
                                  )
                              ]
                              )
                     ]
                     )
            ], state="replaced"))
        commands = ['interface Ethernet1/2', 'no ip access-group ACL1v4 out',
                    'ipv6 port traffic-filter ACL1v6 in', 'interface Ethernet1/5', 'ip port access-group ACL2v4 in']
        self.execute_module(changed=True, commands=commands)

    def test_nxos_acl_interfaces_replaced_idempotent(self):
        set_module_args(
            dict(config=[
                dict(name="Ethernet1/2",
                     access_groups=[
                         dict(afi="ipv4",
                              acls=[
                                  dict(
                                      name="ACL1v4",
                                      direction="out",
                                  )
                              ]
                              )
                     ]
                     )], state="replaced"))
        self.execute_module(changed=False, commands=[])

    def test_nxos_acl_interfaces_overridden(self):
        set_module_args(
            dict(config=[
                dict(name="Ethernet1/3",
                     access_groups=[
                          dict(afi="ipv4",
                               acls=[
                                   dict(
                                       name="ACL2v4",
                                       direction="out"
                                   ),
                                   dict(
                                       name="PortACL",
                                       direction="in",
                                       port=True
                                   ),
                               ]
                               )
                     ]
                     )], state="overridden"))
        commands = ['interface Ethernet1/2', 'no ip access-group ACL1v4 out', 'interface Ethernet1/4',
                    'no ipv6 port traffic-filter ACL2v6 in', 'interface Ethernet1/3', 'ip access-group ACL2v4 out', 'ip port access-group PortACL in']
        self.execute_module(changed=True, commands=commands)

    def test_nxos_acl_interfaces_overridden_idempotent(self):
        set_module_args(
            dict(config=[
                dict(name="Ethernet1/2",
                     access_groups=[
                          dict(afi="ipv4",
                               acls=[
                                   dict(
                                       name="ACL1v4",
                                       direction="out",
                                   )
                               ]
                               )
                     ]
                     ),
                dict(name="Ethernet1/4",
                     access_groups=[
                          dict(afi="ipv6",
                               acls=[
                                   dict(
                                       name="ACL2v6",
                                       direction="in",
                                       port=True
                                   )
                               ]
                               )
                     ]
                     ),
            ], state="overridden"))
        self.execute_module(changed=False, commands=[])

    def test_nxos_acl_interfaces_deletedname(self):
        set_module_args(
            dict(config=[dict(name="Ethernet1/2")], state="deleted"))
        commands = ['interface Ethernet1/2', 'no ip access-group ACL1v4 out']
        self.execute_module(changed=True, commands=commands)

    def test_nxos_acl_interfaces_deletedafi(self):
        set_module_args(
            dict(config=[dict(name="Ethernet1/2", access_groups=[
                dict(afi="ipv4")
            ])], state="deleted"))
        commands = ['interface Ethernet1/2', 'no ip access-group ACL1v4 out']
        self.execute_module(changed=True, commands=commands)

    def test_nxos_acl_interfaces_deletedacl(self):
        set_module_args(
            dict(config=[dict(name="Ethernet1/2", access_groups=[
                dict(afi="ipv4", acls=[
                    dict(
                        name="ACL1v4",
                        direction="out"
                    )
                ])
            ])], state="deleted"))
        commands = ['interface Ethernet1/2', 'no ip access-group ACL1v4 out']
        self.execute_module(changed=True, commands=commands)

    def test_nxos_acl_interfaces_rendered(self):
        set_module_args(
            dict(config=[
                dict(name="Ethernet1/2",
                     access_groups=[
                          dict(afi="ipv4",
                               acls=[
                                   dict(
                                       name="ACL1v4",
                                       direction="out",
                                   )
                               ]
                               )
                     ]
                     ),
                dict(name="Ethernet1/4",
                     access_groups=[
                          dict(afi="ipv6",
                               acls=[
                                   dict(
                                       name="ACL2v6",
                                       direction="in",
                                       port=True
                                   )
                               ]
                               )
                     ]
                     ),
            ], state="rendered"))
        commands = ['interface Ethernet1/2', 'ip access-group ACL1v4 out',
                    'interface Ethernet1/4', 'ipv6 port traffic-filter ACL2v6 in']
        result = self.execute_module(changed=False)
        self.assertEqual(sorted(result['rendered']), sorted(
            commands), result['rendered'])

    def test_nxos_acl_interfaces_parsed(self):
        set_module_args(dict(running_config='''interface Ethernet1/2\n ip access-group ACL1v4 out\n interface Ethernet1/4\n \
          ipv6 port traffic-filter ACL2v6 in''',
                             state="parsed"))
        result = self.execute_module(changed=False)
        compare_list = [{'access_groups': [{'acls': [{'direction': 'out', 'name': 'ACL1v4'}], 'afi': 'ipv4'}], 'name': 'Ethernet1/2'},
                        {'access_groups': [{'acls': [{'direction': 'in', 'name': 'ACL2v6', 'port': True}], 'afi': 'ipv6'}], 'name': 'Ethernet1/4'}]
        self.assertEqual(result['parsed'],
                         compare_list, result['parsed'])

    def test_nxos_acl_interfaces_gathered(self):
        set_module_args(dict(config=[], state="gathered"))
        result = self.execute_module(changed=False)
        compare_list = [{'access_groups': [{'acls': [{'direction': 'out', 'name': 'ACL1v4'}], 'afi': 'ipv4'}], 'name': 'Ethernet1/2'},
                        {'access_groups': [{'acls': [{'direction': 'in', 'name': 'ACL2v6', 'port': True}], 'afi': 'ipv6'}], 'name': 'Ethernet1/4'}]
        self.assertEqual(result['gathered'],
                         compare_list, result['gathered'])
