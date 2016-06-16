#!/usr/bin/python
# -*- coding: UTF-8 -*-

# Copyright (c) 2016, Adfinis SyGroup AG
# Tobias Rueetschi <tobias.ruetschi@adfinis-sygroup.ch>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.univention_umc import (
    umc_module_for_add,
    umc_module_for_edit,
    ldap_search,
    base_dn,
)
import socket


DOCUMENTATION = '''
---
module: udm_share
version_added: "2.2"
author: "Tobias Rueetschi (@2-B)"
short_description: Manage samba shares on a univention corporate server
description:
    - "This module allows to manage samba shares on a univention corporate
       server (UCS).
       It uses the python API of the UCS to create a new object or edit it."
requirements:
    - Python >= 2.6
options:
    state:
        required: false
        default: "present"
        choices: [ present, absent ]
        description:
            - Whether the share is present or not.
    name:
        required: true
        description:
            - Name
    host:
        required: false
        default: None
        description:
            - Host FQDN (server which provides the share), e.g. C({{
              ansible_fqdn }}). Required if C(state=present).
    path:
        required: false
        default: None
        description:
            - Directory on the providing server, e.g. C(/home). Required if C(state=present).
    sambaName:
        required: false
        default: None
        description:
            - Windows name. Required if C(state=present).
    ou:
        required: true
        description:
            - Organisational unit, inside the LDAP Base DN.
    owner:
        required: false
        default: 0
        description:
            - Directory owner of the share's root directory.
    group:
        required: false
        default: '0'
        description:
            - Directory owner group of the share's root directory.
    directorymode:
        required: false
        default: '00755'
        description:
            - Permissions for the share's root directory.
    root_squash:
        required: false
        default: '1'
        description:
            - Modify user ID for root user (root squashing).
    subtree_checking:
        required: false
        default: '1'
        description:
            - Subtree checking.
    sync:
        required: false
        default: 'sync'
        description:
            - NFS synchronisation.
    writeable:
        required: false
        default: '1'
        description:
            - NFS write access.
    sambaBlockSize:
        required: false
        default: None
        description:
            - Blocking size.
    sambaBlockingLocks:
        required: false
        default: '1'
        description:
            - Blocking locks.
    sambaBrowseable:
        required: false
        default: '1'
        description:
            - Show in Windows network environment.
    sambaCreateMode:
        required: false
        default: '0744'
        description:
            - File mode.
    sambaCscPolicy:
        required: false
        default: 'manual'
        description:
            - Client-side caching policy.
    sambaCustomSettings:
        required: false
        default: []
        description:
            - Option name in smb.conf and its value.
    sambaDirectoryMode:
        required: false
        default: '0755'
        description:
            - Directory mode.
    sambaDirectorySecurityMode:
        required: false
        default: '0777'
        description:
            - Directory security mode.
    sambaDosFilemode:
        required: false
        default: '0'
        description:
            - Users with write access may modify permissions.
    sambaFakeOplocks:
        required: false
        default: '0'
        description:
            - Fake oplocks.
    sambaForceCreateMode:
        required: false
        default: '0'
        description:
            - Force file mode.
    sambaForceDirectoryMode:
        required: false
        default: '0'
        description:
            - Force directory mode.
    sambaForceDirectorySecurityMode:
        required: false
        default: '0'
        description:
            - Force directory security mode.
    sambaForceGroup:
        required: false
        default: None
        description:
            - Force group.
    sambaForceSecurityMode:
        required: false
        default: '0'
        description:
            - Force security mode.
    sambaForceUser:
        required: false
        default: None
        description:
            - Force user.
    sambaHideFiles:
        required: false
        default: None
        description:
            - Hide files.
    sambaHideUnreadable:
        required: false
        default: '0'
        description:
            - Hide unreadable files/directories.
    sambaHostsAllow:
        required: false
        default: []
        description:
            - Allowed host/network.
    sambaHostsDeny:
        required: false
        default: []
        description:
            - Denied host/network.
    sambaInheritAcls:
        required: false
        default: '1'
        description:
            - Inherit ACLs.
    sambaInheritOwner:
        required: false
        default: '0'
        description:
            - Create files/directories with the owner of the parent directory.
    sambaInheritPermissions:
        required: false
        default: '0'
        description:
            - Create files/directories with permissions of the parent directory.
    sambaInvalidUsers:
        required: false
        default: None
        description:
            - Invalid users or groups.
    sambaLevel2Oplocks:
        required: false
        default: '1'
        description:
            - Level 2 oplocks.
    sambaLocking:
        required: false
        default: '1'
        description:
            - Locking.
    sambaMSDFSRoot:
        required: false
        default: '0'
        description:
            - MSDFS root.
    sambaNtAclSupport:
        required: false
        default: '1'
        description:
            - NT ACL support.
    sambaOplocks:
        required: false
        default: '1'
        description:
            - Oplocks.
    sambaPostexec:
        required: false
        default: None
        description:
            - Postexec script.
    sambaPreexec:
        required: false
        default: None
        description:
            - Preexec script.
    sambaPublic:
        required: false
        default: '0'
        description:
            - Allow anonymous read-only access with a guest user.
    sambaSecurityMode:
        required: false
        default: '0777'
        description:
            - Security mode.
    sambaStrictLocking:
        required: false
        default: 'Auto'
        description:
            - Strict locking.
    sambaVFSObjects:
        required: false
        default: None
        description:
            - VFS objects.
    sambaValidUsers:
        required: false
        default: None
        description:
            - Valid users or groups.
    sambaWriteList:
        required: false
        default: None
        description:
            - Restrict write access to these users/groups.
    sambaWriteable:
        required: false
        default: '1'
        description:
            - Samba write access.
    nfs_hosts:
        required: false
        default: []
        description:
            - Only allow access for this host, IP address or network.
    nfsCustomSettings:
        required: false
        default: []
        description:
            - Option name in exports file.
'''


EXAMPLES = '''
'''


RETURN = '''# '''


def main():
    module = AnsibleModule(
        argument_spec = dict(
            name                            = dict(required=True,
                                                   type='str'),
            ou                              = dict(required=True,
                                                   type='str'),
            owner                           = dict(type='str',
                                                   default='0'),
            group                           = dict(type='str',
                                                   default='0'),
            path                            = dict(type='path',
                                                   default=None),
            directorymode                   = dict(type='str',
                                                   default='00755'),
            host                            = dict(type='str',
                                                   default=None),
            root_squash                     = dict(type='str',
                                                   default='1'),
            subtree_checking                = dict(type='str',
                                                   default='1'),
            sync                            = dict(type='str',
                                                   default='sync'),
            writeable                       = dict(type='str',
                                                   default='1'),
            sambaBlockSize                  = dict(type='str',
                                                   default=None),
            sambaBlockingLocks              = dict(type='str',
                                                   default='1'),
            sambaBrowseable                 = dict(type='str',
                                                   default='1'),
            sambaCreateMode                 = dict(type='str',
                                                   default='0744'),
            sambaCscPolicy                  = dict(type='str',
                                                   default='manual'),
            sambaCustomSettings             = dict(type='list',
                                                   default=[]),
            sambaDirectoryMode              = dict(type='str',
                                                   default='0755'),
            sambaDirectorySecurityMode      = dict(type='str',
                                                   default='0777'),
            sambaDosFilemode                = dict(type='str',
                                                   default='0'),
            sambaFakeOplocks                = dict(type='str',
                                                   default='0'),
            sambaForceCreateMode            = dict(type='str',
                                                   default='0'),
            sambaForceDirectoryMode         = dict(type='str',
                                                   default='0'),
            sambaForceDirectorySecurityMode = dict(type='str',
                                                   default='0'),
            sambaForceGroup                 = dict(type='str',
                                                   default=None),
            sambaForceSecurityMode          = dict(type='str',
                                                   default='0'),
            sambaForceUser                  = dict(type='str',
                                                   default=None),
            sambaHideFiles                  = dict(type='str',
                                                   default=None),
            sambaHideUnreadable             = dict(type='str',
                                                   default='0'),
            sambaHostsAllow                 = dict(type='list',
                                                   default=[]),
            sambaHostsDeny                  = dict(type='list',
                                                   default=[]),
            sambaInheritAcls                = dict(type='str',
                                                   default='1'),
            sambaInheritOwner               = dict(type='str',
                                                   default='0'),
            sambaInheritPermissions         = dict(type='str',
                                                   default='0'),
            sambaInvalidUsers               = dict(type='str',
                                                   default=None),
            sambaLevel2Oplocks              = dict(type='str',
                                                   default='1'),
            sambaLocking                    = dict(type='str',
                                                   default='1'),
            sambaMSDFSRoot                  = dict(type='str',
                                                   default='0'),
            sambaName                       = dict(type='str',
                                                   default=None),
            sambaNtAclSupport               = dict(type='str',
                                                   default='1'),
            sambaOplocks                    = dict(type='str',
                                                   default='1'),
            sambaPostexec                   = dict(type='str',
                                                   default=None),
            sambaPreexec                    = dict(type='str',
                                                   default=None),
            sambaPublic                     = dict(type='str',
                                                   default='0'),
            sambaSecurityMode               = dict(type='str',
                                                   default='0777'),
            sambaStrictLocking              = dict(type='str',
                                                   default='Auto'),
            sambaVFSObjects                 = dict(type='str',
                                                   default=None),
            sambaValidUsers                 = dict(type='str',
                                                   default=None),
            sambaWriteList                  = dict(type='str',
                                                   default=None),
            sambaWriteable                  = dict(type='str',
                                                   default='1'),
            nfs_hosts                       = dict(type='list',
                                                   default=[]),
            nfsCustomSettings               = dict(type='list',
                                                   default=[]),
            state           = dict(default='present',
                                   choices=['present', 'absent'],
                                   type='str')
        ),
        supports_check_mode=True,
        required_if = ([
            ('state', 'present', ['path', 'host', 'sambaName'])
        ])
    )
    name    = module.params['name']
    state   = module.params['state']
    changed = False

    obj = list(ldap_search(
        '(&(objectClass=univentionShare)(cn={}))'.format(name),
        attr=['cn']
    ))

    exists = bool(len(obj))
    container = 'cn=shares,ou={},{}'.format(module.params['ou'], base_dn())
    dn = 'cn={},{}'.format(name, container)

    if state == 'present':
        try:
            if not exists:
                obj = umc_module_for_add('shares/share', container)
            else:
                obj = umc_module_for_edit('shares/share', dn)

            module.params['printablename'] = '{} ({})'.format(name, module.params['host'])
            for k in obj.keys():
                obj[k] = module.params[k]

            diff = obj.diff()
            if exists:
                for k in obj.keys():
                    if obj.hasChanged(k):
                        changed=True
            else:
                changed=True
            if not module.check_mode:
                if not exists:
                    obj.create()
                elif changed:
                    obj.modify()
        except Exception as e:
            module.fail_json(
                msg='Creating/editing share {} in {} failed: {}'.format(name, container, e)
            )

    if state == 'absent' and exists:
        try:
            obj = umc_module_for_edit('shares/share', dn)
            if not module.check_mode:
                obj.remove()
            changed = True
        except:
            module.fail_json(
                msg='Removing share {} in {} failed: {}'.format(name, container, e)
            )

    module.exit_json(
        changed=changed,
        name=name,
        diff=diff,
        container=container
    )


if __name__ == '__main__':
    main()
