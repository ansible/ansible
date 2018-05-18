#!/usr/bin/python
# -*- coding: UTF-8 -*-

# Copyright (c) 2016, Adfinis SyGroup AG
# Tobias Rueetschi <tobias.ruetschi@adfinis-sygroup.ch>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: udm_group
version_added: "2.2"
author: "Tobias Rueetschi (@2-B)"
short_description: Manage of the posix group
description:
    - "This module allows to manage user groups on a univention corporate server (UCS).
       It uses the python API of the UCS to create a new object or edit it."
requirements:
    - Python >= 2.6
options:
    state:
        required: false
        default: "present"
        choices: [ present, absent ]
        description:
            - Whether the group is present or not.
    name:
        required: true
        description:
            - Name of the posix group.
    description:
        required: false
        description:
            - Group description.
    position:
        required: false
        description:
            - define the whole ldap position of the group, e.g.
              C(cn=g123m-1A,cn=classes,cn=schueler,cn=groups,ou=schule,dc=example,dc=com).
    ou:
        required: false
        description:
            - LDAP OU, e.g. school for LDAP OU C(ou=school,dc=example,dc=com).
    subpath:
        required: false
        description:
            - Subpath inside the OU, e.g. C(cn=classes,cn=students,cn=groups).
'''


EXAMPLES = '''
# Create a POSIX group
- udm_group:
    name: g123m-1A

# Create a POSIX group with the exact DN
# C(cn=g123m-1A,cn=classes,cn=students,cn=groups,ou=school,dc=school,dc=example,dc=com)
- udm_group:
    name: g123m-1A
    subpath: 'cn=classes,cn=students,cn=groups'
    ou: school
# or
- udm_group:
    name: g123m-1A
    position: 'cn=classes,cn=students,cn=groups,ou=school,dc=school,dc=example,dc=com'
'''


RETURN = '''# '''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.univention_umc import (
    umc_module_for_add,
    umc_module_for_edit,
    ldap_search,
    base_dn,
)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True,
                      type='str'),
            description=dict(default=None,
                             type='str'),
            position=dict(default='',
                          type='str'),
            ou=dict(default='',
                    type='str'),
            subpath=dict(default='cn=groups',
                         type='str'),
            state=dict(default='present',
                       choices=['present', 'absent'],
                       type='str')
        ),
        supports_check_mode=True
    )
    name = module.params['name']
    description = module.params['description']
    position = module.params['position']
    ou = module.params['ou']
    subpath = module.params['subpath']
    state = module.params['state']
    changed = False

    groups = list(ldap_search(
        '(&(objectClass=posixGroup)(cn={}))'.format(name),
        attr=['cn']
    ))
    if position != '':
        container = position
    else:
        if ou != '':
            ou = 'ou={},'.format(ou)
        if subpath != '':
            subpath = '{},'.format(subpath)
        container = '{}{}{}'.format(subpath, ou, base_dn())
    group_dn = 'cn={},{}'.format(name, container)

    exists = bool(len(groups))

    if state == 'present':
        try:
            if not exists:
                grp = umc_module_for_add('groups/group', container)
            else:
                grp = umc_module_for_edit('groups/group', group_dn)
            grp['name'] = name
            grp['description'] = description
            diff = grp.diff()
            changed = grp.diff() != []
            if not module.check_mode:
                if not exists:
                    grp.create()
                else:
                    grp.modify()
        except:
            module.fail_json(
                msg="Creating/editing group {} in {} failed".format(name, container)
            )

    if state == 'absent' and exists:
        try:
            grp = umc_module_for_edit('groups/group', group_dn)
            if not module.check_mode:
                grp.remove()
            changed = True
        except:
            module.fail_json(
                msg="Removing group {} failed".format(name)
            )

    module.exit_json(
        changed=changed,
        name=name,
        diff=diff,
        container=container
    )


if __name__ == '__main__':
    main()
