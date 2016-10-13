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
module: nxos_nxapi
version_added: "2.1"
author: "Peter Sprygada (@privateip)"
short_description: Manage NXAPI configuration on an NXOS device.
description:
  - Configures the NXAPI feature on devices running Cisco NXOS.  The
    NXAPI feature is absent from the configuration by default.  Since
    this module manages the NXAPI feature it only supports the use
    of the C(Cli) transport.
extends_documentation_fragment: nxos
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
  config:
    description:
      - The C(config) argument provides an optional argument to
        specify the device running-config to used as the basis for
        configuring the remote system.  The C(config) argument accepts
        a string value that represents the device configuration.
    required: false
    default: null
    version_added: "2.2"
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
# Note: examples below use the following provider dict to handle
#       transport and authentication to the node.
vars:
  cli:
    host: "{{ inventory_hostname }}"
    username: admin
    password: admin

- name: Enable NXAPI access with default configuration
  nxos_nxapi:
    provider: {{ cli }}

- name: Enable NXAPI with no HTTP, HTTPS at port 9443 and sandbox disabled
  nxos_nxapi:
    enable_http: false
    https_port: 9443
    https: yes
    enable_sandbox: no
    provider: {{ cli }}

- name: remove NXAPI configuration
  nxos_nxapi:
    state: absent
    provider: {{ cli }}
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
import time

from ansible.module_utils.netcfg import NetworkConfig, dumps
from ansible.module_utils.nxos import NetworkModule, NetworkError
from ansible.module_utils.basic import get_exception

PRIVATE_KEYS_RE = re.compile('__.+__')

def invoke(name, *args, **kwargs):
    func = globals().get(name)
    if func:
        return func(*args, **kwargs)

def get_instance(module):
    instance = dict(state='absent')
    try:
        resp = module.cli('show nxapi', 'json')
    except NetworkError:
        return instance

    instance['state'] = 'present'

    instance['http'] = 'http_port' in resp[0]
    instance['http_port'] = resp[0].get('http_port') or 80

    instance['https'] = 'https_port' in resp[0]
    instance['https_port'] = resp[0].get('https_port') or 443

    instance['sandbox'] = resp[0]['sandbox_status']

    return instance

def present(module, instance, commands):
    commands.append('feature nxapi')
    setters = set()
    for key, value in module.argument_spec.iteritems():
        setter = value.get('setter') or 'set_%s' % key
        if setter not in setters:
            setters.add(setter)
            if module.params[key] is not None:
                invoke(setter, module, instance, commands)

def absent(module, instance, commands):
    if instance['state'] != 'absent':
        commands.append('no feature nxapi')

def set_http(module, instance, commands):
    port = module.params['http_port']
    if not 0 <= port <= 65535:
        module.fail_json(msg='http_port must be between 1 and 65535')
    elif module.params['http'] is True:
        commands.append('nxapi http port %s' % port)
    elif module.params['http'] is False:
        commands.append('no nxapi http')

def set_https(module, instance, commands):
    port = module.params['https_port']
    if not 0 <= port <= 65535:
        module.fail_json(msg='https_port must be between 1 and 65535')
    elif module.params['https'] is True:
        commands.append('nxapi https port %s' % port)
    elif module.params['https'] is False:
        commands.append('no nxapi https')

def set_sandbox(module, instance, commands):
    if module.params['sandbox'] is True:
        commands.append('nxapi sandbox')
    elif module.params['sandbox'] is False:
        commands.append('no nxapi sandbox')

def get_config(module):
    contents = module.params['config']
    if not contents:
        try:
            contents = module.cli(['show running-config nxapi all'])[0]
        except NetworkError:
            contents = None
    config = NetworkConfig(indent=2)
    if contents:
        config.load(contents)
    return config

def load_checkpoint(module, result):
    try:
        checkpoint = result['__checkpoint__']
        module.cli(['rollback running-config checkpoint %s' % checkpoint,
                    'no checkpoint %s' % checkpoint], output='text')
    except KeyError:
        module.fail_json(msg='unable to rollback, checkpoint not found')
    except NetworkError:
        exc = get_exception()
        msg = 'unable to rollback configuration'
        module.fail_json(msg=msg, checkpoint=checkpoint, **exc.kwargs)

def load_config(module, commands, result):
    # create a config checkpoint
    checkpoint = 'ansible_%s' % int(time.time())
    module.cli(['checkpoint %s' % checkpoint], output='text')
    result['__checkpoint__'] = checkpoint

    # load the config into the device
    module.config.load_config(commands)

    # load was successfully, remove the config checkpoint
    module.cli(['no checkpoint %s' % checkpoint])

def load(module, commands, result):
    candidate = NetworkConfig(indent=2, contents='\n'.join(commands))
    config = get_config(module)
    configobjs = candidate.difference(config)

    if configobjs:
        commands = dumps(configobjs, 'commands').split('\n')
        result['updates'] = commands
        if not module.check_mode:
            load_config(module, commands, result)
        result['changed'] = True

def clean_result(result):
    # strip out any keys that have two leading and two trailing
    # underscore characters
    for key in result.keys():
        if PRIVATE_KEYS_RE.match(key):
            del result[key]


def main():
    """ main entry point for module execution
    """

    argument_spec = dict(
        http=dict(aliases=['enable_http'], default=True, type='bool', setter='set_http'),
        http_port=dict(default=80, type='int', setter='set_http'),

        https=dict(aliases=['enable_https'], default=False, type='bool', setter='set_https'),
        https_port=dict(default=443, type='int', setter='set_https'),

        sandbox=dict(aliases=['enable_sandbox'], default=False, type='bool'),

        # Only allow configuration of NXAPI using cli transport
        transport=dict(required=True, choices=['cli']),

        config=dict(),

        # Support for started and stopped is for backwards capability only and
        # will be removed in a future version
        state=dict(default='present', choices=['started', 'stopped', 'present', 'absent'])
    )

    module = NetworkModule(argument_spec=argument_spec,
                           connect_on_load=False,
                           supports_check_mode=True)

    state = module.params['state']

    warnings = list()

    result = dict(changed=False, warnings=warnings)

    if state == 'started':
        state = 'present'
        warnings.append('state=started is deprecated and will be removed in a '
                        'a future release.  Please use state=present instead')
    elif state == 'stopped':
        state = 'absent'
        warnings.append('state=stopped is deprecated and will be removed in a '
                        'a future release.  Please use state=absent instead')

    commands = list()
    instance = get_instance(module)

    invoke(state, module, instance, commands)

    try:
        load(module, commands, result)
    except (ValueError, NetworkError):
        load_checkpoint(module, result)
        exc = get_exception()
        module.fail_json(msg=str(exc), **exc.kwargs)

    clean_result(result)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
