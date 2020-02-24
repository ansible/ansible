#
# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.eos import eos_acls
from ansible.module_utils.network.eos.config.acls.acls import add_commands
from units.modules.utils import set_module_args
from .eos_module import TestEosModule, load_fixture
import itertools


class TestEosAclsModule(TestEosModule):
    module = eos_acls

    def setUp(self):
        super(TestEosAclsModule, self).setUp()

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
            'ansible.module_utils.network.eos.facts.acls.acls.AclsFacts.get_device_data'
        )
        self.execute_show_command = self.mock_execute_show_command.start()

    def tearDown(self):
        super(TestEosAclsModule, self).tearDown()
        self.mock_get_resource_connection_config.stop()
        self.mock_get_resource_connection_facts.stop()
        self.mock_edit_config.stop()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_execute_show_command.stop()

    def load_fixtures(self, commands=None, transport='cli', filename=None):
        if filename is None:
            filename = 'eos_acls_config.cfg'

        def load_from_file(*args, **kwargs):
            output = load_fixture(filename)
            return output

        self.execute_show_command.side_effect = load_from_file

    def test_eos_acls_merged(self):
        set_module_args(
            dict(config=[
                dict(afi="ipv6",
                     acls=[
                         dict(name="test2",
                              standard="true",
                              aces=[
                                  dict(sequence="10",
                                       grant="permit",
                                       protocol="ospf",
                                       source=dict(subnet_address="30.2.0.0/8"),
                                       destination=dict(any="true"),
                                       log="true")
                              ])
                     ])
            ], state="merged"))
        commands = ['ipv6 access-list standard test2', '10 permit ospf 30.2.0.0/8 any log']
        self.execute_module(changed=True, commands=commands)

    def test_eos_acls_merged_idempotent(self):
        set_module_args(
            dict(config=[
                dict(afi="ipv4",
                     acls=[
                         dict(name="test1",
                              aces=[
                                  dict(sequence="35",
                                       grant="deny",
                                       protocol="tcp",
                                       source=dict(subnet_address="20.0.0.0/8"),
                                       destination=dict(any="true"),
                                       log="true"),
                                  dict(grant="permit",
                                       source=dict(any="true"),
                                       destination=dict(any="true"),
                                       protocol=6)
                              ])
                     ])
            ], state="merged"))
        self.execute_module(changed=False, commands=[])

    def test_eos_acls_replaced(self):
        set_module_args(
            dict(config=[
                dict(afi="ipv4",
                     acls=[
                         dict(name="test1",
                              aces=[
                                  dict(sequence="10",
                                       grant="permit",
                                       protocol="ospf",
                                       source=dict(subnet_address="30.2.0.0/8"),
                                       destination=dict(any="true"),
                                       log="true")
                              ])
                     ])
            ], state="replaced"))
        commands = ['ip access-list test1', 'no 35', 'no 45', '10 permit ospf 30.2.0.0/8 any log']
        self.execute_module(changed=True, commands=commands)

    def test_eos_acls_replaced_idempotent(self):
        set_module_args(
            dict(config=[
                dict(afi="ipv4",
                     acls=[
                         dict(name="test1",
                              aces=[
                                  dict(sequence="35",
                                       grant="deny",
                                       protocol="tcp",
                                       source=dict(subnet_address="20.0.0.0/8"),
                                       destination=dict(any="true"),
                                       log="true"),
                                  dict(grant="permit",
                                       source=dict(any="true"),
                                       destination=dict(any="true"),
                                       sequence="45",
                                       protocol="tcp")
                              ])
                     ])
            ], state="replaced"))
        self.execute_module(changed=False, commands=[])

    def test_eos_acls_overridden(self):
        set_module_args(
            dict(config=[
                dict(afi="ipv4",
                     acls=[
                         dict(name="test1",
                              aces=[
                                  dict(sequence="10",
                                       grant="permit",
                                       protocol="ospf",
                                       source=dict(subnet_address="30.2.0.0/8"),
                                       destination=dict(any="true"),
                                       log="true")
                              ])
                     ])
            ], state="overridden"))
        commands = ['ip access-list test1', 'no 35', 'no 45', 'ip access-list test1', '10 permit ospf 30.2.0.0/8 any log']
        self.execute_module(changed=True, commands=commands)

    def test_eos_acls_overridden_idempotent(self):
        set_module_args(
            dict(config=[
                dict(afi="ipv4",
                     acls=[
                         dict(name="test1",
                              aces=[
                                  dict(sequence="35",
                                       grant="deny",
                                       protocol="tcp",
                                       source=dict(subnet_address="20.0.0.0/8"),
                                       destination=dict(any="true"),
                                       log="true"),
                                  dict(grant="permit",
                                       source=dict(any="true"),
                                       destination=dict(any="true"),
                                       sequence="45",
                                       protocol="tcp")
                              ])
                     ])
            ], state="overridden"))
        self.execute_module(changed=False, commands=[])

    def test_eos_acls_deletedaces(self):
        set_module_args(
            dict(config=[
                dict(afi="ipv4",
                     acls=[
                         dict(name="test1",
                              aces=[
                                  dict(grant="permit",
                                       sequence="45",
                                       source=dict(any="true"),
                                       destination=dict(any="true"),
                                       protocol=6)
                              ])
                     ])
            ], state="deleted"))
        commands = ['ip access-list test1', 'no 45']
        self.execute_module(changed=True, commands=commands)

    def test_eos_acls_deletedacls(self):
        set_module_args(
            dict(config=[
                dict(afi="ipv4",
                     acls=[
                         dict(name="test1")
                     ])
            ], state="deleted"))
        commands = ['no ip access-list test1']
        self.execute_module(changed=True, commands=commands)

    def test_eos_acls_deletedafis(self):
        set_module_args(
            dict(config=[
                dict(afi="ipv4")
            ], state="deleted"))
        commands = ['no ip access-list test1']
        self.execute_module(changed=True, commands=commands)

    def test_eos_acls_gathered(self):
        set_module_args(
            dict(config=[],
                 state="gathered"))
        result = self.execute_module(changed=False, filename='eos_acls_config.cfg')
        commands = []
        for gathered_cmds in result['gathered']:
            cfg = add_commands(gathered_cmds)
            commands.append(cfg)
        commands = list(itertools.chain(*commands))
        config_commands = ['ip access-list test1', '35 deny tcp 20.0.0.0/8 any log', '45 permit tcp any any']
        self.assertEqual(sorted(config_commands), sorted(commands), result['gathered'])

    def test_eos_acls_rendered(self):
        set_module_args(
            dict(config=[
                dict(afi="ipv4",
                     acls=[
                         dict(name="test1",
                              aces=[
                                  dict(grant="permit",
                                       sequence="45",
                                       source=dict(any="true"),
                                       destination=dict(any="true"),
                                       protocol=6)
                              ])
                     ])
            ], state="rendered"))
        commands = ['ip access-list test1', '45 permit tcp any any']
        result = self.execute_module(changed=False)
        self.assertEqual(sorted(result['rendered']), sorted(commands), result['rendered'])

    def test_eos_acls_parsed(self):
        set_module_args(
            dict(running_config="ipv6 access-list test2\n 10 permit icmpv6 host 10.2.33.1 any ttl eq 25",
                 state="parsed"))
        commands = ['ipv6 access-list test2', '10 permit icmpv6 host 10.2.33.1 any ttl eq 25']
        result = self.execute_module(changed=False)
        parsed_commands = []
        for cmds in result['parsed']:
            cfg = add_commands(cmds)
            parsed_commands.append(cfg)
        parsed_commands = list(itertools.chain(*parsed_commands))
        self.assertEqual(sorted(parsed_commands), sorted(commands), result['parsed'])
