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
author: "Chris Houseknecht (@chouseknecht)"
short_description: Manage NXAPI configuration on an NXOS device.
description:
  - Use to enable or disable NXAPI access, set the port and state
    of http and https servers, and enable or disable the sandbox.
  - When enabling NXAPI access the default is to enable HTTP on port
    80, enable HTTPS on port 443, and enable the web based UI sandbox.
    Use the options below to override the default configuration.
extends_documentation_fragment: nxos
options:
    state:
        description:
            - Set to started or stopped. A state of started will
              enable NXAPI access, and a state of stopped will
              disable or shutdown all NXAPI access.
        choices:
            - started
            - stopped
        requred: false
        default: started
    http_port:
        description:
            - Port on which the HTTP server will listen.
        required: false
        default: 80
    https_port:
        description:
            - Port on which the HTTPS server will listen.
        required: false
        default: 443
    http:
        description:
            - Enable/disable HTTP server.
        required: false
        default: true
        aliases:
            - enable_http
    https:
        description:
            - Enable/disable HTTPS server.
        required: false
        default: true
        aliases:
            - enable_https
    sandbox:
        description:
            - Enable/disable NXAPI web based UI for entering commands.
        required: false
        default: true
        aliases:
            - enable_sandbox
"""

EXAMPLES = """
    - name: Enable NXAPI access with default configuration
      nxos_nxapi:
          provider: {{ provider }}

    - name: Enable NXAPI with no HTTP, HTTPS at port 9443 and sandbox disabled
      nxos_nxapi:
          enable_http: false
          https_port: 9443
          enable_sandbox: no
          provider: {{ provider }}

    - name: shutdown NXAPI access
      nxos_nxapi:
          state: stopped
          provider: {{ provider }}
"""

RETURN = """
changed:
    description:
        - Indicates if commands were sent to the device.
    returned: always
    type: boolean
    sample: false

commands:
    description:
        - Set of commands to be executed on remote device. If run in check mode,
          commands will not be executed.
    returned: always
    type: list
    sample: [
        'nxapi feature',
        'nxapi http port 8080'
    ]

_config:
    description:
       - Configuration found on the device prior ro any commands being executed.
    returned: always
    type: object
    sample: {...}
"""


def http_commands(protocol, port, enable, config):
    port_config = config.get('{0}_port'.format(protocol), None)
    changed = False
    commands = []
    if port_config is None and enable:
        # enable
        changed = True
        commands.append('nxapi {0} port {1}'.format(protocol, port))
    elif port_config is not None:
        if not enable:
            # disable
            commands.append('no nxapi {0}'.format(protocol))
            changed = True
        elif port_config != port:
            # update port
            commands.append('nxapi {0} port {1}'.format(protocol, port))
            changed = True
    return commands, changed


def execute_commands(module, commands):
    if not module.params.get('check_mode'):
        module.configure(commands)

def get_nxapi_state(module):
    features = module.execute(['show feature | grep nxapi'])[0]
    if re.search('disabled', features) is None:
        return 'started'
    return 'stopped'


def config_server(module):

    nxapi_state = get_nxapi_state(module)

    config = dict()
    if nxapi_state == 'started':
        config = module.from_json(module.execute(['show nxapi | json'])[0])

    state = module.params.get('state')
    result = dict(changed=False, _config=config, commands=[])
    commands = []

    if config.get('nxapi_status', 'Disabled') == 'Disabled':
        if state == 'started':
            # enable nxapi and get the new default config
            commands.append('feature nxapi')
            result['_config'] = dict()
            result['changed'] = True
            if module.params.get('check_mode'):
                # make an assumption about default state
                config['http_port'] = 80
                config['sandbox_status'] = 'Disabled'
            else:
                # get the default config
                execute_commands(module, commands)
                config = module.from_json(module.execute(['show nxapi | json'])[0])
        else:
            # nxapi already disabled
            return result
    elif config.get('nxapi_status', 'Disabled') == 'Enabled' and state == 'stopped':
        # disable nxapi and exit
        commands.append('no feature nxapi')
        result['changed'] = True
        result['commands'] = commands
        execute_commands(module, commands)
        return result

    # configure http and https
    for protocol in ['http', 'https']:
        cmds, chg = http_commands(protocol, module.params['{0}_port'.format(protocol)],
                                  module.params[protocol], config)
        if chg:
            commands += cmds
            result['changed'] = True

    # configure sandbox
    config_sandbox = config.get('sandbox_status', None)
    enable_sandbox = module.params.get('sandbox')

    if config_sandbox is None:
        # there is no prior state, so we must set one
        result['changed'] = True
        if enable_sandbox:
            commands.append('nxapi sandbox')
        else:
            commands.append('no nxapi sandbox')
    else:
        # there is a prior state, so be idempotent
        if config_sandbox == 'Enabled' and not enable_sandbox:
            # turn off sandbox
            commands.append('no nxapi sandbox')
            result['changed'] = True
        elif config_sandbox == 'Disabled' and enable_sandbox:
            # turn on sandbox
            commands.append('nxapi sandbox')
            result['changed'] = True

    if len(commands) > 0:
        # something requires change
        result['commands'] = commands
        execute_commands(module, commands)

    return result


def main():
    """ main entry point for module execution
    """

    argument_spec = dict(
        state=dict(default='started', choices=['started','stopped']),
        http_port=dict(default=80, type='int'),
        https_port=dict(default=443, type='int'),
        http=dict(aliases=['enable_http'], default=True, type='bool'),
        https=dict(aliases=['enable_https'], default=True, type='bool'),
        sandbox=dict(aliases=['enable_sandbox'], default=True, type='bool'),

        # Only allow configuration of NXAPI using cli transpsort
        transport=dict(required=True, choices=['cli'])
    )

    module = get_module(argument_spec=argument_spec,
                        supports_check_mode=True)

    result = config_server(module)

    return module.exit_json(**result)


from ansible.module_utils.basic import *
from ansible.module_utils.shell import *
from ansible.module_utils.nxos import *
if __name__ == '__main__':
    main()

