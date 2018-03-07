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
        diff=[]
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

    diff = {}
    result['diff'].append(diff)

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
    previous_raw_config = read_config_from_file(name)

    previous_state = 'absent' if previous_raw_config is None else 'present'
    state_changed = state != previous_state

    previous_config = ''
    if previous_state == 'present':
        previous_config = parse_config(previous_raw_config)[name]

    diff['before'] = '' if previous_state == 'absent' else generate_config_file_content(name, previous_config)
    diff['after'] = '' if state == 'absent' else generate_config_file_content(name, config)

    if state_changed:
        result['action'] = ("Creating cgroup %s" if state == 'present' else "Deleting cgroup %s") % (name)
    elif state == 'present' and previous_config != config:
        result['action'] = "Updating cgroup %s" % (name)

    changed = result['action'] is not None
    result['changed'] = changed

    # Check mode or nothing changed exiting here
    if module.check_mode or not changed:
        module.exit_json(**result)

    # Something changed updating configuration
    if state == 'present':
        with open("/etc/cgconfig.d/%s.conf" % (name), 'a') as fh:
            fh.truncate(0)
            fh.write(diff['after'])
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
