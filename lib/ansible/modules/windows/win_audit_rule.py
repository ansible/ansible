#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Noah Sparks <nsparks@outlook.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: win_audit_rule
short_description: Adds an audit rule to files, folders, or registry keys
description:
  - Used to apply audit rules to files, folders or registry keys.
  - Once applied, it will begin recording the user who performed the operation defined into the Security
    Log in the Event viewer.
version_added: "2.5"
author:
  - Noah Sparks (@nwsparks)
options:
  path:
    description:
      - Path to the file, folder, or registry key.
      - Registry paths should be in Powershell format, beginning with an abbreviation for the root
        'hklm:\software'.
    required: true
    aliases: [ dest, destination ]
  identity_reference:
    description:
      - The user or group to adjust rules for.
    required: true
  rights:
    description:
      - Comma seperated list of the rights desired. Only required for adding a rule.
      - If C(path) is a file or directory, rights can be any right under MSDN
        FileSystemRights U(https://msdn.microsoft.com/en-us/library/system.security.accesscontrol.filesystemrights(v=vs.110).aspx).
      - If C(path) is a registry key, rights can be any right under MSDN
        RegistryRights U(https://msdn.microsoft.com/en-us/library/system.security.accesscontrol.registryrights(v=vs.110).aspx).
    required: true
  inheritance_flags:
    description:
      - Defines what objects inside of a folder will inherit the settings.
      - For more information on the choices see MSDN PropagationFlags enumeration
        at U(https://msdn.microsoft.com/en-us/library/system.security.accesscontrol.inheritanceflags(v=vs.110).aspx).
    default: "ContainerInherit,ObjectInherit"
    choices: [ ContainerInherit, ObjectInherit ]
  propagation_flags:
    description:
      - Propagation flag on the audit rules.
      - For more information on the choices see MSDN PropagationFlags enumeration
        at U(https://msdn.microsoft.com/en-us/library/system.security.accesscontrol.propagationflags(v=vs.110).aspx).
    default: "None"
    choices: [ None, InherityOnly, NoPropagateInherit ]
  audit_flags:
    description:
      - Defines whether to log on failure, success, or both.
      - To log both define as comma seperated list "Success, Failure".
    required: true
    choices: [ Success, Failure ]
  state:
    description:
      - Whether the rule should be present or absent.
      - For absent, only path, identity_reference, and state are required.
    default: present
    choices: [ present, absent ]
'''

EXAMPLES = r'''
- name: add filesystem audit rule
  win_audit_rule:
    path: 'c:\inetpub\wwwroot\website'
    identity_reference: 'BUILTIN\Users'
    rights: 'write,delete,changepermissions'
    audit_flags: 'success,failure'
    inheritance_flags: 'ContainerInherit,ObjectInherit'

- name: add registry audit rule
  win_audit_rule:
    path: 'hklm:\software'
    identity_reference: 'BUILTIN\Users'
    rights: 'delete'
    audit_flags: 'success'

- name: remove filesystem audit rule
  win_audit_rule:
    path: 'c:\inetpub\wwwroot\website'
    identity_reference: 'BUILTIN\Users'
    state: absent

- name: remove registry audit rule
  win_audit_rule:
    path: 'hklm:\software'
    identity_reference: 'BUILTIN\Users'
    state: absent
'''

RETURN = r'''
current_audit_rules:
  description:
    - The current rules on the defined I(path)
    - Will return "No audit rules defined on I(path)"
  returned: always
  type: dictionary
  sample: |
    {
      "audit_flags": "Success",
      "identity_reference": "Everyone",
      "inheritance_flags": "False",
      "is_inherited": "False",
      "propagation_flags": "None",
      "rights": "Delete"
    }
'''
