#!/usr/bin/python
# -*- coding: UTF-8 -*-

# Copyright: (c) 2016, Adfinis SyGroup AG
# Tobias Rueetschi <tobias.ruetschi@adfinis-sygroup.ch>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: udm_user
version_added: "2.2"
author:
- Tobias Rüetschi (@keachi)
short_description: Manage posix users on a univention corporate server
description:
    - "This module allows to manage posix users on a univention corporate
       server (UCS).
       It uses the python API of the UCS to create a new object or edit it."
requirements:
    - Python >= 2.6
options:
    state:
        default: "present"
        choices: [ present, absent ]
        description:
            - Whether the user is present or not.
    username:
        required: true
        description:
            - User name
        aliases: ['name']
    firstname:
        description:
            - First name. Required if C(state=present).
    lastname:
        description:
            - Last name. Required if C(state=present).
    password:
        description:
            - Password. Required if C(state=present).
    birthday:
        description:
            - Birthday
    city:
        description:
            - City of users business address.
    country:
        description:
            - Country of users business address.
    department_number:
        description:
            - Department number of users business address.
        aliases: [ departmentNumber ]
    description:
        description:
            - Description (not gecos)
    display_name:
        description:
            - Display name (not gecos)
        aliases: [ displayName ]
    email:
        default: []
        description:
            - A list of e-mail addresses.
    employee_number:
        description:
            - Employee number
        aliases: [ employeeNumber ]
    employee_type:
        description:
            - Employee type
        aliases: [ employeeType ]
    gecos:
        description:
            - GECOS
    groups:
        default: []
        description:
            - "POSIX groups, the LDAP DNs of the groups will be found with the
               LDAP filter for each group as $GROUP:
               C((&(objectClass=posixGroup)(cn=$GROUP)))."
    home_share:
        description:
            - "Home NFS share. Must be a LDAP DN, e.g.
               C(cn=home,cn=shares,ou=school,dc=example,dc=com)."
        aliases: [ homeShare ]
    home_share_path:
        description:
            - Path to home NFS share, inside the homeShare.
        aliases: [ homeSharePath ]
    home_telephone_number:
        default: []
        description:
            - List of private telephone numbers.
        aliases: [ homeTelephoneNumber ]
    homedrive:
        description:
            - Windows home drive, e.g. C("H:").
    mail_alternative_address:
        default: []
        description:
            - List of alternative e-mail addresses.
        aliases: [ mailAlternativeAddress ]
    mail_home_server:
        description:
            - FQDN of mail server
        aliases: [ mailHomeServer ]
    mail_primary_address:
        description:
            - Primary e-mail address
        aliases: [ mailPrimaryAddress ]
    mobile_telephone_number:
        default: []
        description:
            - Mobile phone number
        aliases: [ mobileTelephoneNumber ]
    organisation:
        description:
            - Organisation
        aliases: [ organization ]
    override_pw_history:
        type: bool
        default: 'no'
        description:
            - Override password history
        aliases: [ overridePWHistory ]
    override_pw_length:
        type: bool
        default: 'no'
        description:
            - Override password check
        aliases: [ overridePWLength ]
    pager_telephonenumber:
        default: []
        description:
            - List of pager telephone numbers.
        aliases: [ pagerTelephonenumber ]
    phone:
        description:
            - List of telephone numbers.
    postcode:
        description:
            - Postal code of users business address.
    primary_group:
        default: cn=Domain Users,cn=groups,$LDAP_BASE_DN
        description:
            - Primary group. This must be the group LDAP DN.
        aliases: [ primaryGroup ]
    profilepath:
        description:
            - Windows profile directory
    pwd_change_next_login:
        choices: [ '0', '1' ]
        description:
            - Change password on next login.
        aliases: [ pwdChangeNextLogin ]
    room_number:
        description:
            - Room number of users business address.
        aliases: [ roomNumber ]
    samba_privileges:
        description:
            - "Samba privilege, like allow printer administration, do domain
               join."
        aliases: [ sambaPrivileges ]
    samba_user_workstations:
        description:
            - Allow the authentication only on this Microsoft Windows host.
        aliases: [ sambaUserWorkstations ]
    sambahome:
        description:
            - Windows home path, e.g. C('\\\\$FQDN\\$USERNAME').
    scriptpath:
        description:
            - Windows logon script.
    secretary:
        default: []
        description:
            - A list of superiors as LDAP DNs.
    serviceprovider:
        default: []
        description:
            - Enable user for the following service providers.
    shell:
        default: '/bin/bash'
        description:
            - Login shell
    street:
        description:
            - Street of users business address.
    title:
        description:
            - Title, e.g. C(Prof.).
    unixhome:
        default: '/home/$USERNAME'
        description:
            - Unix home directory
    userexpiry:
        default: Today + 1 year
        description:
            - Account expiry date, e.g. C(1999-12-31).
    position:
        default: ''
        description:
            - "Define the whole position of users object inside the LDAP tree,
               e.g. C(cn=employee,cn=users,ou=school,dc=example,dc=com)."
    update_password:
        default: always
        description:
            - "C(always) will update passwords if they differ.
               C(on_create) will only set the password for newly created users."
        version_added: "2.3"
    ou:
        default: ''
        description:
            - "Organizational Unit inside the LDAP Base DN, e.g. C(school) for
               LDAP OU C(ou=school,dc=example,dc=com)."
    subpath:
        default: 'cn=users'
        description:
            - "LDAP subpath inside the organizational unit, e.g.
               C(cn=teachers,cn=users) for LDAP container
               C(cn=teachers,cn=users,dc=example,dc=com)."
'''


EXAMPLES = '''
# Create a user on a UCS
- udm_user:
    name: FooBar
    password: secure_password
    firstname: Foo
    lastname: Bar

# Create a user with the DN
# C(uid=foo,cn=teachers,cn=users,ou=school,dc=school,dc=example,dc=com)
- udm_user:
    name: foo
    password: secure_password
    firstname: Foo
    lastname: Bar
    ou: school
    subpath: 'cn=teachers,cn=users'
# or define the position
- udm_user:
    name: foo
    password: secure_password
    firstname: Foo
    lastname: Bar
    position: 'cn=teachers,cn=users,ou=school,dc=school,dc=example,dc=com'
'''


RETURN = '''# '''

import crypt
from datetime import date, timedelta

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.univention_umc import (
    umc_module_for_add,
    umc_module_for_edit,
    ldap_search,
    base_dn,
)


def main():
    expiry = date.strftime(date.today() + timedelta(days=365), "%Y-%m-%d")
    module = AnsibleModule(
        argument_spec=dict(
            birthday=dict(default=None,
                          type='str'),
            city=dict(default=None,
                      type='str'),
            country=dict(default=None,
                         type='str'),
            department_number=dict(default=None,
                                   type='str',
                                   aliases=['departmentNumber']),
            description=dict(default=None,
                             type='str'),
            display_name=dict(default=None,
                              type='str',
                              aliases=['displayName']),
            email=dict(default=[''],
                       type='list'),
            employee_number=dict(default=None,
                                 type='str',
                                 aliases=['employeeNumber']),
            employee_type=dict(default=None,
                               type='str',
                               aliases=['employeeType']),
            firstname=dict(default=None,
                           type='str'),
            gecos=dict(default=None,
                       type='str'),
            groups=dict(default=[],
                        type='list'),
            home_share=dict(default=None,
                            type='str',
                            aliases=['homeShare']),
            home_share_path=dict(default=None,
                                 type='str',
                                 aliases=['homeSharePath']),
            home_telephone_number=dict(default=[],
                                       type='list',
                                       aliases=['homeTelephoneNumber']),
            homedrive=dict(default=None,
                           type='str'),
            lastname=dict(default=None,
                          type='str'),
            mail_alternative_address=dict(default=[],
                                          type='list',
                                          aliases=['mailAlternativeAddress']),
            mail_home_server=dict(default=None,
                                  type='str',
                                  aliases=['mailHomeServer']),
            mail_primary_address=dict(default=None,
                                      type='str',
                                      aliases=['mailPrimaryAddress']),
            mobile_telephone_number=dict(default=[],
                                         type='list',
                                         aliases=['mobileTelephoneNumber']),
            organisation=dict(default=None,
                              type='str',
                              aliases=['organization']),
            overridePWHistory=dict(default=False,
                                   type='bool',
                                   aliases=['override_pw_history']),
            overridePWLength=dict(default=False,
                                  type='bool',
                                  aliases=['override_pw_length']),
            pager_telephonenumber=dict(default=[],
                                       type='list',
                                       aliases=['pagerTelephonenumber']),
            password=dict(default=None,
                          type='str',
                          no_log=True),
            phone=dict(default=[],
                       type='list'),
            postcode=dict(default=None,
                          type='str'),
            primary_group=dict(default=None,
                               type='str',
                               aliases=['primaryGroup']),
            profilepath=dict(default=None,
                             type='str'),
            pwd_change_next_login=dict(default=None,
                                       type='str',
                                       choices=['0', '1'],
                                       aliases=['pwdChangeNextLogin']),
            room_number=dict(default=None,
                             type='str',
                             aliases=['roomNumber']),
            samba_privileges=dict(default=[],
                                  type='list',
                                  aliases=['sambaPrivileges']),
            samba_user_workstations=dict(default=[],
                                         type='list',
                                         aliases=['sambaUserWorkstations']),
            sambahome=dict(default=None,
                           type='str'),
            scriptpath=dict(default=None,
                            type='str'),
            secretary=dict(default=[],
                           type='list'),
            serviceprovider=dict(default=[''],
                                 type='list'),
            shell=dict(default='/bin/bash',
                       type='str'),
            street=dict(default=None,
                        type='str'),
            title=dict(default=None,
                       type='str'),
            unixhome=dict(default=None,
                          type='str'),
            userexpiry=dict(default=expiry,
                            type='str'),
            username=dict(required=True,
                          aliases=['name'],
                          type='str'),
            position=dict(default='',
                          type='str'),
            update_password=dict(default='always',
                                 choices=['always', 'on_create'],
                                 type='str'),
            ou=dict(default='',
                    type='str'),
            subpath=dict(default='cn=users',
                         type='str'),
            state=dict(default='present',
                       choices=['present', 'absent'],
                       type='str')
        ),
        supports_check_mode=True,
        required_if=([
            ('state', 'present', ['firstname', 'lastname', 'password'])
        ])
    )
    username = module.params['username']
    position = module.params['position']
    ou = module.params['ou']
    subpath = module.params['subpath']
    state = module.params['state']
    changed = False
    diff = None

    users = list(ldap_search(
        '(&(objectClass=posixAccount)(uid={0}))'.format(username),
        attr=['uid']
    ))
    if position != '':
        container = position
    else:
        if ou != '':
            ou = 'ou={0},'.format(ou)
        if subpath != '':
            subpath = '{0},'.format(subpath)
        container = '{0}{1}{2}'.format(subpath, ou, base_dn())
    user_dn = 'uid={0},{1}'.format(username, container)

    exists = bool(len(users))

    if state == 'present':
        try:
            if not exists:
                obj = umc_module_for_add('users/user', container)
            else:
                obj = umc_module_for_edit('users/user', user_dn)

            if module.params['displayName'] is None:
                module.params['displayName'] = '{0} {1}'.format(
                    module.params['firstname'],
                    module.params['lastname']
                )
            if module.params['unixhome'] is None:
                module.params['unixhome'] = '/home/{0}'.format(
                    module.params['username']
                )
            for k in obj.keys():
                if (k != 'password' and
                        k != 'groups' and
                        k != 'overridePWHistory' and
                        k in module.params and
                        module.params[k] is not None):
                    obj[k] = module.params[k]
            # handle some special values
            obj['e-mail'] = module.params['email']
            password = module.params['password']
            if obj['password'] is None:
                obj['password'] = password
            if module.params['update_password'] == 'always':
                old_password = obj['password'].split('}', 2)[1]
                if crypt.crypt(password, old_password) != old_password:
                    obj['overridePWHistory'] = module.params['overridePWHistory']
                    obj['overridePWLength'] = module.params['overridePWLength']
                    obj['password'] = password

            diff = obj.diff()
            if exists:
                for k in obj.keys():
                    if obj.hasChanged(k):
                        changed = True
            else:
                changed = True
            if not module.check_mode:
                if not exists:
                    obj.create()
                elif changed:
                    obj.modify()
        except Exception:
            module.fail_json(
                msg="Creating/editing user {0} in {1} failed".format(
                    username,
                    container
                )
            )
        try:
            groups = module.params['groups']
            if groups:
                filter = '(&(objectClass=posixGroup)(|(cn={0})))'.format(
                    ')(cn='.join(groups)
                )
                group_dns = list(ldap_search(filter, attr=['dn']))
                for dn in group_dns:
                    grp = umc_module_for_edit('groups/group', dn[0])
                    if user_dn not in grp['users']:
                        grp['users'].append(user_dn)
                        if not module.check_mode:
                            grp.modify()
                        changed = True
        except Exception:
            module.fail_json(
                msg="Adding groups to user {0} failed".format(username)
            )

    if state == 'absent' and exists:
        try:
            obj = umc_module_for_edit('users/user', user_dn)
            if not module.check_mode:
                obj.remove()
            changed = True
        except Exception:
            module.fail_json(
                msg="Removing user {0} failed".format(username)
            )

    module.exit_json(
        changed=changed,
        username=username,
        diff=diff,
        container=container
    )


if __name__ == '__main__':
    main()
