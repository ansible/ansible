#
# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.iosxr import iosxr_acls
from units.modules.utils import set_module_args
from .iosxr_module import TestIosxrModule, load_fixture


class TestIosxrAclsModule(TestIosxrModule):
    module = iosxr_acls

    def setUp(self):
        super(TestIosxrAclsModule, self).setUp()

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
            'ansible.module_utils.network.iosxr.facts.acls.acls.AclsFacts.get_device_data'
        )
        self.execute_show_command = self.mock_execute_show_command.start()

    def tearDown(self):
        super(TestIosxrAclsModule, self).tearDown()
        self.mock_get_resource_connection_config.stop()
        self.mock_get_resource_connection_facts.stop()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_execute_show_command.stop()

    def load_fixtures(self, commands=None):
        def load_from_file(*args, **kwargs):
            return load_fixture('iosxr_acls_config.cfg')

        self.execute_show_command.side_effect = load_from_file

    def test_iosxr_acls_merged(self):
        set_module_args(
            dict(config=[
                dict(afi="ipv4",
                     acls=[
                         dict(name="acl_1",
                              aces=[
                                  dict(sequence="10",
                                       grant="permit",
                                       protocol="ospf",
                                       source=dict(prefix="192.168.1.0/24"),
                                       destination=dict(any="true"),
                                       log="true")
                              ])
                     ])
            ],
                state="merged"))
        commands = [
            'ipv4 access-list acl_1',
            '10 permit ospf 192.168.1.0 0.0.0.255 any log'
        ]
        self.execute_module(changed=True, commands=commands)

    def test_iosxr_acls_merged_idempotent(self):
        set_module_args(
            dict(config=[
                dict(afi="ipv4",
                     acls=[
                         dict(name="acl_2",
                              aces=[
                                  dict(sequence="10",
                                       grant="deny",
                                       protocol='ipv4',
                                       destination=dict(any='true'),
                                       source=dict(any="true")),
                              ])
                     ])
            ],
                state="merged"))
        self.execute_module(changed=False, commands=[])

    def test_iosxr_acls_replaced(self):
        set_module_args(
            dict(config=[
                dict(afi="ipv4",
                     acls=[
                         dict(name="acl_2",
                              aces=[
                                  dict(sequence="30",
                                       grant="permit",
                                       protocol="ospf",
                                       source=dict(prefix="10.0.0.0/8"),
                                       destination=dict(any="true"),
                                       log="true")
                              ])
                     ])
            ],
                state="replaced"))
        commands = [
            'ipv4 access-list acl_2', 'no 10', 'no 20',
            '30 permit ospf 10.0.0.0 0.255.255.255 any log'
        ]
        self.execute_module(changed=True, commands=commands)

    def test_iosxr_acls_replaced_idempotent(self):
        set_module_args(
            dict(config=[
                dict(afi="ipv4",
                     acls=[
                         dict(name="acl_2",
                              aces=[
                                  dict(sequence="10",
                                       grant="deny",
                                       protocol='ipv4',
                                       destination=dict(any='true'),
                                       source=dict(any="true")),
                                  dict(sequence="20",
                                       grant="permit",
                                       protocol="tcp",
                                       destination=dict(any='true'),
                                       source=dict(host="192.168.1.100")),
                              ])
                     ])
            ],
                state="replaced"))
        self.execute_module(changed=False, commands=[])

    def test_iosxr_acls_overridden(self):
        set_module_args(
            dict(config=[
                dict(afi="ipv4",
                     acls=[
                         dict(name="acl_2",
                              aces=[
                                  dict(sequence="40",
                                       grant="permit",
                                       protocol="ospf",
                                       source=dict(any="true"),
                                       destination=dict(any="true"),
                                       log="true")
                              ])
                     ])
            ],
                state="overridden"))
        commands = [
            'no ipv6 access-list acl6_1', 'ipv4 access-list acl_2', 'no 10',
            'no 20', '40 permit ospf any any log'
        ]
        self.execute_module(changed=True, commands=commands)

    def test_iosxr_acls_overridden_idempotent(self):
        set_module_args(
            dict(config=[
                dict(afi="ipv4",
                     acls=[
                         dict(name="acl_2",
                              aces=[
                                  dict(sequence="10",
                                       grant="deny",
                                       protocol='ipv4',
                                       destination=dict(any='true'),
                                       source=dict(any="true")),
                                  dict(sequence="20",
                                       grant="permit",
                                       protocol="tcp",
                                       destination=dict(any='true'),
                                       source=dict(host="192.168.1.100")),
                              ])
                     ]),
                dict(afi='ipv6',
                     acls=[
                         dict(name="acl6_1",
                              aces=[
                                  dict(
                                      sequence="10",
                                      grant="deny",
                                      protocol="icmpv6",
                                      destination=dict(any='true'),
                                      source=dict(any='true'),
                                  )
                              ])
                     ])
            ],
                state="overridden"))
        self.execute_module(changed=False, commands=[])

    def test_iosxr_acls_deletedaces(self):
        set_module_args(
            dict(config=[
                dict(afi="ipv4",
                     acls=[dict(name="acl_2", aces=[dict(sequence="20")])])
            ],
                state="deleted"))
        commands = ['ipv4 access-list acl_2', 'no 20']
        self.execute_module(changed=True, commands=commands)

    def test_iosxr_acls_deletedacls(self):
        set_module_args(
            dict(config=[dict(afi="ipv6", acls=[dict(name="acl6_1")])],
                 state="deleted"))
        commands = ['no ipv6 access-list acl6_1']
        self.execute_module(changed=True, commands=commands)

    def test_iosxr_acls_deletedafis(self):
        set_module_args(dict(config=[dict(afi="ipv4")], state="deleted"))
        commands = ['no ipv4 access-list acl_2']
        self.execute_module(changed=True, commands=commands)

    def test_eos_acls_rendered(self):
        set_module_args(
            dict(config=[
                dict(afi="ipv4",
                     acls=[
                         dict(name="acl_2",
                              aces=[
                                  dict(grant="permit",
                                       source=dict(any="true"),
                                       destination=dict(any="true"),
                                       protocol='igmp')
                              ])
                     ])
            ],
                state="rendered"))
        commands = ['ipv4 access-list acl_2', 'permit igmp any any']
        result = self.execute_module(changed=False)
        self.assertEqual(sorted(result['rendered']), sorted(commands),
                         result['rendered'])
