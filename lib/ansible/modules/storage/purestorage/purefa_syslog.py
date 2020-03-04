#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Simon Dodsley (simon@purestorage.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: purefa_syslog
version_added: '2.9'
short_description: Configure Pure Storage FlashArray syslog settings
description:
- Configure syslog configuration for Pure Storage FlashArrays.
- Add or delete an individual syslog server to the existing
  list of serves.
author:
- Pure Storage Ansible Team (@sdodsley) <pure-ansible-team@purestorage.com>
options:
  state:
    description:
    - Create or delete syslog servers configuration
    default: present
    type: str
    choices: [ absent, present ]
  protocol:
    description:
    - Protocol which server uses
    required: true
    type: str
    choices: [ tcp, tls, udp ]
  port:
    description:
    - Port at which the server is listening. If no port is specified
      the system will use 514
    type: str
  address:
    description:
    - Syslog server address.
      This field supports IPv4, IPv6 or FQDN.
      An invalid IP addresses will cause the module to fail.
      No validation is performed for FQDNs.
    type: str
    required: true
extends_documentation_fragment:
- purestorage.fa
'''

EXAMPLES = r'''
- name: Delete existing syslog server entries
  purefa_syslog:
    address: syslog1.com
    protocol: tcp
    state: absent
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Set array syslog servers
  purefa_syslog:
    state: present
    address: syslog1.com
    protocol: udp
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pure import get_system, purefa_argument_spec


def delete_syslog(module, array):
    """Delete Syslog Server"""
    changed = False
    noport_address = module.params['protocol'] + "://" + module.params['address']

    if module.params['port']:
        full_address = noport_address + ":" + module.params['port']
    else:
        full_address = noport_address

    address_list = array.get(syslogserver=True)['syslogserver']

    if address_list:
        for address in range(0, len(address_list)):
            if address_list[address] == full_address:
                del address_list[address]
                try:
                    array.set(syslogserver=address_list)
                    changed = True
                    break
                except Exception:
                    module.fail_json(msg='Failed to remove syslog server: {0}'.format(full_address))

    module.exit_json(changed=changed)


def add_syslog(module, array):
    """Add Syslog Server"""
    changed = False
    noport_address = module.params['protocol'] + "://" + module.params['address']

    if module.params['port']:
        full_address = noport_address + ":" + module.params['port']
    else:
        full_address = noport_address

    address_list = array.get(syslogserver=True)['syslogserver']
    exists = False

    if address_list:
        for address in range(0, len(address_list)):
            if address_list[address] == full_address:
                exists = True
                break
    if not exists:
        try:
            address_list.append(full_address)
            array.set(syslogserver=address_list)
            changed = True
        except Exception:
            module.fail_json(msg='Failed to add syslog server: {0}'.format(full_address))

    module.exit_json(changed=changed)


def main():
    argument_spec = purefa_argument_spec()
    argument_spec.update(dict(
        address=dict(type='str', required=True),
        protocol=dict(type='str', choices=['tcp', 'tls', 'udp'], required=True),
        port=dict(type='str'),
        state=dict(type='str', default='present', choices=['absent', 'present']),
    ))

    module = AnsibleModule(argument_spec,
                           supports_check_mode=False)

    array = get_system(module)

    if module.params['state'] == 'absent':
        delete_syslog(module, array)
    else:
        add_syslog(module, array)

    module.exit_json(changed=False)


if __name__ == '__main__':
    main()
