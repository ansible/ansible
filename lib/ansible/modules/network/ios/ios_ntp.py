#!/usr/bin/python
import re

from copy import deepcopy
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


def parse_prefer(line, dest):
    if dest == 'server':
        match = re.search(r'(ntp server )(ip )?(\d+\.\d+\.\d+\.\d+)( prefer)', line, re.M)
        if match:
            prefer = match.group(3)
            return prefer


def parse_source_int(line, dest):
    if dest == 'source':
        match = re.search(r'(ntp source )(\S+)', line, re.M)
        if match:
            source = match.group(2)
            return source


def parse_logging(line, dest):
    if dest == 'logging':
        logging = dest
        return logging


def parse_acl(line, dest):
    if dest == 'access-group':
        match = re.search(r'(ntp access-group )(peer )?(serve )?(\S+)', line, re.M)
        if match:
            acl = match.group(3)
            return acl


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



def map_config_to_obj(module):
    obj = []
    config = get_config(module, flags=['| include ntp'])
    for line in config.splitlines():
        match = re.search(r'ntp (\S+)', line, re.M)
        if match:
            dest = match.group(1)

            obj.append({
                'server': parse_server(line, dest),
                'peer': parse_peer(line, dest),
                'prefer': parse_prefer(line, dest),
                'source_int': parse_source_int(line, dest),
                'logging': parse_logging(line, dest),
                'acl': parse_acl(line, dest),
                'auth_key': parse_auth_key(line, dest),
                'key_id': parse_key_id(line, dest)
            })
    return obj


def map_params_to_obj(module, required_if=None):
    obj = []

    obj.append({
        'server': module.params['server'],
        'state': module.params['state'],
        'peer': module.params['peer'],
        'prefer': module.params['prefer'],
        'source_int': module.params['source_int'],
        'logging': module.params['logging'],
        'acl': module.params['acl'],
        'auth_key': module.params['auth_key'],
        'key_id': module.params['key_id'],
            })
    return obj


def map_obj_to_commands(updates, module):
    commands = list()
    want, have = updates
    for w in want:
        state = w['state']
        server = w['server']
        peer = w['peer']
        prefer = w['prefer']
        source_int = w['source_int']
        logging = w['logging']
        acl = w['acl']
        auth_key = w['auth_key']
        key_id = w['key_id']
        del w['state']

        if state == 'absent':
            if server and not prefer:
                commands.append('no ntp server {0}'.format(server))
            if peer and not prefer:
                commands.append('no ntp peer {0}'.format(peer))
            if prefer and server:
                commands.append('no ntp server {0} prefer'.format(server))
            if prefer and peer:
                commands.append('no ntp peer {0} prefer'.format(peer))
            if source_int:
                commands.append('no ntp source {0}'.format(source_int))
            if logging:
                commands.append('no ntp logging')
            if acl:
                commands.append('no ntp access-group peer {0}'.format(acl))
            if auth_key and key_id:
                commands.append('no ntp authentication-key {0}'.format(key_id, auth_key))
                commands.append('no ntp authenticate')
                commands.append('no ntp trusted-key {0}'.format(key_id))


        elif state == 'present' and w not in have:
            if server and not prefer:
                commands.append('ntp server {0}'.format(server))
            if peer and not prefer:
                commands.append('ntp peer {0}'.format(peer))
            if prefer and server:
                commands.append('ntp server {0} prefer'.format(server))
            if prefer and peer:
                commands.append('ntp peer {0} prefer'.format(peer))
            if source_int:
                commands.append('ntp source {0}'.format(source_int))
            if logging:
                commands.append('ntp logging')
            if acl:
                commands.append('ntp access-group peer {0}'.format(acl))
            if auth_key and key_id:
                commands.append('ntp authentication-key {0} md5 {1}'.format(key_id, auth_key))
                commands.append('ntp authenticate')
                commands.append('ntp trusted-key {0}'.format(key_id))

    return commands


def main():

    argument_spec = dict(
        server=dict(type='str'),
        peer=dict(type='str'),
        prefer=dict(type='bool'),
        source_int=dict(type='str'),
        logging=dict(type='str', choices=['enabled', 'disabled'], default='disabled'),
        acl=dict(type='str'),
        auth_key=dict(type='str'),
        key_id=dict(type='str'),
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
