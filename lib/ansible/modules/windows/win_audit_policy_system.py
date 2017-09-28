#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2017 Noah Sparks <nsparks@outlook.com>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: win_audit_policy_system
short_description: Used to make changes to the system wide Audit Policy.
description:
  - Used to make changes to the system wide Audit Policy.
  - See this page for in depth information U(https://technet.microsoft.com/en-us/library/cc766468(v=ws.10).aspx).
version_added: "2.5"
author:
  - Noah Sparks (@nwsparks)
options:
  restore_path:
    description:
      - Restores system audit policy settings, per-user audit policy settings for all users, and all auditing options from a file
        that is syntactically consistent with the comma-separated value (CSV) file format used by the backup option or generated from
        an auditpol /backup command.
      - If used, this parameter should be specified by itself or with I(backup_path). If other parameters are specified they will be ignored.
      - If used with I(backup_path) a backup will be taken before the restore.
      - This task will always return a changed status.
  backup_path:
    description:
      - Backs up system audit policy settings, per-user audit policy settings for all users, and all auditing options to
        a comma-separated value (CSV) text file.
      - This should define a valid filesystem path.
      - Can be defined by itself or with any other set of parameters.
  category:
    description:
      - Single string value for the category you would like to adjust the policy on.
      - Cannot be used with I(subcategory). You must define one or the other.
      - Changing this setting causes all subcategories to be adjusted to the defined I(audit_type).
  subcategory:
    description:
      - Single string value for the subcategory you would like to adjust the policy on.
      - Cannot be used with I(category). You must define one or the other.
  audit_type:
    description:
      - The type of event you would like to audit for.
    choices: [ 'success', 'failure', 'success and failure', 'none' ]
'''

EXAMPLES = r'''
- name: enable failure auditing for the subcategory "File System" and take backup
  win_audit_policy_system:
    subcategory: File System
    audit_type: failure
    backup_path: c:\auditpolicy-{{ '%Y-%m-%d' | strftime }}.csv

- name: enable all auditing types for the category "Account logon events"
  win_audit_policy_system:
    category: Account logon events
    audit_type: success and failure

- name: disable auditing for the subcategory "File System"
  win_audit_policy_system:
    subcategory: File System
    audit_type: none

- name: restore audit policy from backup
  win_audit_policy_system:
    restore_path: c:\auditpolicy_backup.csv
'''

RETURN = '''
backup_taken:
  description: tells you whether or not a backup was taken when the module is run
  returned: always
  type: boolean
  sample: true
current_audit_policy:
  description: details on the policy being targetted
  returned: always
  type: dictionary
  sample: |-
    {
      "File Share":"failure"
    }
'''
