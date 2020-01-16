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
module: pfsense_ipsec
version_added: "2.10"
author: Frederic Bor (@f-bor)
short_description: Manage pfSense ipsec tunnels and phase 1 options
description:
  - Manage pfSense ipsec tunnels and phase 1 options
notes:
options:
  iketype:
    description: Internet Key Exchange protocol version to be used. Auto uses IKEv2 when initiator, and accepts either IKEv1 or IKEv2 as responder.
    required: false
    choices: [ 'ikev1', 'ikev2', 'auto' ]
    type: str
  protocol:
    description: IP family
    default: 'inet'
    choices: [ 'inet', 'inet6', 'both' ]
    type: str
  interface:
    description: Interface for the local endpoint of this phase1 entry.
    required: false
    type: str
  remote_gateway:
    description: Public IP address or host name of the remote gateway.
    required: false
    type: str
  disabled:
    description: Set this option to disable this phase1 without removing it from the list.
    required: false
    type: bool
  authentication_method:
    description: Authenticatin method. Must match the setting chosen on the remote side.
    choices: [ 'pre_shared_key', 'rsasig' ]
    type: str
  mode:
    description: Negotiation mode. Aggressive is more flexible, but less secure. Only for IkeV1 or Auto.
    choices: [ 'main', 'aggressive' ]
    type: str
  myid_type:
    description: Local identifier type.
    default: 'myaddress'
    choices: [ 'myaddress', 'address', 'fqdn', 'user_fqdn', 'asn1dn', 'keyid tag', 'dyn_dns' ]
    type: str
  myid_data:
    description: Local identifier value.
    required: false
    type: str
  peerid_type:
    description: Remote identifier type.
    default: 'peeraddress'
    choices: [ 'any', 'peeraddress', 'address', 'fqdn', 'user_fqdn', 'asn1dn', 'keyid tag' ]
    type: str
  peerid_data:
    description: Remote identifier value.
    required: false
    type: str
  certificate:
    description: a certificate previously configured
    required: false
    type: str
  certificate_authority:
    description: a certificate authority previously configured
    required: false
    type: str
  preshared_key:
    description: This key must match on both peers.
    required: false
    type: str
  lifetime:
    description: The lifetime defines how often the connection will be rekeyed, in seconds.
    default: 28800
    type: int
  disable_rekey:
    description: Disables renegotiation when a connection is about to expire.
    default: false
    type: bool
  margintime:
    description: How long before connection expiry or keying-channel expiry should attempt to negotiate a replacement begin.
    required: false
    type: int
  responderonly:
    description: Enable this option to never initiate this connection from this side, only respond to incoming requests.
    default: false
    type: bool
  disable_reauth:
    description: (IKEv2 only) Whether rekeying of an IKE_SA should also reauthenticate the peer. In IKEv1, reauthentication is always done.
    default: false
    type: bool
  mobike:
    description: (IKEv2 only) Set this option to control the use of MOBIKE
    default: 'off'
    choices: [ 'on', 'off' ]
    type: str
  splitconn:
    description: (IKEv2 only) Enable this to split connection entries with multiple phase 2 configurations
    default: false
    type: bool
  nat_traversal:
    description:
      Set this option to enable the use of NAT-T (i.e. the encapsulation of ESP in UDP packets) if needed,
      which can help with clients that are behind restrictive firewalls.
    default: 'on'
    choices: [ 'on', 'force' ]
    type: str
  enable_dpd:
    description: Enable dead peer detection
    default: True
    type: bool
  dpd_delay:
    description: Delay between requesting peer acknowledgement.
    default: 10
    type: int
  dpd_maxfail:
    description: Number of consecutive failures allowed before disconnect.
    default: 5
    type: int
  descr:
    description: The description of the ipsec tunnel
    required: true
    default: null
    type: str
  state:
    description: State in which to leave the ipsec tunnel
    choices: [ "present", "absent" ]
    default: present
    type: str
  apply:
    description: Apply VPN configuration on target pfSense
    default: True
    type: bool
"""


EXAMPLES = """
- name: Add simple tunnel
  pfsense_ipsec:
    state: present
    descr: test_tunnel
    interface: wan
    remote_gateway: 1.2.3.4
    iketype: ikev2
    authentication_method: pre_shared_key
    preshared_key: azerty123

- name: Remove tunnel
  pfsense_ipsec:
    state: absent
    descr: test_tunnel
"""

RETURN = """
commands:
    description: the set of commands that would be pushed to the remote device (if pfSense had a CLI)
    returned: always
    type: list
    sample: ["create ipsec 'test_tunnel', iketype='ikev2', protocol='inet', interface='wan', remote_gateway='1.2.3.4', ...", "delete ipsec 'test_tunnel'"]
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.pfsense.ipsec import PFSenseIpsecModule, IPSEC_ARGUMENT_SPEC, IPSEC_REQUIRED_IF


def main():
    module = AnsibleModule(
        argument_spec=IPSEC_ARGUMENT_SPEC,
        required_if=IPSEC_REQUIRED_IF,
        supports_check_mode=True)

    pfmodule = PFSenseIpsecModule(module)
    pfmodule.run(module.params)
    pfmodule.commit_changes()


if __name__ == '__main__':
    main()
