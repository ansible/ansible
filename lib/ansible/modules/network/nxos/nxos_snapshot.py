#!/usr/bin/python
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
#

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: nxos_snapshot
version_added: "2.2"
short_description: Manage snapshots of the running states of selected features.
description:
    - Create snapshots of the running states of selected features, add
      new show commands for snapshot creation, delete and compare
      existing snapshots.
author:
    - Gabriele Gerbino (@GGabriele)
notes:
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
        choices: ['create','add','compare','delete']
    snapshot_name:
        description:
            - Snapshot name, to be used when C(action=create)
              or C(action=delete).
        required: false
        default: null
    description:
        description:
            - Snapshot description to be used when C(action=create).
        required: false
        default: null
    snapshot1:
        description:
            - First snapshot to be used when C(action=compare).
        required: false
        default: null
    snapshot2:
        description:
            - Second snapshot to be used when C(action=compare).
        required: false
        default: null
    comparison_results_file:
        description:
            - Name of the file where snapshots comparison will be store.
        required: false
        default: null
    compare_option:
        description:
            - Snapshot options to be used when C(action=compare).
        required: false
        default: null
        choices: ['summary','ipv4routes','ipv6routes']
    section:
        description:
            - Used to name the show command output, to be used
              when C(action=add).
        required: false
        default: null
    show_command:
        description:
            - Specify a new show command, to be used when C(action=add).
        required: false
        default: null
    row_id:
        description:
            - Specifies the tag of each row entry of the show command's
              XML output, to be used when C(action=add).
        required: false
        default: null
    element_key1:
        description:
            - Specify the tags used to distinguish among row entries,
              to be used when C(action=add).
        required: false
        default: null
    element_key2:
        description:
            - Specify the tags used to distinguish among row entries,
              to be used when C(action=add).
        required: false
        default: null
    save_snapshot_locally:
        description:
            - Specify to locally store a new created snapshot,
              to be used when C(action=create).
        required: false
        default: false
        choices: ['true','false']
    path:
        description:
            - Specify the path of the file where new created snapshot or
              snapshots comparison will be stored, to be used when
              C(action=create) and C(save_snapshot_locally=true) or
              C(action=compare).
        required: false
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
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"

# Delete a snapshot
- nxos_snapshot:
    action: delete
    snapshot_name: test_snapshot
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"

# Delete all existing snapshots
- nxos_snapshot:
    action: delete_all
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"

# Add a show command for snapshots creation
- nxos_snapshot:
    section: myshow
    show_command: show ip interface brief
    row_id: ROW_intf
    element_key1: intf-name
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"

# Compare two snapshots
- nxos_snapshot:
    action: compare
    snapshot1: pre_snapshot
    snapshot2: post_snapshot
    comparison_results_file: compare_snapshots.txt
    compare_option: summary
    path: '../snapshot_reports/'
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
'''

RETURN = '''
existing_snapshots:
    description: list of existing snapshots.
    returned: verbose mode
    type: list
    sample: [{"date": "Tue Sep 13 10:58:08 2016",
              "description": "First snapshot", "name": "first_snap"},
            {"date": "Tue Sep 13 10:27:31 2016", "description": "Pre-snapshot",
            "name": "pre_snapshot"}]
final_snapshots:
    description: list of final snapshots.
    returned: verbose mode
    type: list
    sample: [{"date": "Tue Sep 13 10:58:08 2016",
              "description": "First snapshot", "name": "first_snap"},
            {"date": "Tue Sep 13 10:27:31 2016", "description": "Pre-snapshot",
            "name": "pre_snapshot"},
            {"date": "Tue Sep 13 10:37:50 2016", "description": "Post-snapshot",
            "name": "post_snapshot"}]
report_file:
    description: name of the file where the new snapshot or snapshots
                 comparison have been stored.
    returned: verbose mode
    type: string
    sample: "/home/gabriele/Desktop/ntc-ansible/ansible_snapshot"
updates:
    description: commands sent to the device
    returned: verbose mode
    type: list
    sample: ["snapshot create post_snapshot Post-snapshot"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''

from ansible.module_utils.nxos import get_config, load_config, run_commands
from ansible.module_utils.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netcfg import CustomNetworkConfig

import os
import re
import re


def execute_show_command(command, module, command_type='cli_show_ascii'):
    cmds = [command]
    if module.params['transport'] == 'cli':
        body = run_commands(module, cmds)
    elif module.params['transport'] == 'nxapi':
        body = run_commands(module, cmds)

    return body


def get_existing(module):
    existing = []
    command = 'show snapshots'

    body = execute_show_command(command, module)[0]
    if body:
        split_body = body.splitlines()
        snapshot_regex = ('(?P<name>\S+)\s+(?P<date>\w+\s+\w+\s+\d+\s+\d+'
                          ':\d+:\d+\s+\d+)\s+(?P<description>.*)')
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
        section_regex = '.*\[(?P<section>\S+)\].*'
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


def get_snapshot(module):
    command = 'show snapshot dump {0}'.format(module.params['snapshot_name'])
    body = execute_show_command(command, module)[0]
    return body


def write_on_file(content, filename, module):
    path = module.params['path']
    if path[-1] != '/':
        path += '/'
    filepath = '{0}{1}'.format(path, filename)
    try:
        report = open(filepath, 'w')
        report.write(content)
        report.close()
    except:
        module.fail_json(msg="Error while writing on file.")

    return filepath

def main():
    argument_spec = dict(
        action=dict(required=True, choices=['create', 'add',
                                                'compare', 'delete',
                                                'delete_all']),
        snapshot_name=dict(required=False, type='str'),
        description=dict(required=False, type='str'),
        snapshot1=dict(required=False, type='str'),
        snapshot2=dict(required=False, type='str'),
        compare_option=dict(required=False,
                        choices=['summary', 'ipv4routes', 'ipv6routes']),
        comparison_results_file=dict(required=False, type='str'),
        section=dict(required=False, type='str'),
        show_command=dict(required=False, type='str'),
        row_id=dict(required=False, type='str'),
        element_key1=dict(required=False, type='str'),
        element_key2=dict(required=False, type='str'),
        save_snapshot_locally=dict(required=False, type='bool',
                                       default=False),
        path=dict(required=False, type='str', default='./')
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                                mutually_exclusive=[['delete_all',
                                                     'delete_snapshot']],
                                supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)


    action = module.params['action']
    comparison_results_file = module.params['comparison_results_file']

    CREATE_PARAMS = ['snapshot_name', 'description']
    ADD_PARAMS = ['section', 'show_command', 'row_id', 'element_key1']
    COMPARE_PARAMS = ['snapshot1', 'snapshot2', 'comparison_results_file']

    if not os.path.isdir(module.params['path']):
        module.fail_json(msg='{0} is not a valid directory name.'.format(
            module.params['path']))

    if action == 'create':
        for param in CREATE_PARAMS:
            if not module.params[param]:
                module.fail_json(msg='snapshot_name and description are '
                                     'required when action=create')
    elif action == 'add':
        for param in ADD_PARAMS:
            if not module.params[param]:
                module.fail_json(msg='section, show_command, row_id '
                                     'and element_key1 are required '
                                     'when action=add')
    elif action == 'compare':
        for param in COMPARE_PARAMS:
            if not module.params[param]:
                module.fail_json(msg='snapshot1 and snapshot2 are required '
                                     'when action=create')
    elif action == 'delete' and not module.params['snapshot_name']:
        module.fail_json(msg='snapshot_name is required when action=delete')

    existing_snapshots = invoke('get_existing', module)
    final_snapshots = existing_snapshots
    changed = False

    action_results = invoke('action_%s' % action, module, existing_snapshots)

    result = {}
    written_file = ''
    if module.check_mode and action != 'compare':
        module.exit_json(changed=True, commands=action_results)
    else:
        if action == 'compare':
            written_file = write_on_file(action_results,
                          module.params['comparison_results_file'],
                module)
            result['updates'] = []
        else:
            if action_results:
                load_config(module, action_results)
                changed = True
                final_snapshots = invoke('get_existing', module)
                result['updates'] = action_results

                if (action == 'create' and
                    module.params['save_snapshot_locally']):
                    snapshot = get_snapshot(module)
                    written_file = write_on_file(snapshot,
                                    module.params['snapshot_name'], module)

    result['connected'] = module.connected
    result['changed'] = changed
    if module._verbosity > 0:
        end_state = invoke('get_existing', module)
        result['final_snapshots'] = final_snapshots
        result['existing_snapshots'] = existing_snapshots
        if written_file:
            result['report_file'] = written_file

    module.exit_json(**result)


if __name__ == '__main__':
    main()

