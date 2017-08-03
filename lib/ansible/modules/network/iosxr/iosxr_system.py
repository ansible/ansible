#!/usr/bin/python
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = """
---
module: iosxr_system
version_added: "2.3"
author: "Peter Sprygada (@privateip)"
short_description: Manage the system attributes on Cisco IOS XR devices
description:
  - This module provides declarative management of node system attributes
    on Cisco IOS XR devices.  It provides an option to configure host system
    parameters or remove those parameters from the device active
    configuration.
extends_documentation_fragment: iosxr
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
  lookup_source:
    description:
      - The C(lookup_source) argument provides one or more source
        interfaces to use for performing DNS lookups.  The interface
        provided in C(lookup_source) must be a valid interface configured
        on the device.
  lookup_enabled:
    description:
      - Provides administrative control
        for enabling or disabling DNS lookups.  When this argument is
        set to True, lookups are performed and when it is set to False,
        lookups are not performed.
    type: bool
  name_servers:
    description:
      - The C(name_serves) argument accepts a list of DNS name servers by
        way of either FQDN or IP address to use to perform name resolution
        lookups.  This argument accepts wither a list of DNS servers See
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
  iosxr_system:
    hostname: iosxr01
    domain_name: test.example.com
    domain-search:
      - ansible.com
      - redhat.com
      - cisco.com
- name: remove configuration
  iosxr_system:
    state: absent
- name: configure DNS lookup sources
  iosxr_system:
    lookup_source: MgmtEth0/0/CPU0/0
    lookup_enabled: yes
- name: configure name servers
  iosxr_system:
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
    - hostname iosxr01
    - ip domain-name test.example.com
"""
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.iosxr import get_config, load_config
from ansible.module_utils.iosxr import iosxr_argument_spec, check_args

def diff_list(want, have):
    adds = set(want).difference(have)
    removes = set(have).difference(want)
    return (adds, removes)

def map_obj_to_commands(want, have, module):
    commands = list()
    state = module.params['state']

    needs_update = lambda x: want.get(x) and (want.get(x) != have.get(x))

    if state == 'absent':
        if have['hostname'] != 'ios':
            commands.append('no hostname')
        if have['domain_name']:
            commands.append('no domain name')
        if have['lookup_source']:
            commands.append('no domain lookup source-interface %s' % have['lookup_source'])
        if not have['lookup_enabled']:
            commands.append('no domain lookup disable')
        for item in have['name_servers']:
            commands.append('no domain name-server %s' % item)
        for item in have['domain_search']:
            commands.append('no domain list %s' % item)

    elif state == 'present':
        if needs_update('hostname'):
            commands.append('hostname %s' % want['hostname'])

        if needs_update('domain_name'):
            commands.append('domain name %s' % want['domain_name'])

        if needs_update('lookup_source'):
            commands.append('domain lookup source-interface %s' % want['lookup_source'])

        if needs_update('lookup_enabled'):
            cmd = 'domain lookup disable'
            if want['lookup_enabled']:
                cmd = 'no %s' % cmd
            commands.append(cmd)

        if want['name_servers'] is not None:
            adds, removes = diff_list(want['name_servers'], have['name_servers'])
            for item in adds:
                commands.append('domain name-server %s' % item)
            for item in removes:
                commands.append('no domain name-server %s' % item)

        if want['domain_search'] is not None:
            adds, removes = diff_list(want['domain_search'], have['domain_search'])
            for item in adds:
                commands.append('domain list %s' % item)
            for item in removes:
                commands.append('no domain list %s' % item)

    return commands

def parse_hostname(config):
    match = re.search('^hostname (\S+)', config, re.M)
    return match.group(1)

def parse_domain_name(config):
    match = re.search('^domain name (\S+)', config, re.M)
    if match:
        return match.group(1)

def parse_lookup_source(config):
    match = re.search('^domain lookup source-interface (\S+)', config, re.M)
    if match:
        return match.group(1)

def map_config_to_obj(module):
    config = get_config(module)
    return {
        'hostname': parse_hostname(config),
        'domain_name': parse_domain_name(config),
        'domain_search': re.findall('^domain list (\S+)', config, re.M),
        'lookup_source': parse_lookup_source(config),
        'lookup_enabled': 'domain lookup disable' not in config,
        'name_servers': re.findall('^domain name-server (\S+)', config, re.M)
    }

def map_params_to_obj(module):
    return {
        'hostname': module.params['hostname'],
        'domain_name': module.params['domain_name'],
        'domain_search': module.params['domain_search'],
        'lookup_source': module.params['lookup_source'],
        'lookup_enabled': module.params['lookup_enabled'],
        'name_servers': module.params['name_servers']
    }

def main():
    """ Main entry point for Ansible module execution
    """
    argument_spec = dict(
        hostname=dict(),
        domain_name=dict(),
        domain_search=dict(type='list'),

        name_servers=dict(type='list'),
        lookup_source=dict(),
        lookup_enabled=dict(type='bool'),

        state=dict(choices=['present', 'absent'], default='present')
    )

    argument_spec.update(iosxr_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    result = {'changed': False, 'warnings': warnings}

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)

    commands = map_obj_to_commands(want, have, module)
    result['commands'] = commands

    if commands:
        if not module.check_mode:
            load_config(module, commands, result['warnings'], commit=True)
        result['changed'] = True

    module.exit_json(**result)

if __name__ == "__main__":
    main()
