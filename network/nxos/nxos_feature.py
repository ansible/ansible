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

DOCUMENTATION = '''
---
module: nxos_feature
version_added: "2.1"
short_description: Manage features in NX-OS switches
description:
    - Offers ability to enable and disable features in NX-OS
extends_documentation_fragment: nxos
author: Jason Edelman (@jedelman8), Gabriele Gerbino (@GGabriele)
options:
    feature:
        description:
            - Name of feature
        required: true
    state:
        description:
            - Desired state of the feature
        required: false
        default: 'enabled'
        choices: ['enabled','disabled']
'''

EXAMPLES = '''
# Ensure lacp is enabled
- nxos_feature: feature=lacp state=enabled host={{ inventory_hostname }}
# Ensure ospf is disabled
- nxos_feature: feature=ospf state=disabled host={{ inventory_hostname }}
# Ensure vpc is enabled
- nxos_feature: feature=vpc state=enabled host={{ inventory_hostname }}
'''

RETURN = '''
proposed:
    description: proposed feature state
    returned: always
    type: dict
    sample: {"state": "disabled"}
existing:
    description: existing state of feature
    returned: always
    type: dict
    sample: {"state": "enabled"}
end_state:
    description: feature state after executing module
    returned: always
    type: dict
    sample: {"state": "disabled"}
state:
    description: state as sent in from the playbook
    returned: always
    type: string
    sample: "disabled"
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["no feature eigrp"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
feature:
    description: the feature that has been examined
    returned: always
    type: string
    sample: "vpc"
'''


def execute_config_command(commands, module):
    try:
        module.configure(commands)
    except ShellError: 
        clie = get_exception()
        module.fail_json(msg='Error sending CLI commands',
                         error=str(clie), commands=commands)


def get_cli_body_ssh(command, response, module):
    """Get response for when transport=cli.  This is kind of a hack and mainly
    needed because these modules were originally written for NX-API.  And
    not every command supports "| json" when using cli/ssh.  As such, we assume
    if | json returns an XML string, it is a valid command, but that the
    resource doesn't exist yet.
    """
    if 'xml' in response[0]:
        body = []
    else:
        try:
            body = [json.loads(response[0])]
        except ValueError:
            module.fail_json(msg='Command does not support JSON output',
                             command=command)
    return body


def execute_show(cmds, module, command_type=None):
    try:
        if command_type:
            response = module.execute(cmds, command_type=command_type)
        else:
            response = module.execute(cmds)
    except ShellError:
        clie = get_exception()
        module.fail_json(msg='Error sending {0}'.format(cmds),
                         error=str(clie))
    return response


def execute_show_command(command, module, command_type='cli_show'):
    if module.params['transport'] == 'cli':
        command += ' | json'
        cmds = [command]
        response = execute_show(cmds, module)
        body = get_cli_body_ssh(command, response, module)
    elif module.params['transport'] == 'nxapi':
        cmds = [command]
        body = execute_show(cmds, module, command_type=command_type)

    return body


def apply_key_map(key_map, table):
    new_dict = {}
    for key, value in table.items():
        new_key = key_map.get(key)
        if new_key:
            value = table.get(key)
            if value:
                new_dict[new_key] = str(value)
            else:
                new_dict[new_key] = value
    return new_dict


def get_available_features(feature, module):
    available_features = {}
    command = 'show feature'
    body = execute_show_command(command, module)

    try:
        body = body[0]['TABLE_cfcFeatureCtrlTable']['ROW_cfcFeatureCtrlTable']
    except (TypeError, IndexError):
        return available_features

    for each_feature in body:
        feature = each_feature['cfcFeatureCtrlName2']
        state = each_feature['cfcFeatureCtrlOpStatus2']

        if 'enabled' in state:
            state = 'enabled'

        if feature not in available_features.keys():
            available_features[feature] = state
        else:
            if (available_features[feature] == 'disabled' and
                    state == 'enabled'):
                available_features[feature] = state

    return available_features


def get_commands(proposed, existing, state, module):
    feature = validate_feature(module, mode='config')

    commands = []
    feature_check = proposed == existing
    if not feature_check:
        if state == 'enabled':
            command = 'feature {0}'.format(feature)
            commands.append(command)
        elif state == 'disabled':
            command = "no feature {0}".format(feature)
            commands.append(command)
    return commands


def validate_feature(module, mode='show'):
    '''Some features may need to be mapped due to inconsistency
    between how they appear from "show feature" output and
    how they are configured'''

    feature = module.params['feature']

    feature_to_be_mapped = {
        'show': {
                'nv overlay': 'nve'},
        'config':
                {
                'nve': 'nv overlay'}
        }

    if feature in feature_to_be_mapped[mode]:
        feature = feature_to_be_mapped[mode][feature]

    return feature


def main():
    argument_spec = dict(
            feature=dict(type='str', required=True),
            state=dict(choices=['enabled', 'disabled'], default='enabled',
                       required=False),
    )
    module = get_module(argument_spec=argument_spec,
                        supports_check_mode=True)

    feature = validate_feature(module)
    state = module.params['state'].lower()

    available_features = get_available_features(feature, module)
    if feature not in available_features.keys():
        module.fail_json(
            msg='Invalid feature name.',
            features_currently_supported=available_features,
            invalid_feature=feature)
    else:
        existstate = available_features[feature]

        existing = dict(state=existstate)
        proposed = dict(state=state)
        changed = False
        end_state = existing

        cmds = get_commands(proposed, existing, state, module)

        if cmds:
            if module.check_mode:
                module.exit_json(changed=True, commands=cmds)
            else:
                execute_config_command(cmds, module)
                changed = True
                updated_features = get_available_features(feature, module)
                existstate = updated_features[feature]
                end_state = dict(state=existstate)

    results = {}
    results['proposed'] = proposed
    results['existing'] = existing
    results['end_state'] = end_state
    results['state'] = state
    results['updates'] = cmds
    results['changed'] = changed
    results['feature'] = module.params['feature']

    module.exit_json(**results)


from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.shell import *
from ansible.module_utils.netcfg import *
from ansible.module_utils.nxos import *
if __name__ == '__main__':
    main()
