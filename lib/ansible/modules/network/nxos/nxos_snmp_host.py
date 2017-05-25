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


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: nxos_snmp_host
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages SNMP host configuration.
description:
    - Manages SNMP host configuration parameters.
author:
    - Jason Edelman (@jedelman8)
    - Gabriele Gerbino (@GGabriele)
notes:
    - C(state=absent) removes the host configuration if it is configured.
options:
    snmp_host:
        description:
            - IP address of hostname of target host.
        required: true
    version:
        description:
            - SNMP version.
        required: false
        default: v2c
        choices: ['v2c', 'v3']
    community:
        description:
            - Community string or v3 username.
        required: false
        default: null
    udp:
        description:
            - UDP port number (0-65535).
        required: false
        default: null
    type:
        description:
            - type of message to send to host.
        required: false
        default: traps
        choices: ['trap', 'inform']
    vrf:
        description:
            - VRF to use to source traffic to source.
        required: false
        default: null
    vrf_filter:
        description:
            - Name of VRF to filter.
        required: false
        default: null
    src_intf:
        description:
            - Source interface.
        required: false
        default: null
    state:
        description:
            - Manage the state of the resource.
        required: true
        default: present
        choices: ['present','absent']

'''

EXAMPLES = '''
# ensure snmp host is configured
- nxos_snmp_host:
    snmp_host: 3.3.3.3
    community: TESTING
    state: present
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"community": "TESTING", "snmp_host": "3.3.3.3",
            "snmp_type": "trap", "version": "v2c", "vrf_filter": "one_more_vrf"}
existing:
    description: k/v pairs of existing snmp host
    returned: always
    type: dict
    sample: {"community": "TESTING", "snmp_type": "trap",
            "udp": "162", "v3": "noauth", "version": "v2c",
            "vrf": "test_vrf", "vrf_filter": ["test_vrf",
            "another_test_vrf"]}
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict
    sample: {"community": "TESTING", "snmp_type": "trap",
            "udp": "162", "v3": "noauth", "version": "v2c",
            "vrf": "test_vrf", "vrf_filter": ["test_vrf",
            "another_test_vrf", "one_more_vrf"]}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["snmp-server host 3.3.3.3 filter-vrf another_test_vrf"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''


from ansible.module_utils.nxos import get_config, load_config, run_commands
from ansible.module_utils.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule


import re
import re


def execute_show_command(command, module, command_type='cli_show'):
    if module.params['transport'] == 'cli':
        if 'show run' not in command:
            command += ' | json'
        cmds = [command]
        body = run_commands(module, cmds)
    elif module.params['transport'] == 'nxapi':
        cmds = [command]
        body = run_commands(module, cmds)

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


def get_snmp_host(host, module):
    command = 'show snmp host'
    body = execute_show_command(command, module)

    host_map = {
        'port': 'udp',
        'version': 'version',
        'level': 'v3',
        'type': 'snmp_type',
        'secname': 'community'
    }

    resource = {}

    if body:
        try:
            resource_table = body[0]['TABLE_host']['ROW_host']

            if isinstance(resource_table, dict):
                resource_table = [resource_table]

            for each in resource_table:
                key = str(each['host'])
                src = each.get('src_intf', None)
                host_resource = apply_key_map(host_map, each)

                if src:
                    host_resource['src_intf'] = src.split(':')[1].strip()

                vrf_filt = each.get('TABLE_vrf_filters', None)
                if vrf_filt:
                    vrf_filter = vrf_filt['ROW_vrf_filters']['vrf_filter'].split(':')[1].split(',')
                    filters = [vrf.strip() for vrf in vrf_filter]
                    host_resource['vrf_filter'] = filters

                vrf = each.get('vrf', None)
                if vrf:
                    host_resource['vrf'] = vrf.split(':')[1].strip()
                resource[key] = host_resource

        except (KeyError, AttributeError, TypeError):
            return resource

        find = resource.get(host, None)

        if find:
            fix_find = {}
            for (key, value) in find.items():
                if isinstance(value, str):
                    fix_find[key] = value.strip()
                else:
                    fix_find[key] = value
            return fix_find
        else:
            return {}
    else:
        return {}


def remove_snmp_host(host, existing):
    commands = []
    if existing['version'] == 'v3':
        existing['version'] = '3'
        command = 'no snmp-server host {0} {snmp_type} version \
                    {version} {v3} {community}'.format(host, **existing)

    elif existing['version'] == 'v2c':
        existing['version'] = '2c'
        command = 'no snmp-server host {0} {snmp_type} version \
                    {version} {community}'.format(host, **existing)

    if command:
        commands.append(command)
    return commands


def config_snmp_host(delta, proposed, existing, module):
    commands = []
    command_builder = []
    host = proposed['snmp_host']
    cmd = 'snmp-server host {0}'.format(proposed['snmp_host'])

    snmp_type = delta.get('snmp_type', None)
    version = delta.get('version', None)
    ver = delta.get('v3', None)
    community = delta.get('community', None)

    command_builder.append(cmd)
    if any([snmp_type, version, ver, community]):
        type_string = snmp_type or existing.get('type')
        if type_string:
            command_builder.append(type_string)

        version = version or existing.get('version')
        if version:
            if version == 'v2c':
                vn = '2c'
            elif version == 'v3':
                vn = '3'

            version_string = 'version {0}'.format(vn)
            command_builder.append(version_string)

        if ver:
            ver_string = ver or existing.get('v3')
            command_builder.append(ver_string)

        if community:
            community_string = community or existing.get('community')
            command_builder.append(community_string)

        cmd = ' '.join(command_builder)

        commands.append(cmd)

    CMDS = {
        'vrf_filter': 'snmp-server host {0} filter-vrf {vrf_filter}',
        'vrf': 'snmp-server host {0} use-vrf {vrf}',
        'udp': 'snmp-server host {0} udp-port {udp}',
        'src_intf': 'snmp-server host {0} source-interface {src_intf}'
    }

    for key, value in delta.items():
        if key in ['vrf_filter', 'vrf', 'udp', 'src_intf']:
            command = CMDS.get(key, None)
            if command:
                cmd = command.format(host, **delta)
                commands.append(cmd)
            cmd = None
    return commands


def flatten_list(command_lists):
    flat_command_list = []
    for command in command_lists:
        if isinstance(command, list):
            flat_command_list.extend(command)
        else:
            flat_command_list.append(command)
    return flat_command_list


def main():
    argument_spec = dict(
        snmp_host=dict(required=True, type='str'),
        community=dict(type='str'),
        udp=dict(type='str'),
        version=dict(choices=['v2c', 'v3'], default='v2c'),
        src_intf=dict(type='str'),
        v3=dict(choices=['noauth', 'auth', 'priv']),
        vrf_filter=dict(type='str'),
        vrf=dict(type='str'),
        snmp_type=dict(choices=['trap', 'inform'], default='trap'),
        state=dict(choices=['absent', 'present'], default='present'),
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                                supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)



    snmp_host = module.params['snmp_host']
    community = module.params['community']
    udp = module.params['udp']
    version = module.params['version']
    src_intf = module.params['src_intf']
    v3 = module.params['v3']
    vrf_filter = module.params['vrf_filter']
    vrf = module.params['vrf']
    snmp_type = module.params['snmp_type']

    state = module.params['state']

    if snmp_type == 'inform' and version != 'v3':
        module.fail_json(msg='inform requires snmp v3')

    if version == 'v2c' and v3:
        module.fail_json(msg='param: "v3" should not be used when '
                             'using version v2c')

    if not any([vrf_filter, vrf, udp, src_intf]):
        if not all([snmp_type, version, community]):
            module.fail_json(msg='when not configuring options like '
                                 'vrf_filter, vrf, udp, and src_intf,'
                                 'the following params are required: '
                                 'type, version, community')

    if version == 'v3' and v3 is None:
        module.fail_json(msg='when using version=v3, the param v3 '
                             '(options: auth, noauth, priv) is also required')

    existing = get_snmp_host(snmp_host, module)

    # existing returns the list of vrfs configured for a given host
    # checking to see if the proposed is in the list
    store = existing.get('vrf_filter', None)
    if existing and store:
        if vrf_filter not in existing['vrf_filter']:
            existing['vrf_filter'] = None
        else:
            existing['vrf_filter'] = vrf_filter

    args = dict(
        community=community,
        snmp_host=snmp_host,
        udp=udp,
        version=version,
        src_intf=src_intf,
        vrf_filter=vrf_filter,
        v3=v3,
        vrf=vrf,
        snmp_type=snmp_type
        )

    proposed = dict((k, v) for k, v in args.items() if v is not None)

    delta = dict(set(proposed.items()).difference(existing.items()))

    changed = False
    commands = []
    end_state = existing

    if state == 'absent':
        if existing:
            command = remove_snmp_host(snmp_host, existing)
            commands.append(command)
    elif state == 'present':
        if delta:
            command = config_snmp_host(delta, proposed, existing, module)
            commands.append(command)

    cmds = flatten_list(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            load_config(module, cmds)
            end_state = get_snmp_host(snmp_host, module)
            if 'configure' in cmds:
                cmds.pop(0)

    if store:
        existing['vrf_filter'] = store

    results = {}
    results['proposed'] = proposed
    results['existing'] = existing
    results['end_state'] = end_state
    results['updates'] = cmds
    results['changed'] = changed
    results['warnings'] = warnings

    module.exit_json(**results)


if __name__ == "__main__":
    main()

