#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = '''
---
module: nxos_snapshot
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manage snapshots of the running states of selected features.
description:
    - Create snapshots of the running states of selected features, add
      new show commands for snapshot creation, delete and compare
      existing snapshots.
author:
    - Gabriele Gerbino (@GGabriele)
notes:
    - Tested against NXOSv 7.3.(0)D1(1) on VIRL
    - C(transport=cli) may cause timeout errors.
    - The C(element_key1) and C(element_key2) parameter specify the tags used
      to distinguish among row entries. In most cases, only the element_key1
      parameter needs to specified to be able to distinguish among row entries.
    - C(action=compare) will always store a comparison report on a local file.
options:
    action:
        description:
            - Define what snapshot action the module would perform.
        required: true
        choices: [ add, compare, create, delete, delete_all ]
    snapshot_name:
        description:
            - Snapshot name, to be used when C(action=create)
              or C(action=delete).
    description:
        description:
            - Snapshot description to be used when C(action=create).
    snapshot1:
        description:
            - First snapshot to be used when C(action=compare).
    snapshot2:
        description:
            - Second snapshot to be used when C(action=compare).
    comparison_results_file:
        description:
            - Name of the file where snapshots comparison will be stored when C(action=compare).
    compare_option:
        description:
            - Snapshot options to be used when C(action=compare).
        choices: ['summary','ipv4routes','ipv6routes']
    section:
        description:
            - Used to name the show command output, to be used
              when C(action=add).
    show_command:
        description:
            - Specify a new show command, to be used when C(action=add).
    row_id:
        description:
            - Specifies the tag of each row entry of the show command's
              XML output, to be used when C(action=add).
    element_key1:
        description:
            - Specify the tags used to distinguish among row entries,
              to be used when C(action=add).
    element_key2:
        description:
            - Specify the tags used to distinguish among row entries,
              to be used when C(action=add).
    save_snapshot_locally:
        description:
            - Specify to locally store a new created snapshot,
              to be used when C(action=create).
        type: bool
        default: 'no'
    path:
        description:
            - Specify the path of the file where new created snapshot or
              snapshots comparison will be stored, to be used when
              C(action=create) and C(save_snapshot_locally=true) or
              C(action=compare).
        default: './'
'''

EXAMPLES = '''
# Create a snapshot and store it locally
- nxos_snapshot:
    action: create
    snapshot_name: test_snapshot
    description: Done with Ansible
    save_snapshot_locally: true
    path: /home/user/snapshots/

# Delete a snapshot
- nxos_snapshot:
    action: delete
    snapshot_name: test_snapshot

# Delete all existing snapshots
- nxos_snapshot:
    action: delete_all

# Add a show command for snapshots creation
- nxos_snapshot:
    section: myshow
    show_command: show ip interface brief
    row_id: ROW_intf
    element_key1: intf-name

# Compare two snapshots
- nxos_snapshot:
    action: compare
    snapshot1: pre_snapshot
    snapshot2: post_snapshot
    comparison_results_file: compare_snapshots.txt
    compare_option: summary
    path: '../snapshot_reports/'
'''

RETURN = '''
commands:
    description: commands sent to the device
    returned: verbose mode
    type: list
    sample: ["snapshot create post_snapshot Post-snapshot"]
'''

import os
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.nxos.nxos import load_config, run_commands
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args


def execute_show_command(command, module):
    command = [{
        'command': command,
        'output': 'text',
    }]

    return run_commands(module, command)


def get_existing(module):
    existing = []
    command = 'show snapshots'

    body = execute_show_command(command, module)[0]
    if body:
        split_body = body.splitlines()
        snapshot_regex = (r'(?P<name>\S+)\s+(?P<date>\w+\s+\w+\s+\d+\s+\d+'
                          r':\d+:\d+\s+\d+)\s+(?P<description>.*)')
        for snapshot in split_body:
            temp = {}
            try:
                match_snapshot = re.match(snapshot_regex, snapshot, re.DOTALL)
                snapshot_group = match_snapshot.groupdict()
                temp['name'] = snapshot_group['name']
                temp['date'] = snapshot_group['date']
                temp['description'] = snapshot_group['description']
                existing.append(temp)
            except AttributeError:
                pass

    return existing


def action_create(module, existing_snapshots):
    commands = list()
    exist = False
    for snapshot in existing_snapshots:
        if module.params['snapshot_name'] == snapshot['name']:
            exist = True

    if exist is False:
        commands.append('snapshot create {0} {1}'.format(
            module.params['snapshot_name'], module.params['description']))

    return commands


def action_add(module, existing_snapshots):
    commands = list()
    command = 'show snapshot sections'
    sections = []
    body = execute_show_command(command, module)[0]

    if body:
        section_regex = r'.*\[(?P<section>\S+)\].*'
        split_body = body.split('\n\n')
        for section in split_body:
            temp = {}
            for line in section.splitlines():
                try:
                    match_section = re.match(section_regex, section, re.DOTALL)
                    temp['section'] = match_section.groupdict()['section']
                except (AttributeError, KeyError):
                    pass

                if 'show command' in line:
                    temp['show_command'] = line.split('show command: ')[1]
                elif 'row id' in line:
                    temp['row_id'] = line.split('row id: ')[1]
                elif 'key1' in line:
                    temp['element_key1'] = line.split('key1: ')[1]
                elif 'key2' in line:
                    temp['element_key2'] = line.split('key2: ')[1]

            if temp:
                sections.append(temp)

    proposed = {
        'section': module.params['section'],
        'show_command': module.params['show_command'],
        'row_id': module.params['row_id'],
        'element_key1': module.params['element_key1'],
        'element_key2': module.params['element_key2'] or '-',
    }

    if proposed not in sections:
        if module.params['element_key2']:
            commands.append('snapshot section add {0} "{1}" {2} {3} {4}'.format(
                module.params['section'], module.params['show_command'],
                module.params['row_id'], module.params['element_key1'],
                module.params['element_key2']))
        else:
            commands.append('snapshot section add {0} "{1}" {2} {3}'.format(
                module.params['section'], module.params['show_command'],
                module.params['row_id'], module.params['element_key1']))

    return commands


def action_compare(module, existing_snapshots):
    command = 'show snapshot compare {0} {1}'.format(
        module.params['snapshot1'], module.params['snapshot2'])

    if module.params['compare_option']:
        command += ' {0}'.format(module.params['compare_option'])

    body = execute_show_command(command, module)[0]
    return body


def action_delete(module, existing_snapshots):
    commands = list()

    exist = False
    for snapshot in existing_snapshots:
        if module.params['snapshot_name'] == snapshot['name']:
            exist = True

    if exist:
        commands.append('snapshot delete {0}'.format(
            module.params['snapshot_name']))

    return commands


def action_delete_all(module, existing_snapshots):
    commands = list()
    if existing_snapshots:
        commands.append('snapshot delete all')
    return commands


def invoke(name, *args, **kwargs):
    func = globals().get(name)
    if func:
        return func(*args, **kwargs)


def write_on_file(content, filename, module):
    path = module.params['path']
    if path[-1] != '/':
        path += '/'
    filepath = '{0}{1}'.format(path, filename)
    try:
        report = open(filepath, 'w')
        report.write(content)
        report.close()
    except Exception:
        module.fail_json(msg="Error while writing on file.")

    return filepath


def main():
    argument_spec = dict(
        action=dict(required=True, choices=['create', 'add', 'compare', 'delete', 'delete_all']),
        snapshot_name=dict(type='str'),
        description=dict(type='str'),
        snapshot1=dict(type='str'),
        snapshot2=dict(type='str'),
        compare_option=dict(choices=['summary', 'ipv4routes', 'ipv6routes']),
        comparison_results_file=dict(type='str'),
        section=dict(type='str'),
        show_command=dict(type='str'),
        row_id=dict(type='str'),
        element_key1=dict(type='str'),
        element_key2=dict(type='str'),
        save_snapshot_locally=dict(type='bool', default=False),
        path=dict(type='str', default='./')
    )

    argument_spec.update(nxos_argument_spec)

    required_if = [("action", "compare", ["snapshot1", "snapshot2", "comparison_results_file"]),
                   ("action", "create", ["snapshot_name", "description"]),
                   ("action", "add", ["section", "show_command", "row_id", "element_key1"]),
                   ("action", "delete", ["snapshot_name"])]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=required_if,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    action = module.params['action']
    comparison_results_file = module.params['comparison_results_file']

    if not os.path.isdir(module.params['path']):
        module.fail_json(msg='{0} is not a valid directory name.'.format(
            module.params['path']))

    existing_snapshots = invoke('get_existing', module)
    action_results = invoke('action_%s' % action, module, existing_snapshots)

    result = {'changed': False, 'commands': []}

    if not module.check_mode:
        if action == 'compare':
            result['commands'] = []

            if module.params['path'] and comparison_results_file:
                snapshot1 = module.params['snapshot1']
                snapshot2 = module.params['snapshot2']
                compare_option = module.params['compare_option']
                command = 'show snapshot compare {0} {1}'.format(snapshot1, snapshot2)
                if compare_option:
                    command += ' {0}'.format(compare_option)
                content = execute_show_command(command, module)[0]
                if content:
                    write_on_file(content, comparison_results_file, module)
        else:
            if action_results:
                load_config(module, action_results)
                result['commands'] = action_results
                result['changed'] = True

            if action == 'create' and module.params['path'] and module.params['save_snapshot_locally']:
                command = 'show snapshot dump {0} | json'.format(module.params['snapshot_name'])
                content = execute_show_command(command, module)[0]
                if content:
                    write_on_file(str(content), module.params['snapshot_name'], module)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
