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
module: pfsense_ipsec_proposal
version_added: "2.10"
author: Frederic Bor (@f-bor)
short_description: Manage pfSense ipsec proposals
description:
  - Manage pfSense ipsec proposals
notes:
options:
  encryption:
    description:
      Encryption algorithm. aes128gcm, aes192gcm and aes256gcm can only be used with IKEv2 tunnels.
      Blowfish, 3DES and CAST128 provide weak security and should be avoided.
    required: True
    choices: [ 'aes', 'aes128gcm', 'aes192gcm', 'aes256gcm', 'blowfish', '3des', 'cast128' ]
    type: str
  key_length:
    description: Encryption key length
    required: False
    choices: [ 64, 96, 128, 192, 256 ]
    type: int
  hash:
    description: Hash algorithm. MD5 and SHA1 provide weak security and should be avoided.
    required: True
    choices: [ 'md5', 'sha1', 'sha256', 'sha384', 'sha512', 'aesxcbc' ]
    type: str
  dhgroup:
    description: DH group. DH groups 1, 2, 22, 23, and 24 provide weak security and should be avoided.
    required: True
    choices: [ 1, 2, 5, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 28, 29, 30 ]
    type: int
  descr:
    description: The description of the ipsec tunnel on which to create/delete the proposal.
    default: null
    type: str
  state:
    description: State in which to leave the ipsec proposal.
    choices: [ "present", "absent" ]
    default: present
    type: str
  apply:
    description: Apply VPN configuration on target pfSense
    default: True
    type: bool
"""


EXAMPLES = """
- name: Add proposal
  pfsense_ipsec_proposal:
    descr: test_tunnel
    state: present
    encryption: aes128gcm
    key_length: 128
    hash: sha256
    dhgroup: 14
    apply: False

- name: Remove proposal
  pfsense_ipsec_proposal:
    descr: test_tunnel
    state: absent
    encryption: aes128gcm
    key_length: 128
    hash: sha256
    dhgroup: 14
    apply: False
"""

RETURN = """
commands:
    description: the set of commands that would be pushed to the remote device (if pfSense had a CLI)
    returned: always
    type: list
    sample: [
      "create ipsec_proposal on 'test_tunnel', encryption='aes128gcm', key_length=128, hash='sha256', dhgroup='14'",
      "delete ipsec_proposal on 'test_tunnel', encryption='aes128gcm', key_length=128, hash='sha256', dhgroup='14'",
    ]
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.pfsense.ipsec_proposal import PFSenseIpsecProposalModule, IPSEC_PROPOSAL_ARGUMENT_SPEC, IPSEC_PROPOSAL_REQUIRED_IF


def main():
    module = AnsibleModule(
        argument_spec=IPSEC_PROPOSAL_ARGUMENT_SPEC,
        required_if=IPSEC_PROPOSAL_REQUIRED_IF,
        supports_check_mode=True)

    pfmodule = PFSenseIpsecProposalModule(module)
    pfmodule.run(module.params)
    pfmodule.commit_changes()


if __name__ == '__main__':
    main()
