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
# Note: examples below use the following provider dict to handle
#       transport and authentication to the node.
vars:
  cli:
    host: "{{ inventory_hostname }}"
    username: admin
    password: admin

- name: Enable eAPI access with default configuration
  eos_eapi:
    state: started
    provider: {{ cli }}

- name: Enable eAPI with no HTTP, HTTPS at port 9443, local HTTP at port 80, and socket enabled
  eos_eapi:
    state: started
    http: false
    https_port: 9443
    local_http: yes
    local_http_port: 80
    socket: yes
    provider: {{ cli }}

- name: Shutdown eAPI access
  eos_eapi:
    state: stopped
    provider: {{ cli }}
"""

RETURN = """
updates:
  description:
    - Set of commands to be executed on remote device
  returned: always
  type: list
  sample: ['management api http-commands', 'shutdown']
urls:
  description: Hash of URL endpoints eAPI is listening on per interface
  returned: when eAPI is started
  type: dict
  sample: {'Management1': ['http://172.26.10.1:80']}
"""
import re
import time

import ansible.module_utils.eos

from ansible.module_utils.basic import get_exception
from ansible.module_utils.network import NetworkModule, NetworkError
from ansible.module_utils.netcfg import NetworkConfig, dumps

PRIVATE_KEYS_RE = re.compile('__.+__')


def invoke(name, *args, **kwargs):
    func = globals().get(name)
    if func:
        return func(*args, **kwargs)

def get_instance(module):
    try:
        resp = module.cli('show management api http-commands', 'json')
        return dict(
            http=resp[0]['httpServer']['configured'],
            http_port=resp[0]['httpServer']['port'],
            https=resp[0]['httpsServer']['configured'],
            https_port=resp[0]['httpsServer']['port'],
            local_http=resp[0]['localHttpServer']['configured'],
            local_http_port=resp[0]['localHttpServer']['port'],
            socket=resp[0]['unixSocketServer']['configured'],
            vrf=resp[0]['vrf']
        )
    except NetworkError:
        exc = get_exception()
        module.fail_json(msg=str(exc), **exc.kwargs)

def started(module, instance, commands):
    commands.append('no shutdown')
    setters = set()
    for key, value in module.argument_spec.iteritems():
        if module.params[key] is not None:
            setter = value.get('setter') or 'set_%s' % key
            if setter not in setters:
                setters.add(setter)
            invoke(setter, module, instance, commands)

def stopped(module, instance, commands):
    commands.append('shutdown')

def set_protocol_http(module, instance, commands):
    port = module.params['http_port']
    if not 1 <= port <= 65535:
        module.fail_json(msg='http_port must be between 1 and 65535')
    elif any((module.params['http'], instance['http'])):
        commands.append('protocol http port %s' % port)
    elif module.params['http'] is False:
        commands.append('no protocol http')

def set_protocol_https(module, instance, commands):
    port = module.params['https_port']
    if not 1 <= port <= 65535:
        module.fail_json(msg='https_port must be between 1 and 65535')
    elif any((module.params['https'], instance['https'])):
        commands.append('protocol https port %s' % port)
    elif module.params['https'] is False:
        commands.append('no protocol https')

def set_local_http(module, instance, commands):
    port = module.params['local_http_port']
    if not 1 <= port <= 65535:
        module.fail_json(msg='local_http_port must be between 1 and 65535')
    elif any((module.params['local_http'], instance['local_http'])):
        commands.append('protocol http localhost port %s' % port)
    elif module.params['local_http'] is False:
        commands.append('no protocol http localhost port 8080')

def set_socket(module, instance, commands):
    if any((module.params['socket'], instance['socket'])):
        commands.append('protocol unix-socket')
    elif module.params['socket'] is False:
        commands.append('no protocol unix-socket')

def set_vrf(module, instance, commands):
    vrf = module.params['vrf']
    if vrf != 'default':
        resp = module.cli(['show vrf'])
        if vrf not in resp[0]:
            module.fail_json(msg="vrf '%s' is not configured" % vrf)
    commands.append('vrf %s' % vrf)

def get_config(module):
    contents = module.params['config']
    if not contents:
        cmd = 'show running-config all section management api http-commands'
        contents = module.cli([cmd])
    config = NetworkConfig(indent=3, contents=contents[0])
    return config

def load_config(module, instance, commands, result):
    commit = not module.check_mode
    diff = module.config.load_config(commands, commit=commit)
    if diff:
        result['diff'] = dict(prepared=diff)
        result['changed'] = True

def load(module, instance, commands, result):
    candidate = NetworkConfig(indent=3)
    candidate.add(commands, parents=['management api http-commands'])

    config = get_config(module)
    configobjs = candidate.difference(config)

    if configobjs:
        commands = dumps(configobjs, 'commands').split('\n')
        result['updates'] = commands
        load_config(module, instance, commands, result)

def clean_result(result):
    # strip out any keys that have two leading and two trailing
    # underscore characters
    for key in result.keys():
        if PRIVATE_KEYS_RE.match(key):
            del result[key]

def collect_facts(module, result):
    resp = module.cli(['show management api http-commands'], output='json')
    facts = dict(eos_eapi_urls=dict())
    for each in resp[0]['urls']:
        intf, url = each.split(' : ')
        key = str(intf).strip()
        if  key not in facts['eos_eapi_urls']:
            facts['eos_eapi_urls'][key] = list()
        facts['eos_eapi_urls'][key].append(str(url).strip())
    result['ansible_facts'] = facts


def main():
    """ main entry point for module execution
    """

    argument_spec = dict(
        http=dict(aliases=['enable_http'], default=False, type='bool', setter='set_protocol_http'),
        http_port=dict(default=80, type='int', setter='set_protocol_http'),

        https=dict(aliases=['enable_https'], default=True, type='bool', setter='set_protocol_https'),
        https_port=dict(default=443, type='int', setter='set_protocol_https'),

        local_http=dict(aliases=['enable_local_http'], default=False, type='bool', setter='set_local_http'),
        local_http_port=dict(default=8080, type='int', setter='set_local_http'),

        socket=dict(aliases=['enable_socket'], default=False, type='bool'),

        vrf=dict(default='default'),

        config=dict(),

        # Only allow use of transport cli when configuring eAPI
        transport=dict(default='cli', choices=['cli']),

        state=dict(default='started', choices=['stopped', 'started']),
    )

    module = NetworkModule(argument_spec=argument_spec,
                           connect_on_load=False,
                           supports_check_mode=True)

    state = module.params['state']

    result = dict(changed=False)

    commands = list()
    instance = get_instance(module)

    invoke(state, module, instance, commands)

    try:
        load(module, instance, commands, result)
    except NetworkError:
        exc = get_exception()
        module.fail_json(msg=str(exc), **exc.kwargs)

    collect_facts(module, result)
    clean_result(result)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
