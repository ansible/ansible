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
        choices: ['aaa', 'bfd', 'bgp', 'bridge', 'callhome', 'cfs', 'config',
          'eigrp', 'entity', 'feature-control', 'generic', 'hsrp', 'license',
          'link', 'lldp', 'mmode', 'ospf', 'pim', 'rf', 'rmon', 'snmp',
          'storm-control', 'stpx', 'switchfabric', 'syslog', 'sysmgr', 'system',
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
from ansible.module_utils.network.nxos.nxos import get_capabilities
from ansible.module_utils.basic import AnsibleModule


def get_platform_id(module):
    info = get_capabilities(module).get('device_info', {})
    return (info.get('network_os_platform', ''))


def execute_show_command(command, module):
    command = {
        'command': command,
        'output': 'text',
    }

    return run_commands(module, command)


def flatten_list(command_lists):
    flat_command_list = []
    for command in command_lists:
        if isinstance(command, list):
            flat_command_list.extend(command)
        else:
            flat_command_list.append(command)
    return flat_command_list


def get_snmp_traps(group, module):
    body = execute_show_command('show run snmp all', module)[0].split('\n')

    resource = {}
    feature_list = ['aaa', 'bfd', 'bgp', 'bridge', 'callhome', 'cfs', 'config',
                    'eigrp', 'entity', 'feature-control', 'generic', 'hsrp',
                    'license', 'link', 'lldp', 'mmode', 'ospf', 'pim',
                    'rf', 'rmon', 'snmp', 'storm-control', 'stpx',
                    'switchfabric', 'syslog', 'sysmgr', 'system', 'upgrade',
                    'vtp']

    if 'all' in group and 'N3K-C35' in get_platform_id(module):
        module.warn("Platform does not support bfd traps; bfd ignored for 'group: all' request")
        feature_list.remove('bfd')

    for each in feature_list:
        for line in body:
            if each == 'ospf':
                # ospf behaves differently when routers are present
                if 'snmp-server enable traps ospf' == line:
                    resource[each] = True
                    break
            else:
                if 'enable traps {0}'.format(each) in line:
                    if 'no ' in line:
                        resource[each] = False
                        break
                    else:
                        resource[each] = True

    for each in feature_list:
        if resource.get(each) is None:
            # on some platforms, the 'no' cmd does not
            # show up and so check if the feature is enabled
            body = execute_show_command('show run | inc feature', module)[0]
            if 'feature {0}'.format(each) in body:
                resource[each] = False

    find = resource.get(group, None)

    if group == 'all'.lower():
        return resource
    elif find is not None:
        trap_resource = {group: find}
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
                if existing[feature]:
                    trap_command = 'no snmp-server enable traps {0}'.format(feature)
                    commands.append(trap_command)

        elif state == 'enabled':
            for feature in existing:
                if existing[feature] is False:
                    trap_command = 'snmp-server enable traps {0}'.format(feature)
                    commands.append(trap_command)

    else:
        if group in existing:
            if existing[group]:
                enabled = True
            else:
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
        group=dict(choices=['aaa', 'bfd', 'bgp', 'bridge', 'callhome', 'cfs', 'config',
                            'eigrp', 'entity', 'feature-control', 'generic', 'hsrp',
                            'license', 'link', 'lldp', 'mmode', 'ospf', 'pim',
                            'rf', 'rmon', 'snmp', 'storm-control', 'stpx',
                            'switchfabric', 'syslog', 'sysmgr', 'system', 'upgrade',
                            'vtp', 'all'],
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
