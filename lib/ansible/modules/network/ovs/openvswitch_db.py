#!/usr/bin/python
# coding: utf-8 -*-

#
# (c) 2015, Mark Hamilton <mhamilton@vmware.com>
# Portions copyright @ 2015 VMware, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: openvswitch_db
author: "Mark Hamilton (@markleehamilton) <mhamilton@vmware.com>"
version_added: 2.0
short_description: Configure open vswitch database.
requirements: [ "ovs-vsctl >= 2.3.3" ]
description:
    - Set column values in record in database table.
options:
    state:
        required: false
        description:
            - Configures the state of the key. When set
              to I(present), the I(key) and I(value) pair will be set
              on the I(record) and when set to I(absent) the I(key)
              will not be set.
        default: present
        choices: ['present', 'absent']
        version_added: "2.4"
    table:
        required: true
        description:
            - Identifies the table in the database.
    record:
        required: true
        description:
            - Identifies the record in the table.
    col:
        required: true
        description:
            - Identifies the column in the record.
    key:
        required: false
        description:
            - Identifies the key in the record column, when the column is a map
              type.
    value:
        required: true
        description:
            - Expected value for the table, record, column and key.
    timeout:
        required: false
        default: 5
        description:
            - How long to wait for ovs-vswitchd to respond
"""

EXAMPLES = '''
# Increase the maximum idle time to 50 seconds before pruning unused kernel
# rules.
- openvswitch_db:
    table: open_vswitch
    record: .
    col: other_config
    key: max-idle
    value: 50000

# Disable in band copy
- openvswitch_db:
    table: Bridge
    record: br-int
    col: other_config
    key: disable-in-band
    value: true

# Remove in band key
- openvswitch_db:
    state: present
    table: Bridge
    record: br-int
    col: other_config
    key: disable-in-band

# Mark port with tag 10
- openvswitch_db:
    table: Port
    record: port0
    col: tag
    value: 10
'''
import re

from ansible.module_utils.basic import AnsibleModule

# Regular expression for map type, must not be empty
NON_EMPTY_MAP_RE = re.compile(r'{.+}')
# Regular expression for a map column type
MAP_RE = re.compile(r'{.*}')


def map_obj_to_commands(want, have, module):
    """ Define ovs-vsctl command to meet desired state """
    commands = list()

    if module.params['state'] == 'absent':
        if 'key' in have.keys():
            templatized_command = "%(ovs-vsctl)s -t %(timeout)s remove %(table)s %(record)s " \
                                  "%(col)s %(key)s=%(value)s"
            commands.append(templatized_command % module.params)
        elif module.params['key'] is None:
            templatized_command = "%(ovs-vsctl)s -t %(timeout)s remove %(table)s %(record)s " \
                                  "%(col)s"
            commands.append(templatized_command % module.params)
    else:
        if want == have:
            # Nothing to commit
            return commands
        if module.params['key'] is None:
            templatized_command = "%(ovs-vsctl)s -t %(timeout)s set %(table)s %(record)s " \
                                  "%(col)s=%(value)s"
            commands.append(templatized_command % module.params)
        else:
            templatized_command = "%(ovs-vsctl)s -t %(timeout)s set %(table)s %(record)s " \
                                  "%(col)s:%(key)s=%(value)s"
            commands.append(templatized_command % module.params)

    return commands


def map_config_to_obj(module):
    templatized_command = "%(ovs-vsctl)s -t %(timeout)s list %(table)s %(record)s"
    command = templatized_command % module.params
    rc, out, err = module.run_command(command, check_rc=True)
    if rc != 0:
        module.fail_json(msg=err)

    match = re.search(r'^' + module.params['col'] + r'(\s+):(\s+)(.*)$', out, re.M)

    col_value = match.group(3)

    # Map types require key argument
    has_key = module.params['key'] is not None
    is_map = MAP_RE.match(col_value)
    if is_map and not has_key:
        module.fail_json(
            msg="missing required arguments: key for map type of column")

    col_value_to_dict = {}
    if NON_EMPTY_MAP_RE.match(col_value):
        for kv in col_value[1:-1].split(', '):
            k, v = kv.split('=')
            col_value_to_dict[k.strip()] = v.strip()

    obj = {
        'table': module.params['table'],
        'record': module.params['record'],
        'col': module.params['col'],
    }

    if has_key and is_map:
        if module.params['key'] in col_value_to_dict:
            obj['key'] = module.params['key']
            obj['value'] = col_value_to_dict[module.params['key']]
    else:
        obj['value'] = str(col_value.strip())

    return obj


def map_params_to_obj(module):
    obj = {
        'table': module.params['table'],
        'record': module.params['record'],
        'col': module.params['col'],
        'value': module.params['value']
    }

    key = module.params['key']
    if key is not None:
        obj['key'] = key

    return obj


def main():
    """ Entry point for ansible module. """
    argument_spec = {
        'state': {'default': 'present', 'choices': ['present', 'absent']},
        'table': {'required': True},
        'record': {'required': True},
        'col': {'required': True},
        'key': {'required': False},
        'value': {'required': True, 'type': 'str'},
        'timeout': {'default': 5, 'type': 'int'},
    }

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    result = {'changed': False}

    # We add ovs-vsctl to module_params to later build up templatized commands
    module.params["ovs-vsctl"] = module.get_bin_path("ovs-vsctl", True)

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)

    commands = map_obj_to_commands(want, have, module)
    result['commands'] = commands

    if commands:
        if not module.check_mode:
            for c in commands:
                module.run_command(c, check_rc=True)
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
