#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Cédric Nisio <cedric.nisio@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: cgroup

short_description: Manage cgroup configurations

version_added: "2.6"

description:
    - Manages cgroup configurations in the C(/etc/cgconfig.d) directory.

options:
    name:
        description:
            - The cgroup name.
        required: true
    state:
        description:
            - Whether the cgroup should be present or absent.
        required: true
        choices: ['absent', 'present']
    memlimit:
        description:
            - The maximum RSS memory for the cgroup.
              It allows the use of k, K, m, M, g and G as units.
        required: false
    memswaplimit:
        description:
            - The maximum RSS memory and swap for the cgroup. This can't be lower than the memlimit.
              It allows the use of k, K, m, M, g and G as units.
        required: false

author:
    - Cedric Nisio (@Dayde)
'''

EXAMPLES = '''
# Checks a cgroup is present with only a memory limit
- cgroup:
    name: my_cgroup
    state: present
    memlimit: 256m

# Checks a cgroup is absent
- cgroup:
    name: my_cgroup
    state: absent
'''

RETURN = '''
action:
    description: If something changed the corresponding action (Creating, Updating or Deleting cgroup)
    type: str
    returned: only if changed
config_diff:
    description: If we're updating the configuration, the diff between the former and the new configuration
    type: str
    returned: only when updating configuration
'''

import os
from ansible.module_utils.basic import AnsibleModule


def run_module():
    module_args = dict(
        name=dict(type='str', required=True),
        state=dict(type='str', required=True, choices=['absent', 'present']),
        memlimit=dict(type='str', required=False),
        memswaplimit=dict(type='str', required=False)
    )

    result = dict(
        changed=False,
        action=None,
        config_diff=None
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    name = module.params['name']
    state = module.params['state']
    memlimit = module.params['memlimit']
    memswaplimit = module.params['memswaplimit']

    config = {}
    if memlimit is not None or memswaplimit is not None:
        config['memory'] = {}

    if memlimit is not None:
        config['memory']['memory.limit_in_bytes'] = memlimit

    if memswaplimit is not None:
        config['memory']['memory.memsw.limit_in_bytes'] = memswaplimit

    # Checks if cgroup exists
    raw_config = read_config_from_file(name)

    previous_state = 'absent' if raw_config is None else 'present'
    state_changed = state != previous_state

    if state_changed:
        result['action'] = ("Creating cgroup %s" if state == 'present' else "Deleting cgroup %s") % (name)

    if previous_state == 'present' and state != 'absent':
        # Checks for changes in existing cgroup only if it exists and is to be kept
        diff = has_config_changed(name, raw_config, config)
        if len(diff) > 0:
            result['action'] = "Updating cgroup %s" % (name)
            result['config_diff'] = diff

    changed = result['action'] is not None
    result['changed'] = changed

    # Check mode or nothing changed exiting here
    if module.check_mode or not changed:
        module.exit_json(**result)

    # Something changed updating configuration
    if state == 'present':
        with open("/etc/cgconfig.d/%s.conf" % (name), 'a') as fh:
            fh.truncate(0)
            fh.write(generate_config_file_content(name, config))
            fh.close()
    else:
        os.remove("/etc/cgconfig.d/%s.conf" % (name))

    module.exit_json(**result)


def read_config_from_file(desired_cgroup):
    file_name = get_cgconfig_file_name(desired_cgroup)
    if os.path.exists(file_name):
        with open(file_name, 'r') as fh:
            file_content = fh.read()
            fh.close()
        return file_content
    else:
        return None


def get_cgconfig_file_name(cgroup_name):
    return "/etc/cgconfig.d/%s.conf" % (cgroup_name)


def has_config_changed(cgroup_name, raw_config, desired_config):
    subsystems = set()
    added_params = {}
    deleted_params = {}
    modified_params = {}

    config = parse_config(raw_config)

    if cgroup_name not in config:
        return ''

    config = config[cgroup_name]

    for subsystem in config:
        subsystems.add(subsystem)
        for param in config[subsystem]:
            if subsystem not in desired_config or param not in desired_config[subsystem]:
                # Some param disappeared
                if subsystem not in deleted_params:
                    deleted_params[subsystem] = []
                deleted_params[subsystem].append(param)

    for subsystem in desired_config:
        subsystems.add(subsystem)
        for param in desired_config[subsystem]:
            if subsystem not in config or param not in config[subsystem]:
                if subsystem not in added_params:
                    added_params[subsystem] = []
                added_params[subsystem].append(param)
            else:
                if config[subsystem][param] != desired_config[subsystem][param]:
                    if subsystem not in modified_params:
                        modified_params[subsystem] = []
                    modified_params[subsystem].append(param)

    diff = []
    for subsystem in subsystems:
        changes = []
        if subsystem in added_params:
            for param in added_params[subsystem]:
                changes.append("+\t%s = \"%s\";" % (param, desired_config[subsystem][param]))

        if subsystem in deleted_params:
            for param in deleted_params[subsystem]:
                changes.append("-\t%s = \"%s\";" % (param, config[subsystem][param]))

        if subsystem in modified_params:
            for param in modified_params[subsystem]:
                changes.append("-\t%s = \"%s\";" % (param, config[subsystem][param]))
                changes.append("+\t%s = \"%s\";" % (param, desired_config[subsystem][param]))
        if len(changes) > 0:
            diff.append("%s {" % (subsystem))
            diff.extend(changes)
            diff.append("}")

    return '\n'.join(diff)


def parse_config(config):
    NEW_BLOCK = '{'
    END_BLOCK = '}'
    NEW_PARAM = '='
    END_PARAM = ';'
    COMMENT = '#'
    LINE_BREAK = '\n'
    SPACES = [' ', '\t', '\n', '\r']

    char_iterator = iter(config)

    word = ''
    config_object = {}
    result_stack = [config_object]
    word_stack = []

    for char in char_iterator:
        if char in SPACES:
            if word != '':
                word_stack.append(word)
                word = ''
            continue

        if char == COMMENT:
            while char != LINE_BREAK:
                char = next(char_iterator)
            continue

        if char == NEW_BLOCK:
            current_object = result_stack[len(result_stack) - 1]
            object_name = word_stack.pop()
            current_object[object_name] = {}
            result_stack.append(current_object[object_name])
            continue

        if char == END_BLOCK:
            result_stack.pop()
            continue

        if char == NEW_PARAM:
            continue
        if char == END_PARAM:
            if word == '':
                word = word_stack.pop()

            current_object = result_stack[len(result_stack) - 1]
            param_value = word
            param_name = word_stack.pop()
            current_object[param_name] = param_value
            continue

        word += char

    return config_object


def generate_config_file_content(name, config):
    lines = []

    lines.append("# Ansible: %s" % (name))
    lines.append("group %s {" % (name))
    for subsystem, params in config.items():
        lines.append("\t%s {" % (subsystem))
        for param, value in params.items():
            lines.append("\t\t%s = %s;" % (param, value))
        lines.append("\t}")
    lines.append("}")

    return '\n'.join(lines)


def main():
    run_module()

if __name__ == '__main__':
    main()
