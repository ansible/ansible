#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: pfsense_nat_outbound
version_added: "2.10"
author: Frederic Bor (@f-bor)
short_description: Manage pfSense Outbound NAT Entries
description:
  - Manage pfSense Outbound NAT Entries
notes:
options:
  descr:
    description: The name of the nat rule
    required: true
    default: null
    type: str
  disabled:
    description: Is the rule disabled
    default: false
    type: bool
  nonat:
    description: This option will disable NAT for traffic matching this rule and stop processing Outbound NAT rules
    default: false
    type: bool
  interface:
    description: The interface for the rule
    required: false
    type: str
  ipprotocol:
    description: The Internet Protocol version this rule applies to.
    default: inet46
    choices: [ "inet", "inet46", "inet6" ]
    type: str
  protocol:
    description: Which protocol this rule should match.
    default: any
    choices: [ "any", "tcp", "udp", "tcp/udp", "icmp", "esp", "ah", "gre", "ipv6", "igmp", "carp", "pfsync" ]
    type: str
  source:
    description: The matching source address, in {any,(self),ALIAS,NETWORK}[:port] format.
    required: false
    default: null
    type: str
  destination:
    description: The matching destination address, in {any,ALIAS,NETWORK}[:port] format.
    required: false
    default: null
    type: str
  invert:
    description: Invert the sense of the destination match.
    default: false
    type: bool
  address:
    description: The translated to address, in {ALIAS,NETWORK}[:port] format. Leave address part empty to use interface address.
    required: false
    default: null
    type: str
  poolopts:
    description: When an address pool is used, there are several options available that control how NAT translations happen on the pool.
    default: ""
    choices: [ "", "round-robin", "round-robin sticky-address", "random", "random sticky-address", "source-hash", "bitmask" ]
    type: str
  source_hash_key:
    description: >
        The key that is fed to the hashing algorithm in hex format, preceeded by "0x", or any string.
        A non-hex string is hashed using md5 to a hexadecimal key. Defaults to a randomly generated value.
    required: false
    default: ''
    type: str
  staticnatport:
    description: Do not randomize source port
    default: false
    type: bool
  nosync:
    description: Prevents the rule on Master from automatically syncing to other CARP members. This does NOT prevent the rule from being overwritten on Slave.
    default: false
    type: bool
  state:
    description: State in which to leave the rule
    default: present
    choices: [ "present", "absent" ]
    type: str
  after:
    description: Rule to go after, or "top"
    type: str
  before:
    description: Rule to go before, or "bottom"
    type: str
"""

EXAMPLES = """
- name: "Add NAT outbound traffic rule"
  pfsense_nat_outbound:
    descr: 'NAT outbound traffic'
    interface: wan
    source: any
    destination: any
    state: present
- name: "Delete NAT outbound traffic rule"
  pfsense_nat_outbound:
    descr: 'NAT outbound traffic'
    state: absent
"""

RETURN = """
commands:
    description: the set of commands that would be pushed to the remote device (if pfSense had a CLI)
    returned: always
    type: list
    sample: ["create nat_outbound 'NAT outbound traffic', interface='wan', source='any', destination='any'", "delete nat_outbound 'NAT outbound traffic'"]
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.pfsense.nat_outbound import PFSenseNatOutboundModule, NAT_OUTBOUND_ARGUMENT_SPEC, NAT_OUTBOUD_REQUIRED_IF


def main():
    module = AnsibleModule(
        argument_spec=NAT_OUTBOUND_ARGUMENT_SPEC,
        required_if=NAT_OUTBOUD_REQUIRED_IF,
        supports_check_mode=True)

    pfmodule = PFSenseNatOutboundModule(module)
    pfmodule.run(module.params)
    pfmodule.commit_changes()


if __name__ == '__main__':
    main()
