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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = '''
---
module: nxos_snmp_traps
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages SNMP traps.
description:
    - Manages SNMP traps configurations.
author:
    - Jason Edelman (@jedelman8)
notes:
    - Tested against NXOSv 7.3.(0)D1(1) on VIRL
    - This module works at the group level for traps.  If you need to only
      enable/disable 1 specific trap within a group, use the M(nxos_command)
      module.
    - Be aware that you can set a trap only for an enabled feature.
options:
    group:
        description:
            - Case sensitive group.
        required: true
        choices: ['aaa', 'bridge', 'callhome', 'cfs', 'config', 'entity',
          'feature-control', 'hsrp', 'license', 'link', 'lldp', 'ospf', 'pim',
          'rf', 'rmon', 'snmp', 'storm-control', 'stpx', 'sysmgr', 'system',
          'upgrade', 'vtp', 'all']
    state:
        description:
            - Manage the state of the resource.
        required: false
        default: enabled
        choices: ['enabled','disabled']
'''

EXAMPLES = '''
# ensure lldp trap configured
- nxos_snmp_traps:
    group: lldp
    state: enabled

# ensure lldp trap is not configured
- nxos_snmp_traps:
    group: lldp
    state: disabled
'''

RETURN = '''
commands:
    description: command sent to the device
    returned: always
    type: list
    sample: "snmp-server enable traps lldp ;"
'''


from ansible.module_utils.network.nxos.nxos import load_config, run_commands
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule


def execute_show_command(command, module):
    command = {
        'command': command,
        'output': 'json',
    }

    return run_commands(module, command)


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


def flatten_list(command_lists):
    flat_command_list = []
    for command in command_lists:
        if isinstance(command, list):
            flat_command_list.extend(command)
        else:
            flat_command_list.append(command)
    return flat_command_list


def get_snmp_traps(group, module):
    body = execute_show_command('show snmp trap', module)

    trap_key = {
        'description': 'trap',
        'isEnabled': 'enabled'
    }

    trap_key_5k = {
        'trap': 'trap',
        'enabled': 'enabled'
    }

    resource = {}
    feature_list = ['aaa', 'bridge', 'callhome', 'cfs', 'config',
                    'entity', 'feature-control', 'hsrp', 'license',
                    'link', 'lldp', 'ospf', 'pim', 'rf', 'rmon',
                    'snmp', 'storm-control', 'stpx', 'sysmgr',
                    'system', 'upgrade', 'vtp']
    try:
        resource_table = body[0]['TABLE_snmp_trap']['ROW_snmp_trap']

        for each_feature in feature_list:
            resource[each_feature] = []

        for each_resource in resource_table:
            key = str(each_resource['trap_type'])
            mapped_trap = apply_key_map(trap_key, each_resource)

            if key != 'Generic':
                resource[key].append(mapped_trap)
    except KeyError:
        try:
            resource_table = body[0]['TABLE_mib']['ROW_mib']

            for each_feature in feature_list:
                resource[each_feature] = []

            for each_resource in resource_table:
                key = str(each_resource['mib'])
                each_resource = each_resource['TABLE_trap']['ROW_trap']
                mapped_trap = apply_key_map(trap_key_5k, each_resource)

                if key != 'Generic':
                    resource[key].append(mapped_trap)
        except (KeyError, AttributeError):
            return resource
    except AttributeError:
        return resource

    find = resource.get(group, None)

    if group == 'all'.lower():
        return resource
    elif find:
        trap_resource = {group: resource[group]}
        return trap_resource
    else:
        # if 'find' is None, it means that 'group' is a
        # currently disabled feature.
        return {}


def get_trap_commands(group, state, existing, module):
    commands = []
    enabled = False
    disabled = False

    if group == 'all':
        if state == 'disabled':
            for feature in existing:
                trap_commands = ['no snmp-server enable traps {0}'.format(feature) for
                                 trap in existing[feature] if trap['enabled'] == 'Yes']
                trap_commands = list(set(trap_commands))
                commands.append(trap_commands)

        elif state == 'enabled':
            for feature in existing:
                trap_commands = ['snmp-server enable traps {0}'.format(feature) for
                                 trap in existing[feature] if trap['enabled'] == 'No']
                trap_commands = list(set(trap_commands))
                commands.append(trap_commands)

    else:
        if group in existing:
            for each_trap in existing[group]:
                check = each_trap['enabled']
                if check.lower() == 'yes':
                    enabled = True
                if check.lower() == 'no':
                    disabled = True

            if state == 'disabled' and enabled:
                commands.append(['no snmp-server enable traps {0}'.format(group)])
            elif state == 'enabled' and disabled:
                commands.append(['snmp-server enable traps {0}'.format(group)])
        else:
            module.fail_json(msg='{0} is not a currently '
                                 'enabled feature.'.format(group))

    return commands


def main():
    argument_spec = dict(
        state=dict(choices=['enabled', 'disabled'], default='enabled'),
        group=dict(choices=['aaa', 'bridge', 'callhome', 'cfs', 'config',
                            'entity', 'feature-control', 'hsrp',
                            'license', 'link', 'lldp', 'ospf', 'pim', 'rf',
                            'rmon', 'snmp', 'storm-control', 'stpx',
                            'sysmgr', 'system', 'upgrade', 'vtp', 'all'],
                   required=True),
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)
    results = {'changed': False, 'commands': [], 'warnings': warnings}

    group = module.params['group'].lower()
    state = module.params['state']

    existing = get_snmp_traps(group, module)

    commands = get_trap_commands(group, state, existing, module)
    cmds = flatten_list(commands)
    if cmds:
        results['changed'] = True
        if not module.check_mode:
            load_config(module, cmds)

        if 'configure' in cmds:
            cmds.pop(0)
        results['commands'] = cmds

    module.exit_json(**results)


if __name__ == '__main__':
    main()
