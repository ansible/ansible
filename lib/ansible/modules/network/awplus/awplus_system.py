#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2020, Allied Telesis Ltd.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: awplus_system
author:
    - Jeremy Toth (@jtsource)
    - Isaac Daly (@dalyIsaac)
short_description: Manage the system attributes on AlliedWare Plus devices
description:
    - This module provides declarative management of node system attributes
        on awplus devices. It provides an option to configure host system
        parameters or remove those parameters from the device active
        configuration.
version_added: "2.10"
options:
    hostname:
        description:
            - Configure the device hostname parameter. This option takes an ASCII string value.
    domain_name:
        description:
            - Configure the IP domain name
                on the remote device to the provided value. Value
                should be in the dotted name form and will be
                appended to the C(hostname) to create a fully-qualified
                domain name.
    domain_list:
        description:
            - Provides the list of domain suffixes to
                append to the hostname for the purpose of doing name resolution.
                This argument accepts a list of names and will be reconciled
                with the current active configuration on the running node.
    lookup_enabled:
        description:
            - Administrative control
                for enabling or disabling DNS lookups. When this argument is
                set to True, lookups are performed and when it is set to False,
                lookups are not performed.
        type: bool
    name_servers:
        description:
            - List of DNS name servers by IP address to use to perform name resolution
                lookups. This argument accepts either a list of DNS servers See
                examples.
    state:
        description:
            - State of the configuration
                values in the device's current active configuration. When set
                to I(present), the values should be configured in the device active
                configuration and when set to I(absent) the values should not be
                in the device active configuration
        default: present
        choices: ['present', 'absent']
notes:
    - Check mode is supported.
"""

EXAMPLES = """
- name: configure hostname and domain name
    awplus_system:
        hostname: awplus01
        domain_name: test.example.com
        domain_list:
            - ansible.com
            - redhat.com
            - cisco.com
- name: remove configuration
    awplus_system:
        state: absent
- name: configure DNS lookup sources
    awplus_system:
        lookup_enabled: yes
- name: configure name servers
    awplus_system:
        name_servers:
            - 8.8.8.8
            - 8.8.4.4
"""

RETURN = """
commands:
    description: The list of configuration mode commands to send to the device
    returned: always
    type: list
    sample:
        - hostname awplus01
      - ip domain name test.example.com
"""

import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.awplus.awplus import get_config, load_config
from ansible.module_utils.network.awplus.awplus import awplus_argument_spec


_CONFIGURED_VRFS = None


def has_vrf(module, vrf):
    global _CONFIGURED_VRFS
    if _CONFIGURED_VRFS is not None:
        return vrf in _CONFIGURED_VRFS
    config = get_config(module)
    _CONFIGURED_VRFS = re.findall(r'vrf definition (\S+)', config)
    return vrf in _CONFIGURED_VRFS


def requires_vrf(module, vrf):
    if not has_vrf(module, vrf):
        module.fail_json(msg='vrf %s is not configured' % vrf)


def diff_list(want, have):
    want = [w.strip() for w in want]  # remove leading whitespace
    adds = [w for w in want if w not in have]
    removes = [h for h in have if h not in want]
    return (adds, removes)


def same_list(want, have):
    return [w for w in want if w.strip() in have]


def map_obj_to_commands(want, have, module):
    commands = list()
    state = module.params['state']

    def needs_update(x):
        return want.get(x) is not None and (want.get(x) != have.get(x))

    if state == 'absent':
        if have['hostname']:
            commands.append('no hostname')

        if have['lookup_enabled'] is False:
            commands.append('ip domain-lookup')

        if have['domain_name']:
            commands.append('no ip domain-name %s' % have['domain_name'])

        if want['domain_list']:
            removes = same_list(want['domain_list'], have['domain_list'])
        else:
            removes = have['domain_list']
        for item in removes:
            commands.append('no ip domain-list %s' % item)

        if want['name_servers']:
            removes = same_list(want['name_servers'], have['name_servers'])
        else:
            removes = have['name_servers']
        for item in removes:
            commands.append('no ip name-server %s' % item)

    elif state == 'present':
        if needs_update('hostname'):
            commands.append('hostname %s' % want['hostname'])

        if needs_update('lookup_enabled'):
            cmd = 'ip domain-lookup'
            if want['lookup_enabled'] is False:
                cmd = 'no %s' % cmd
            commands.append(cmd)

        if needs_update('domain_name'):
            commands.append('ip domain-name %s' % want['domain_name'])

        if want['domain_list']:
            adds, removes = diff_list(want['domain_list'], have['domain_list'])
            for item in removes:
                commands.append('no ip domain-list %s' % item)
            for item in adds:
                commands.append('ip domain-list %s' % item)

        if want['name_servers']:
            adds, removes = diff_list(want['name_servers'], have['name_servers'])
            for item in removes:
                commands.append('no ip name-server %s ' % item)
            for item in adds:
                commands.append('ip name-server %s' % item)

    return commands


def parse_hostname(config):
    match = re.search(r'^hostname (\S+)', config, re.M)
    if match:
        return match.group(1)
    return None


def parse_domain_name(config):
    match = re.search(r'^ip domain[- ]name (\S+)', config, re.M)
    if match:
        return match.group(1)
    return match


def parse_domain_list(config):
    match = re.findall(r'^ip domain[- ]list (\S+)', config, re.M)
    matches = list()
    for name in match:
        matches.append(name)
    return matches


def parse_name_servers(config):
    match = re.findall(r'^ip name-server (?:vrf (\S+) )*(.*)', config, re.M)
    matches = list()
    for vrf, servers in match:
        for server in servers.split():
            if vrf:
                matches.append('vrf ' + vrf + ' ' + server)
            else:
                matches.append(server)
    return matches


def map_config_to_obj(module):
    config = get_config(module)
    return {
        'hostname': parse_hostname(config),
        'domain_name': parse_domain_name(config),
        'domain_list': parse_domain_list(config),
        'lookup_enabled': 'no ip domain-lookup' not in config and 'no ip domain-lookup' not in config,
        'name_servers': parse_name_servers(config)
    }


def map_params_to_obj(module):
    obj = {
        'hostname': module.params['hostname'],
        'lookup_enabled': module.params['lookup_enabled'],
        'domain_name': module.params['domain_name'],
        'domain_list': module.params['domain_list'],
        'name_servers': module.params['name_servers']
    }

    return obj


def main():
    argument_spec = dict(
        hostname=dict(),
        domain_name=dict(),
        domain_list=dict(type='list'),
        name_servers=dict(type='list'),
        lookup_enabled=dict(type='bool'),
        state=dict(choices=['present', 'absent'], default='present')
    )

    argument_spec.update(awplus_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    result = {'changed': False}

    warnings = list()
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
