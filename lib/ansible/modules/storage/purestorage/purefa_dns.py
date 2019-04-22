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
module: purefa_dns
version_added: '2.8'
short_description: Configure FlashArray DNS settings
description:
- Set or erase configuration for the DNS settings.
- Nameservers provided will overwrite any existing nameservers.
author:
- Pure Storage Ansible Team (@sdodsley) <pure-ansible-team@purestorage.com>
options:
  state:
    description:
    - Set or delete directory service configuration
    default: present
    type: str
    choices: [ absent, present ]
  domain:
    description:
    - Domain suffix to be appended when perofrming DNS lookups.
    type: str
  nameservers:
    description:
    - List of up to 3 unique DNS server IP addresses. These can be
      IPv4 or IPv6 - No validation is done of the addresses is performed.
    type: list
extends_documentation_fragment:
- purestorage.fa
'''

EXAMPLES = r'''
- name: Delete exisitng DNS settings
  purefa_dns:
    state: absent
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Set DNS settings
  purefa_dns:
    domain: purestorage.com
    nameservers:
      - 8.8.8.8
      - 8.8.4.4
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pure import get_system, purefa_argument_spec


def remove(duplicate):
    final_list = []
    for num in duplicate:
        if num not in final_list:
            final_list.append(num)
    return final_list


def delete_dns(module, array):
    """Delete DNS settings"""
    changed = False
    current_dns = array.get_dns()
    if current_dns['domain'] == '' and current_dns['nameservers'] == ['']:
        module.exit_json(changed=changed)
    else:
        try:
            array.set_dns(domain='', nameservers=[])
            changed = True
        except Exception:
            module.fail_json(msg='Delete DNS settigs failed')
    module.exit_json(changed=changed)


def create_dns(module, array):
    """Set DNS settings"""
    changed = False
    current_dns = array.get_dns()
    if current_dns['domain'] != module.params['domain'] or sorted(module.params['nameservers']) != sorted(current_dns['nameservers']):
        try:
            array.set_dns(domain=module.params['domain'],
                          nameservers=module.params['nameservers'][0:3])
            changed = True
        except Exception:
            module.fail_json(msg='Set DNS settings failed: Check configuration')
    module.exit_json(changed=changed)


def main():
    argument_spec = purefa_argument_spec()
    argument_spec.update(dict(
        state=dict(type='str', default='present', choices=['absent', 'present']),
        domain=dict(type='str'),
        nameservers=dict(type='list'),
    ))

    required_if = [('state', 'present', ['domain', 'nameservers'])]

    module = AnsibleModule(argument_spec,
                           required_if=required_if,
                           supports_check_mode=False)

    state = module.params['state']
    array = get_system(module)

    if state == 'absent':
        delete_dns(module, array)
    elif state == 'present':
        module.params['nameservers'] = remove(module.params['nameservers'])
        create_dns(module, array)
    else:
        module.exit_json(changed=False)


if __name__ == '__main__':
    main()
