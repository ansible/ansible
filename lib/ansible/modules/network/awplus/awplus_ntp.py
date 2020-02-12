#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2020, Allied Telesis Ltd.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: awplus_ntp
version_added: "2.10"
short_description: Manages core NTP configuration.
description:
    - Manages core NTP configuration.
author:
    - Cheng Yi Kok (@cyk19)
    - Isaac Daly (@dalyIsaac)
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
            - Enable NTP auhentication. Data type boolean.
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
notes:
    - Check mode is supported.
"""


EXAMPLES = """
commands:
   - name: testing out ntp module
     awplus_ntp:
        server: 192.168.5.2
        source_int: 192.66.44.33
        restrict: 192.155.56.4 allow
        state: present
        auth_key: ajsdlksa
        key_id: 8900
"""


RETURN = """
commands:
    description: The list of commands to send to the device
    returned: always
    type: list
    sample: ['ntp server 192.0.1.23']
"""

from ansible.module_utils.network.awplus.awplus import awplus_argument_spec
from ansible.module_utils.network.awplus.awplus import get_config, load_config
from ansible.module_utils.basic import AnsibleModule
import re


def map_obj_to_commands(want, have, module):

    commands = list()

    server_have = have[0].get('server', None)
    source_int_have = have[0].get('source_int', None)
    restrict_have = have[0].get('restrict', None)
    auth_have = have[0].get('auth', None)
    auth_key_have = have[0].get('auth_key', None)
    key_id_have = have[0].get('key_id', None)

    for w in want:
        server = w['server']
        source_int = w['source_int']
        restrict = w['restrict']
        state = w['state']
        auth = w['auth']
        auth_key = w['auth_key']
        key_id = w['key_id']

        if state == 'absent':
            if server_have and server in server_have:
                commands.append('no ntp server {0}'.format(server))
            if source_int and source_int_have:
                commands.append('no ntp source')
            if restrict and restrict_have:
                commands.append('no ntp restrict {0}'.format(restrict))
            if auth is True and auth_have:
                commands.append('no ntp authenticate')
            if auth_key and auth_key_have:
                if key_id and key_id_have:
                    commands.append(
                        'no ntp authentication-key {0} md5 {1}'.format(key_id, auth_key))

        elif state == 'present':
            if server is not None and server not in server_have:
                commands.append('ntp server {0}'.format(server))
            if source_int is not None and source_int != source_int_have:
                commands.append('ntp source {0}'.format(source_int))
            if restrict is not None and restrict != restrict_have:
                commands.append('ntp restrict {0}'.format(restrict))
            if auth_key is not None and auth_key != auth_key_have:
                if key_id is not None:
                    commands.append(
                        'ntp authentication-key {0} md5 {1}'.format(key_id, auth_key))

    return commands


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


def parse_restrict(line, dest):
    if dest == 'restrict':
        match = re.search(
            r'(ntp restrict )(\d+\.\d+\.\d+\.\d+ \w+)', line, re.M)
        if match:
            restrict = match.group(2)
            return restrict


def parse_auth_key(line, dest):
    if dest == 'authentication-key':
        print('not working')
        match = re.search(
            r'ntp authentication-key (\d+) (md5|sha1) (\w+)', line, re.M)
        if match:
            key_id = match.group(1)
            auth_key = match.group(3)
            return key_id, auth_key
    else:
        return (None, None)


def parse_auth(dest):
    return dest == 'authenticate-key'


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
            restrict = parse_restrict(line, dest)
            auth = parse_auth(dest)
            key_id, auth_key = parse_auth_key(line, dest)

            if server:
                server_list.append(server)
            if source_int:
                obj_dict['source_int'] = source_int
            if restrict:
                obj_dict['restrict'] = restrict
            if auth:
                obj_dict['auth'] = auth
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
        'restrict': module.params['restrict'],
        'auth': module.params['auth'],
        'auth_key': module.params['auth_key'],
        'key_id': module.params['key_id']
    })

    return obj


def main():

    argument_spec = dict(
        server=dict(),
        source_int=dict(),
        restrict=dict(),
        auth=dict(type='bool', default=False),
        auth_key=dict(),
        key_id=dict(),
        state=dict(choices=['absent', 'present'], default='present')
    )

    argument_spec.update(awplus_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    result = {'changed': False}

    warnings = list()
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
