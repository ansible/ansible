#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Andrew Saraceni <andrew.saraceni@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_eventlog
version_added: "2.4"
short_description: Manage Windows event logs
description:
     - Allows the addition, clearing and removal of local Windows event logs,
       and the creation and removal of sources from a given event log.  Also
       allows the specification of settings per log and source.
options:
  name:
    description:
      - Name of the event log to manage.
    type: str
    required: yes
  state:
    description:
      - Desired state of the log and/or sources.
      - When C(sources) is populated, state is checked for sources.
      - When C(sources) is not populated, state is checked for the specified log itself.
      - If C(state) is C(clear), event log entries are cleared for the target log.
    type: str
    choices: [ absent, clear, present ]
    default: present
  sources:
    description:
      - A list of one or more sources to ensure are present/absent in the log.
      - When C(category_file), C(message_file) and/or C(parameter_file) are specified,
        these values are applied across all sources.
    type: list
  category_file:
    description:
      - For one or more sources specified, the path to a custom category resource file.
    type: path
  message_file:
    description:
      - For one or more sources specified, the path to a custom event message resource file.
    type: path
  parameter_file:
    description:
      - For one or more sources specified, the path to a custom parameter resource file.
    type: path
  maximum_size:
    description:
      - The maximum size of the event log.
      - Value must be between 64KB and 4GB, and divisible by 64KB.
      - Size can be specified in KB, MB or GB (e.g. 128KB, 16MB, 2.5GB).
    type: str
  overflow_action:
    description:
      - The action for the log to take once it reaches its maximum size.
      - For C(DoNotOverwrite), all existing entries are kept and new entries are not retained.
      - For C(OverwriteAsNeeded), each new entry overwrites the oldest entry.
      - For C(OverwriteOlder), new log entries overwrite those older than the C(retention_days) value.
    type: str
    choices: [ DoNotOverwrite, OverwriteAsNeeded, OverwriteOlder ]
  retention_days:
    description:
      - The minimum number of days event entries must remain in the log.
      - This option is only used when C(overflow_action) is C(OverwriteOlder).
    type: int
seealso:
- module: win_eventlog_entry
author:
    - Andrew Saraceni (@andrewsaraceni)
'''

EXAMPLES = r'''
- name: Add a new event log with two custom sources
  win_eventlog:
    name: MyNewLog
    sources:
      - NewLogSource1
      - NewLogSource2
    state: present

- name: Change the category and message resource files used for NewLogSource1
  win_eventlog:
    name: MyNewLog
    sources:
      - NewLogSource1
    category_file: C:\NewApp\CustomCategories.dll
    message_file: C:\NewApp\CustomMessages.dll
    state: present

- name: Change the maximum size and overflow action for MyNewLog
  win_eventlog:
    name: MyNewLog
    maximum_size: 16MB
    overflow_action: DoNotOverwrite
    state: present

- name: Clear event entries for MyNewLog
  win_eventlog:
    name: MyNewLog
    state: clear

- name: Remove NewLogSource2 from MyNewLog
  win_eventlog:
    name: MyNewLog
    sources:
      - NewLogSource2
    state: absent

- name: Remove MyNewLog and all remaining sources
  win_eventlog:
    name: MyNewLog
    state: absent
'''

RETURN = r'''
name:
    description: The name of the event log.
    returned: always
    type: str
    sample: MyNewLog
exists:
    description: Whether the event log exists or not.
    returned: success
    type: bool
    sample: true
entries:
    description: The count of entries present in the event log.
    returned: success
    type: int
    sample: 50
maximum_size_kb:
    description: Maximum size of the log in KB.
    returned: success
    type: int
    sample: 512
overflow_action:
    description: The action the log takes once it reaches its maximum size.
    returned: success
    type: str
    sample: OverwriteOlder
retention_days:
    description: The minimum number of days entries are retained in the log.
    returned: success
    type: int
    sample: 7
sources:
    description: A list of the current sources for the log.
    returned: success
    type: list
    sample: ["MyNewLog", "NewLogSource1", "NewLogSource2"]
sources_changed:
    description: A list of sources changed (e.g. re/created, removed) for the log;
      this is empty if no sources are changed.
    returned: always
    type: list
    sample: ["NewLogSource2"]
'''
