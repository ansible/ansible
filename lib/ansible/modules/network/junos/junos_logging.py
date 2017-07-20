#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
#
# This file is part of Ansible by Red Hat
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = """
---
module: junos_logging
version_added: "2.4"
author: "Ganesh Nalawade (@ganeshrn)"
short_description: Manage logging on network devices
description:
  - This module provides declarative management of logging
    on Juniper JUNOS devices.
options:
  dest:
    description:
      - Destination of the logs.
    choices: ['console', 'host', 'file', 'user']
  name:
    description:
      - If value of C(dest) is I(file) it indicates file-name,
        for I(user) it indicates username and for I(host) indicates
        the host name to be notified.
  facility:
    description:
      - Set logging facility.
  level:
    description:
      - Set logging severity levels.
  collection:
    description: List of logging definitions.
  purge:
    description:
      - Purge logging not defined in the collections parameter.
    default: no
  state:
    description:
      - State of the logging configuration.
    default: present
    choices: ['present', 'absent']
  active:
    description:
      - Specifies whether or not the configuration is active or deactivated
    default: True
    choices: [True, False]
  rotate_frequency:
    description:
      - Rotate log frequency in minutes, this is applicable if value
        of I(dest) is C(file). The acceptable value is in range of 1 to 59.
        This controls the frequency after which log file is rotated.
    required: false
  size:
    description:
      - Size of the file in archive, this is applicable if value
        of I(dest) is C(file). The acceptable value is in range from 65536 to
        1073741824 bytes.
    required: false
  files:
    description:
      - Number of files to be archived, this is applicable if value
        of I(dest) is C(file). The acceptable value is in range from 1 to 1000.
    required: false
"""

EXAMPLES = """
- name: configure console logging
  junos_logging:
    dest: console
    facility: any
    level: critical

- name: remove console logging configuration
  junos_logging:
    dest: console
    state: absent

- name: configure file logging
  junos_logging:
    dest: file
    name: test
    facility: pfe
    level: error

- name: configure logging parameter
  junos_logging:
    files: 30
    size: 65536
    rotate_frequency: 10
"""

RETURN = """
diff.prepared:
  description: Configuration difference before and after applying change.
  returned: when configuration is changed and diff option is enabled.
  type: string
  sample: >
          [edit system syslog]
          +    [edit system syslog]
               file interactive-commands { ... }
          +    file test {
          +        pfe critical;
          +    }
"""
import collections

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.junos import junos_argument_spec, check_args
from ansible.module_utils.junos import load_config, map_params_to_obj, map_obj_to_ele
from ansible.module_utils.junos import commit_configuration, discard_changes, locked_config

try:
    from lxml.etree import tostring
except ImportError:
    from xml.etree.ElementTree import tostring

USE_PERSISTENT_CONNECTION = True


def validate_files(value, module):
    if value and not 1 <= value <= 1000:
        module.fail_json(msg='files must be between 1 and 1000')


def validate_size(value, module):
    if value and not 65536 <= value <= 1073741824:
        module.fail_json(msg='size must be between 65536 and 1073741824')


def validate_rotate_frequency(value, module):
    if value and not 1 <= value <= 59:
        module.fail_json(msg='rotate_frequency must be between 1 and 59')


def validate_param_values(module, obj):
    for key in obj:
        # validate the param value (if validator func exists)
        validator = globals().get('validate_%s' % key)
        if callable(validator):
            validator(module.params.get(key), module)


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        dest=dict(choices=['console', 'host', 'file', 'user']),
        name=dict(),
        facility=dict(),
        level=dict(),
        rotate_frequency=dict(type='int'),
        size=dict(type='int'),
        files=dict(type='int'),
        src_addr=dict(),
        collection=dict(),
        purge=dict(default=False, type='bool'),
        state=dict(default='present', choices=['present', 'absent']),
        active=dict(default=True, type='bool')
    )

    argument_spec.update(junos_argument_spec)

    required_if = [('dest', 'host', ['name', 'facility', 'level']),
                   ('dest', 'file', ['name', 'facility', 'level']),
                   ('dest', 'user', ['name', 'facility', 'level']),
                   ('dest', 'console', ['facility', 'level'])]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=required_if,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    result = {'changed': False}

    if warnings:
        result['warnings'] = warnings

    dest = module.params.get('dest')
    if dest == 'console' and module.params.get('name'):
        module.fail_json(msg="%s and %s are mutually exclusive" % ('console', 'name'))

    top = 'system/syslog'
    is_facility_key = False
    field_top = None
    if dest:
        if dest == 'console':
            field_top = dest
            is_facility_key = True
        else:
            field_top = dest + '/contents'
            is_facility_key = False

    param_to_xpath_map = collections.OrderedDict()
    param_to_xpath_map.update([
        ('name', {'xpath': 'name', 'is_key': True, 'top': dest}),
        ('facility', {'xpath': 'name', 'is_key': is_facility_key, 'top': field_top}),
        ('level', {'xpath': module.params.get('level'), 'tag_only': True, 'top': field_top}),
        ('size', {'xpath': 'size', 'leaf_only': True, 'is_key': True, 'top': 'archive'}),
        ('files', {'xpath': 'files', 'leaf_only': True, 'is_key': True, 'top': 'archive'}),
        ('rotate_frequency', {'xpath': 'log-rotate-frequency', 'leaf_only': True}),
    ])

    validate_param_values(module, param_to_xpath_map)

    want = map_params_to_obj(module, param_to_xpath_map)
    ele = map_obj_to_ele(module, want, top)

    with locked_config(module):
        diff = load_config(module, tostring(ele), warnings, action='replace')

        commit = not module.check_mode
        if diff:
            if commit:
                commit_configuration(module)
            else:
                discard_changes(module)
            result['changed'] = True

            if module._diff:
                result['diff'] = {'prepared': diff}

    module.exit_json(**result)

if __name__ == "__main__":
    main()
