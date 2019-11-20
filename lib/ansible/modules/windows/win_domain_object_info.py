#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Shachaf Goldstein <shachaf.gold@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_domain_object_info
version_added: '2.10'
short_description: Retrive info regarding domain objects of all kinds
description:
   - With the module you can retrieve and output detailed information about all kinds of AD objects.
options:
  filter:
    description:
      - Powershell style filter.
    type: str
  identity:
    description:
      - Identity parameter used to find the Object in Active Directory.
      - This value can be in the forms C(Distinguished Name), C(objectGUID).
    type: str
  includeDeletedObjects:
    description:
      - Should deleted objects be included.
    type: bool
    default: false
  ldapFilter:
    description:
      - LDAP style filter.
    type: str
  searchScope:
    description:
      - The scope of the search.
      - A Base query searches only the current path or object.
      - A OneLevel query searches the immediate children of that path or object.
      - A Subtree query searches the current path or object and all children of that path or object.
    type: str
    default: Subtree
    choices:
      - Base
      - OneLevel
      - Subtree
  searchBase:
    description:
      - Where in the Active Directory should the search begin.
    type: str
  jsonDepth:
    description:
      - The number of levels into the object properties that should be parsed to JSON.
    type: int
    default: 3
  properties:
    description:
      - A list of properties to retrive.
    type: list
    elements: str
    default: "*"
  username:
    description:
      - The username to use when interacting with AD.
      - If this is not set then the user Ansible used to log in with will be
        used instead when using CredSSP or Kerberos with credential delegation.
    type: str
    aliases: 
      - domain_username
  password:
    description:
      - The password for I(username).
    type: str
    aliases: 
      - domain_password
  server:
    description:
      - Specifies the Active Directory Domain Services instance to connect to.
      - Can be in the form of an FQDN or NetBIOS name.
      - If not specified then the value is based on the domain of the computer
        running PowerShell.
    type: str
    aliases: 
      - domain_server
author:
  - Shachaf Goldstein (@Shachaf92)
'''

EXAMPLES = r'''
- name: Get ALL objects
  win_domain_object_info:
    filter: "*"

- name: Get by filter
  win_domain_object_info:
    filter: "SAMAccountName -eq 'test*'"
  register: filtered_result

- name: Output first result
  debug:
    var: filtered_result.objects[0]

- name: Get by filter in a specific OU
  win_domain_object_info:
    filter: "SAMAccountName -eq 'test*'"
    searchBase: "OU=Users,DC=contoso,DC=com"
  register: filtered_result_ou

- name: Output first result
  debug:
    var: filtered_result_ou.objects[0]
'''

RETURN = r'''
objects:
    description: List of retrived objects, each formatted to JSON according to the I(jsonDepth) option.
    returned: always
    type: list
    contains: JSON varies according to object type.
'''