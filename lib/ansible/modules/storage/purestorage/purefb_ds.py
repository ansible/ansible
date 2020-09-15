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
  an existing configuration and then recreate with new settings.
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
  nis_servers:
    description:
    - A list of up to 30 IP addresses or FQDNs for NIS servers.
    - This cannot be used in conjunction with LDAP configurations.
    type: list
    version_added: 2.9
  nis_domain:
    description:
    - The NIS domain to search
    - This cannot be used in conjunction with LDAP configurations.
    type: str
    version_added: 2.9
  join_ou:
    description:
      - The optional organizational unit (OU) where the machine account
        for the directory service will be created.
    type: str
    version_added: 2.9
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
    uri: "ldaps://lab.purestorage.com"
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
    uri: "ldaps://lab.purestorage.com"
    base_dn: "DC=lab,DC=purestorage,DC=com"
    bind_user: Administrator
    bind_password: password
    fb_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
'''

RETURN = r'''
'''


NIS_API_VERSION = '1.7'
HAS_PURITY_FB = True
try:
    from purity_fb import DirectoryService
except ImportError:
    HAS_PURITY_FB = False


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pure import get_blade, purefb_argument_spec


def update_ds(module, blade):
    """Update Directory Service"""
# This module is a place-holder until we figure out a way to
# update the config on the fly rather than deleting and resetting
    changed = False
    module.exit_json(changed=changed)


def enable_ds(module, blade):
    """Enable Directory Service"""
    changed = True
    if not module.check_mode:
        try:
            blade.directory_services.update_directory_services(names=[module.params['dstype']],
                                                               directory_service=DirectoryService(enabled=True))
            changed = True
        except Exception:
            module.fail_json(msg='Enable {0} Directory Service failed: Check Configuration'.format(module.params['dstype']))
    module.exit_json(changed=changed)


def disable_ds(module, blade):
    """Disable Directory Service"""
    changed = True
    if not module.check_mode:
        try:
            blade.directory_services.update_directory_services(names=[module.params['dstype']],
                                                               directory_service=DirectoryService(enabled=False))
        except Exception:
            module.fail_json(msg='Disable {0} Directory Service failed'.format(module.params['dstype']))
    module.exit_json(changed=changed)


def delete_ds(module, blade):
    """Delete Directory Service"""
    changed = True
    if not module.check_mode:
        dirserv = blade.directory_services.list_directory_services(names=[module.params['dstype']])
        try:
            if module.params['dstype'] == 'management':
                if dirserv.items[0].uris:
                    dir_service = DirectoryService(uris=[''],
                                                   base_dn="",
                                                   bind_user="",
                                                   bind_password="",
                                                   enabled=False)
                else:
                    changed = False
            elif module.params['dstype'] == 'smb':
                if dirserv.items[0].uris:
                    smb_attrs = {'join_ou': ''}
                    dir_service = DirectoryService(uris=[''],
                                                   base_dn='',
                                                   bind_user='',
                                                   bind_password='',
                                                   smb=smb_attrs,
                                                   enabled=False)
                else:
                    changed = False
            elif module.params['dstype'] == 'nfs':
                if dirserv.items[0].uris:
                    dir_service = DirectoryService(uris=[''],
                                                   base_dn='',
                                                   bind_user='',
                                                   bind_password='',
                                                   enabled=False)
                elif dirserv.items[0].nfs.nis_domains:
                    nfs_attrs = {'nis_domains': [],
                                 'nis_servers': []}
                    dir_service = DirectoryService(nfs=nfs_attrs,
                                                   enabled=False)
                else:
                    changed = False
            if changed:
                blade.directory_services.update_directory_services(names=[module.params['dstype']],
                                                                   directory_service=dir_service)
        except Exception:
            module.fail_json(msg='Delete {0} Directory Service failed'.format(module.params['dstype']))
    module.exit_json(changed=changed)


def create_ds(module, blade):
    """Create Directory Service"""
    changed = True
    if not module.check_mode:
        try:
            if module.params['dstype'] == 'management':
                if module.params['uri']:
                    dir_service = DirectoryService(uris=module.params['uri'][0:30],
                                                   base_dn=module.params['base_dn'],
                                                   bind_user=module.params['bind_user'],
                                                   bind_password=module.params['bind_password'],
                                                   enabled=module.params['enable'])
                else:
                    module.fail_json(msg="URI and associated params must be specified to create dstype {0}".format(module.params['dstype']))
            elif module.params['dstype'] == 'smb':
                if module.params['uri']:
                    smb_attrs = {'join_ou': module.params['join_ou']}
                    dir_service = DirectoryService(uris=module.params['uri'][0:30],
                                                   base_dn=module.params['base_dn'],
                                                   bind_user=module.params['bind_user'],
                                                   bind_password=module.params['bind_password'],
                                                   smb=smb_attrs,
                                                   enabled=module.params['enable'])
                else:
                    module.fail_json(msg="URI and associated params must be specified to create dstype {0}".format(module.params['dstype']))
            elif module.params['dstype'] == 'nfs':
                if module.params['nis_domain']:
                    nfs_attrs = {'nis_domains': [module.params['nis_domain']],
                                 'nis_servers': module.params['nis_servers'][0:30]}
                    dir_service = DirectoryService(nfs=nfs_attrs,
                                                   enabled=module.params['enable'])
                else:
                    dir_service = DirectoryService(uris=module.params['uri'][0:30],
                                                   base_dn=module.params['base_dn'],
                                                   bind_user=module.params['bind_user'],
                                                   bind_password=module.params['bind_password'],
                                                   enabled=module.params['enable'])
            blade.directory_services.update_directory_services(names=[module.params['dstype']],
                                                               directory_service=dir_service)
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
        join_ou=dict(type='str'),
        nis_domain=dict(type='str'),
        nis_servers=dict(type='list'),
    ))

    required_together = [['uri', 'bind_password', 'bind_user', 'base_dn'],
                         ['nis_servers', 'nis_domain'],
                         ['join_ou', 'uri']]
    mutually_exclusive = [['uri', 'nis_domain']]

    module = AnsibleModule(argument_spec,
                           required_together=required_together,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)
    if not HAS_PURITY_FB:
        module.fail_json(msg='purity_fb sdk is required for this module')

    state = module.params['state']
    blade = get_blade(module)
    api_version = blade.api_version.list_versions().versions
    ds_configured = False
    dirserv = blade.directory_services.list_directory_services(names=[module.params['dstype']])
    ds_enabled = dirserv.items[0].enabled
    if dirserv.items[0].base_dn is not None:
        ds_configured = True
    if (module.params['nis_domain'] or module.params['join_ou']) and (NIS_API_VERSION not in api_version):
        module.fail_json(msg="NFS or SMB directory service attributes are not supported in your FlashBlade Purity version.")
    ldap_uri = False
    set_ldap = False
    for uri in range(0, len(dirserv.items[0].uris)):
        if "ldap" in dirserv.items[0].uris[uri].lower():
            ldap_uri = True
    if module.params['uri']:
        for uri in range(0, len(module.params['uri'])):
            if "ldap" in module.params['uri'][uri].lower():
                set_ldap = True
    if not module.params['uri'] and ldap_uri or \
       module.params['uri'] and set_ldap:
        if module.params['nis_servers'] or module.params['nis_domain']:
            module.fail_json(msg="NIS configuration not supported in an LDAP environment")
    if state == 'absent':
        delete_ds(module, blade)
    elif ds_configured and module.params['enable'] and ds_enabled:
        update_ds(module, blade)
    elif ds_configured and not module.params['enable'] and ds_enabled:
        disable_ds(module, blade)
    elif ds_configured and module.params['enable'] and not ds_enabled:
        enable_ds(module, blade)
# Now we have enabled the DS lets make sure there aren't any new updates...
        update_ds(module, blade)
    elif not ds_configured and state == 'present':
        create_ds(module, blade)
    else:
        module.exit_json(changed=False)


if __name__ == '__main__':
    main()
