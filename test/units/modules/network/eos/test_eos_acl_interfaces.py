#
# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.eos import eos_acl_interfaces
from units.modules.utils import set_module_args
from .eos_module import TestEosModule, load_fixture


class TestEosAclInterfacesModule(TestEosModule):
    module = eos_acl_interfaces

    def setUp(self):
        super(TestEosAclInterfacesModule, self).setUp()

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

        self.mock_edit_config = patch(
            'ansible.module_utils.network.eos.providers.providers.CliProvider.edit_config'
        )
        self.edit_config = self.mock_edit_config.start()

        self.mock_execute_show_command = patch(
            'ansible.module_utils.network.eos.facts.acl_interfaces.acl_interfaces.Acl_interfacesFacts.get_device_data'
        )
        self.execute_show_command = self.mock_execute_show_command.start()

    def tearDown(self):
        super(TestEosAclInterfacesModule, self).tearDown()
        self.mock_get_resource_connection_config.stop()
        self.mock_get_resource_connection_facts.stop()
        self.mock_edit_config.stop()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_execute_show_command.stop()

    def load_fixtures(self, commands=None, transport='cli', filename=None):
        if filename is None:
            filename = 'eos_acl_interfaces_config.cfg'

        def load_from_file(*args, **kwargs):
            output = load_fixture(filename)
            return output

        self.execute_show_command.side_effect = load_from_file

    def test_eos_acl_interfaces_merged(self):
        set_module_args(
            dict(config=[
                dict(name="GigabitEthernet0/0",
                     access_groups=[
                         dict(afi="ipv4",
                              acls=[
                                  dict(name="aclv401",
                                       direction="in"),
                                  dict(name="aclv402",
                                       direction="out")
                              ]),
                         dict(afi="ipv6",
                              acls=[
                                  dict(name="aclv601",
                                       direction="in")
                              ])
                     ]),
                dict(name="GigabitEthernet0/1",
                     access_groups=[
                         dict(afi="ipv4",
                              acls=[
                                  dict(name="aclv401",
                                       direction="in")
                              ])
                     ])
            ], state="merged"))
        commands = ['interface GigabitEthernet0/0', 'ip access-group aclv401 in',
                    'ip access-group aclv402 out', 'ipv6 access-group aclv601 in', 'interface GigabitEthernet0/1',
                    'ip access-group aclv401 in']
        self.execute_module(changed=True, commands=commands)

    def test_eos_acl_interfaces_merged_idempotent(self):
        set_module_args(
            dict(config=[
                dict(name="GigabitEthernet0/0",
                     access_groups=[
                         dict(afi="ipv4",
                              acls=[
                                  dict(name="aclv404",
                                       direction="in"),
                              ]),
                         dict(afi="ipv6",
                              acls=[dict(name="aclv601", direction="out")])
                     ]),
                dict(name="GigabitEthernet0/1",
                     access_groups=[
                         dict(afi="ipv6",
                              acls=[dict(name="aclv601", direction="in")])
                     ])
            ], state="merged"))
        self.execute_module(changed=False, commands=[])

    def test_eos_acl_interfaces_replaced(self):
        set_module_args(
            dict(config=[
                dict(name="GigabitEthernet0/0",
                     access_groups=[
                         dict(afi="ipv4",
                              acls=[
                                  dict(name="aclv401",
                                       direction="in"),
                                  dict(name="aclv402",
                                       direction="out")
                              ]),
                     ])
            ], state="replaced"))
        commands = ['interface GigabitEthernet0/0', 'no ip access-group aclv404 in',
                    'no ipv6 access-group aclv601 out', 'ip access-group aclv402 out',
                    'ip access-group aclv401 in']
        self.execute_module(changed=True, commands=commands)

    def test_eos_acl_interfaces_replaced_idempotent(self):
        set_module_args(
            dict(config=[
                dict(name="GigabitEthernet0/0",
                     access_groups=[
                         dict(afi="ipv4",
                              acls=[
                                  dict(name="aclv404",
                                       direction="in"),
                              ]),
                         dict(afi="ipv6",
                              acls=[dict(name="aclv601", direction="out")])
                     ]),
            ], state="replaced"))
        self.execute_module(changed=False, commands=[])

    def test_eos_acl_interfaces_overridden(self):
        set_module_args(
            dict(config=[
                dict(name="GigabitEthernet0/0",
                     access_groups=[
                         dict(afi="ipv4",
                              acls=[
                                  dict(name="aclv401",
                                       direction="in"),
                                  dict(name="aclv402",
                                       direction="out")
                              ]),
                     ])
            ], state="overridden"))
        commands = ['interface GigabitEthernet0/0', 'no ip access-group aclv404 in',
                    'no ipv6 access-group aclv601 out', 'ip access-group aclv402 out',
                    'ip access-group aclv401 in', 'interface GigabitEthernet0/1',
                    'no ipv6 access-group aclv601 in']
        self.execute_module(changed=True, commands=commands)

    def test_eos_acl_interfaces_overridden_idempotent(self):
        set_module_args(
            dict(config=[
                dict(name="GigabitEthernet0/0",
                     access_groups=[
                         dict(afi="ipv4",
                              acls=[
                                  dict(name="aclv404",
                                       direction="in"),
                              ]),
                         dict(afi="ipv6",
                              acls=[dict(name="aclv601", direction="out")])
                     ]),
                dict(name="GigabitEthernet0/1",
                     access_groups=[
                         dict(afi="ipv6",
                              acls=[
                                  dict(name="aclv601",
                                       direction="in")
                              ])
                     ])
            ], state="overridden"))
        self.execute_module(changed=False, commands=[])

    def test_eos_acl_interfaces_deletedafi(self):
        set_module_args(
            dict(config=[
                dict(name="GigabitEthernet0/0",
                     access_groups=[
                         dict(afi="ipv6")])
            ], state="deleted"))
        commands = ['interface GigabitEthernet0/0', 'no ipv6 access-group aclv601 out']
        self.execute_module(changed=True, commands=commands)

    def test_eos_acl_interfaces_deletedint(self):
        set_module_args(
            dict(config=[
                dict(name="GigabitEthernet0/0")
            ], state="deleted"))
        commands = ['interface GigabitEthernet0/0', 'no ipv6 access-group aclv601 out',
                    'no ip access-group aclv404 in']
        self.execute_module(changed=True, commands=commands)

    def test_eos_acl_interfaces_deletedacl(self):
        set_module_args(
            dict(config=[
                dict(name="GigabitEthernet0/0",
                     access_groups=[
                         dict(afi="ipv4",
                              acls=[
                                  dict(name="aclv404",
                                       direction="in"),
                              ]),
                     ])
            ], state="deleted"))
        commands = ['interface GigabitEthernet0/0', 'no ip access-group aclv404 in']
        self.execute_module(changed=True, commands=commands)

    def test_eos_acl_interfaces_gathered(self):
        set_module_args(
            dict(state="gathered"))
        result = self.execute_module(changed=False, filename='eos_acl_interfaces_config.cfg')
        gathered_list = [{'access_groups': [{'acls': [{'direction': 'in', 'name': 'aclv404'}], 'afi': 'ipv4'},
                                            {'acls': [{'direction': 'out', 'name': 'aclv601'}], 'afi': 'ipv6'}],
                          'name': 'GigabitEthernet0/0'},
                         {'access_groups': [{'acls': [{'direction': 'in', 'name': 'aclv601'}], 'afi': 'ipv6'}],
                          'name': 'GigabitEthernet0/1'}]
        self.assertEqual(gathered_list, result['gathered'])

    def test_eos_acl_interfaces_parsed(self):
        set_module_args(
            dict(running_config="interface GigabitEthernet0/0\nipv6 access-group aclv601 out\nip access-group aclv404 in",
                 state="parsed"))
        result = self.execute_module(changed=False)
        parsed_list = [{'access_groups': [{'acls': [{'direction': 'in', 'name': 'aclv404'}], 'afi': 'ipv4'},
                                          {'acls': [{'direction': 'out', 'name': 'aclv601'}], 'afi': 'ipv6'}],
                        'name': 'GigabitEthernet0/0'}]
        self.assertEqual(parsed_list, result['parsed'])

    def test_eos_acl_interfaces_rendered(self):
        set_module_args(
            dict(config=[
                dict(name="GigabitEthernet0/0",
                     access_groups=[
                         dict(afi="ipv4",
                              acls=[
                                  dict(name="aclv401",
                                       direction="in"),
                                  dict(name="aclv402",
                                       direction="out")
                              ]),
                         dict(afi="ipv6",
                              acls=[dict(name="aclv601", direction="in")])
                     ]),
                dict(name="GigabitEthernet0/1",
                     access_groups=[
                         dict(afi="ipv4",
                              acls=[
                                  dict(name="aclv401",
                                       direction="in")
                              ])
                     ])
            ], state="rendered"))
        commands = ['interface GigabitEthernet0/0', 'ip access-group aclv401 in',
                    'ip access-group aclv402 out', 'ipv6 access-group aclv601 in', 'interface GigabitEthernet0/1',
                    'ip access-group aclv401 in']
        result = self.execute_module(changed=False)
        self.assertEqual(sorted(result['rendered']), sorted(commands), result['rendered'])
