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
    type: bool
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
    type: bool
    aliases: ['enable_https']
  sandbox:
    description:
      - The NXAPI feature provides a web base UI for developers for
        entering commands.  This feature is initially disabled when
        the NXAPI feature is configured for the first time.  When the
        C(sandbox) argument is set to True, the developer sandbox URL
        will accept requests and when the value is set to False, the
        sandbox URL is unavailable. This is supported on NX-OS 7K series.
    required: false
    default: no
    type: bool
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

from ansible.module_utils.network.nxos.nxos import run_commands, load_config
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec
from ansible.module_utils.network.nxos.nxos import get_capabilities
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems


def check_args(module, warnings):
    device_info = get_capabilities(module)

    network_api = device_info.get('network_api', 'nxapi')
    if network_api == 'nxapi':
        module.fail_json(msg='module not supported over nxapi transport')

    os_platform = device_info['device_info']['network_os_platform']
    if '7K' not in os_platform and module.params['sandbox']:
        module.fail_json(msg='sandbox or enable_sandbox is supported on NX-OS 7K series of switches')

    state = module.params['state']

    if state == 'started':
        module.params['state'] = 'present'
        warnings.append('state=started is deprecated and will be removed in a '
                        'a future release.  Please use state=present instead')
    elif state == 'stopped':
        module.params['state'] = 'absent'
        warnings.append('state=stopped is deprecated and will be removed in a '
                        'a future release.  Please use state=absent instead')

    for key in ['http_port', 'https_port']:
        if module.params[key] is not None:
            if not 1 <= module.params[key] <= 65535:
                module.fail_json(msg='%s must be between 1 and 65535' % key)

    return warnings


def map_obj_to_commands(want, have, module):
    send_commands = list()
    commands = dict()

    def needs_update(x):
        return want.get(x) is not None and (want.get(x) != have.get(x))

    if needs_update('state'):
        if want['state'] == 'absent':
            return ['no feature nxapi']
        send_commands.append('feature nxapi')
    elif want['state'] == 'absent':
        return send_commands

    for parameter in ['http', 'https']:
        port_param = parameter + '_port'
        if needs_update(parameter):
            if want.get(parameter) is False:
                commands[parameter] = 'no nxapi %s' % parameter
            else:
                commands[parameter] = 'nxapi %s port %s' % (parameter, want.get(port_param))

        if needs_update(port_param) and want.get(parameter) is True:
            commands[parameter] = 'nxapi %s port %s' % (parameter, want.get(port_param))

    if needs_update('sandbox'):
        commands['sandbox'] = 'nxapi sandbox'
        if not want['sandbox']:
            commands['sandbox'] = 'no %s' % commands['sandbox']

    for parameter in commands.keys():
        send_commands.append(commands[parameter])

    return send_commands


def parse_http(data):
    http_res = [r'nxapi http port (\d+)']
    http_port = None

    for regex in http_res:
        match = re.search(regex, data, re.M)
        if match:
            http_port = int(match.group(1))
            break

    return {'http': http_port is not None, 'http_port': http_port}


def parse_https(data):
    https_res = [r'nxapi https port (\d+)']
    https_port = None

    for regex in https_res:
        match = re.search(regex, data, re.M)
        if match:
            https_port = int(match.group(1))
            break

    return {'https': https_port is not None, 'https_port': https_port}


def parse_sandbox(data):
    sandbox = [item for item in data.split('\n') if re.search(r'.*sandbox.*', item)]
    value = False
    if sandbox and sandbox[0] == 'nxapi sandbox':
        value = True
    return {'sandbox': value}


def map_config_to_obj(module):
    out = run_commands(module, ['show run all | inc nxapi'], check_rc=False)[0]
    match = re.search(r'no feature nxapi', out, re.M)
    # There are two possible outcomes when nxapi is disabled on nxos platforms.
    # 1. Nothing is displayed in the running config.
    # 2. The 'no feature nxapi' command is displayed in the running config.
    if match or out == '':
        return {'state': 'absent'}

    out = str(out).strip()

    obj = {'state': 'present'}
    obj.update(parse_http(out))
    obj.update(parse_https(out))
    obj.update(parse_sandbox(out))

    return obj


def map_params_to_obj(module):
    obj = {
        'http': module.params['http'],
        'http_port': module.params['http_port'],
        'https': module.params['https'],
        'https_port': module.params['https_port'],
        'sandbox': module.params['sandbox'],
        'state': module.params['state']
    }

    return obj


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        http=dict(aliases=['enable_http'], type='bool', default=True),
        http_port=dict(type='int', default=80),
        https=dict(aliases=['enable_https'], type='bool', default=False),
        https_port=dict(type='int', default=443),
        sandbox=dict(aliases=['enable_sandbox'], type='bool'),
        state=dict(default='present', choices=['started', 'stopped', 'present', 'absent'])
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()
    warning_msg = "Module nxos_nxapi currently defaults to configure 'http port 80'. "
    warning_msg += "Default behavior is changing to configure 'https port 443'"
    warning_msg += " when params 'http, http_port, https, https_port' are not set in the playbook"
    module.deprecate(msg=warning_msg, version="2.11")

    check_args(module, warnings)

    result = {'changed': False, 'warnings': warnings}

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
