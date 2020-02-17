#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_domain_object_info
version_added: '2.10'
short_description: Gather information an Active Directory object
description:
- Gather information about multiple Active Directory object(s).
options:
  domain_password:
    description:
    - The password for C(domain_username).
    type: str
  domain_server:
    description:
    - Specified the Active Directory Domain Services instance to connect to.
    - Can be in the form of an FQDN or NetBIOS name.
    - If not specified then the value is based on the default domain of the computer running PowerShell.
    type: str
  domain_username:
    description:
    - The username to use when interacting with AD.
    - If this is not set then the user that is used for authentication will be the connection user.
    - Ansible will be unable to use the connection user unless auth is Kerberos with credential delegation or CredSSP,
      or become is used on the task.
    type: str
  filter:
    description:
    - Specifies a query string using the PowerShell Expression Language syntax.
    - This follows the same rules and formatting as the C(-Filter) parameter for the PowerShell AD cmdlets exception
      there is no variable substitutions.
    - This is mutually exclusive with I(identity) and I(ldap_filter).
    type: str
  identity:
    description:
    - Specifies a single Active Directory object by its distinguished name or its object GUID.
    - This is mutually exclusive with I(filter) and I(ldap_filter).
    - This cannot be used with either the I(search_base) or I(search_scope) options.
    type: str
  include_deleted:
    description:
    - Also search for deleted Active Directory objects.
    default: no
    type: bool
  ldap_filter:
    description:
    - Like I(filter) but this is a tradiitional LDAP query string to filter the objects to return.
    - This is mutually exclusive with I(filter) and I(identity).
    type: str
  properties:
    description:
    - A list of properties to return.
    - If a property is C(*), all properties that have a set value on the AD object will be returned.
    - If a property is valid on the object but not set, it is only returned if defined explicitly in this option list.
    - The properties C(DistinguishedName), C(Name), C(ObjectClass), and C(ObjectGUID) are always returned.
    - Specifying multiple properties can have a performance impact, it is best to only return what is needed.
    - If an invalid property is specified then the module will display a warning for each object it is invalid on.
    type: list
    elements: str
  search_base:
    description:
    - Specify the Active Directory path to search for objects in.
    - This cannot be set with I(identity).
    - By default the search base is the default naming context of the target AD instance which is the DN returned by
      "(Get-ADRootDSE).defaultNamingContext".
    type: str
  search_scope:
    description:
    - Specify the scope of when searching for an object in the C(search_base).
    - C(base) will limit the search to the base object so the maximum number of objects returned is always one. This
      will not search any objects inside a container..
    - C(one_level) will search the current path and any immediate objects in that path.
    - C(subtree) will search the current path and all objects of that path recursively.
    - This cannot be set with I(identity).
    choices:
    - base
    - one_level
    - subtree
    type: str
notes:
- The C(sAMAccountType_AnsibleFlags) and C(userAccountControl_AnsibleFlags) return property is something set by the
  module itself as an easy way to view what those flags represent. These properties cannot be used as part of the
  I(filter) or I(ldap_filter) and are automatically added if those properties were requested.
author:
- Jordan Borean (@jborean93)
'''

EXAMPLES = r'''
- name: Get all properties for the specified account using its DistinguishedName
  win_domain_object_info:
    identity: CN=Username,CN=Users,DC=domain,DC=com
    properties: '*'

- name: Get the SID for all user accounts as a filter
  win_domain_object_info:
    filter: ObjectClass -eq 'user' -and objectCategory -eq 'Person'
    properties:
    - objectSid

- name: Get the SID for all user accounts as a LDAP filter
  win_domain_object_info:
    ldap_filter: (&(objectClass=user)(objectCategory=Person))
    properties:
    - objectSid

- name: Search all computer accounts in a specific path that were added after February 1st
  win_domain_object_info:
    filter: objectClass -eq 'computer' -and whenCreated -gt '20200201000000.0Z'
    properties: '*'
    search_scope: one_level
    search_base: CN=Computers,DC=domain,DC=com
'''

RETURN = r'''
objects:
  description:
  - A list of dictionaries that are the Active Directory objects found and the properties requested.
  - The dict's keys are the property name and the value is the value for the property.
  - All date properties are return in the ISO 8601 format in the UTC timezone.
  - All SID properties are returned as a dict with the keys C(Sid) as the SID string and C(Name) as the translated SID
    account name.
  - All byte properties are returned as a base64 string.
  - All security descriptor properties are returned as the SDDL string of that descriptor.
  - The properties C(DistinguishedName), C(Name), C(ObjectClass), and C(ObjectGUID) are always returned.
  returned: always
  type: list
  elements: dict
  sample: |
    [{
      "accountExpires": 0,
      "adminCount": 1,
      "CanonicalName": "domain.com/Users/Administrator",
      "CN": "Administrator",
      "Created": "2020-01-13T09:03:22.0000000Z",
      "Description": "Built-in account for administering computer/domain",
      "DisplayName": null,
      "DistinguishedName": "CN=Administrator,CN=Users,DC=domain,DC=com",
      "memberOf": [
        "CN=Group Policy Creator Owners,CN=Users,DC=domain,DC=com",
        "CN=Domain Admins",CN=Users,DC=domain,DC=com"
      ],
      "Name": "Administrator",
      "nTSecurityDescriptor": "O:DAG:DAD:PAI(A;;LCRPLORC;;;AU)(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;SY)(A;;CCDCLCSWRPWPLOCRSDRCWDWO;;;BA)",
      "ObjectCategory": "CN=Person,CN=Schema,CN=Configuration,DC=domain,DC=com",
      "ObjectClass": "user",
      "ObjectGUID": "c8c6569e-4688-4f3c-8462-afc4ff60817b",
      "objectSid": {
        "Sid": "S-1-5-21-2959096244-3298113601-420842770-500",
        "Name": "DOMAIN\Administrator"
      },
      "sAMAccountName": "Administrator",
    }]
'''
