#!/usr/bin/python
# -*- coding: utf-8 -*-
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

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: win_domain_user
version_added: "2.4"
short_description: Manages Windows Active Directory user accounts
description:
     - Manages Windows Active Directory user accounts

options:
  name:
    description:
      - Name of the user to create, remove or modify.
    required: true

  state:
    description:
      - When C(present), creates or updates the user account.  When C(absent),
        removes the user account if it exists.  When C(query),
        retrieves the user account details without making any changes.
    required: false
    choices:
      - present
      - absent
      - query
    default: present

  enabled:
    description:
      - C(yes) will enable the user account. C(no) will disable the account.
    required: false
    choices:
      - yes
      - no
    default: yes

  account_locked:
    description:
      - C(no) will unlock the user account if locked.
    required: false
    choices: [ 'no' ]
    default: null

  description:
    description:
      - Description of the user
    required: false
    default: null

  groups:
    description:
      - Adds or removes the user from this list of groups,
        depending on the value of I(groups_action). To remove all but the
        Principal Group, set C(groups=<principal group name>) and
        I(groups_action=replace). Note that users cannot be removed from
        their principal group (for example, "Domain Users").
    required: false

  groups_action:
    description:
      - If C(replace), the user is added as a member of each group in
        I(groups) and removed from any other groups.  If C(add), the user is
        added to each group in I(groups) where not already a member.  If
        C(remove), the user is removed from each group in I(groups).
    required: false
    choices: [ 'replace', 'add', 'remove' ]
    default: replace

  password:
    description:
      - Optionally set the user's password to this (plain text) value. In order
        to enable an account - I(enabled) - a password must already be
        configured on the account, or you must provide a password here.
    required: false
    default: null

  update_password:
    description:
      - C(always) will update passwords if they differ.  C(on_create) will
        only set the password for newly created users. Note that C(always) will
        always report an Ansible status of 'changed' because we cannot
        determine whether the new password differs from the old password.
    required: false
    choices: [ 'always', 'on_create' ]
    default: always

  password_expired:
    description:
      - C(yes) will require the user to change their password at next login.
        C(no) will clear the expired password flag. This is mutually exclusive
        with I(password_never_expires).
    required: false
    choices: [ 'yes', 'no' ]
    default: null

  password_never_expires:
    description:
      - C(yes) will set the password to never expire.  C(no) will allow the
        password to expire. This is mutually exclusive with I(password_expired)
    required: false
    choices: [ 'yes', 'no' ]
    default: null

  user_cannot_change_password:
    description:
      - C(yes) will prevent the user from changing their password.  C(no) will
        allow the user to change their password.
    required: false
    choices: [ 'yes', 'no' ]
    default: null

  firstname:
    description:
      - Configures the user's first name (given name)
    required: false
    default: null

  surname:
    description:
      - Configures the user's last name (surname)
    required: false
    default: null

  company:
    description:
      - Configures the user's company name
    required: false
    default: null

  upn:
    description:
      - Configures the User Principal Name (UPN) for the account. This is not
        required, but is best practice to configure for modern versions of
        Active Directory. The format is "<username>@<domain>".
    required: false
    default: null

  email:
    description:
      - Configures the user's email address. This is a record in AD and does
        not do anything to configure any email servers or systems.
    required: false
    default: null

  street:
    description:
      - Configures the user's street address
    required: false
    default: null

  city:
    description:
      - Configures the user's city
    required: false
    default: null

  state_province:
    description:
      - Configures the user's state or province
    required: false
    default: null

  postal_code:
    description:
      - Configures the user's postal code / zip code
    required: false
    default: null

  country:
    description:
      - Configures the user's country code. Note that this is a two-character
        ISO 3166 code.
    required: false
    default: null

  path:
    description:
      - Container or OU for the new user; if you do not specify this, the
        user will be placed in the default container for users in the domain.
        Setting the path is only available when a new user is created;
        if you specify a path on an existing user, the user's path will not
        be updated - you must delete (e.g., state=absent) the user and
        then re-add the user with the appropriate path.
    required: false
    default: null

author:
    - "Nick Chandler (@nwchandler)"
'''

EXAMPLES = r'''
- name: Ensure user bob is present with address information
  win_domain_user:
    name: bob
    password: B0bP4ssw0rd
    state: present
    groups:
      - Domain Admins
    street: 123 4th St.
    city: Sometown
    state_province: IN
    postal_code: 12345
    country: US

- name: Ensure user bob is present in OU ou=test,dc=domain,dc=local
  win_domain_user:
    name: bob
    password: B0bP4ssw0rd
    state: present
    path: ou=test,dc=domain,dc=local
    groups:
      - Domain Admins

- name: Ensure user bob is absent
  win_domain_user:
    name: bob
    state: absent
'''

RETURN = r'''
account_locked:
    description: 'True' if the account is locked
    returned: always
    type: boolean
    sample: false
changed:
    description: 'True' if the account changed during execution
    returned: always
    type: boolean
    sample: false
city:
    description: The user's city
    returned: always
    type: string
    sample: Indianapolis
company:
    description: The user's company
    returned: always
    type: string
    sample: RedHat
country:
    description: The user's country
    returned: always
    type: string
    sample: US
description:
    description: A description of the account
    returned: always
    type: string
    sample: Server Administrator
distinguished_name:
    description: DN of the user account
    returned: always
    type: string
    sample: "CN=nick,OU=test,DC=domain,DC=local"
email:
    description: The user's email address
    returned: always
    type: string
    sample: nick@domain.local
enabled:
    description: 'True' if the account is enabled and 'False if disabled'
    returned: always
    type: string
    sample: true
firstname:
    description: The user's first name
    returned: always
    type: string
    sample: Nick
groups:
    description: AD Groups to which the account belongs
    returned: always
    type: list
    sample: [ "Domain Admins", "Domain Users" ]
msg:
    description: Summary message of whether the user is present or absent
    returned: always
    type: string
    sample: "User 'nick' is present"
name:
    description: The username on the account
    returned: always
    type: string
    sample: nick
password_expired:
    description: 'True' if the account password has expired
    returned: always
    type: boolean
    sample: false
password_updated:
    description: 'True' if the password changed during this execution
    returned: always
    type: boolean
    sample: true
postal_code:
    description: The user's postal code / zip code
    returned: always
    type: string
    sample: 46033
sid:
    description: The SID of the account
    returned: always
    type: string
    sample: S-1-5-21-2752426336-228313920-2202711348-1175
state:
    description: The state of the user account
    returned: always
    type: string
    sample: present
state_province:
    description: The user's state or province
    returned: always
    type: string
    sample: IN
street:
    description: The user's street address
    returned: always
    type: string
    sample: 123 4th St.
surname:
    description: The user's last name / surname
    returned: always
    type: string
    sample: Doe
upn:
    description: The User Principal Name of the account
    returned: always
    type: string
    sample: nick@domain.local
user_cannot_change_password:
    description: 'True' if the user is not allowed to change his/her password
    returned: always
    type: string
    sample: false
'''
