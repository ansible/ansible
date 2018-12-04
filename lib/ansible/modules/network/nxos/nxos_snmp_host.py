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
    - Tested against NXOSv 7.3.(0)D1(1) on VIRL
    - C(state=absent) removes the host configuration if it is configured.
options:
    snmp_host:
        description:
            - IP address of hostname of target host.
        required: true
    version:
        description:
            - SNMP version. If this is not specified, v1 is used.
        choices: ['v1', 'v2c', 'v3']
    v3:
        description:
            - Use this when verion is v3. SNMPv3 Security level.
        choices: ['noauth', 'auth', 'priv']
    community:
        description:
            - Community string or v3 username.
    udp:
        description:
            - UDP port number (0-65535).
        default: 162
    snmp_type:
        description:
            - type of message to send to host. If this is not
              specified, trap type is used.
        choices: ['trap', 'inform']
    vrf:
        description:
            - VRF to use to source traffic to source.
              If state = absent, the vrf is removed.
    vrf_filter:
        description:
            - Name of VRF to filter.
              If state = absent, the vrf is removed from the filter.
    src_intf:
        description:
            - Source interface. Must be fully qualified interface name.
              If state = absent, the interface is removed.
    state:
        description:
            - Manage the state of the resource. If state = present, the
              host is added to the configuration. If only vrf and/or
              vrf_filter and/or src_intf are given, they will be added to
              the existing host configuration. If state = absent, the
              host is removed if community parameter is given. It is possible
              to remove only vrf and/or src_int and/or vrf_filter
              by providing only those parameters and no community parameter.
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''
# ensure snmp host is configured
- nxos_snmp_host:
    snmp_host: 192.0.2.3
    community: TESTING
    state: present
'''

RETURN = '''
commands:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["snmp-server host 192.0.2.3 filter-vrf another_test_vrf"]
'''


import re
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


def get_snmp_host(host, udp, module):
    body = execute_show_command('show snmp host', module)

    host_map = {
        'port': 'udp',
        'version': 'version',
        'level': 'v3',
        'type': 'snmp_type',
        'secname': 'community'
    }

    host_map_5k = {
        'port': 'udp',
        'version': 'version',
        'sec_level': 'v3',
        'notif_type': 'snmp_type',
        'commun_or_user': 'community'
    }

    resource = {}

    if body:
        try:
            resource_table = body[0]['TABLE_host']['ROW_host']

            if isinstance(resource_table, dict):
                resource_table = [resource_table]

            for each in resource_table:
                key = str(each['host']) + '_' + str(each['port']).strip()
                src = each.get('src_intf')
                host_resource = apply_key_map(host_map, each)

                if src:
                    host_resource['src_intf'] = src
                    if re.search(r'interface:', src):
                        host_resource['src_intf'] = src.split(':')[1].strip()

                vrf_filt = each.get('TABLE_vrf_filters')
                if vrf_filt:
                    vrf_filter = vrf_filt['ROW_vrf_filters']['vrf_filter'].split(':')[1].split(',')
                    filters = [vrf.strip() for vrf in vrf_filter]
                    host_resource['vrf_filter'] = filters

                vrf = each.get('vrf')
                if vrf:
                    host_resource['vrf'] = vrf.split(':')[1].strip()
                resource[key] = host_resource
        except KeyError:
            # Handle the 5K case
            try:
                resource_table = body[0]['TABLE_hosts']['ROW_hosts']

                if isinstance(resource_table, dict):
                    resource_table = [resource_table]

                for each in resource_table:
                    key = str(each['address']) + '_' + str(each['port']).strip()
                    src = each.get('src_intf')
                    host_resource = apply_key_map(host_map_5k, each)

                    if src:
                        host_resource['src_intf'] = src
                        if re.search(r'interface:', src):
                            host_resource['src_intf'] = src.split(':')[1].strip()

                    vrf = each.get('use_vrf_name')
                    if vrf:
                        host_resource['vrf'] = vrf.strip()

                    vrf_filt = each.get('TABLE_filter_vrf')
                    if vrf_filt:
                        vrf_filter = vrf_filt['ROW_filter_vrf']['filter_vrf_name'].split(',')
                        filters = [vrf.strip() for vrf in vrf_filter]
                        host_resource['vrf_filter'] = filters

                    resource[key] = host_resource
            except (KeyError, AttributeError, TypeError):
                return resource
        except (AttributeError, TypeError):
            return resource

        find = resource.get(host + '_' + udp)

        if find:
            fix_find = {}
            for (key, value) in find.items():
                if isinstance(value, str):
                    fix_find[key] = value.strip()
                else:
                    fix_find[key] = value
            return fix_find

    return {}


def remove_snmp_host(host, udp, existing):
    commands = []
    if existing['version'] == 'v3':
        existing['version'] = '3'
        command = 'no snmp-server host {0} {snmp_type} version \
                    {version} {v3} {community} udp-port {1}'.format(host, udp, **existing)

    elif existing['version'] == 'v2c':
        existing['version'] = '2c'
        command = 'no snmp-server host {0} {snmp_type} version \
                    {version} {community} udp-port {1}'.format(host, udp, **existing)

    elif existing['version'] == 'v1':
        existing['version'] = '1'
        command = 'no snmp-server host {0} {snmp_type} version \
                    {version} {community} udp-port {1}'.format(host, udp, **existing)

    if command:
        commands.append(command)
    return commands


def remove_vrf(host, udp, proposed, existing):
    commands = []
    if existing.get('vrf'):
        commands.append('no snmp-server host {0} use-vrf \
                    {1} udp-port {2}'.format(host, proposed.get('vrf'), udp))
    return commands


def remove_filter(host, udp, proposed, existing):
    commands = []
    if existing.get('vrf_filter'):
        if proposed.get('vrf_filter') in existing.get('vrf_filter'):
            commands.append('no snmp-server host {0} filter-vrf \
                    {1} udp-port {2}'.format(host, proposed.get('vrf_filter'), udp))
    return commands


def remove_src(host, udp, proposed, existing):
    commands = []
    if existing.get('src_intf'):
        commands.append('no snmp-server host {0} source-interface \
                    {1} udp-port {2}'.format(host, proposed.get('src_intf'), udp))
    return commands


def config_snmp_host(delta, udp, proposed, existing, module):
    commands = []
    command_builder = []
    host = proposed['snmp_host']
    cmd = 'snmp-server host {0}'.format(proposed['snmp_host'])

    snmp_type = delta.get('snmp_type')
    version = delta.get('version')
    ver = delta.get('v3')
    community = delta.get('community')

    command_builder.append(cmd)
    if any([snmp_type, version, ver, community]):
        type_string = snmp_type or existing.get('type')
        if type_string:
            command_builder.append(type_string)

        version = version or existing.get('version')
        if version:
            if version == 'v1':
                vn = '1'
            elif version == 'v2c':
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

        udp_string = ' udp-port {0}'.format(udp)
        command_builder.append(udp_string)

        cmd = ' '.join(command_builder)

        commands.append(cmd)

    CMDS = {
        'vrf_filter': 'snmp-server host {0} filter-vrf {vrf_filter} udp-port {1}',
        'vrf': 'snmp-server host {0} use-vrf {vrf} udp-port {1}',
        'src_intf': 'snmp-server host {0} source-interface {src_intf} udp-port {1}'
    }

    for key in delta:
        command = CMDS.get(key)
        if command:
            cmd = command.format(host, udp, **delta)
            commands.append(cmd)
    return commands


def main():
    argument_spec = dict(
        snmp_host=dict(required=True, type='str'),
        community=dict(type='str'),
        udp=dict(type='str', default='162'),
        version=dict(choices=['v1', 'v2c', 'v3']),
        src_intf=dict(type='str'),
        v3=dict(choices=['noauth', 'auth', 'priv']),
        vrf_filter=dict(type='str'),
        vrf=dict(type='str'),
        snmp_type=dict(choices=['trap', 'inform']),
        state=dict(choices=['absent', 'present'], default='present'),
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)
    results = {'changed': False, 'commands': [], 'warnings': warnings}

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

    existing = get_snmp_host(snmp_host, udp, module)

    if version is None:
        if existing:
            version = existing.get('version')
        else:
            version = 'v1'

    if snmp_type is None:
        if existing:
            snmp_type = existing.get('snmp_type')
        else:
            snmp_type = 'trap'

    if v3 is None:
        if version == 'v3' and existing:
            v3 = existing.get('v3')

    if snmp_type == 'inform' and version == 'v1':
        module.fail_json(msg='inform requires snmp v2c or v3')

    if (version == 'v1' or version == 'v2c') and v3:
        module.fail_json(msg='param: "v3" should not be used when '
                             'using version v1 or v2c')

    if not any([vrf_filter, vrf, src_intf]):
        if not all([snmp_type, version, community, udp]):
            module.fail_json(msg='when not configuring options like '
                                 'vrf_filter, vrf, and src_intf,'
                                 'the following params are required: '
                                 'type, version, community')

    if version == 'v3' and v3 is None:
        module.fail_json(msg='when using version=v3, the param v3 '
                             '(options: auth, noauth, priv) is also required')

    # existing returns the list of vrfs configured for a given host
    # checking to see if the proposed is in the list
    store = existing.get('vrf_filter')
    if existing and store:
        if vrf_filter not in existing['vrf_filter']:
            existing['vrf_filter'] = None
        else:
            existing['vrf_filter'] = vrf_filter
    commands = []

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

    if state == 'absent' and existing:
        if proposed.get('community'):
            commands.append(remove_snmp_host(snmp_host, udp, existing))
        else:
            if proposed.get('src_intf'):
                commands.append(remove_src(snmp_host, udp, proposed, existing))
            if proposed.get('vrf'):
                commands.append(remove_vrf(snmp_host, udp, proposed, existing))
            if proposed.get('vrf_filter'):
                commands.append(remove_filter(snmp_host, udp, proposed, existing))

    elif state == 'present':
        delta = dict(set(proposed.items()).difference(existing.items()))
        if delta:
            command = config_snmp_host(delta, udp, proposed, existing, module)
            commands.append(command)

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
