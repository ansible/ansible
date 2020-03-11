#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2019, Simon Dodsley (simon@purestorage.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: purefa_snmp
version_added: '2.9'
short_description: Configure FlashArray SNMP Managers
description:
- Manage SNMP managers on a Pure Storage FlashArray.
- Changing of a named SNMP managers version is not supported.
- This module is not idempotent and will always modify an
  existing SNMP manager due to hidden parameters that cannot
  be compared to the play parameters.
author:
- Pure Storage Ansible Team (@sdodsley) <pure-ansible-team@purestorage.com>
options:
  name:
    description:
    - Name of SNMP Manager
    required: True
    type: str
  state:
    description:
    - Create or delete SNMP manager
    type: str
    default: present
    choices: [ absent, present ]
  auth_passphrase:
    type: str
    description:
    - SNMPv3 only. Passphrase of 8 - 32 characters.
  auth_protocol:
    type: str
    description:
    - SNMP v3 only. Hash algorithm to use
    choices: [ MD5, SHA ]
  community:
    type: str
    description:
    - SNMP v2c only. Manager community ID. Between 1 and 32 characters long.
  host:
    type: str
    description:
    - IPv4 or IPv6 address or FQDN to send trap messages to.
  user:
    type: str
    description:
    - SNMP v3 only. User ID recognized by the specified SNMP manager.
      Must be between 1 and 32 characters.
  version:
    type: str
    description:
    - Version of SNMP protocol to use for the manager.
    choices: [ v2c, v3 ]
    default: v2c
  notification:
    type: str
    description:
    - Action to perform on event.
    default: trap
    choices: [ inform, trap ]
  privacy_passphrase:
    type: str
    description:
    - SNMPv3 only. Passphrase to encrypt SNMP messages.
      Must be between 8 and 63 non-space ASCII characters.
  privacy_protocol:
    type: str
    description:
    - SNMP v3 only. Encryption protocol to use
    choices: [ AES, DES ]
extends_documentation_fragment:
- purestorage.fa
'''

EXAMPLES = r'''
- name: Delete existing SNMP manager
  purefa_snmp:
    name: manager1
    state: absent
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Create v2c SNMP manager
  purefa_snmp:
    name: manager1
    community: public
    host: 10.21.22.23
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Create v3 SNMP manager
  purefa_snmp:
    name: manager2
    version: v3
    auth_protocol: MD5
    auth_passphrase: password
    host: 10.21.22.23
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Update existing SNMP manager
  purefa_snmp:
    name: manager1
    community: private
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
'''

RETURN = r'''
'''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pure import get_system, purefa_argument_spec


def update_manager(module, array):
    """Update SNMP Manager"""
    changed = True
    if not module.check_mode:
        try:
            mgr = array.get_snmp_manager(module.params['name'])
        except Exception:
            module.fail_json(msg="Failed to get current configuration for SNMP manager {0}.".format(module.params['name']))
        if mgr['version'] != module.params['version']:
            module.fail_json(msg="Changing an SNMP managers version is not supported.")
        elif module.params['version'] == "v2c":
            try:
                array.set_snmp_manager(module.params['name'],
                                       community=module.params['community'],
                                       notification=module.params['notification'],
                                       host=module.params['host']
                                       )
            except Exception:
                module.fail_json(msg="Failed to update SNMP manager {0}.".format(module.params['name']))
        else:
            if module.params['auth_protocol'] and module.params['privacy_protocol']:
                try:
                    array.set_snmp_manager(module.params['name'],
                                           auth_passphrase=module.params['auth_passphrase'],
                                           auth_protocol=module.params['auth_protocol'],
                                           privacy_passphrase=module.params['privacy_passphrase'],
                                           privacy_protocol=module.params['privacy_protocol'],
                                           notification=module.params['notification'],
                                           user=module.params['user'],
                                           host=module.params['host']
                                           )
                except Exception:
                    module.fail_json(msg="Failed to update SNMP manager {0}.".format(module.params['name']))
            elif module.params['auth_protocol'] and not module.params['privacy_protocol']:
                try:
                    array.set_snmp_manager(module.params['name'],
                                           version=module.params['version'],
                                           auth_passphrase=module.params['auth_passphrase'],
                                           auth_protocol=module.params['auth_protocol'],
                                           notification=module.params['notification'],
                                           user=module.params['user'],
                                           host=module.params['host']
                                           )
                except Exception:
                    module.fail_json(msg="Failed to update SNMP manager {0}.".format(module.params['name']))
            elif not module.params['auth_protocol'] and module.params['privacy_protocol']:
                try:
                    array.set_snmp_manager(module.params['name'],
                                           version=module.params['version'],
                                           privacy_passphrase=module.params['privacy_passphrase'],
                                           privacy_protocol=module.params['privacy_protocol'],
                                           notification=module.params['notification'],
                                           user=module.params['user'],
                                           host=module.params['host']
                                           )
                except Exception:
                    module.fail_json(msg="Failed to update SNMP manager {0}.".format(module.params['name']))
            elif not module.params['auth_protocol'] and not module.params['privacy_protocol']:
                try:
                    array.set_snmp_manager(module.params['name'],
                                           version=module.params['version'],
                                           notification=module.params['notification'],
                                           user=module.params['user'],
                                           host=module.params['host']
                                           )
                except Exception:
                    module.fail_json(msg="Failed to update SNMP manager {0}.".format(module.params['name']))
            else:
                module.fail_json(msg="Invalid parameters selected in update. Please raise issue in Ansible GitHub")

    module.exit_json(changed=changed)


def delete_manager(module, array):
    """Delete SNMP Manager"""
    changed = True
    if not module.check_mode:
        try:
            array.delete_snmp_manager(module.params['name'])
        except Exception:
            module.fail_json(msg='Delete SNMP manager {0} failed'.format(module.params['name']))
    module.exit_json(changed=changed)


def create_manager(module, array):
    """Create SNMP Manager"""
    changed = True
    if not module.check_mode:
        if module.params['version'] == "v2c":
            try:
                array.create_snmp_manager(module.params['name'],
                                          version=module.params['version'],
                                          community=module.params['community'],
                                          notification=module.params['notification'],
                                          host=module.params['host']
                                          )
            except Exception:
                module.fail_json(msg="Failed to create SNMP manager {0}.".format(module.params['name']))
        else:
            if module.params['auth_protocol'] and module.params['privacy_protocol']:
                try:
                    array.create_snmp_manager(module.params['name'],
                                              version=module.params['version'],
                                              auth_passphrase=module.params['auth_passphrase'],
                                              auth_protocol=module.params['auth_protocol'],
                                              privacy_passphrase=module.params['privacy_passphrase'],
                                              privacy_protocol=module.params['privacy_protocol'],
                                              notification=module.params['notification'],
                                              user=module.params['user'],
                                              host=module.params['host']
                                              )
                except Exception:
                    module.fail_json(msg="Failed to create SNMP manager {0}.".format(module.params['name']))
            elif module.params['auth_protocol'] and not module.params['privacy_protocol']:
                try:
                    array.create_snmp_manager(module.params['name'],
                                              version=module.params['version'],
                                              auth_passphrase=module.params['auth_passphrase'],
                                              auth_protocol=module.params['auth_protocol'],
                                              notification=module.params['notification'],
                                              user=module.params['user'],
                                              host=module.params['host']
                                              )
                except Exception:
                    module.fail_json(msg="Failed to create SNMP manager {0}.".format(module.params['name']))
            elif not module.params['auth_protocol'] and module.params['privacy_protocol']:
                try:
                    array.create_snmp_manager(module.params['name'],
                                              version=module.params['version'],
                                              privacy_passphrase=module.params['privacy_passphrase'],
                                              privacy_protocol=module.params['privacy_protocol'],
                                              notification=module.params['notification'],
                                              user=module.params['user'],
                                              host=module.params['host']
                                              )
                except Exception:
                    module.fail_json(msg="Failed to create SNMP manager {0}.".format(module.params['name']))
            elif not module.params['auth_protocol'] and not module.params['privacy_protocol']:
                try:
                    array.create_snmp_manager(module.params['name'],
                                              version=module.params['version'],
                                              notification=module.params['notification'],
                                              user=module.params['user'],
                                              host=module.params['host']
                                              )
                except Exception:
                    module.fail_json(msg="Failed to create SNMP manager {0}.".format(module.params['name']))
            else:
                module.fail_json(msg="Invalid parameters selected in create. Please raise issue in Ansible GitHub")
    module.exit_json(changed=changed)


def main():
    argument_spec = purefa_argument_spec()
    argument_spec.update(dict(
        name=dict(type='str', required=True),
        host=dict(type='str'),
        state=dict(type='str', default='present', choices=['absent', 'present']),
        user=dict(type='str'),
        notification=dict(type='str', choices=['inform', 'trap'], default='trap'),
        auth_passphrase=dict(type='str', no_log=True),
        auth_protocol=dict(type='str', choices=['MD5', 'SHA']),
        privacy_passphrase=dict(type='str', no_log=True),
        privacy_protocol=dict(type='str', choices=['AES', 'DES']),
        version=dict(type='str', default='v2c', choices=['v2c', 'v3']),
        community=dict(type='str'),
    ))

    required_together = [['auth_passphrase', 'auth_protocol'],
                         ['privacy_passphrase', 'privacy_protocol']]
    required_if = [['version', 'v2c', ['community', 'host']],
                   ['version', 'v3', ['host', 'user']]]

    module = AnsibleModule(argument_spec,
                           required_together=required_together,
                           required_if=required_if,
                           supports_check_mode=True)

    state = module.params['state']
    array = get_system(module)
    mgr_configured = False
    mgrs = array.list_snmp_managers()
    for mgr in range(0, len(mgrs)):
        if mgrs[mgr]['name'] == module.params['name']:
            mgr_configured = True
            break
    if module.params['version'] == "v3":
        if module.params['auth_passphrase'] and (8 > len(module.params['auth_passphrase']) > 32):
            module.fail_json(msg="auth_password must be between 8 and 32 characters")
        if module.params['privacy_passphrase'] and 8 > len(module.params['privacy_passphrase']) > 63:
            module.fail_json(msg="privacy_password must be between 8 and 63 characters")
    if state == 'absent' and mgr_configured:
        delete_manager(module, array)
    elif mgr_configured and state == 'present':
        update_manager(module, array)
    elif not mgr_configured and state == 'present':
        create_manager(module, array)
    else:
        module.exit_json(changed=False)


if __name__ == '__main__':
    main()
