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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = """
---
module: nxos_nxapi
extends_documentation_fragment: nxos
version_added: "2.1"
author: "Peter Sprygada (@privateip)"
short_description: Manage NXAPI configuration on an NXOS device.
description:
  - Configures the NXAPI feature on devices running Cisco NXOS.  The
    NXAPI feature is absent from the configuration by default.  Since
    this module manages the NXAPI feature it only supports the use
    of the C(Cli) transport.
options:
  http_port:
    description:
      - Configure the port with which the HTTP server will listen on
        for requests.  By default, NXAPI will bind the HTTP service
        to the standard HTTP port 80.  This argument accepts valid
        port values in the range of 1 to 65535.
    required: false
    default: 80
  http:
    description:
      - Controls the operating state of the HTTP protocol as one of the
        underlying transports for NXAPI.  By default, NXAPI will enable
        the HTTP transport when the feature is first configured.  To
        disable the use of the HTTP transport, set the value of this
        argument to False.
    required: false
    default: yes
    choices: ['yes', 'no']
    aliases: ['enable_http']
  https_port:
    description:
      - Configure the port with which the HTTPS server will listen on
        for requests.  By default, NXAPI will bind the HTTPS service
        to the standard HTTPS port 443.  This argument accepts valid
        port values in the range of 1 to 65535.
    required: false
    default: 443
  https:
    description:
      - Controls the operating state of the HTTPS protocol as one of the
        underlying transports for NXAPI.  By default, NXAPI will disable
        the HTTPS transport when the feature is first configured.  To
        enable the use of the HTTPS transport, set the value of this
        argument to True.
    required: false
    default: no
    choices: ['yes', 'no']
    aliases: ['enable_https']
  sandbox:
    description:
      - The NXAPI feature provides a web base UI for developers for
        entering commands.  This feature is initially disabled when
        the NXAPI feature is configured for the first time.  When the
        C(sandbox) argument is set to True, the developer sandbox URL
        will accept requests and when the value is set to False, the
        sandbox URL is unavailable.
    required: false
    default: no
    choices: ['yes', 'no']
    aliases: ['enable_sandbox']
  state:
    description:
      - The C(state) argument controls whether or not the NXAPI
        feature is configured on the remote device.  When the value
        is C(present) the NXAPI feature configuration is present in
        the device running-config.  When the values is C(absent) the
        feature configuration is removed from the running-config.
    choices: ['present', 'absent']
    required: false
    default: present
"""

EXAMPLES = """
- name: Enable NXAPI access with default configuration
  nxos_nxapi:
    state: present

- name: Enable NXAPI with no HTTP, HTTPS at port 9443 and sandbox disabled
  nxos_nxapi:
    enable_http: false
    https_port: 9443
    https: yes
    enable_sandbox: no

- name: remove NXAPI configuration
  nxos_nxapi:
    state: absent
"""

RETURN = """
updates:
  description:
    - Returns the list of commands that need to be pushed into the remote
      device to satisfy the arguments
  returned: always
  type: list
  sample: ['no feature nxapi']
"""
import re

from functools import partial

from ansible.module_utils.nxos import run_commands, load_config
from ansible.module_utils.nxos import nxos_argument_spec
from ansible.module_utils.nxos import check_args as nxos_check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netcfg import NetworkConfig
from ansible.module_utils.six import iteritems

def check_args(module, warnings):
    transport = module.params['transport']
    provider_transport = (module.params['provider'] or {}).get('transport')
    if 'nxapi' in (transport, provider_transport):
        module.fail_json(msg='transport=nxapi is not supporting when configuring nxapi')

    nxos_check_args(module, warnings)

    state = module.params['state']

    if state == 'started':
        module.params['state'] = 'present'
        warnings.append('state=started is deprecated and will be removed in a '
                        'a future release.  Please use state=present instead')
    elif state == 'stopped':
        module.params['state'] = 'absent'
        warnings.append('state=stopped is deprecated and will be removed in a '
                        'a future release.  Please use state=absent instead')

    if module.params['transport'] == 'nxapi':
        module.fail_json(msg='module not supported over nxapi transport')

    for key in ['config']:
        if module.params[key]:
            warnings.append('argument %s is deprecated and will be ignored' % key)

    return warnings

def map_obj_to_commands(updates, module):
    commands = list()
    want, have = updates

    needs_update = lambda x: want.get(x) is not None and (want.get(x) != have.get(x))

    if needs_update('state'):
        if want['state'] == 'absent':
            return ['no feature nxapi']
        commands.append('feature nxapi')

    if any((needs_update('http'), needs_update('http_port'))):
        if want['http'] is True or (want['http'] is None and have['http'] is True):
            port = want['http_port'] or 80
            commands.append('nxapi http port %s' % port)
        elif want['http'] is False:
            commands.append('no nxapi http')

    if any((needs_update('https'), needs_update('https_port'))):
        if want['https'] is True or (want['https'] is None and have['https'] is True):
            port = want['https_port'] or 443
            commands.append('nxapi https port %s' % port)
        elif want['https'] is False:
            commands.append('no nxapi https')

    if needs_update('sandbox'):
        cmd = 'nxapi sandbox'
        if not want['sandbox']:
            cmd = 'no %s' % cmd
        commands.append(cmd)

    return commands

def parse_http(data):
    match = re.search('HTTP Port:\s+(\d+)', data, re.M)
    if match:
        return {'http': True, 'http_port': int(match.group(1))}
    else:
        return {'http': False, 'http_port': None}

def parse_https(data):
    match = re.search('HTTPS Port:\s+(\d+)', data, re.M)
    if match:
        return {'https': True, 'https_port': int(match.group(1))}
    else:
        return {'https': False, 'https_port': None}

def parse_sandbox(data):
    match = re.search('Sandbox:\s+(.+)$', data, re.M)
    value = None
    if match:
        value = match.group(1) == 'Enabled'
    return {'sandbox': value}

def map_config_to_obj(module):
    out = run_commands(module, ['show nxapi'], check_rc=False)
    if out[0] == '':
        return {'state': 'absent'}

    out = str(out[0]).strip()

    obj = {'state': 'present'}
    obj.update(parse_http(out))
    obj.update(parse_https(out))
    obj.update(parse_sandbox(out))

    return obj

def validate_http_port(value, module):
    if not 1 <= module.params['http_port'] <= 65535:
        module.fail_json(msg='http_port must be between 1 and 65535')

def validate_https_port(value, module):
    if not 1 <= module.params['https_port'] <= 65535:
        module.fail_json(msg='https_port must be between 1 and 65535')

def map_params_to_obj(module):
    obj = {
        'http': module.params['http'],
        'http_port': module.params['http_port'],
        'https': module.params['https'],
        'https_port': module.params['https_port'],
        'sandbox': module.params['sandbox'],
        'state': module.params['state']
    }

    for key, value in iteritems(obj):
        if value:
            validator = globals().get('validate_%s' % key)
            if validator:
                validator(value, module)

    return obj

def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        http=dict(aliases=['enable_http'], type='bool'),
        http_port=dict(type='int'),

        https=dict(aliases=['enable_https'], type='bool'),
        https_port=dict(type='int'),

        sandbox=dict(aliases=['enable_sandbox'], type='bool'),

        # deprecated (Ansible 2.3) arguments
        config=dict(),

        state=dict(default='present', choices=['started', 'stopped', 'present', 'absent'])
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)


    result = {'changed': False}

    warnings = list()
    check_args(module, warnings)
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
