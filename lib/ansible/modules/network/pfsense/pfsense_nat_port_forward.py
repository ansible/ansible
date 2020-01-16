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
module: pfsense_nat_port_forward
version_added: "2.10"
author: Frederic Bor (@f-bor)
short_description: Manage pfSense Port Forward NAT Entries
description:
  - Manage pfSense Port Forward NAT Entries
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
  nordr:
    description: Disable redirection for traffic matching this rule
    default: false
    type: bool
  interface:
    description: The interface for the rule
    required: false
    type: str
  protocol:
    description: Which protocol this rule should match.
    default: tcp
    choices: [ "tcp", "udp", "tcp/udp", "icmp", "esp", "ah", "gre", "ipv6", "igmp", "pim", "ospf" ]
    type: str
  source:
    description: The source address, in [!]{IP,HOST,ALIAS,any,IP:INTERFACE,NET:INTERFACE}[:port] format.
    default: null
    type: str
  destination:
    description: The destination address, in [!]{IP,HOST,ALIAS,any,IP:INTERFACE,NET:INTERFACE}[:port] format.
    default: null
    type: str
  target:
    description: The translated to address, in {ALIAS,IP}[:port] format.
    required: false
    default: null
    type: str
  natreflection:
    description: Allows NAT reflection to be enabled or disabled on a per-port forward basis.
    default: system-default
    choices: [ "system-default", "enable", "purenat", "disable" ]
    type: str
  associated_rule:
    description: >
      Choose one of Add an associated filter rule gets updated when the port forward is updated,
      or Add an unassociated filter rule, or pass which passes all traffic that matches the entry without having a firewall rule at all.
    default: associated
    choices: [ "associated", "unassociated", "pass", "none" ]
    type: str
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
- name: "Add NAT port forward traffic rule"
  pfsense_nat_port_forward:
    descr: 'ssh'
    interface: wan
    source: any
    destination: any:22
    target: 1.2.3.4:22
    associated_rule: pass
    state: present
- name: "Delete NAT port forward traffic rule"
  pfsense_nat_port_forward:
    descr: 'ssh'
    state: absent
"""

RETURN = """
commands:
    description: the set of commands that would be pushed to the remote device (if pfSense had a CLI)
    returned: always
    type: list
    sample: [
        "create nat_port_forward 'ssh', interface='wan', source='any', destination='any:22', target='1.2.3.4:22', associated_rule='pass'",
        "delete nat_port_forward 'ssh'"
    ]
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.pfsense.nat_port_forward import (
    PFSenseNatPortForwardModule,
    NAT_PORT_FORWARD_ARGUMENT_SPEC,
    NAT_PORT_FORWARD_REQUIRED_IF
)


def main():
    module = AnsibleModule(
        argument_spec=NAT_PORT_FORWARD_ARGUMENT_SPEC,
        required_if=NAT_PORT_FORWARD_REQUIRED_IF,
        supports_check_mode=True)

    pfmodule = PFSenseNatPortForwardModule(module)
    pfmodule.run(module.params)
    pfmodule.commit_changes()


if __name__ == '__main__':
    main()
