#!/usr/bin/python
# -*- coding: UTF-8 -*-


from ansible.module_utils.basic import *
from ansible.module_utils.univention_umc import (
    umc_module_for_add,
    umc_module_for_edit,
    ldap_search,
    base_dn,
)
import socket


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
        supports_check_mode=True
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
