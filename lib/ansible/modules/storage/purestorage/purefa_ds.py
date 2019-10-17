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
module: purefa_ds
version_added: '2.6'
short_description: Configure FlashArray Directory Service
description:
- Set or erase configuration for the directory service. There is no facility
  to SSL certificates at this time. Use the FlashArray GUI for this
  additional configuration work.
- To modify an existing directory service configuration you must first delete
  an existing configuration and then recreate with new settings.
author:
- Pure Storage Ansible Team (@sdodsley) <pure-ansible-team@purestorage.com>
options:
  state:
    type: str
    description:
    - Create or delete directory service configuration
    default: present
    choices: [ absent, present ]
  enable:
    description:
    - Whether to enable or disable directory service support.
    default: false
    type: bool
  uri:
    type: list
    description:
    - A list of up to 30 URIs of the directory servers. Each URI must include
      the scheme ldap:// or ldaps:// (for LDAP over SSL), a hostname, and a
      domain name or IP address. For example, ldap://ad.company.com configures
      the directory service with the hostname "ad" in the domain "company.com"
      while specifying the unencrypted LDAP protocol.
  base_dn:
    type: str
    description:
    - Sets the base of the Distinguished Name (DN) of the directory service
      groups. The base should consist of only Domain Components (DCs). The
      base_dn will populate with a default value when a URI is entered by
      parsing domain components from the URI. The base DN should specify DC=
      for each domain component and multiple DCs should be separated by commas.
    required: true
  bind_password:
    type: str
    description:
    - Sets the password of the bind_user user name account.
  bind_user:
    type: str
    description:
    - Sets the user name that can be used to bind to and query the directory.
    - For Active Directory, enter the username - often referred to as
      sAMAccountName or User Logon Name - of the account that is used to
      perform directory lookups.
    - For OpenLDAP, enter the full DN of the user.
  group_base:
    type: str
    description:
    - Specifies where the configured groups are located in the directory
      tree. This field consists of Organizational Units (OUs) that combine
      with the base DN attribute and the configured group CNs to complete
      the full Distinguished Name of the groups. The group base should
      specify OU= for each OU and multiple OUs should be separated by commas.
      The order of OUs is important and should get larger in scope from left
      to right. Each OU should not exceed 64 characters in length.
    - Not Supported from Purity 5.2.0 or higher. Use I(purefa_dsrole) module.
  ro_group:
    type: str
    description:
    - Sets the common Name (CN) of the configured directory service group
      containing users with read-only privileges on the FlashArray. This
      name should be just the Common Name of the group without the CN=
      specifier. Common Names should not exceed 64 characters in length.
    - Not Supported from Purity 5.2.0 or higher. Use I(purefa_dsrole) module.
  sa_group:
    type: str
    description:
    - Sets the common Name (CN) of the configured directory service group
      containing administrators with storage-related privileges on the
      FlashArray. This name should be just the Common Name of the group
      without the CN= specifier. Common Names should not exceed 64
      characters in length.
    - Not Supported from Purity 5.2.0 or higher. Use I(purefa_dsrole) module.
  aa_group:
    type: str
    description:
    - Sets the common Name (CN) of the directory service group containing
      administrators with full privileges when managing the FlashArray.
      The name should be just the Common Name of the group without the
      CN= specifier. Common Names should not exceed 64 characters in length.
    - Not Supported from Purity 5.2.0 or higher. Use I(purefa_dsrole) module.
extends_documentation_fragment:
- purestorage.fa
'''

EXAMPLES = r'''
- name: Delete existing directory service
  purefa_ds:
    state: absent
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Create directory service (disabled) - Pre-5.2.0
  purefa_ds:
    uri: "ldap://lab.purestorage.com"
    base_dn: "DC=lab,DC=purestorage,DC=com"
    bind_user: Administrator
    bind_password: password
    group_base: "OU=Pure-Admin"
    ro_group: PureReadOnly
    sa_group: PureStorage
    aa_group: PureAdmin
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Create directory service (disabled) - 5.2.0 or higher
  purefa_ds:
    uri: "ldap://lab.purestorage.com"
    base_dn: "DC=lab,DC=purestorage,DC=com"
    bind_user: Administrator
    bind_password: password
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Enable existing directory service
  purefa_ds:
    enable: true
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Disable existing directory service
  purefa_ds:
    enable: false
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Create directory service (enabled) - Pre-5.2.0
  purefa_ds:
    enable: true
    uri: "ldap://lab.purestorage.com"
    base_dn: "DC=lab,DC=purestorage,DC=com"
    bind_user: Administrator
    bind_password: password
    group_base: "OU=Pure-Admin"
    ro_group: PureReadOnly
    sa_group: PureStorage
    aa_group: PureAdmin
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Create directory service (enabled) - 5.2.0 or higher
  purefa_ds:
    enable: true
    uri: "ldap://lab.purestorage.com"
    base_dn: "DC=lab,DC=purestorage,DC=com"
    bind_user: Administrator
    bind_password: password
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pure import get_system, purefa_argument_spec


DS_ROLE_REQUIRED_API_VERSION = '1.16'


def update_ds(module, array):
    """Update Directory Service"""
    changed = False
    module.exit_json(changed=changed)


def enable_ds(module, array):
    """Enable Directory Service"""
    changed = False
    try:
        array.enable_directory_service()
        changed = True
    except Exception:
        module.fail_json(msg='Enable Directory Service failed: Check Configuration')
    module.exit_json(changed=changed)


def disable_ds(module, array):
    """Disable Directory Service"""
    """Disable Directory Service"""
    changed = False
    try:
        array.disable_directory_service()
        changed = True
    except Exception:
        module.fail_json(msg='Disable Directory Service failed')
    module.exit_json(changed=changed)


def delete_ds(module, array):
    """Delete Directory Service"""
    changed = False
    try:
        api_version = array._list_available_rest_versions()
        array.set_directory_service(enabled=False)
        if DS_ROLE_REQUIRED_API_VERSION in api_version:
            array.set_directory_service(uri=[''],
                                        base_dn="",
                                        bind_user="",
                                        bind_password="",
                                        certificate="")
            changed = True
        else:
            array.set_directory_service(uri=[''],
                                        base_dn="",
                                        group_base="",
                                        bind_user="",
                                        bind_password="",
                                        readonly_group="",
                                        storage_admin_group="",
                                        array_admin_group="",
                                        certificate="")
            changed = True
    except Exception:
        module.fail_json(msg='Delete Directory Service failed')
    module.exit_json(changed=changed)


def create_ds(module, array):
    """Create Directory Service"""
    changed = False
    api_version = array._list_available_rest_versions()
    if DS_ROLE_REQUIRED_API_VERSION in api_version:
        if not module.params['role']:
            module.fail_json(msg='At least one role must be configured')
        try:
            array.set_directory_service(uri=module.params['uri'],
                                        base_dn=module.params['base_dn'],
                                        bind_user=module.params['bind_user'],
                                        bind_password=module.params['bind_password'])
            array.set_directory_service(enabled=module.params['enable'])
            changed = True
        except Exception:
            module.fail_json(msg='Create Directory Service failed: Check configuration')
    else:
        groups_rule = [not module.params['ro_group'],
                       not module.params['sa_group'],
                       not module.params['aa_group']]

        if all(groups_rule):
            module.fail_json(msg='At least one group must be configured')
        try:
            array.set_directory_service(uri=module.params['uri'],
                                        base_dn=module.params['base_dn'],
                                        group_base=module.params['group_base'],
                                        bind_user=module.params['bind_user'],
                                        bind_password=module.params['bind_password'],
                                        readonly_group=module.params['ro_group'],
                                        storage_admin_group=module.params['sa_group'],
                                        array_admin_group=module.params['aa_group'])
            array.set_directory_service(enabled=module.params['enable'])
            changed = True
        except Exception:
            module.fail_json(msg='Create Directory Service failed: Check configuration')
    module.exit_json(changed=changed)


def main():
    argument_spec = purefa_argument_spec()
    argument_spec.update(dict(
        uri=dict(type='list'),
        state=dict(type='str', default='present', choices=['absent', 'present']),
        enable=dict(type='bool', default=False),
        bind_password=dict(type='str', no_log=True),
        bind_user=dict(type='str'),
        base_dn=dict(type='str'),
        group_base=dict(type='str'),
        ro_group=dict(type='str'),
        sa_group=dict(type='str'),
        aa_group=dict(type='str'),
    ))

    required_together = [['uri', 'bind_password', 'bind_user',
                          'base_dn', 'group_base']]

    module = AnsibleModule(argument_spec,
                           required_together=required_together,
                           supports_check_mode=False)

    state = module.params['state']
    array = get_system(module)
    ds_exists = False
    dirserv = array.get_directory_service()
    ds_enabled = dirserv['enabled']
    if dirserv['base_dn']:
        ds_exists = True

    if state == 'absent' and ds_exists:
        delete_ds(module, array)
    elif ds_exists and module.params['enable'] and ds_enabled:
        update_ds(module, array)
    elif ds_exists and not module.params['enable'] and ds_enabled:
        disable_ds(module, array)
    elif ds_exists and module.params['enable'] and not ds_enabled:
        enable_ds(module, array)
    elif not ds_exists and state == 'present':
        create_ds(module, array)
    else:
        module.exit_json(changed=False)


if __name__ == '__main__':
    main()
