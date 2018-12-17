#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = '''
---
module: ios_ntp
extends_documentation_fragment: ios
version_added: "2.8"
short_description: Manages core NTP configuration.
description:
    - Manages core NTP configuration.
author:
    - Federico Olivieri (@Federico87)
options:
    server:
        description:
            - Network address of NTP server.
    source_int:
        description:
            - Interface for sourcing NTP packets.
    acl:
        description:
            - ACL for peer/server access restricition.
    state:
        description:
            - Manage the state of the resource.
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''
# Set NTP Server with parameters
- ios_ntp:
    server: 8.8.8.8
    source_int: Loopback0
    acl: NTP_ACL
    state: absent
    provider: "{{ staging }}"
'''

RETURN = '''
commands:
    description: command sent to the device
    returned: always
    type: list
    sample: ["ntp server 192.0.2.2 prefer key 48",
             "no ntp source-interface ethernet2/1", "ntp source 192.0.2.3"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.ios.ios import get_config, load_config
from ansible.module_utils.network.ios.ios import ios_argument_spec, check_args


def parse_server(line, dest):
    if dest == 'server':
        match = re.search(r'(ntp server )(\d+\.\d+\.\d+\.\d+)', line, re.M)
        if match:
            server = match.group(2)
            return server


def parse_source_int(line, dest):
    if dest == 'source':
        match = re.search(r'(ntp source )(\S+)', line, re.M)
        if match:
            source = match.group(2)
            return source


def parse_acl(line, dest):
    if dest == 'access-group':
        match = re.search(r'(ntp access-group )(peer )?(serve )?(\S+)', line, re.M)
        if match:
            acl = match.group(4)
            return acl


def map_config_to_obj(module):
    obj_dict = {}
    obj = []
    server_list = []
    config = get_config(module, flags=['| include ntp'])
    for line in config.splitlines():
        match = re.search(r'ntp (\S+)', line, re.M)
        if match:
            dest = match.group(1)

            server = parse_server(line, dest)
            source_int = parse_source_int(line, dest)
            acl = parse_acl(line, dest)

            if server:
                server_list.append(server)
            if source_int:
                obj_dict['source_int'] = source_int
            if acl:
                obj_dict['acl'] = acl

    obj_dict['server'] = server_list
    obj.append(obj_dict)

    return obj


def map_params_to_obj(module):
    obj = []
    obj.append({
        'state': module.params['state'],
        'server': module.params['server'],
        'source_int': module.params['source_int'],
        'acl': module.params['acl']
    })

    return obj


def map_obj_to_commands(want, have, module):
    commands = list()
    server_have = have[0]['server']
    try:
        source_int_have = have[0]['source_int']
    except KeyError:
        source_int_have = None
    try:
        acl_have = have[0]['acl']
    except KeyError:
        acl_have = None

    for w in want:
        server = w['server']
        source_int = w['source_int']
        acl = w['acl']
        state = w['state']

        if state == 'absent':
            if server in server_have:
                commands.append('no ntp server {0}'.format(server))
            if source_int and source_int_have:
                commands.append('no ntp source {0}'.format(source_int))
            if acl and acl_have:
                commands.append('no ntp access-group peer {0}'.format(acl))

        elif state == 'present':
            if server not in server_have:
                commands.append('ntp server {0}'.format(server))
            if source_int != source_int_have:
                commands.append('ntp source {0}'.format(source_int))
            if acl != acl_have:
                commands.append('ntp access-group peer {0}'.format(acl))

    return commands


def main():

    argument_spec = dict(
        server=dict(type='str'),
        source_int=dict(type='str'),
        acl=dict(type='str'),
        state=dict(choices=['absent', 'present'], default='present')
        )

    argument_spec.update(ios_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
        )

    result = {'changed': False}

    warnings = list()
    check_args(module, warnings)
    if warnings:
        result['warnings'] = warnings

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)

    commands = map_obj_to_commands(want, have, module)
    result['commands'] = commands

    if commands:
        if not module.check_mode:
            load_config(module, commands)
            result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
