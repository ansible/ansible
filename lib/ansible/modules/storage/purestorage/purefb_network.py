#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Simon Dodsley (simon@purestorage.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: purefb_network
version_added: "2.8"
short_description:  Manage network interfaces in a Pure Storage FlashBlade
description:
    - This module manages network interfaces on Pure Storage FlashBlade.
    - When creating a network interface a subnet must already exist with
      a network prefix that covers the IP address of the interface being
      created.
author: Pure Storage Ansible Team (@sdodsley) <pure-ansible-team@purestorage.com>
options:
  name:
    description:
      - Interface Name.
    required: true
    type: str
  state:
    description:
      - Create, delete or modifies a network interface.
    required: false
    default: present
    choices: [ "present", "absent" ]
    type: str
  address:
    description:
      - IP address of interface.
    required: false
    type: str
  services:
    description:
      - Define which services are configured for the interfaces.
    required: false
    choices: [ "data" ]
    default: data
    type: str
  itype:
    description:
      - Type of interface.
    required: false
    choices: [ "vip" ]
    default: vip
    type: str
extends_documentation_fragment:
    - purestorage.fb
'''

EXAMPLES = '''
- name: Create new network interface named foo
  purefb_network:
    name: foo
    address: 10.21.200.23
    state: present
    fb_url: 10.10.10.2
    api_token: T-55a68eb5-c785-4720-a2ca-8b03903bf641

- name: Change IP address of network interface named foo
  purefb_network:
    name: foo
    state: present
    address: 10.21.200.123
    fb_url: 10.10.10.2
    api_token: T-55a68eb5-c785-4720-a2ca-8b03903bf641

- name: Delete network interface named foo
  purefb_network:
    name: foo
    state: absent
    fb_url: 10.10.10.2
    api_token: T-55a68eb5-c785-4720-a2ca-8b03903bf641'''

RETURN = '''
'''

HAS_PURITY_FB = True
try:
    from purity_fb import NetworkInterface
except ImportError:
    HAS_PURITY_FB = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pure import get_blade, purefb_argument_spec


MINIMUM_API_VERSION = '1.3'


def get_iface(module, blade):
    """Return Filesystem or None"""
    iface = []
    iface.append(module.params['name'])
    try:
        res = blade.network_interfaces.list_network_interfaces(names=iface)
        return res.items[0]
    except Exception:
        return None


def create_iface(module, blade):
    """Create Network Interface"""

    iface = []
    services = []
    iface.append(module.params['name'])
    services.append(module.params['services'])
    try:
        blade.network_interfaces.create_network_interfaces(names=iface,
                                                           network_interface=NetworkInterface(address=module.params['address'],
                                                                                              services=services,
                                                                                              type=module.params['itype']
                                                                                              )
                                                           )
        changed = True
    except Exception:
        module.fail_json(msg='Interface creation failed. Check valid subnet exists for IP address {0}'.format(module.params['address']))
        changed = False
    module.exit_json(changed=changed)


def modify_iface(module, blade):
    """Modify Network Interface IP address"""
    changed = False
    iface = get_iface(module, blade)
    iface_new = []
    iface_new.append(module.params['name'])
    if module.params['address'] != iface.address:
        try:
            blade.network_interfaces.update_network_interfaces(names=iface_new,
                                                               network_interface=NetworkInterface(address=module.params['address']))
            changed = True
        except Exception:
            changed = False
    module.exit_json(changed=changed)


def delete_iface(module, blade):
    """ Delete Network Interface"""
    iface = []
    iface.append(module.params['name'])
    try:
        blade.network_interfaces.delete_network_interfaces(names=iface)
        changed = True
    except Exception:
        changed = False
    module.exit_json(changed=changed)


def main():
    argument_spec = purefb_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True),
            state=dict(default='present', choices=['present', 'absent']),
            address=dict(),
            services=dict(default='data', choices=['data']),
            itype=dict(default='vip', choices=['vip']),
        )
    )

    required_if = [["state", "present", ["address"]]]

    module = AnsibleModule(argument_spec,
                           required_if=required_if,
                           supports_check_mode=False)

    if not HAS_PURITY_FB:
        module.fail_json(msg='purity_fb sdk is required for this module')

    state = module.params['state']
    blade = get_blade(module)
    api_version = blade.api_version.list_versions().versions
    if MINIMUM_API_VERSION not in api_version:
        module.fail_json(msg='Upgrade Purity//FB to enable this module')
    iface = get_iface(module, blade)

    if state == 'present' and not iface:
        create_iface(module, blade)
    elif state == 'present' and iface:
        modify_iface(module, blade)
    elif state == 'absent' and iface:
        delete_iface(module, blade)
    elif state == 'absent' and not iface:
        module.exit_json(changed=False)


if __name__ == '__main__':
    main()
