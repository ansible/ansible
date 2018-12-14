#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = '''
---
module: ios_ntp
extends_documentation_fragment: nxos
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
    peer:
        description:
            - Network address of NTP peer.
    source_int:
        description:
            - Source interface for NTP requests.  
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
    state: present
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
        match = re.search(r'(ntp server )(ip )?(\d+\.\d+\.\d+\.\d+)', line, re.M)
        if match:
            server = match.group(3)
            return server


def parse_peer(line, dest):
    if dest == 'peer':
        match = re.search(r'(ntp peer )(ip )?(\d+\.\d+\.\d+\.\d+)', line, re.M)
        if match:
            peer = match.group(3)
            return peer


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
    obj = []
    config = get_config(module, flags=['| include ntp'])
    for line in config.splitlines():
        match = re.search(r'ntp (\S+)', line, re.M)
        if match:
            dest = match.group(1)

            server = parse_server(line, dest)
            peer = parse_peer(line, dest)
            source_int = parse_source_int(line, dest)
            acl = parse_acl(line, dest)

            if server is not None:
                obj.append({'server': server})
            if peer is not None:
                obj.append({'peer': peer})
            if source_int is not None:
                obj.append({'source_int': source_int})
            if acl is not None:
                obj.append({'acl': acl})

    return obj

def map_params_to_obj(module, required_if=None):
    obj = []

    obj.append({
        'state': module.params['state'],
        'server': module.params['server'],
        'peer': module.params['peer'],
        'source_int': module.params['source_int'],
        'acl': module.params['acl']
            })
    return obj


def map_obj_to_commands(updates, module):
    commands = list()
    want, have = updates
    for w in want:
        server = w.get('server')
        peer = w.get('peer')
        source_int = w.get('source_int')
        acl = w.get('acl')
        state = w.get('state')

        if state == 'absent' and w in have:
            if server:
                commands.append('no ntp server {0}'.format(server))
            if peer:
                commands.append('no ntp peer {0}'.format(peer))
            if source_int:
                commands.append('no ntp source {0}'.format(source_int))
            if acl:
                commands.append('no ntp access-group peer {0}'.format(acl))

        elif state == 'present' and w not in have:
            if server:
                commands.append('ntp server {0}'.format(server))
            if peer:
                commands.append('ntp peer {0}'.format(peer))
            if source_int:
                commands.append('ntp source {0}'.format(source_int))
            if acl:
                commands.append('ntp access-group peer {0}'.format(acl))


    return commands


def main():

    argument_spec = dict(
        server=dict(type='str'),
        peer=dict(type='str'),
        source_int=dict(type='str'),
        acl=dict(type='str'),
        state=dict(choices=['absent', 'present'], default='present')
        )

    argument_spec.update(ios_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
        )

    warnings = list()
    check_args(module, warnings)

    result = {'changed': False}
    if warnings:
        result['warnings'] = warnings

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)
    commands = map_obj_to_commands((want, have), module)

    result['commands'] = commands

    if commands:
        if not module.check_mode:
            load_config(module, commands)
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
