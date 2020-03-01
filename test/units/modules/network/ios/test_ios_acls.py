#
# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys

import pytest

# These tests and/or the module under test are unstable on Python 3.5.
# See: https://app.shippable.com/github/ansible/ansible/runs/161331/15/tests
# This is most likely due to CPython 3.5 not maintaining dict insertion order.
pytestmark = pytest.mark.skipif(sys.version_info[:2] == (3, 5), reason="Tests and/or module are unstable on Python 3.5.")

from units.compat.mock import patch
from ansible.modules.network.ios import ios_acls
from units.modules.utils import set_module_args
from .ios_module import TestIosModule, load_fixture


class TestIosAclsModule(TestIosModule):
    module = ios_acls

    def setUp(self):
        super(TestIosAclsModule, self).setUp()

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

        self.mock_execute_show_command = patch('ansible.module_utils.network.ios.facts.acls.acls.'
                                               'AclsFacts.get_acl_data')
        self.execute_show_command = self.mock_execute_show_command.start()

    def tearDown(self):
        super(TestIosAclsModule, self).tearDown()
        self.mock_get_resource_connection_config.stop()
        self.mock_get_resource_connection_facts.stop()
        self.mock_edit_config.stop()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_execute_show_command.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        def load_from_file(*args, **kwargs):
            return load_fixture('ios_acls_config.cfg')
        self.execute_show_command.side_effect = load_from_file

    def test_ios_acls_merged(self):
        set_module_args(
            dict(config=[
                dict(afi="ipv4",
                     acls=[
                         dict(name="std_acl",
                              acl_type="standard",
                              aces=[
                                  dict(
                                      grant="deny",
                                      source=dict(
                                          address="192.0.2.0",
                                          wildcard_bits="0.0.0.255"
                                      )
                                  )
                              ])
                     ]),
                dict(afi="ipv6",
                     acls=[
                         dict(name="merge_v6_acl",
                              aces=[
                                  dict(
                                      grant="deny",
                                      protocol_options=dict(
                                          tcp=dict(ack="true")
                                      ),
                                      source=dict(
                                          any="true",
                                          port_protocol=dict(eq="www")
                                      ),
                                      destination=dict(
                                          any="true",
                                          port_protocol=dict(eq="telnet")),
                                      dscp="af11"
                                  )
                              ])
                     ])
            ], state="merged"
            )
        )
        result = self.execute_module(changed=True)
        commands = [
            'ip access-list standard std_acl',
            'deny 192.0.2.0 0.0.0.255',
            'ipv6 access-list merge_v6_acl',
            'deny tcp any eq www any eq telnet ack dscp af11'
        ]
        self.assertEqual(result['commands'], commands)

    def test_ios_acls_merged_idempotent(self):
        set_module_args(
            dict(config=[
                dict(afi="ipv4",
                     acls=[
                         dict(name="110",
                              aces=[
                                  dict(
                                      grant="deny",
                                      protocol_options=dict(
                                          icmp=dict(echo="true")
                                      ),
                                      source=dict(
                                          address="192.0.2.0",
                                          wildcard_bits="0.0.0.255"
                                      ),
                                      destination=dict(
                                          address="192.0.3.0",
                                          wildcard_bits="0.0.0.255"
                                      ),
                                      dscp="ef",
                                      ttl=dict(eq=10)
                                  )
                              ])
                     ]),
                dict(afi="ipv6",
                     acls=[
                         dict(name="R1_TRAFFIC",
                              aces=[
                                  dict(
                                      grant="deny",
                                      protocol_options=dict(tcp=dict(ack="true")),
                                      source=dict(
                                          any="true",
                                          port_protocol=dict(eq="www")
                                      ),
                                      destination=dict(
                                          any="true",
                                          port_protocol=dict(eq="telnet")
                                      ),
                                      dscp="af11"
                                  )
                              ])
                     ])
            ], state="merged"
            ))
        self.execute_module(changed=False, commands=[], sort=True)

    def test_ios_acls_replaced(self):
        set_module_args(
            dict(config=[
                dict(afi="ipv4",
                     acls=[
                         dict(name="replace_acl",
                              acl_type="extended",
                              aces=[
                                  dict(
                                      grant="deny",
                                      protocol_options=dict(
                                          tcp=dict(ack="true")
                                      ),
                                      source=dict(
                                          address="198.51.100.0",
                                          wildcard_bits="0.0.0.255"
                                      ),
                                      destination=dict(
                                          address="198.51.101.0",
                                          wildcard_bits="0.0.0.255",
                                          port_protocol=dict(eq="telnet")
                                      ),
                                      tos=dict(service_value=12)
                                  )
                              ])
                     ])
            ], state="replaced"
            ))
        result = self.execute_module(changed=True)
        commands = [
            'ip access-list extended replace_acl',
            'deny tcp 198.51.100.0 0.0.0.255 198.51.101.0 0.0.0.255 eq telnet ack tos 12'
        ]
        self.assertEqual(result['commands'], commands)

    def test_ios_acls_replaced_idempotent(self):
        set_module_args(
            dict(config=[
                dict(afi="ipv4",
                     acls=[
                         dict(name="110",
                              aces=[
                                  dict(
                                      grant="deny",
                                      protocol_options=dict(
                                          icmp=dict(echo="true")
                                      ),
                                      source=dict(
                                          address="192.0.2.0",
                                          wildcard_bits="0.0.0.255"
                                      ),
                                      destination=dict(
                                          address="192.0.3.0",
                                          wildcard_bits="0.0.0.255"
                                      ),
                                      dscp="ef",
                                      ttl=dict(eq=10)
                                  )
                              ])
                     ])
            ], state="replaced"
            ))
        self.execute_module(changed=False, commands=[], sort=True)

    def test_ios_acls_overridden(self):
        set_module_args(
            dict(config=[
                dict(afi="ipv4",
                     acls=[
                         dict(name="150",
                              aces=[
                                  dict(
                                      grant="deny",
                                      protocol_options=dict(
                                          tcp=dict(syn="true")
                                      ),
                                      source=dict(
                                          address="198.51.100.0",
                                          wildcard_bits="0.0.0.255",
                                          port_protocol=dict(eq="telnet")
                                      ),
                                      destination=dict(
                                          address="198.51.110.0",
                                          wildcard_bits="0.0.0.255",
                                          port_protocol=dict(eq="telnet")
                                      ),
                                      dscp="ef",
                                      ttl=dict(eq=10)
                                  )
                              ])
                     ])
            ], state="overridden"
            ))
        result = self.execute_module(changed=True)
        commands = [
            'no ip access-list extended 110',
            'no ipv6 access-list R1_TRAFFIC',
            'ip access-list extended 150',
            'deny tcp 198.51.100.0 0.0.0.255 eq telnet 198.51.110.0 0.0.0.255 eq telnet syn dscp ef ttl eq 10'
        ]
        self.assertEqual(result['commands'], commands)

    def test_ios_acls_overridden_idempotent(self):
        set_module_args(
            dict(config=[
                dict(afi="ipv4",
                     acls=[
                         dict(name="110",
                              aces=[
                                  dict(
                                      grant="deny",
                                      protocol_options=dict(
                                          icmp=dict(echo="true")
                                      ),
                                      source=dict(
                                          address="192.0.2.0",
                                          wildcard_bits="0.0.0.255"
                                      ),
                                      destination=dict(
                                          address="192.0.3.0",
                                          wildcard_bits="0.0.0.255"
                                      ),
                                      dscp="ef",
                                      ttl=dict(eq=10)
                                  )
                              ])
                     ]),
                dict(afi="ipv6",
                     acls=[
                         dict(name="R1_TRAFFIC",
                              aces=[
                                  dict(
                                      grant="deny",
                                      protocol_options=dict(tcp=dict(ack="true")),
                                      source=dict(
                                          any="true",
                                          port_protocol=dict(eq="www")
                                      ),
                                      destination=dict(
                                          any="true",
                                          port_protocol=dict(eq="telnet")
                                      ),
                                      dscp="af11"
                                  )
                              ])
                     ])
            ], state="overridden"
            ))
        self.execute_module(changed=False, commands=[], sort=True)

    def test_ios_acls_deleted_afi_based(self):
        set_module_args(
            dict(config=[
                dict(afi="ipv4")
            ], state="deleted"
            ))
        result = self.execute_module(changed=True)
        commands = [
            'no ip access-list extended 110'
        ]
        self.assertEqual(result['commands'], commands)

    def test_ios_acls_deleted_acl_based(self):
        set_module_args(
            dict(config=[
                dict(afi="ipv4",
                     acls=[
                         dict(name="110",
                              aces=[
                                  dict(
                                      grant="deny",
                                      protocol_options=dict(
                                          icmp=dict(echo="true")
                                      ),
                                      source=dict(
                                          address="192.0.2.0",
                                          wildcard_bits="0.0.0.255"
                                      ),
                                      destination=dict(
                                          address="192.0.3.0",
                                          wildcard_bits="0.0.0.255"
                                      ),
                                      dscp="ef",
                                      ttl=dict(eq=10)
                                  )
                              ])
                     ]),
                dict(afi="ipv6",
                     acls=[
                         dict(name="R1_TRAFFIC",
                              aces=[
                                  dict(
                                      grant="deny",
                                      protocol_options=dict(tcp=dict(ack="true")),
                                      source=dict(
                                          any="true",
                                          port_protocol=dict(eq="www")
                                      ),
                                      destination=dict(
                                          any="true",
                                          port_protocol=dict(eq="telnet")
                                      ),
                                      dscp="af11"
                                  )
                              ])
                     ])
            ], state="deleted"
            ))
        result = self.execute_module(changed=True)
        commands = [
            'no ip access-list extended 110',
            'no ipv6 access-list R1_TRAFFIC',
        ]
        self.assertEqual(result['commands'], commands)

    def test_ios_acls_rendered(self):
        set_module_args(
            dict(config=[
                dict(afi="ipv4",
                     acls=[
                         dict(name="110",
                              aces=[
                                  dict(
                                      grant="deny",
                                      sequence="10",
                                      protocol_options=dict(
                                          tcp=dict(syn="true")
                                      ),
                                      source=dict(
                                          address="192.0.2.0",
                                          wildcard_bits="0.0.0.255"
                                      ),
                                      destination=dict(
                                          address="192.0.3.0",
                                          wildcard_bits="0.0.0.255",
                                          port_protocol=dict(eq="www")
                                      ),
                                      dscp="ef",
                                      ttl=dict(eq=10)
                                  )
                              ])
                     ])
            ], state="rendered"))
        commands = [
            'ip access-list extended 110',
            '10 deny tcp 192.0.2.0 0.0.0.255 192.0.3.0 0.0.0.255 eq www syn dscp ef ttl eq 10'
        ]
        result = self.execute_module(changed=False)
        self.assertEqual(result['rendered'], commands)

    def test_ios_acls_parsed(self):
        set_module_args(
            dict(running_config="ipv6 access-list R1_TRAFFIC\ndeny tcp any eq www any eq telnet ack dscp af11",
                 state="parsed"))
        result = self.execute_module(changed=False)
        parsed_list = [
            {
                "acls": [
                    {
                        "aces": [
                            {
                                "destination": {
                                    "any": True,
                                    "port_protocol": {
                                        "eq": "telnet"
                                    }
                                },
                                "dscp": "af11",
                                "grant": "deny",
                                "protocol": "tcp",
                                "protocol_options": {
                                    "tcp": {
                                        "ack": True
                                    }
                                },
                                "source": {
                                    "any": True,
                                    "port_protocol": {
                                        "eq": "www"
                                    }
                                }
                            }
                        ],
                        "name": "R1_TRAFFIC"
                    }
                ],
                "afi": "ipv6"
            }
        ]
        self.assertEqual(parsed_list, result['parsed'])
