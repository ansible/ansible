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


DOCUMENTATION = """
---
module: eos_system
version_added: "2.3"
author: "Peter Sprygada (@privateip)"
short_description: Manage the system attributes on Arista EOS devices
description:
  - This module provides declarative management of node system attributes
    on Arista EOS devices.  It provides an option to configure host system
    parameters or remove those parameters from the device active
    configuration.
extends_documentation_fragment: eos
notes:
  - Tested against EOS 4.15
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
  domain_search:
    description:
      - Provides the list of domain suffixes to
        append to the hostname for the purpose of doing name resolution.
        This argument accepts a list of names and will be reconciled
        with the current active configuration on the running node.
    aliases: ['domain_list']
  lookup_source:
    description:
      - Provides one or more source
        interfaces to use for performing DNS lookups.  The interface
        provided in C(lookup_source) can only exist in a single VRF.  This
        argument accepts either a list of interface names or a list of
        hashes that configure the interface name and VRF name.  See
        examples.
  name_servers:
    description:
      - List of DNS name servers by IP address to use to perform name resolution
        lookups.  This argument accepts either a list of DNS servers or
        a list of hashes that configure the name server and VRF name.  See
        examples.
  state:
    description:
      - State of the configuration
        values in the device's current active configuration.  When set
        to I(present), the values should be configured in the device active
        configuration and when set to I(absent) the values should not be
        in the device active configuration
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: configure hostname and domain-name
  eos_system:
    hostname: eos01
    domain_name: test.example.com

- name: remove configuration
  eos_system:
    state: absent

- name: configure DNS lookup sources
  eos_system:
    lookup_source: Management1

- name: configure DNS lookup sources with VRF support
  eos_system:
      lookup_source:
        - interface: Management1
          vrf: mgmt
        - interface: Ethernet1
          vrf: myvrf

- name: configure name servers
  eos_system:
    name_servers:
      - 8.8.8.8
      - 8.8.4.4

- name: configure name servers with VRF support
  eos_system:
    name_servers:
      - { server: 8.8.8.8, vrf: mgmt }
      - { server: 8.8.4.4, vrf: mgmt }
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - hostname eos01
    - ip domain-name test.example.com
session_name:
  description: The EOS config session name used to load the configuration
  returned: changed
  type: str
  sample: ansible_1479315771
"""
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import ComplexList
from ansible.module_utils.network.eos.eos import load_config, get_config
from ansible.module_utils.network.eos.eos import eos_argument_spec

_CONFIGURED_VRFS = None


def has_vrf(module, vrf):
    global _CONFIGURED_VRFS
    if _CONFIGURED_VRFS is not None:
        return vrf in _CONFIGURED_VRFS
    config = get_config(module)
    _CONFIGURED_VRFS = re.findall(r'vrf definition (\S+)', config)
    _CONFIGURED_VRFS.append('default')
    return vrf in _CONFIGURED_VRFS


def map_obj_to_commands(want, have, module):
    commands = list()
    state = module.params['state']

    def needs_update(x):
        return want.get(x) and (want.get(x) != have.get(x))

    if state == 'absent':
        if have['domain_name']:
            commands.append('no ip domain-name')

        if have['hostname'] != 'localhost':
            commands.append('no hostname')

    if state == 'present':
        if needs_update('hostname'):
            commands.append('hostname %s' % want['hostname'])

        if needs_update('domain_name'):
            commands.append('ip domain-name %s' % want['domain_name'])

        if want['domain_list']:
            # handle domain_list items to be removed
            for item in set(have['domain_list']).difference(want['domain_list']):
                commands.append('no ip domain-list %s' % item)

            # handle domain_list items to be added
            for item in set(want['domain_list']).difference(have['domain_list']):
                commands.append('ip domain-list %s' % item)

        if want['lookup_source']:
            # handle lookup_source items to be removed
            for item in have['lookup_source']:
                if item not in want['lookup_source']:
                    if item['vrf']:
                        if not has_vrf(module, item['vrf']):
                            module.fail_json(msg='vrf %s is not configured' % item['vrf'])
                        values = (item['vrf'], item['interface'])
                        commands.append('no ip domain lookup vrf %s source-interface %s' % values)
                    else:
                        commands.append('no ip domain lookup source-interface %s' % item['interface'])

            # handle lookup_source items to be added
            for item in want['lookup_source']:
                if item not in have['lookup_source']:
                    if item['vrf']:
                        if not has_vrf(module, item['vrf']):
                            module.fail_json(msg='vrf %s is not configured' % item['vrf'])
                        values = (item['vrf'], item['interface'])
                        commands.append('ip domain lookup vrf %s source-interface %s' % values)
                    else:
                        commands.append('ip domain lookup source-interface %s' % item['interface'])

        if want['name_servers']:
            # handle name_servers items to be removed.  Order does matter here
            # since name servers can only be in one vrf at a time
            for item in have['name_servers']:
                if item not in want['name_servers']:
                    if not has_vrf(module, item['vrf']):
                        module.fail_json(msg='vrf %s is not configured' % item['vrf'])
                    if item['vrf'] not in ('default', None):
                        values = (item['vrf'], item['server'])
                        commands.append('no ip name-server vrf %s %s' % values)
                    else:
                        commands.append('no ip name-server %s' % item['server'])

            # handle name_servers items to be added
            for item in want['name_servers']:
                if item not in have['name_servers']:
                    if not has_vrf(module, item['vrf']):
                        module.fail_json(msg='vrf %s is not configured' % item['vrf'])
                    if item['vrf'] not in ('default', None):
                        values = (item['vrf'], item['server'])
                        commands.append('ip name-server vrf %s %s' % values)
                    else:
                        commands.append('ip name-server %s' % item['server'])

    return commands


def parse_hostname(config):
    match = re.search(r'^hostname (\S+)', config, re.M)
    if match:
        return match.group(1)


def parse_domain_name(config):
    match = re.search(r'^ip domain-name (\S+)', config, re.M)
    if match:
        return match.group(1)


def parse_lookup_source(config):
    objects = list()
    regex = r'ip domain lookup (?:vrf (\S+) )*source-interface (\S+)'
    for vrf, intf in re.findall(regex, config, re.M):
        if len(vrf) == 0:
            vrf = None
        objects.append({'interface': intf, 'vrf': vrf})
    return objects


def parse_name_servers(config):
    objects = list()
    for vrf, addr in re.findall(r'ip name-server vrf (\S+) (\S+)', config, re.M):
        objects.append({'server': addr, 'vrf': vrf})
    return objects


def map_config_to_obj(module):
    config = get_config(module)
    return {
        'hostname': parse_hostname(config),
        'domain_name': parse_domain_name(config),
        'domain_list': re.findall(r'^ip domain-list (\S+)', config, re.M),
        'lookup_source': parse_lookup_source(config),
        'name_servers': parse_name_servers(config)
    }


def map_params_to_obj(module):
    obj = {
        'hostname': module.params['hostname'],
        'domain_name': module.params['domain_name'],
        'domain_list': module.params['domain_list']
    }

    lookup_source = ComplexList(dict(
        interface=dict(key=True),
        vrf=dict()
    ), module)

    name_servers = ComplexList(dict(
        server=dict(key=True),
        vrf=dict(default='default')
    ), module)

    for arg, cast in [('lookup_source', lookup_source), ('name_servers', name_servers)]:
        if module.params[arg] is not None:
            obj[arg] = cast(module.params[arg])
        else:
            obj[arg] = None

    return obj


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        hostname=dict(),

        domain_name=dict(),
        domain_list=dict(type='list', aliases=['domain_search']),

        # { interface: <str>, vrf: <str> }
        lookup_source=dict(type='list'),

        # { server: <str>; vrf: <str> }
        name_servers=dict(type='list'),

        state=dict(default='present', choices=['present', 'absent'])
    )

    argument_spec.update(eos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    result = {'changed': False}

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)

    commands = map_obj_to_commands(want, have, module)
    result['commands'] = commands

    if commands:
        commit = not module.check_mode
        response = load_config(module, commands, commit=commit)
        if response.get('diff') and module._diff:
            result['diff'] = {'prepared': response.get('diff')}
        result['session_name'] = response.get('session')
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
