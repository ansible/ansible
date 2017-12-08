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
module: eos_eapi
version_added: "2.1"
author: "Peter Sprygada (@privateip)"
short_description: Manage and configure Arista EOS eAPI.
requirements:
  - "EOS v4.12 or greater"
description:
  - Use to enable or disable eAPI access, and set the port and state
    of http, https, local_http and unix-socket servers.
  - When enabling eAPI access the default is to enable HTTP on port
    80, enable HTTPS on port 443, disable local HTTP, and disable
    Unix socket server. Use the options listed below to override the
    default configuration.
  - Requires EOS v4.12 or greater.
extends_documentation_fragment: eos
options:
  http:
    description:
      - The C(http) argument controls the operating state of the HTTP
        transport protocol when eAPI is present in the running-config.
        When the value is set to True, the HTTP protocol is enabled and
        when the value is set to False, the HTTP protocol is disabled.
        By default, when eAPI is first configured, the HTTP protocol is
        disabled.
    required: false
    default: no
    choices: ['yes', 'no']
    aliases: ['enable_http']
  http_port:
    description:
      - Configures the HTTP port that will listen for connections when
        the HTTP transport protocol is enabled.  This argument accepts
        integer values in the valid range of 1 to 65535.
    required: false
    default: 80
  https:
    description:
      - The C(https) argument controls the operating state of the HTTPS
        transport protocol when eAPI is present in the running-config.
        When the value is set to True, the HTTPS protocol is enabled and
        when the value is set to False, the HTTPS protocol is disabled.
        By default, when eAPI is first configured, the HTTPS protocol is
        enabled.
    required: false
    default: yes
    choices: ['yes', 'no']
    aliases: ['enable_http']
  https_port:
    description:
      - Configures the HTTP port that will listen for connections when
        the HTTP transport protocol is enabled.  This argument accepts
        integer values in the valid range of 1 to 65535.
    required: false
    default: 443
  local_http:
    description:
      - The C(local_http) argument controls the operating state of the
        local HTTP transport protocol when eAPI is present in the
        running-config.  When the value is set to True, the HTTP protocol
        is enabled and restricted to connections from localhost only.  When
        the value is set to False, the HTTP local protocol is disabled.
      - Note is value is independent of the C(http) argument
    required: false
    default: false
    choices: ['yes', 'no']
    aliases: ['enable_local_http']
  local_http_port:
    description:
      - Configures the HTTP port that will listen for connections when
        the HTTP transport protocol is enabled.  This argument accepts
        integer values in the valid range of 1 to 65535.
    required: false
    default: 8080
  socket:
    description:
      - The C(socket) argument controls the operating state of the UNIX
        Domain Socket used to receive eAPI requests.  When the value
        of this argument is set to True, the UDS will listen for eAPI
        requests.  When the value is set to False, the UDS will not be
        available to handle requests.  By default when eAPI is first
        configured, the UDS is disabled.
    required: false
    default: false
    choices: ['yes', 'no']
    aliases: ['enable_socket']
  vrf:
    description:
      - The C(vrf) argument will configure eAPI to listen for connections
        in the specified VRF.  By default, eAPI transports will listen
        for connections in the global table.  This value requires the
        VRF to already be created otherwise the task will fail.
    required: false
    default: default
    version_added: "2.2"
  config:
    description:
      - The module, by default, will connect to the remote device and
        retrieve the current running-config to use as a base for comparing
        against the contents of source.  There are times when it is not
        desirable to have the task get the current running-config for
        every task in a playbook.  The I(config) argument allows the
        implementer to pass in the configuration to use as the base
        config for comparison.
    required: false
    default: nul
    version_added: "2.2"
  state:
    description:
      - The C(state) argument controls the operational state of eAPI
        on the remote device.  When this argument is set to C(started),
        eAPI is enabled to receive requests and when this argument is
        C(stopped), eAPI is disabled and will not receive requests.
    required: false
    default: started
    choices: ['started', 'stopped']
"""

EXAMPLES = """
- name: Enable eAPI access with default configuration
  eos_eapi:
    state: started

- name: Enable eAPI with no HTTP, HTTPS at port 9443, local HTTP at port 80, and socket enabled
  eos_eapi:
    state: started
    http: false
    https_port: 9443
    local_http: yes
    local_http_port: 80
    socket: yes

- name: Shutdown eAPI access
  eos_eapi:
    state: stopped
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - management api http-commands
    - protocol http port 81
    - no protocol https
urls:
  description: Hash of URL endpoints eAPI is listening on per interface
  returned: when eAPI is started
  type: dict
  sample: {'Management1': ['http://172.26.10.1:80']}
session_name:
  description: The EOS config session name used to load the configuration
  returned: when changed is True
  type: str
  sample: ansible_1479315771
"""
import re
import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.eos.eos import run_commands, load_config
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.eos.eos import eos_argument_spec, check_args


def check_transport(module):
    transport = module.params['transport']
    provider_transport = (module.params['provider'] or {}).get('transport')

    if 'eapi' in (transport, provider_transport):
        module.fail_json(msg='eos_eapi module is only supported over cli transport')


def validate_http_port(value, module):
    if not 1 <= value <= 65535:
        module.fail_json(msg='http_port must be between 1 and 65535')


def validate_https_port(value, module):
    if not 1 <= value <= 65535:
        module.fail_json(msg='http_port must be between 1 and 65535')


def validate_local_http_port(value, module):
    if not 1 <= value <= 65535:
        module.fail_json(msg='http_port must be between 1 and 65535')


def validate_vrf(value, module):
    out = run_commands(module, ['show vrf'])
    configured_vrfs = re.findall(r'^\s+(\w+)(?=\s)', out[0], re.M)
    configured_vrfs.append('default')
    if value not in configured_vrfs:
        module.fail_json(msg='vrf `%s` is not configured on the system' % value)


def map_obj_to_commands(updates, module, warnings):
    commands = list()
    want, have = updates

    def needs_update(x):
        return want.get(x) is not None and (want.get(x) != have.get(x))

    def add(cmd):
        if 'management api http-commands' not in commands:
            commands.insert(0, 'management api http-commands')
        commands.append(cmd)

    if any((needs_update('http'), needs_update('http_port'))):
        if want['http'] is False:
            add('no protocol http')
        else:
            if have['http'] is False and want['http'] in (False, None):
                warnings.append('protocol http is not enabled, not configuring http port value')
            else:
                port = want['http_port'] or 80
                add('protocol http port %s' % port)

    if any((needs_update('https'), needs_update('https_port'))):
        if want['https'] is False:
            add('no protocol https')
        else:
            if have['https'] is False and want['https'] in (False, None):
                warnings.append('protocol https is not enabled, not configuring https port value')
            else:
                port = want['https_port'] or 443
                add('protocol https port %s' % port)

    if any((needs_update('local_http'), needs_update('local_http_port'))):
        if want['local_http'] is False:
            add('no protocol http localhost')
        else:
            if have['local_http'] is False and want['local_http'] in (False, None):
                warnings.append('protocol local_http is not enabled, not configuring local_http port value')
            else:
                port = want['local_http_port'] or 8080
                add('protocol http localhost port %s' % port)

    if any((needs_update('socket'), needs_update('socket'))):
        if want['socket'] is False:
            add('no protocol unix-socket')
        else:
            add('protocol unix-socket')

    if needs_update('state') and not needs_update('vrf'):
        if want['state'] == 'stopped':
            add('shutdown')
        elif want['state'] == 'started':
            add('no shutdown')

    if needs_update('vrf'):
        add('vrf %s' % want['vrf'])
        # switching operational vrfs here
        # need to add the desired state as well
        if want['state'] == 'stopped':
            add('shutdown')
        elif want['state'] == 'started':
            add('no shutdown')

    return commands


def parse_state(data):
    if data[0]['enabled']:
        return 'started'
    else:
        return 'stopped'


def map_config_to_obj(module):
    out = run_commands(module, ['show management api http-commands | json'])
    return {
        'http': out[0]['httpServer']['configured'],
        'http_port': out[0]['httpServer']['port'],
        'https': out[0]['httpsServer']['configured'],
        'https_port': out[0]['httpsServer']['port'],
        'local_http': out[0]['localHttpServer']['configured'],
        'local_http_port': out[0]['localHttpServer']['port'],
        'socket': out[0]['unixSocketServer']['configured'],
        'vrf': out[0]['vrf'],
        'state': parse_state(out)
    }


def map_params_to_obj(module):
    obj = {
        'http': module.params['http'],
        'http_port': module.params['http_port'],
        'https': module.params['https'],
        'https_port': module.params['https_port'],
        'local_http': module.params['local_http'],
        'local_http_port': module.params['local_http_port'],
        'socket': module.params['socket'],
        'vrf': module.params['vrf'],
        'state': module.params['state']
    }

    for key, value in iteritems(obj):
        if value:
            validator = globals().get('validate_%s' % key)
            if validator:
                validator(value, module)

    return obj


def verify_state(updates, module):
    want, have = updates

    invalid_state = [('http', 'httpServer'),
                     ('https', 'httpsServer'),
                     ('local_http', 'localHttpServer'),
                     ('socket', 'unixSocketServer')]

    timeout = module.params['timeout'] or 30
    state = module.params['state']

    while invalid_state:
        out = run_commands(module, ['show management api http-commands | json'])
        for index, item in enumerate(invalid_state):
            want_key, eapi_key = item
            if want[want_key] is not None:
                if want[want_key] == out[0][eapi_key]['running']:
                    del invalid_state[index]
            elif state == 'stopped':
                if not out[0][eapi_key]['running']:
                    del invalid_state[index]
            else:
                del invalid_state[index]
        time.sleep(1)
        timeout -= 1
        if timeout == 0:
            module.fail_json(msg='timeout expired before eapi running state changed')


def collect_facts(module, result):
    out = run_commands(module, ['show management api http-commands | json'])
    facts = dict(eos_eapi_urls=dict())
    for each in out[0]['urls']:
        intf, url = each.split(' : ')
        key = str(intf).strip()
        if key not in facts['eos_eapi_urls']:
            facts['eos_eapi_urls'][key] = list()
        facts['eos_eapi_urls'][key].append(str(url).strip())
    result['ansible_facts'] = facts


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        http=dict(aliases=['enable_http'], type='bool'),
        http_port=dict(type='int'),

        https=dict(aliases=['enable_https'], type='bool'),
        https_port=dict(type='int'),

        local_http=dict(aliases=['enable_local_http'], type='bool'),
        local_http_port=dict(type='int'),

        socket=dict(aliases=['enable_socket'], type='bool'),

        vrf=dict(default='default'),

        config=dict(),
        state=dict(default='started', choices=['stopped', 'started']),
    )

    argument_spec.update(eos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    check_transport(module)

    result = {'changed': False}

    warnings = list()
    if module.params['config']:
        warnings.append('config parameter is no longer necessary and will be ignored')

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)

    commands = map_obj_to_commands((want, have), module, warnings)
    result['commands'] = commands

    if commands:
        commit = not module.check_mode
        response = load_config(module, commands, commit=commit)
        if response.get('diff') and module._diff:
            result['diff'] = {'prepared': response.get('diff')}
        result['session_name'] = response.get('session')
        result['changed'] = True

    if result['changed']:
        verify_state((want, have), module)

    collect_facts(module, result)

    if warnings:
        result['warnings'] = warnings

    module.exit_json(**result)


if __name__ == '__main__':
    main()
