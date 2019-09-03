#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage Check Point Firewall (c) 2019
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
#

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: cp_mgmt_time
short_description: Manages time objects on Check Point over Web Services API
description:
  - Manages time objects on Check Point devices including creating, updating and removing objects.
  - All operations are performed over Web Services API.
version_added: "2.9"
author: "Or Soffer (@chkp-orso)"
options:
  name:
    description:
      - Object name.
    type: str
    required: True
  end:
    description:
      - End time. Note, Each gateway may interpret this time differently according to its time zone.
    type: dict
    suboptions:
      date:
        description:
          - Date in format dd-MMM-yyyy.
        type: str
      iso_8601:
        description:
          - Date and time represented in international ISO 8601 format. Time zone information is ignored.
        type: str
      posix:
        description:
          - Number of milliseconds that have elapsed since 00,00,00, 1 January 1970.
        type: int
      time:
        description:
          - Time in format HH,mm.
        type: str
  end_never:
    description:
      - End never.
    type: bool
  hours_ranges:
    description:
      - Hours recurrence. Note, Each gateway may interpret this time differently according to its time zone.
    type: list
    suboptions:
      enabled:
        description:
          - Is hour range enabled.
        type: bool
      from:
        description:
          - Time in format HH,MM.
        type: str
      index:
        description:
          - Hour range index.
        type: int
      to:
        description:
          - Time in format HH,MM.
        type: str
  start:
    description:
      - Starting time. Note, Each gateway may interpret this time differently according to its time zone.
    type: dict
    suboptions:
      date:
        description:
          - Date in format dd-MMM-yyyy.
        type: str
      iso_8601:
        description:
          - Date and time represented in international ISO 8601 format. Time zone information is ignored.
        type: str
      posix:
        description:
          - Number of milliseconds that have elapsed since 00,00,00, 1 January 1970.
        type: int
      time:
        description:
          - Time in format HH,mm.
        type: str
  start_now:
    description:
      - Start immediately.
    type: bool
  tags:
    description:
      - Collection of tag identifiers.
    type: list
  recurrence:
    description:
      - Days recurrence.
    type: dict
    suboptions:
      days:
        description:
          - Valid on specific days. Multiple options, support range of days in months. Example,["1","3","9-20"].
        type: list
      month:
        description:
          - Valid on month. Example, "1", "2","12","Any".
        type: str
      pattern:
        description:
          - Valid on "Daily", "Weekly", "Monthly" base.
        type: str
      weekdays:
        description:
          - Valid on weekdays. Example, "Sun", "Mon"..."Sat".
        type: list
  color:
    description:
      - Color of the object. Should be one of existing colors.
    type: str
    choices: ['aquamarine', 'black', 'blue', 'crete blue', 'burlywood', 'cyan', 'dark green', 'khaki', 'orchid', 'dark orange', 'dark sea green',
             'pink', 'turquoise', 'dark blue', 'firebrick', 'brown', 'forest green', 'gold', 'dark gold', 'gray', 'dark gray', 'light green', 'lemon chiffon',
             'coral', 'sea green', 'sky blue', 'magenta', 'purple', 'slate blue', 'violet red', 'navy blue', 'olive', 'orange', 'red', 'sienna', 'yellow']
  comments:
    description:
      - Comments string.
    type: str
  details_level:
    description:
      - The level of detail for some of the fields in the response can vary from showing only the UID value of the object to a fully detailed
        representation of the object.
    type: str
    choices: ['uid', 'standard', 'full']
  groups:
    description:
      - Collection of group identifiers.
    type: list
  ignore_warnings:
    description:
      - Apply changes ignoring warnings.
    type: bool
  ignore_errors:
    description:
      - Apply changes ignoring errors. You won't be able to publish such a changes. If ignore-warnings flag was omitted - warnings will also be ignored.
    type: bool
extends_documentation_fragment: checkpoint_objects
"""

EXAMPLES = """
- name: add-time
  cp_mgmt_time:
    end:
      date: 24-Nov-2014
      time: '21:22'
    end_never: 'false'
    hours_ranges:
    - enabled: true
      from: 00:00
      index: 1
      to: 00:00
    - enabled: false
      from: 00:00
      index: 2
      to: 00:00
    name: timeObject1
    recurrence:
      days:
      - '1'
      month: Any
      pattern: Daily
      weekdays:
      - Sun
      - Mon
    start_now: 'true'
    state: present

- name: set-time
  cp_mgmt_time:
    hours_ranges:
    - from: 00:22
      to: 00:33
    name: timeObject1
    recurrence:
      month: Any
      pattern: Weekly
      weekdays:
      - Fri
    state: present

- name: delete-time
  cp_mgmt_time:
    name: timeObject1
    state: absent
"""

RETURN = """
cp_mgmt_time:
  description: The checkpoint object created or updated.
  returned: always, except when deleting the object.
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec_for_objects, api_call


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        end=dict(type='dict', options=dict(
            date=dict(type='str'),
            iso_8601=dict(type='str'),
            posix=dict(type='int'),
            time=dict(type='str')
        )),
        end_never=dict(type='bool'),
        hours_ranges=dict(type='list', options=dict(
            enabled=dict(type='bool'),
            index=dict(type='int'),
            to=dict(type='str')
        )),
        start=dict(type='dict', options=dict(
            date=dict(type='str'),
            iso_8601=dict(type='str'),
            posix=dict(type='int'),
            time=dict(type='str')
        )),
        start_now=dict(type='bool'),
        tags=dict(type='list'),
        recurrence=dict(type='dict', options=dict(
            days=dict(type='list'),
            month=dict(type='str'),
            pattern=dict(type='str'),
            weekdays=dict(type='list')
        )),
        color=dict(type='str', choices=['aquamarine', 'black', 'blue', 'crete blue', 'burlywood', 'cyan', 'dark green',
                                        'khaki', 'orchid', 'dark orange', 'dark sea green', 'pink', 'turquoise', 'dark blue', 'firebrick', 'brown',
                                        'forest green', 'gold', 'dark gold', 'gray', 'dark gray', 'light green', 'lemon chiffon', 'coral', 'sea green',
                                        'sky blue', 'magenta', 'purple', 'slate blue', 'violet red', 'navy blue', 'olive', 'orange', 'red', 'sienna',
                                        'yellow']),
        comments=dict(type='str'),
        details_level=dict(type='str', choices=['uid', 'standard', 'full']),
        groups=dict(type='list'),
        ignore_warnings=dict(type='bool'),
        ignore_errors=dict(type='bool')
    )
    argument_spec['hours_ranges']['options']['from'] = dict(type='str')
    argument_spec.update(checkpoint_argument_spec_for_objects)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    api_call_object = 'time'

    result = api_call(module, api_call_object)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
