#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""UCS access module"""

import univention.uldap
import univention.config_registry
import univention.admin.uldap
import univention.admin.objects
import univention.admin.config
import re
import thread
import time
import ldap as orig_ldap
import socket

__all__ = [
    'ldap_search',
    'config_registry',
    'base_dn',
    'ldap',
    'config',
    'position_base_dn',
    'get_umc_admin_objects',
]

config_registry = univention.config_registry.ConfigRegistry()
config_registry.load()
base_dn         = config_registry["ldap/base"]

try:
    secret_file = open('/etc/ldap.secret', 'r')
    bind_dn     = 'cn=admin,{}'.format(base_dn)
except IOError:  # pragma: no cover
    secret_file = open('/etc/machine.secret', 'r')
    bind_dn     = config_registry["ldap/hostdn"]
pwd_line    = secret_file.readline()
pwd         = re.sub('\n', '', pwd_line)

ldap = univention.admin.uldap.access(
    host      = config_registry['ldap/master'],
    base      = base_dn,
    binddn    = bind_dn,
    bindpw    = pwd,
    start_tls = 1
)
config = univention.admin.config.config()
univention.admin.modules.update()
position_base_dn = univention.admin.uldap.position(base_dn)
modules_by_name = {}


def ldap_dn_tree_parent(dn, count=1):
    dn_array = dn.split(',')
    dn_array[0:count] = []
    return ','.join(dn_array)


def ldap_search(filter, base=base_dn, attr=None):
    """Replaces uldaps search and uses a generator.
   !! Arguments are not the same."""
    msgid = ldap.lo.lo.search(
        base,
        orig_ldap.SCOPE_SUBTREE,
        filterstr=filter,
        attrlist=attr
    )
    # I used to have a try: finally: here but there seems to be a bug in python
    # which swallows the KeyboardInterrupt
    # The abandon now doesn't make too much sense
    while True:
        result_type, result_data = ldap.lo.lo.result(msgid, all=0)
        if not result_data:
            break
        if result_type is orig_ldap.RES_SEARCH_RESULT:  # pragma: no cover
            break
        else:
            if result_type is orig_ldap.RES_SEARCH_ENTRY:
                for res in result_data:
                    yield res
    ldap.lo.lo.abandon(msgid)


def module_name(module_name_):
    """Returns an initialized UMC module, identified by the given name.

   The module is a module specification according to the udm commandline.
   Example values are:
       * users/user
       * shares/share
       * groups/group

   If the module does not exist, a KeyError is raised.

   The modules are cached, so they won't be re-initialized
   in subsequent calls.
   """

    if module_name_ not in modules_by_name:
        module = univention.admin.modules.get(module_name_)
        univention.admin.modules.init(ldap, position_base_dn, module)

        modules_by_name[module_name_] = module

    return modules_by_name[module_name_]


def get_umc_admin_objects():
    """Convenience accessor for getting univention.admin.objects.

   This implements delayed importing, so the univention.* modules
   are not loaded until this function is called.
   """
    return univention.admin.objects


def umc_module_for_add(module, container_dn, superordinate=None):
    """Returns an UMC module object prepared for creating a new entry.

   The module is a module specification according to the udm commandline.
   Example values are:
       * users/user
       * shares/share
       * groups/group

   The container_dn MUST be the dn of the container (not of the object to
   be created itself!).
   """
    mod = module_name(module)

    position = position_base_dn
    position.setDn(container_dn)

    # config, ldap objects from common module
    obj = mod.object(config, ldap, position, superordinate=superordinate)
    obj.open()

    return obj


def umc_module_for_edit(module, object_dn, superordinate=None):
    """Returns an UMC module object prepared for editing an existing entry.

   The module is a module specification according to the udm commandline.
   Example values are:
       * users/user
       * shares/share
       * groups/group

   The object_dn MUST be the dn of the object itself, not the container!
   """
    mod = module_name(module)

    objects = get_umc_admin_objects()

    position = position_base_dn
    position.setDn(ldap_dn_tree_parent(object_dn))

    obj = objects.get(
        mod,
        config,
        ldap,
        position=position,
        superordinate=superordinate,
        dn=object_dn
    )
    obj.open()

    return obj


def create_containers_and_parents(container_dn):
    """Create a container and if needed the parents containers"""
    import univention.admin.uexceptions as uexcp
    assert container_dn.startswith("cn=")
    try:
        parent = ldap_dn_tree_parent(container_dn)
        obj = umc_module_for_add(
            'container/cn',
            parent
        )
        obj['name'] = container_dn.split(',')[0].split('=')[1]
        obj['description'] = "container created by import"
    except uexcp.ldapError:
        create_containers_and_parents(parent)
        obj = umc_module_for_add(
            'container/cn',
            parent
        )
        obj['name'] = container_dn.split(',')[0].split('=')[1]
        obj['description'] = "container created by import"


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
    container = 'cn=shares,ou={},{}'.format(module.params['ou'], base_dn)
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


from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
