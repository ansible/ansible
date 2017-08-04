#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


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
  aggregate:
    description: List of logging definitions.
  purge:
    description:
      - Purge logging not defined in the aggregate parameter.
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

- name: Configure file logging using aggregate
  junos_logging:
    aggregate:
    - {dest: file, name: test-1,  facility: pfe, level: critical, active: True}
    - {dest: file, name: test-2,  facility: kernel, level: emergency, active: True}

- name: Delete file logging using aggregate
  junos_logging:
    aggregate:
    - {dest: file, name: test-1,  facility: pfe, level: critical, active: True, state: absent}
    - {dest: file, name: test-2,  facility: kernel, level: emergency, active: True, state: absent}
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

from copy import copy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.junos import junos_argument_spec, check_args
from ansible.module_utils.junos import load_config, map_params_to_obj, map_obj_to_ele, to_param_list
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


def validate_param_values(module, obj, param=None):
    if not param:
        param = module.params
    for key in obj:
        # validate the param value (if validator func exists)
        validator = globals().get('validate_%s' % key)
        if callable(validator):
            validator(param.get(key), module)


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        dest=dict(choices=['console', 'host', 'file', 'user']),
        name=dict(),
        facility=dict(),
        level=dict(),
        rotate_frequency=dict(type='int'),
        size=dict(type='int'),
        files=dict(type='int'),
        src_addr=dict(),
        state=dict(default='present', choices=['present', 'absent']),
        active=dict(default=True, type='bool')
    )

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=element_spec),
        purge=dict(default=False, type='bool')
    )

    argument_spec.update(element_spec)
    argument_spec.update(junos_argument_spec)

    mutually_exclusive = [['dest', 'aggregate'],
                          ['name', 'aggregate'],
                          ['facility', 'aggregate'],
                          ['rotate_frequency', 'aggregate'],
                          ['size', 'aggregate'],
                          ['files', 'aggregate'],
                          ['src_addr', 'aggregate'],
                          ['state', 'aggregate'],
                          ['active', 'aggregate']]

    required_if = [('dest', 'host', ['name', 'facility', 'level']),
                   ('dest', 'file', ['name', 'facility', 'level']),
                   ('dest', 'user', ['name', 'facility', 'level']),
                   ('dest', 'console', ['facility', 'level'])]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=required_if,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    result = {'changed': False}

    if warnings:
        result['warnings'] = warnings

    params = to_param_list(module)

    requests = list()
    for param in params:
        item = copy(param)
        dest = item.get('dest')
        if dest == 'console' and item.get('name'):
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
            ('size', {'xpath': 'size', 'leaf_only': True, 'is_key': True, 'top': 'archive'}),
            ('files', {'xpath': 'files', 'leaf_only': True, 'is_key': True, 'top': 'archive'}),
            ('rotate_frequency', {'xpath': 'log-rotate-frequency', 'leaf_only': True}),
        ])

        if item.get('level'):
            param_to_xpath_map['level'] = {'xpath': item.get('level'), 'tag_only': True, 'top': field_top}

        validate_param_values(module, param_to_xpath_map, param=item)

        want = map_params_to_obj(module, param_to_xpath_map, param=item)
        requests.append(map_obj_to_ele(module, want, top, param=item))

    diff = None
    with locked_config(module):
        for req in requests:
            diff = load_config(module, tostring(req), warnings, action='replace')

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
