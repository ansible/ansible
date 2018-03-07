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
        default: present
        choices: ['absent', 'present']
    permtaskuser:
        description:
            - The system user id allowed to submit tasks to the cgroup.
        default: root
    permtaskgroup:
        description:
            - The system group id allowed to submit tasks to the cgroup.
        default: root
    permadminuser:
        description:
            - The system user id allowed to modify the cgroup subsystem parameters.
        default: root
    permadmingroup:
        description:
            - The system group id allowed to modify the cgroup subsystem parameters.
        default: root
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
        state=dict(type='str', default='present', choices=['absent', 'present']),
        permtaskuser=dict(type='str', default='root'),
        permtaskgroup=dict(type='str', default='root'),
        permadminuser=dict(type='str', default='root'),
        permadmingroup=dict(type='str', default='root'),
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

    permtaskuser = module.params['permtaskuser']
    permtaskgroup = module.params['permtaskgroup']
    permadminuser = module.params['permadminuser']
    permadmingroup = module.params['permadmingroup']

    memlimit = module.params['memlimit']
    memswaplimit = module.params['memswaplimit']

    config = {}

    if permtaskuser != 'root' or permtaskgroup != 'root' or permadminuser != 'root' or permadmingroup != 'root':
        config['perm'] = {
            'task': {
                'uid': permtaskuser,
                'gid': permtaskgroup
            },
            'admin': {
                'uid': permadminuser,
                'gid': permadmingroup
            }
        }

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
        if subsystem == 'perm':
            continue
        subsystems.add(subsystem)
        for param in config[subsystem]:
            if subsystem not in desired_config or param not in desired_config[subsystem]:
                # Some param disappeared
                if subsystem not in deleted_params:
                    deleted_params[subsystem] = []
                deleted_params[subsystem].append(param)

    for subsystem in desired_config:
        if subsystem == 'perm':
            continue
        subsystems.add(subsystem)
        for param in desired_config[subsystem]:
            if subsystem not in config or param not in config[subsystem]:
                # Some param was added
                if subsystem not in added_params:
                    added_params[subsystem] = []
                added_params[subsystem].append(param)
            else:
                if config[subsystem][param] != desired_config[subsystem][param]:
                    # Some param was modified
                    if subsystem not in modified_params:
                        modified_params[subsystem] = []
                    modified_params[subsystem].append(param)

    diff = diff_perm(config, desired_config)

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


def diff_perm(config, desired_config):
    previous_perm_settings = 'perm' in config
    desired_perm_settings = 'perm' in desired_config

    diff = []

    if desired_perm_settings != previous_perm_settings:
        if desired_perm_settings:
            # Perm settings were added
            diff.append('perm {')
            diff.append('\ttask {')
            diff.append('+\t\tuid = %s;' % desired_config['perm']['task']['uid'])
            diff.append('+\t\tgid = %s;' % desired_config['perm']['task']['gid'])
            diff.append('\t} admin {')
            diff.append('+\t\tuid = %s;' % desired_config['perm']['admin']['uid'])
            diff.append('+\t\tgid = %s;' % desired_config['perm']['admin']['gid'])
            diff.append('\t}')
            diff.append('}')
        else:
            # Perm settings were deleted
            diff.append('perm {')
            diff.append('\ttask {')
            diff.append('-\t\tuid = %s;' % config['perm']['task']['uid'])
            diff.append('-\t\tgid = %s;' % config['perm']['task']['gid'])
            diff.append('\t} admin {')
            diff.append('-\t\tuid = %s;' % config['perm']['admin']['uid'])
            diff.append('-\t\tgid = %s;' % config['perm']['admin']['gid'])
            diff.append('\t}')
            diff.append('}')
    elif desired_perm_settings and config['perm'] != desired_config['perm']:
        # Perm settings have been altered
        permtaskuser = config['perm']['task']['uid']
        permtaskgroup = config['perm']['task']['gid']
        permadminuser = config['perm']['admin']['uid']
        permadmingroup = config['perm']['admin']['gid']
        desired_permtaskuser = desired_config['perm']['task']['uid']
        desired_permtaskgroup = desired_config['perm']['task']['gid']
        desired_permadminuser = desired_config['perm']['admin']['uid']
        desired_permadmingroup = desired_config['perm']['admin']['gid']

        diff.append('perm {')

        if config['perm']['task'] != desired_config['perm']['task']:
            diff.append('\ttask {')
            if permtaskuser != desired_permtaskuser:
                diff.append('-\t\tuid = %s;' % config['perm']['task']['uid'])
                diff.append('+\t\tuid = %s;' % desired_config['perm']['task']['uid'])
            if permtaskgroup != desired_permtaskgroup:
                diff.append('-\t\tgid = %s;' % config['perm']['task']['gid'])
                diff.append('+\t\tgid = %s;' % desired_config['perm']['task']['gid'])
            diff.append('\t}')

        if config['perm']['admin'] != desired_config['perm']['admin']:
            diff.append('\tadmin {')
            if permadminuser != desired_permadminuser:
                diff.append('-\t\tuid = %s;' % config['perm']['admin']['uid'])
                diff.append('+\t\tuid = %s;' % desired_config['perm']['admin']['uid'])
            if permadmingroup != desired_permadmingroup:
                diff.append('-\t\tgid = %s;' % config['perm']['admin']['gid'])
                diff.append('+\t\tgid = %s;' % desired_config['perm']['admin']['gid'])
            diff.append('\t}')

        diff.append('}')
    return diff


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
            if word == '':
                word = word_stack.pop()

            current_object = result_stack[len(result_stack) - 1]
            object_name = word
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
    if 'perm' in config:
        lines.append('\tperm {')
        lines.append('\t\ttask {')
        lines.append('\t\t\tuid = %s;' % config['perm']['task']['uid'])
        lines.append('\t\t\tgid = %s;' % config['perm']['task']['gid'])
        lines.append('\t\t} admin {')
        lines.append('\t\t\tuid = %s;' % config['perm']['admin']['uid'])
        lines.append('\t\t\tgid = %s;' % config['perm']['admin']['gid'])
        lines.append('\t\t}')
        lines.append('\t}')

    for subsystem, params in config.items():
        if subsystem == 'perm':
            continue
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
