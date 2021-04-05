#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: icx_system
version_added: "2.9"
author: "Ruckus Wireless (@Commscope)"
short_description: Manage the system attributes on Ruckus ICX 7000 series switches
description:
  - This module provides declarative management of node system attributes
    on Ruckus ICX 7000 series switches.  It provides an option to configure host system
    parameters or remove those parameters from the device active
    configuration.
notes:
  - Tested against ICX 10.1.
  - For information on using ICX platform, see L(the ICX OS Platform Options guide,../network/user_guide/platform_icx.html).
options:
  hostname:
    description:
      - Configure the device hostname parameter. This option takes an ASCII string value.
    type: str
  domain_name:
    description:
      - Configure the IP domain name on the remote device to the provided value.
       Value should be in the dotted name form and
       will be appended to the hostname to create a fully-qualified domain name.
    type: list
  domain_search:
    description:
      - Provides the list of domain names to
        append to the hostname for the purpose of doing name resolution.
        This argument accepts a list of names and will be reconciled
        with the current active configuration on the running node.
    type: list
  name_servers:
    description:
      - List of DNS name servers by IP address to use to perform name resolution
        lookups.
    type: list
  aaa_servers:
    description:
      - Configures radius/tacacs server
    type: list
    suboptions:
      type:
        description:
          - specify the type of the server
        type: str
        choices: ['radius','tacacs']
      hostname:
        description:
          - Configures the host name of the RADIUS server
        type: str
      auth_port_type:
        description:
          - specifies the type of the authentication port
        type: str
        choices: ['auth-port']
      auth_port_num:
        description:
          - Configures the authentication UDP port. The default value is 1812.
        type: str
      acct_port_num:
        description:
          - Configures the accounting UDP port. The default value is 1813.
        type: str
      acct_type:
        description:
          - Usage of the accounting port.
        type: str
        choices: ['accounting-only', 'authentication-only','authorization-only', default]
      auth_key:
        description:
          - Configure the key for the server
        type: str
      auth_key_type:
        description:
          - List of authentication level specified in the choices
        type: list
        choices: ['dot1x','mac-auth','web-auth']
  state:
    description:
      - State of the configuration
        values in the device's current active configuration.  When set
        to I(present), the values should be configured in the device active
        configuration and when set to I(absent) the values should not be
        in the device active configuration
    type: str
    default: present
    choices: ['present', 'absent']
  check_running_config:
    description:
      - Check running configuration. This can be set as environment variable.
       Module will use environment variable value(default:True), unless it is overridden, by specifying it as module parameter.
    type: bool
    default: yes
"""

EXAMPLES = """
- name: configure hostname and domain name
  icx_system:
    hostname: icx
    domain_search:
      - ansible.com
      - redhat.com
      - ruckus.com

- name: configure radius server of type auth-port
  icx_system:
    aaa_servers:
      - type: radius
        hostname: radius-server
        auth_port_type: auth-port
        auth_port_num: 1821
        acct_port_num: 1321
        acct_type: accounting-only
        auth_key: abc
        auth_key_type:
          - dot1x
          - mac-auth

- name: configure tacacs server
  icx_system:
    aaa_servers:
      - type: tacacs
        hostname: tacacs-server
        auth_port_type: auth-port
        auth_port_num: 1821
        acct_port_num: 1321
        acct_type: accounting-only
        auth_key: xyz

- name: configure name servers
  icx_system:
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
    - hostname icx
    - ip domain name test.example.com
    - radius-server host 172.16.10.12 auth-port 2083 acct-port 1850 default key abc dot1x mac-auth
    - tacacs-server host 10.2.3.4 auth-port 4058 authorization-only key xyz

"""


import re
from copy import deepcopy
from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.network.icx.icx import get_config, load_config
from ansible.module_utils.network.common.utils import ComplexList, validate_ip_v6_address
from ansible.module_utils.connection import Connection, ConnectionError, exec_command


def diff_list(want, have):
    adds = [w for w in want if w not in have]
    removes = [h for h in have if h not in want]
    return (adds, removes)


def map_obj_to_commands(want, have, module):
    commands = list()
    state = module.params['state']

    def needs_update(x):
        return want.get(x) is not None and (want.get(x) != have.get(x))

    if state == 'absent':
        if have['name_servers'] == [] and have['aaa_servers'] == [] and have['domain_search'] == [] and have['hostname'] is None:
            if want['hostname']:
                commands.append('no hostname')

            if want['domain_search']:
                for item in want['domain_search']:
                    commands.append('no ip dns domain-list %s' % item)

            if want['name_servers']:
                for item in want['name_servers']:
                    commands.append('no ip dns server-address %s' % item)

            if want['aaa_servers']:
                want_servers = []
                want_server = want['aaa_servers']
                if want_server:
                    want_list = deepcopy(want_server)
                    for items in want_list:
                        items['auth_key'] = None
                        want_servers.append(items)
                for item in want_servers:
                    ipv6addr = validate_ip_v6_address(item['hostname'])
                    if ipv6addr:
                        commands.append('no ' + item['type'] + '-server host ipv6 ' + item['hostname'])
                    else:
                        commands.append('no ' + item['type'] + '-server host ' + item['hostname'])

        if want['hostname']:
            if have['hostname'] == want['hostname']:
                commands.append('no hostname')

        if want['domain_search']:
            for item in want['domain_search']:
                if item in have['domain_search']:
                    commands.append('no ip dns domain-list %s' % item)

        if want['name_servers']:
            for item in want['name_servers']:
                if item in have['name_servers']:
                    commands.append('no ip dns server-address %s' % item)

        if want['aaa_servers']:
            want_servers = []
            want_server = want['aaa_servers']
            have_server = have['aaa_servers']
            if want_server:
                want_list = deepcopy(want_server)
                for items in want_list:
                    items['auth_key'] = None
                    want_servers.append(items)
            for item in want_servers:
                if item in have_server:
                    ipv6addr = validate_ip_v6_address(item['hostname'])
                    if ipv6addr:
                        commands.append('no ' + item['type'] + '-server host ipv6 ' + item['hostname'])
                    else:
                        commands.append('no ' + item['type'] + '-server host ' + item['hostname'])

    elif state == 'present':
        if needs_update('hostname'):
            commands.append('hostname %s' % want['hostname'])

        if want['domain_search']:
            adds, removes = diff_list(want['domain_search'], have['domain_search'])
            for item in removes:
                commands.append('no ip dns domain-list %s' % item)
            for item in adds:
                commands.append('ip dns domain-list %s' % item)

        if want['name_servers']:
            adds, removes = diff_list(want['name_servers'], have['name_servers'])
            for item in removes:
                commands.append('no ip dns server-address %s' % item)
            for item in adds:
                commands.append('ip dns server-address %s' % item)

        if want['aaa_servers']:
            want_servers = []
            want_server = want['aaa_servers']
            have_server = have['aaa_servers']
            want_list = deepcopy(want_server)
            for items in want_list:
                items['auth_key'] = None
                want_servers.append(items)

            adds, removes = diff_list(want_servers, have_server)

            for item in removes:
                ip6addr = validate_ip_v6_address(item['hostname'])
                if ip6addr:
                    cmd = 'no ' + item['type'] + '-server host ipv6 ' + item['hostname']
                else:
                    cmd = 'no ' + item['type'] + '-server host ' + item['hostname']
                commands.append(cmd)

            for w_item in adds:
                for item in want_server:
                    if item['hostname'] == w_item['hostname'] and item['type'] == w_item['type']:
                        auth_key = item['auth_key']

                ip6addr = validate_ip_v6_address(w_item['hostname'])
                if ip6addr:
                    cmd = w_item['type'] + '-server host ipv6 ' + w_item['hostname']
                else:
                    cmd = w_item['type'] + '-server host ' + w_item['hostname']
                if w_item['auth_port_type']:
                    cmd += ' ' + w_item['auth_port_type'] + ' ' + w_item['auth_port_num']
                if w_item['acct_port_num'] and w_item['type'] == 'radius':
                    cmd += ' acct-port ' + w_item['acct_port_num']
                if w_item['type'] == 'tacacs':
                    if any((w_item['acct_port_num'], w_item['auth_key_type'])):
                        module.fail_json(msg='acct_port and auth_key_type is not applicable for tacacs server')
                if w_item['acct_type']:
                    cmd += ' ' + w_item['acct_type']
                if auth_key is not None:
                    cmd += ' key ' + auth_key
                if w_item['auth_key_type'] and w_item['type'] == 'radius':
                    val = ''
                    for y in w_item['auth_key_type']:
                        val = val + ' ' + y
                    cmd += val
                commands.append(cmd)

    return commands


def parse_hostname(config):
    match = re.search(r'^hostname (\S+)', config, re.M)
    if match:
        return match.group(1)


def parse_domain_search(config):
    match = re.findall(r'^ip dns domain[- ]list (\S+)', config, re.M)
    matches = list()
    for name in match:
        matches.append(name)
    return matches


def parse_name_servers(config):
    matches = list()
    values = list()
    lines = config.split('\n')
    for line in lines:
        if 'ip dns server-address' in line:
            values = line.split(' ')
            for val in values:
                match = re.search(r'([0-9.]+)', val)
                if match:
                    matches.append(match.group())

    return matches


def parse_aaa_servers(config):
    configlines = config.split('\n')
    obj = []
    for line in configlines:
        auth_key_type = []
        if 'radius-server' in line or 'tacacs-server' in line:
            aaa_type = 'radius' if 'radius-server' in line else 'tacacs'
            match = re.search(r'(host ipv6 (\S+))|(host (\S+))', line)
            if match:
                hostname = match.group(2) if match.group(2) is not None else match.group(4)
            match = re.search(r'auth-port ([0-9]+)', line)
            if match:
                auth_port_num = match.group(1)
            else:
                auth_port_num = None
            match = re.search(r'acct-port ([0-9]+)', line)
            if match:
                acct_port_num = match.group(1)
            else:
                acct_port_num = None
            match = re.search(r'acct-port [0-9]+ (\S+)', line)
            if match:
                acct_type = match.group(1)
            else:
                acct_type = None
            if aaa_type == 'tacacs':
                match = re.search(r'auth-port [0-9]+ (\S+)', line)
                if match:
                    acct_type = match.group(1)
                else:
                    acct_type = None
            match = re.search(r'(dot1x)', line)
            if match:
                auth_key_type.append('dot1x')
            match = re.search(r'(mac-auth)', line)
            if match:
                auth_key_type.append('mac-auth')
            match = re.search(r'(web-auth)', line)
            if match:
                auth_key_type.append('web-auth')

            obj.append({
                'type': aaa_type,
                'hostname': hostname,
                'auth_port_type': 'auth-port',
                'auth_port_num': auth_port_num,
                'acct_port_num': acct_port_num,
                'acct_type': acct_type,
                'auth_key': None,
                'auth_key_type': set(auth_key_type) if len(auth_key_type) > 0 else None
            })

    return obj


def map_config_to_obj(module):
    compare = module.params['check_running_config']
    config = get_config(module, None, compare=compare)
    return {
        'hostname': parse_hostname(config),
        'domain_search': parse_domain_search(config),
        'name_servers': parse_name_servers(config),
        'aaa_servers': parse_aaa_servers(config)
    }


def map_params_to_obj(module):
    if module.params['aaa_servers']:
        for item in module.params['aaa_servers']:
            if item['auth_key_type']:
                item['auth_key_type'] = set(item['auth_key_type'])
    obj = {
        'hostname': module.params['hostname'],
        'domain_name': module.params['domain_name'],
        'domain_search': module.params['domain_search'],
        'name_servers': module.params['name_servers'],
        'state': module.params['state'],
        'aaa_servers': module.params['aaa_servers']
    }
    return obj


def main():
    """ Main entry point for Ansible module execution
    """
    server_spec = dict(
        type=dict(choices=['radius', 'tacacs']),
        hostname=dict(),
        auth_port_type=dict(choices=['auth-port']),
        auth_port_num=dict(),
        acct_port_num=dict(),
        acct_type=dict(choices=['accounting-only', 'authentication-only', 'authorization-only', 'default']),
        auth_key=dict(no_log=True),
        auth_key_type=dict(type='list', choices=['dot1x', 'mac-auth', 'web-auth'])
    )
    argument_spec = dict(
        hostname=dict(),

        domain_name=dict(type='list'),
        domain_search=dict(type='list'),
        name_servers=dict(type='list'),

        aaa_servers=dict(type='list', elements='dict', options=server_spec),
        state=dict(choices=['present', 'absent'], default='present'),
        check_running_config=dict(default=True, type='bool', fallback=(env_fallback, ['ANSIBLE_CHECK_ICX_RUNNING_CONFIG']))
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    result = {'changed': False}

    warnings = list()

    result['warnings'] = warnings
    exec_command(module, 'skip')
    want = map_params_to_obj(module)
    have = map_config_to_obj(module)
    commands = map_obj_to_commands(want, have, module)
    result['commands'] = commands

    if commands:
        if not module.check_mode:
            load_config(module, commands)
        result['changed'] = True

    module.exit_json(**result)


if __name__ == "__main__":
    main()
