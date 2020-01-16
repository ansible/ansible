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
module: pfsense_ipsec_p2
version_added: "2.10"
author: Frederic Bor (@f-bor)
short_description: Manage pfSense ipsec tunnels phase 2 options
description:
  - Manage pfSense ipsec tunnels phase 2 options
notes:
options:
  disabled:
    description: Set this option to disable this phase2 without removing it from the list.
    required: false
    type: bool
  mode:
    description: Method for managing ipsec traffic
    required: False
    choices: [ 'tunnel', 'tunnel6', 'transport', 'vti' ]
    type: str
  local:
    description: Local network component of this IPsec security association.
    required: False
    type: str
  nat:
    description: If NAT/BINAT is required on the local network specify the address to be translated
    required: False
    type: str
  remote:
    description: Remote network component of this IPsec security association.
    required: False
    type: str
  protocol:
    description: Encapsulating Security Payload (ESP) is encryption, Authentication Header (AH) is authentication only.
    default: 'esp'
    choices: [ 'esp', 'ah' ]
    type: str
  aes:
    description: Set this option to enable AES encryption.
    required: false
    type: bool
  aes_len:
    description: AES encryption key length
    required: False
    choices: [ 'auto', '128', '192', '256' ]
    type: str
  aes128gcm:
    description: Set this option to enable AES128-GCM encryption.
    required: false
    type: bool
  aes128gcm_len:
    description: AES128-GCM encryption key length
    required: False
    choices: [ 'auto', '64', '96', '128' ]
    type: str
  aes192gcm:
    description: Set this option to enable AES192-GCM encryption.
    required: false
    type: bool
  aes192gcm_len:
    description: AES192-GCM encryption key length
    required: False
    choices: [ 'auto', '64', '96', '128' ]
    type: str
  aes256gcm:
    description: Set this option to enable AES256-GCM encryption.
    required: false
    type: bool
  aes256gcm_len:
    description: AES256-GCM encryption key length
    required: False
    choices: [ 'auto', '64', '96', '128' ]
    type: str
  blowfish:
    description: Set this option to enable Blowfish encryption.
    required: false
    type: bool
  blowfish_len:
    description: AES encryption key length
    required: False
    choices: [ 'auto', '128', '192', '256' ]
    type: str
  des:
    description: Set this option to enable 3DES encryption.
    required: false
    type: bool
  cast128:
    description: Set this option to enable CAST128 encryption.
    required: false
    type: bool
  md5:
    description: Set this option to enable MD5 hashing.
    required: false
    type: bool
  sha1:
    description: Set this option to enable SHA1 hashing.
    required: false
    type: bool
  sha256:
    description: Set this option to enable SHA256 hashing.
    required: false
    type: bool
  sha384:
    description: Set this option to enable SHA384 hashing.
    required: false
    type: bool
  sha512:
    description: Set this option to enable SHA512 hashing.
    required: false
    type: bool
  aesxcbc:
    description: Set this option to enable AES-XCBC hashing.
    required: false
    type: bool
  pfsgroup:
    description: PFS key group, 0 for off. DH groups 1, 2, 22, 23, and 24 provide weak security and should be avoided.
    default: '14'
    choices: [ '0', '1', '2', '5', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '28', '29', '30' ]
    type: str
  lifetime:
    description: Specifies how often the connection must be rekeyed, in seconds
    default: 3600
    type: int
  pinghost:
    description: Automatically ping host
    required: False
    type: str
  descr:
    description: The description of the ipsec tunnel phase2
    required: true
    type: str
  p1_descr:
    description: The description of the ipsec tunnel
    required: true
    type: str
  state:
    description: State in which to leave the ipsec tunnel phase2
    choices: [ "present", "absent" ]
    default: present
    type: str
  apply:
    description: Apply VPN configuration on target pfSense
    default: True
    type: bool
"""


EXAMPLES = """
- name: Add simple phase2
  pfsense_ipsec_p2:
    p1_descr: test_tunnel
    descr: test_p2
    state: present
    apply: False
    mode: vti
    local: 1.2.3.1
    remote: 1.2.3.2
    aes: True
    aes_len: auto
    sha256: True

- name: Remove phase2
  pfsense_ipsec_p2:
    state: absent
    p1_descr: test_tunnel
    descr: test_p2
    apply: False
"""

RETURN = """
commands:
    description: the set of commands that would be pushed to the remote device (if pfSense had a CLI)
    returned: always
    type: list
    sample: ["create ipsec_p2 'test_p2' on 'test_tunnel', disabled='False', mode='vti', local='1.2.3.1', ...", "delete ipsec_p2 'test_p2' on 'test_tunnel'"]
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.pfsense.ipsec_p2 import PFSenseIpsecP2Module, IPSEC_P2_ARGUMENT_SPEC, IPSEC_P2_REQUIRED_IF


def main():
    module = AnsibleModule(
        argument_spec=IPSEC_P2_ARGUMENT_SPEC,
        required_if=IPSEC_P2_REQUIRED_IF,
        supports_check_mode=True)

    pfmodule = PFSenseIpsecP2Module(module)
    pfmodule.run(module.params)
    pfmodule.commit_changes()


if __name__ == '__main__':
    main()
