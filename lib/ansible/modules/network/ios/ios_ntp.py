#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

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
            - Source interface for NTP packets.
    acl:
        description:
            - ACL for peer/server access restricition.
    logging:
        description:
            - Enable NTP logs. Data type boolean.
        type: bool
        default: False
    auth:
        description:
            - Enable NTP authentication. Data type boolean.
        type: bool
        default: False
    auth_key:
        description:
            - md5 NTP authentication key of type 7.
    key_id:
        description:
            - auth_key id. Data type string
    state:
        description:
            - Manage the state of the resource.
        default: present
        choices: ['present', 'absent']
'''

EXAMPLES = '''
# Set new NTP server and source interface
- ios_ntp:
    server: 10.0.255.10
    source_int: Loopback0
    logging: false
    state: present

# Remove NTP ACL and logging
- ios_ntp:
    acl: NTP_ACL
    logging: true
    state: absent

# Set NTP authentication
- ios_ntp:
    key_id: 10
    auth_key: 15435A030726242723273C21181319000A
    auth: true
    state: present

# Set new NTP configuration
- ios_ntp:
    server: 10.0.255.10
    source_int: Loopback0
    acl: NTP_ACL
    logging: true
    key_id: 10
    auth_key: 15435A030726242723273C21181319000A
    auth: true
    state: present
'''

RETURN = '''
commands:
    description: command sent to the device
    returned: always
    type: list
    sample: ["no ntp server 10.0.255.10", "no ntp source Loopback0"]
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
        match = re.search(r'ntp access-group (?:peer|serve)(?:\s+)(\S+)', line, re.M)
        if match:
            acl = match.group(1)
            return acl


def parse_logging(line, dest):
    if dest == 'logging':
        logging = dest
        return logging


def parse_auth_key(line, dest):
    if dest == 'authentication-key':
        match = re.search(r'(ntp authentication-key \d+ md5 )(\w+)', line, re.M)
        if match:
            auth_key = match.group(2)
            return auth_key


def parse_key_id(line, dest):
    if dest == 'trusted-key':
        match = re.search(r'(ntp trusted-key )(\d+)', line, re.M)
        if match:
            auth_key = match.group(2)
            return auth_key


def parse_auth(dest):
    if dest == 'authenticate':
        return dest


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
            logging = parse_logging(line, dest)
            auth = parse_auth(dest)
            auth_key = parse_auth_key(line, dest)
            key_id = parse_key_id(line, dest)

            if server:
                server_list.append(server)
            if source_int:
                obj_dict['source_int'] = source_int
            if acl:
                obj_dict['acl'] = acl
            if logging:
                obj_dict['logging'] = True
            if auth:
                obj_dict['auth'] = True
            if auth_key:
                obj_dict['auth_key'] = auth_key
            if key_id:
                obj_dict['key_id'] = key_id

    obj_dict['server'] = server_list
    obj.append(obj_dict)

    return obj


def map_params_to_obj(module):
    obj = []
    obj.append({
        'state': module.params['state'],
        'server': module.params['server'],
        'source_int': module.params['source_int'],
        'logging': module.params['logging'],
        'acl': module.params['acl'],
        'auth': module.params['auth'],
        'auth_key': module.params['auth_key'],
        'key_id': module.params['key_id']
    })

    return obj


def map_obj_to_commands(want, have, module):

    commands = list()

    server_have = have[0].get('server', None)
    source_int_have = have[0].get('source_int', None)
    acl_have = have[0].get('acl', None)
    logging_have = have[0].get('logging', None)
    auth_have = have[0].get('auth', None)
    auth_key_have = have[0].get('auth_key', None)
    key_id_have = have[0].get('key_id', None)

    for w in want:
        server = w['server']
        source_int = w['source_int']
        acl = w['acl']
        logging = w['logging']
        state = w['state']
        auth = w['auth']
        auth_key = w['auth_key']
        key_id = w['key_id']

        if state == 'absent':
            if server_have and server in server_have:
                commands.append('no ntp server {0}'.format(server))
            if source_int and source_int_have:
                commands.append('no ntp source {0}'.format(source_int))
            if acl and acl_have:
                commands.append('no ntp access-group peer {0}'.format(acl))
            if logging is True and logging_have:
                commands.append('no ntp logging')
            if auth is True and auth_have:
                commands.append('no ntp authenticate')
            if key_id and key_id_have:
                commands.append('no ntp trusted-key {0}'.format(key_id))
            if auth_key and auth_key_have:
                if key_id and key_id_have:
                    commands.append('no ntp authentication-key {0} md5 {1} 7'.format(key_id, auth_key))

        elif state == 'present':
            if server is not None and server not in server_have:
                commands.append('ntp server {0}'.format(server))
            if source_int is not None and source_int != source_int_have:
                commands.append('ntp source {0}'.format(source_int))
            if acl is not None and acl != acl_have:
                commands.append('ntp access-group peer {0}'.format(acl))
            if logging is not None and logging != logging_have and logging is not False:
                commands.append('ntp logging')
            if auth is not None and auth != auth_have and auth is not False:
                commands.append('ntp authenticate')
            if key_id is not None and key_id != key_id_have:
                commands.append('ntp trusted-key {0}'.format(key_id))
            if auth_key is not None and auth_key != auth_key_have:
                if key_id is not None:
                    commands.append('ntp authentication-key {0} md5 {1} 7'.format(key_id, auth_key))

    return commands


def main():

    argument_spec = dict(
        server=dict(),
        source_int=dict(),
        acl=dict(),
        logging=dict(type='bool', default=False),
        auth=dict(type='bool', default=False),
        auth_key=dict(no_log=True),
        key_id=dict(),
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
