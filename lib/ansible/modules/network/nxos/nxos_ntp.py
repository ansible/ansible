#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = '''
---
module: nxos_ntp
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages core NTP configuration.
description:
    - Manages core NTP configuration.
author:
    - Jason Edelman (@jedelman8)
options:
    server:
        description:
            - Network address of NTP server.
    peer:
        description:
            - Network address of NTP peer.
    key_id:
        description:
            - Authentication key identifier to use with
              given NTP server or peer or keyword 'default'.
    prefer:
        description:
            - Makes given NTP server or peer the preferred
              NTP server or peer for the device.
        choices: ['enabled', 'disabled']
    vrf_name:
        description:
            - Makes the device communicate with the given
              NTP server or peer over a specific VRF or
              keyword 'default'.
    source_addr:
        description:
            - Local source address from which NTP messages are sent
              or keyword 'default'
    source_int:
        description:
            - Local source interface from which NTP messages are sent.
              Must be fully qualified interface name or keyword 'default'
    state:
        description:
            - Manage the state of the resource.
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''
# Set NTP Server with parameters
- nxos_ntp:
    server: 1.2.3.4
    key_id: 32
    prefer: enabled
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"address": "192.0.2.2", "key_id": "48",
            "peer_type": "server", "prefer": "enabled",
            "source": "192.0.2.3", "source_type": "source"}
existing:
    description:
        - k/v pairs of existing ntp server/peer
    returned: always
    type: dict
    sample: {"address": "192.0.2.2", "key_id": "32",
            "peer_type": "server", "prefer": "enabled",
            "source": "ethernet2/1", "source_type": "source-interface"}
end_state:
    description: k/v pairs of ntp info after module execution
    returned: always
    type: dict
    sample: {"address": "192.0.2.2", "key_id": "48",
            "peer_type": "server", "prefer": "enabled",
            "source": "192.0.2.3", "source_type": "source"}
updates:
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
from ansible.module_utils.network.nxos.nxos import check_args, load_config, nxos_argument_spec, run_commands


def execute_show_command(command, module, command_type='cli_show'):
    if 'show run' not in command:
        output = 'json'
    else:
        output = 'text'

    commands = [{
        'command': command,
        'output': output,
    }]
    return run_commands(module, commands)


def flatten_list(command_lists):
    flat_command_list = []
    for command in command_lists:
        if isinstance(command, list):
            flat_command_list.extend(command)
        else:
            flat_command_list.append(command)
    return flat_command_list


def get_ntp_source(module):
    source_type = None
    source = None
    command = 'show run | inc ntp.source'
    output = execute_show_command(command, module, command_type='cli_show_ascii')

    if output:
        try:
            if 'interface' in output[0]:
                source_type = 'source-interface'
            else:
                source_type = 'source'
            source = output[0].split()[2].lower()
        except (AttributeError, IndexError):
            source_type = None
            source = None

    return source_type, source


def get_ntp_peer(module):
    command = 'show run | inc ntp.(server|peer)'
    ntp_peer_list = []
    response = execute_show_command(
        command, module, command_type='cli_show_ascii')

    if response:
        if isinstance(response, list):
            ntp = response[0]
        else:
            ntp = response
        if ntp:
            ntp_regex = (
                r".*ntp\s(server\s(?P<address>\S+)|peer\s(?P<peer_address>\S+))"
                r"\s*((?P<prefer>prefer)\s*)?(use-vrf\s(?P<vrf_name>\S+)\s*)?"
                r"(key\s(?P<key_id>\d+))?.*"
            )

            split_ntp = ntp.splitlines()
            for peer_line in split_ntp:
                if 'access-group' in peer_line:
                    continue
                ntp_peer = {}
                try:
                    peer_address = None
                    vrf_name = 'default'
                    prefer = None
                    key_id = None
                    match_ntp = re.match(ntp_regex, peer_line, re.DOTALL)
                    group_ntp = match_ntp.groupdict()

                    address = group_ntp["address"]
                    peer_address = group_ntp['peer_address']
                    prefer = group_ntp['prefer']
                    vrf_name = group_ntp['vrf_name']
                    key_id = group_ntp['key_id']

                    if prefer is not None:
                        prefer = 'enabled'
                    else:
                        prefer = 'disabled'

                    if address is not None:
                        peer_type = 'server'
                    elif peer_address is not None:
                        peer_type = 'peer'
                        address = peer_address

                    args = dict(peer_type=peer_type, address=address, prefer=prefer,
                                vrf_name=vrf_name, key_id=key_id)

                    ntp_peer = dict((k, v) for k, v in args.items())
                    ntp_peer_list.append(ntp_peer)
                except AttributeError:
                    ntp_peer_list = []

    return ntp_peer_list


def get_ntp_existing(address, peer_type, module):
    peer_dict = {}
    peer_server_list = []

    peer_list = get_ntp_peer(module)
    for peer in peer_list:
        if peer['address'] == address:
            peer_dict.update(peer)
        else:
            peer_server_list.append(peer)

    source_type, source = get_ntp_source(module)

    if (source_type is not None and source is not None):
        peer_dict['source_type'] = source_type
        peer_dict['source'] = source

    return (peer_dict, peer_server_list)


def set_ntp_server_peer(peer_type, address, prefer, key_id, vrf_name):
    command_strings = []

    if prefer:
        command_strings.append(' prefer')
    if key_id:
        command_strings.append(' key {0}'.format(key_id))
    if vrf_name:
        command_strings.append(' use-vrf {0}'.format(vrf_name))

    command_strings.insert(0, 'ntp {0} {1}'.format(peer_type, address))

    command = ''.join(command_strings)

    return command


def config_ntp(delta, existing):
    if (delta.get('address') or delta.get('peer_type') or delta.get('vrf_name') or
            delta.get('key_id') or delta.get('prefer')):
        address = delta.get('address', existing.get('address'))
        peer_type = delta.get('peer_type', existing.get('peer_type'))
        key_id = delta.get('key_id', existing.get('key_id'))
        prefer = delta.get('prefer', existing.get('prefer'))
        vrf_name = delta.get('vrf_name', existing.get('vrf_name'))
        if delta.get('key_id') == 'default':
            key_id = None
    else:
        peer_type = None
        prefer = None

    source_type = delta.get('source_type')
    source = delta.get('source')

    if prefer:
        if prefer == 'enabled':
            prefer = True
        elif prefer == 'disabled':
            prefer = False

    if source:
        source_type = delta.get('source_type', existing.get('source_type'))

    ntp_cmds = []
    if peer_type:
        if existing.get('peer_type') and existing.get('address'):
            ntp_cmds.append('no ntp {0} {1}'.format(existing.get('peer_type'),
                                                    existing.get('address')))
        ntp_cmds.append(set_ntp_server_peer(
            peer_type, address, prefer, key_id, vrf_name))
    if source:
        existing_source_type = existing.get('source_type')
        existing_source = existing.get('source')
        if existing_source_type and source_type != existing_source_type:
            ntp_cmds.append('no ntp {0} {1}'.format(existing_source_type, existing_source))
        if source == 'default':
            if existing_source_type and existing_source:
                ntp_cmds.append('no ntp {0} {1}'.format(existing_source_type, existing_source))
        else:
            ntp_cmds.append('ntp {0} {1}'.format(source_type, source))

    return ntp_cmds


def main():
    argument_spec = dict(
        server=dict(type='str'),
        peer=dict(type='str'),
        key_id=dict(type='str'),
        prefer=dict(type='str', choices=['enabled', 'disabled']),
        vrf_name=dict(type='str'),
        source_addr=dict(type='str'),
        source_int=dict(type='str'),
        state=dict(choices=['absent', 'present'], default='present'),
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=[
                               ['server', 'peer'],
                               ['source_addr', 'source_int']],
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    server = module.params['server'] or None
    peer = module.params['peer'] or None
    key_id = module.params['key_id']
    prefer = module.params['prefer']
    vrf_name = module.params['vrf_name']
    source_addr = module.params['source_addr']
    source_int = module.params['source_int']
    state = module.params['state']

    if source_int is not None:
        source_int = source_int.lower()

    if server:
        peer_type = 'server'
        address = server
    elif peer:
        peer_type = 'peer'
        address = peer
    else:
        peer_type = None
        address = None

    source_type = None
    source = None
    if source_addr:
        source_type = 'source'
        source = source_addr
    elif source_int:
        source_type = 'source-interface'
        source = source_int

    if key_id or vrf_name or prefer:
        if not server and not peer:
            module.fail_json(
                msg='Please supply the server or peer parameter')

    args = dict(peer_type=peer_type, address=address, key_id=key_id,
                prefer=prefer, vrf_name=vrf_name, source_type=source_type,
                source=source)

    proposed = dict((k, v) for k, v in args.items() if v is not None)

    existing, peer_server_list = get_ntp_existing(address, peer_type, module)

    end_state = existing
    changed = False
    commands = []

    if state == 'present':
        delta = dict(set(proposed.items()).difference(existing.items()))
        if delta.get('key_id') and delta.get('key_id') == 'default':
            if not existing.get('key_id'):
                delta.pop('key_id')
        if delta:
            command = config_ntp(delta, existing)
            if command:
                commands.append(command)

    elif state == 'absent':
        if existing.get('peer_type') and existing.get('address'):
            command = 'no ntp {0} {1}'.format(
                existing['peer_type'], existing['address'])
            if command:
                commands.append([command])

        existing_source_type = existing.get('source_type')
        existing_source = existing.get('source')
        proposed_source_type = proposed.get('source_type')
        proposed_source = proposed.get('source')

        if proposed_source_type:
            if proposed_source_type == existing_source_type:
                if proposed_source == existing_source:
                    command = 'no ntp {0} {1}'.format(
                        existing_source_type, existing_source)
                    if command:
                        commands.append([command])

    cmds = flatten_list(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            load_config(module, cmds)
            end_state = get_ntp_existing(address, peer_type, module)[0]
            if 'configure' in cmds:
                cmds.pop(0)

    results = {}
    results['proposed'] = proposed
    results['existing'] = existing
    results['updates'] = cmds
    results['changed'] = changed
    results['warnings'] = warnings
    results['end_state'] = end_state
    results['peer_server_list'] = peer_server_list

    module.exit_json(**results)


if __name__ == '__main__':
    main()
