#!/usr/bin/python
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

# this is a windows documentation stub, actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: win_domain_group
version_added: '2.4'
short_description: creates, modifies or removes domain groups
description:
- Creates, modifies or removes groups in Active Directory.
- For local groups, use the M(win_group) module instead.
options:
  attributes:
    description:
    - A dict of custom LDAP attributes to set on the group.
    - This can be used to set custom attributes that are not exposed as module
      parameters, e.g. C(mail).
    - See the examples on how to format this parameter.
  category:
    description:
    - The category of the group, this is the value to assign to the LDAP
      C(groupType) attribute.
    - If a new group is created then C(security) will be used by default.
    choices: [ distribution, security ]
  description:
    description:
    - The value to be assigned to the LDAP C(description) attribute.
  display_name:
    description:
    - The value to assign to the LDAP C(displayName) attribute.
  domain_username:
    description:
    - The username to use when interacting with AD.
    - If this is not set then the user Ansible used to log in with will be
      used instead.
  domain_password:
    description:
    - The password for C(username).
  ignore_protection:
    description:
    - Will ignore the C(ProtectedFromAccidentalDeletion) flag when deleting or
      moving a group.
    - The module will fail if one of these actions need to occur and this value
      is set to no.
    type: bool
    default: 'no'
  managed_by:
    description:
    - The value to be assigned to the LDAP C(managedBy) attribute.
    - This value can be in the forms C(Distinguished Name), C(objectGUID),
      C(objectSid) or C(sAMAccountName), see examples for more details.
  name:
    description:
    - The name of the group to create, modify or remove.
    - This value can be in the forms C(Distinguished Name), C(objectGUID),
      C(objectSid) or C(sAMAccountName), see examples for more details.
    required: yes
  organizational_unit:
    description:
    - The full LDAP path to create or move the group to.
    - This should be the path to the parent object to create or move the group
      to.
    - See examples for details of how this path is formed.
    aliases: [ ou, path ]
  protect:
    description:
    - Will set the C(ProtectedFromAccidentalDeletion) flag based on this value.
    - This flag stops a user from deleting or moving a group to a different
      path.
    type: bool
  scope:
    description:
    - The scope of the group.
    - If C(state=present) and the group doesn't exist then this must be set.
    choices: [domainlocal, global, universal]
  state:
    description:
    - If C(state=present) this module will ensure the group is created and is
      configured accordingly.
    - If C(state=absent) this module will delete the group if it exists
    default: present
    choices: [ absent, present ]
notes:
- This must be run on a host that has the ActiveDirectory powershell module
  installed.
author:
- Jordan Borean (@jborean93)
'''

EXAMPLES = r'''
- name: ensure the group Cow exists using sAMAccountName
  win_domain_group:
    name: Cow
    scope: global
    path: OU=groups,DC=ansible,DC=local

- name: ensure the group Cow does't exist using the Distinguished Name
  win_domain_group:
    name: CN=Cow,OU=groups,DC=ansible,DC=local
    state: absent

- name: delete group ignoring the protection flag
  win_domain_group:
    name: Cow
    state: absent
    ignore_protection: yes

- name: create group with delete protection enabled and custom attributes
  win_domain_group:
    name: Ansible Users
    scope: domainlocal
    category: security
    attributes:
      mail: helpdesk@ansible.com
      wWWHomePage: www.ansible.com
    ignore_protection: yes

- name: change the OU of a group using the SID and ignore the protection flag
  win_domain_group:
    name: S-1-5-21-2171456218-3732823212-122182344-1189
    scope: global
    organizational_unit: OU=groups,DC=ansible,DC=local
    ignore_protection: True

- name: add managed_by user
  win_domain_group:
    name: Group Name Here
    managed_by: Domain Admins
'''

RETURN = r'''
attributes:
  description: Custom attributes that were set by the module. This does not
    show all the custom attributes rather just the ones that were set by the
    module.
  returned: group exists and attributes are set on the module invocation
  type: dict
  sample:
    mail: 'helpdesk@ansible.com'
    wWWHomePage: 'www.ansible.com'
canonical_name:
  description: The canonical name of the group.
  returned: group exists
  type: string
  sample: ansible.local/groups/Cow
category:
  description: The Group type value of the group, i.e. Security or Distribution.
  returned: group exists
  type: string
  sample: Security
description:
  description: The Description of the group.
  returned: group exists
  type: string
  sample: Group Description
display_name:
  description: The Display name of the group.
  returned: group exists
  type: string
  sample: Users who connect through RDP
distinguished_name:
  description: The full Distinguished Name of the group.
  returned: group exists
  type: string
  sample: CN=Cow,OU=groups,DC=ansible,DC=local
group_scope:
  description: The Group scope value of the group.
  returned: group exists
  type: string
  sample: Universal
guid:
  description: The guid of the group.
  returned: group exists
  type: string
  sample: 512a9adb-3fc0-4a26-9df0-e6ea1740cf45
managed_by:
  description: The full Distinguished Name of the AD object that is set on the
    managedBy attribute.
  returned: group exists
  type: string
  sample: CN=Domain Admins,CN=Users,DC=ansible,DC=local
name:
  description: The name of the group.
  returned: group exists
  type: string
  sample: Cow
protected_from_accidental_deletion:
  description: Whether the group is protected from accidental deletion.
  returned: group exists
  type: bool
  sample: True
sid:
  description: The Security ID of the group.
  returned: group exists
  type: string
  sample: S-1-5-21-2171456218-3732823212-122182344-1189
'''
