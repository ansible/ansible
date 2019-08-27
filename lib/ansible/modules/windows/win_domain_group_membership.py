#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Andrew Saraceni <andrew.saraceni@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_domain_group_membership
version_added: "2.8"
short_description: Manage Windows domain group membership
description:
     - Allows the addition and removal of domain users
       and domain groups from/to a domain group.
options:
  name:
    description:
      - Name of the domain group to manage membership on.
    type: str
    required: yes
  members:
    description:
      - A list of members to ensure are present/absent from the group.
      - The given names must be a SamAccountName of a user, group, service account, or computer.
      - For computers, you must add "$" after the name; for example, to add "Mycomputer" to a group, use "Mycomputer$" as the member.
    type: list
    required: yes
  state:
    description:
      - Desired state of the members in the group.
      - When C(state) is C(pure), only the members specified will exist,
        and all other existing members not specified are removed.
    type: str
    choices: [ absent, present, pure ]
    default: present
  domain_username:
    description:
    - The username to use when interacting with AD.
    - If this is not set then the user Ansible used to log in with will be
      used instead when using CredSSP or Kerberos with credential delegation.
    type: str
  domain_password:
    description:
    - The password for I(username).
    type: str
  domain_server:
    description:
    - Specifies the Active Directory Domain Services instance to connect to.
    - Can be in the form of an FQDN or NetBIOS name.
    - If not specified then the value is based on the domain of the computer
      running PowerShell.
    type: str
notes:
- This must be run on a host that has the ActiveDirectory powershell module installed.
seealso:
- module: win_domain_user
- module: win_domain_group
author:
    - Marius Rieder (@jiuka)
'''

EXAMPLES = r'''
- name: Add a domain user/group to a domain group
  win_domain_group_membership:
    name: Foo
    members:
      - Bar
    state: present

- name: Remove a domain user/group from a domain group
  win_domain_group_membership:
    name: Foo
    members:
      - Bar
    state: absent

- name: Ensure only a domain user/group exists in a domain group
  win_domain_group_membership:
    name: Foo
    members:
      - Bar
    state: pure

- name: Add a computer to a domain group
  win_domain_group_membership:
    name: Foo
    members:
      - DESKTOP$
    state: present
'''

RETURN = r'''
name:
    description: The name of the target domain group.
    returned: always
    type: str
    sample: Domain-Admins
added:
    description: A list of members added when C(state) is C(present) or
      C(pure); this is empty if no members are added.
    returned: success and C(state) is C(present) or C(pure)
    type: list
    sample: ["UserName", "GroupName"]
removed:
    description: A list of members removed when C(state) is C(absent) or
      C(pure); this is empty if no members are removed.
    returned: success and C(state) is C(absent) or C(pure)
    type: list
    sample: ["UserName", "GroupName"]
members:
    description: A list of all domain group members at completion; this is empty
      if the group contains no members.
    returned: success
    type: list
    sample: ["UserName", "GroupName"]
'''
