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
module: purefb_ds
version_added: '2.8'
short_description: Configure FlashBlade Directory Service
description:
- Create or erase directory services configurations. There is no facility
  to SSL certificates at this time. Use the FlashBlade GUI for this
  additional configuration work.
- To modify an existing directory service configuration you must first delete
  an exisitng configuration and then recreate with new settings.
author:
- Pure Storage Ansible Team (@sdodsley) <pure-ansible-team@purestorage.com>
options:
  state:
    description:
    - Create or delete directory service configuration
    default: present
    type: str
    choices: [ absent, present ]
  dstype:
    description:
    - The type of directory service to work on
    choices: [ management, nfs, smb ]
    type: str
  enable:
    description:
    - Whether to enable or disable directory service support.
    default: false
    type: bool
  uri:
    description:
    - A list of up to 30 URIs of the directory servers. Each URI must include
      the scheme ldap:// or ldaps:// (for LDAP over SSL), a hostname, and a
      domain name or IP address. For example, ldap://ad.company.com configures
      the directory service with the hostname "ad" in the domain "company.com"
      while specifying the unencrypted LDAP protocol.
    type: list
  base_dn:
    description:
    - Sets the base of the Distinguished Name (DN) of the directory service
      groups. The base should consist of only Domain Components (DCs). The
      base_dn will populate with a default value when a URI is entered by
      parsing domain components from the URI. The base DN should specify DC=
      for each domain component and multiple DCs should be separated by commas.
    required: true
    type: str
  bind_password:
    description:
    - Sets the password of the bind_user user name account.
    type: str
  bind_user:
    description:
    - Sets the user name that can be used to bind to and query the directory.
    - For Active Directory, enter the username - often referred to as
      sAMAccountName or User Logon Name - of the account that is used to
      perform directory lookups.
    - For OpenLDAP, enter the full DN of the user.
    type: str
extends_documentation_fragment:
- purestorage.fb
'''

EXAMPLES = r'''
- name: Delete existing management directory service
  purefb_ds:
    dstype: management
    state: absent
    fb_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Create NFS directory service (disabled)
  purefb_ds:
    dstype: nfs
    uri: "ldap://lab.purestorage.com"
    base_dn: "DC=lab,DC=purestorage,DC=com"
    bind_user: Administrator
    bind_password: password
    fb_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Enable existing SMB directory service
  purefb_ds:
    dstypr: smb
    enable: true
    fb_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Disable existing management directory service
  purefb_ds:
    dstype: management
    enable: false
    fb_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Create NFS directory service (enabled)
  purefb_ds:
    dstype: nfs
    enable: true
    uri: "ldap://lab.purestorage.com"
    base_dn: "DC=lab,DC=purestorage,DC=com"
    bind_user: Administrator
    bind_password: password
    fb_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
'''

RETURN = r'''
'''


HAS_PURITY_FB = True
try:
    from purity_fb import DirectoryService
except ImportError:
    HAS_PURITY_FB = False


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pure import get_blade, purefb_argument_spec


def update_ds(module, blade):
    """Update Directory Service"""
    changed = False
    module.exit_json(changed=changed)


def enable_ds(module, blade):
    """Enable Directory Service"""
    changed = False
    try:
        blade.directory_services.update_directory_services(names=[module.params['dstype']],
                                                           directory_service=DirectoryService(enabled=True))
        changed = True
    except Exception:
        module.fail_json(msg='Enable {0} Directory Service failed: Check Configuration'.format(module.params['dstype']))
    module.exit_json(changed=changed)


def disable_ds(module, blade):
    """Disable Directory Service"""
    changed = False
    try:
        blade.directory_services.update_directory_services(names=[module.params['dstype']],
                                                           directory_service=DirectoryService(enabled=False))
        changed = True
    except Exception:
        module.fail_json(msg='Disable {0} Directory Service failed'.format(module.params['dstype']))
    module.exit_json(changed=changed)


def delete_ds(module, blade):
    """Delete Directory Service"""
    changed = False
    try:
        dir_service = DirectoryService(uris=[''],
                                       base_dn="",
                                       bind_user="",
                                       bind_password="",
                                       enabled=False)
        blade.directory_services.update_directory_services(names=[module.params['dstype']],
                                                           directory_service=dir_service)
        changed = True
    except Exception:
        module.fail_json(msg='Delete {0} Directory Service failed'.format(module.params['dstype']))
    module.exit_json(changed=changed)


def create_ds(module, blade):
    """Create Directory Service"""
    changed = False
    try:
        dir_service = DirectoryService(uris=module.params['uri'],
                                       base_dn=module.params['base_dn'],
                                       bind_user=module.params['bind_user'],
                                       bind_password=module.params['bind_password'],
                                       enabled=module.params['enable'])
        blade.directory_services.update_directory_services(names=[module.params['dstype']],
                                                           directory_service=dir_service)
        changed = True
    except Exception:
        module.fail_json(msg='Create {0} Directory Service failed: Check configuration'.format(module.params['dstype']))
    module.exit_json(changed=changed)


def main():
    argument_spec = purefb_argument_spec()
    argument_spec.update(dict(
        uri=dict(type='list'),
        dstype=dict(required=True, type='str', choices=['management', 'nfs', 'smb']),
        state=dict(type='str', default='present', choices=['absent', 'present']),
        enable=dict(type='bool', default=False),
        bind_password=dict(type='str', no_log=True),
        bind_user=dict(type='str'),
        base_dn=dict(type='str'),
    ))

    required_together = [['uri', 'bind_password', 'bind_user', 'base_dn']]

    module = AnsibleModule(argument_spec,
                           required_together=required_together,
                           supports_check_mode=False)
    if not HAS_PURITY_FB:
        module.fail_json(msg='purity_fb sdk is required for this module')

    state = module.params['state']
    blade = get_blade(module)
    ds_configured = False
    dirserv = blade.directory_services.list_directory_services(names=[module.params['dstype']])
    ds_enabled = dirserv.items[0].enabled
    if dirserv.items[0].base_dn is not None:
        ds_configured = True

    if state == 'absent' and ds_configured:
        delete_ds(module, blade)
    elif ds_configured and module.params['enable'] and ds_enabled:
        update_ds(module, blade)
    elif ds_configured and not module.params['enable'] and ds_enabled:
        disable_ds(module, blade)
    elif ds_configured and module.params['enable'] and not ds_enabled:
        enable_ds(module, blade)
    elif not ds_configured and state == 'present':
        create_ds(module, blade)
    else:
        module.exit_json(changed=False)


if __name__ == '__main__':
    main()
