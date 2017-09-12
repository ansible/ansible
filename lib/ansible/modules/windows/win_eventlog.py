#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Andrew Saraceni <andrew.saraceni@gmail.com>
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
    required: true
  state:
    description:
      - Desired state of the log and/or sources.
      - When C(sources) is populated, state is checked for sources.
      - When C(sources) is not populated, state is checked for the specified log itself.
      - If C(state) is C(clear), event log entries are cleared for the target log.
    choices:
      - present
      - clear
      - absent
    default: present
  sources:
    description:
      - A list of one or more sources to ensure are present/absent in the log.
      - When C(category_file), C(message_file) and/or C(parameter_file) are specified,
        these values are applied across all sources.
  category_file:
    description:
      - For one or more sources specified, the path to a custom category resource file.
  message_file:
    description:
      - For one or more sources specified, the path to a custom event message resource file.
  parameter_file:
    description:
      - For one or more sources specified, the path to a custom parameter resource file.
  maximum_size:
    description:
      - The maximum size of the event log.
      - Value must be between 64KB and 4GB, and divisible by 64KB.
      - Size can be specified in KB, MB or GB (e.g. 128KB, 16MB, 2.5GB).
  overflow_action:
    description:
      - The action for the log to take once it reaches its maximum size.
      - For C(OverwriteOlder), new log entries overwrite those older than the C(retention_days) value.
      - For C(OverwriteAsNeeded), each new entry overwrites the oldest entry.
      - For C(DoNotOverwrite), all existing entries are kept and new entries are not retained.
    choices:
      - OverwriteOlder
      - OverwriteAsNeeded
      - DoNotOverwrite
  retention_days:
    description:
      - The minimum number of days event entries must remain in the log.
      - This option is only used when C(overflow_action) is C(OverwriteOlder).
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
    type: string
    sample: MyNewLog
exists:
    description: Whether the event log exists or not.
    returned: success
    type: boolean
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
    type: string
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
