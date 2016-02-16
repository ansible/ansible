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
author: "Chris Houseknecht (@chouseknecht)"
short_description: Manage and configure EAPI. Requires EOS v4.12 or greater. 
description:
  - Use to enable or disable EAPI access, and set the port and state
    of http, https, localHttp and unix-socket servers.
  - When enabling EAPI access the default is to enable HTTP on port
    80, enable HTTPS on port 443, disable local HTTP, and disable
    Unix socket server. Use the options listed below to override the
    default configuration.
  - Requires EOS v4.12 or greater.
extends_documentation_fragment: eos
options:
    state:
        description:
            - Set to started or stopped. A state of started will
              enable EAPI access, and a state of stopped will
              disable or shutdown all EAPI access.
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
    local_http_port:
        description:
            - Port on which the local HTTP server will listen.
        required: false
        default: 8080
    http:
        description:
            - Enable HTTP server access.
        required: false
        default: true
        aliases:
            - enable_http
    https:
        description:
            - Enable HTTPS server access.
        required: false
        default: true
        aliases:
            - enable_https
    local_http:
        description:
            - Enable local HTTP server access.
        required: false
        default: false
        aliases:
            - enable_local_http
    socket:
        description:
            - Enable Unix socket server access.
        required: false
        default: false
        aliases:
            - enable_socket
"""

EXAMPLES = """
    - name: Enable EAPI access with default configuration
      eos_eapi:
          state: started
          provider: {{ provider }}

    - name: Enable EAPI with no HTTP, HTTPS at port 9443, local HTTP at port 80, and socket enabled
      eos_eapi:
          state: started
          http: false
          https_port: 9443
          local_http: yes
          local_http_port: 80
          socket: yes
          provider: {{ provider }}

    - name: Shutdown EAPI access
      eos_eapi:
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
        - Set of commands to be executed on remote device
    returned: always
    type: list
    sample: [
        'management api http-commands',
        'shutdown'
    ]

_config:
    description:
       - Configuration found on the device prior to executing any commands.
    returned: always
    type: object
    sample: {...}
"""


def http_commands(protocol, port, enable, config):

    started_config = config['{0}Server'.format(protocol)]
    commands = []
    changed = False

    if started_config.get('running'):
        if not enable:
            # turn off server
            commands.append('no protocol {0}'.format(protocol))
            changed = True
        elif started_config.get('port') != port:
            # update the port
            commands.append('protocol {0} port {1}'.format(protocol, port))
            changed = True
    elif not started_config.get('runnng') and enable:
        # turn on server
        commands.append('protocol {0} port {1}'.format(protocol, port))
        changed = True

    return commands, changed


def execute_commands(module, commands):

    if not module.params.get('check_mode'):
        module.configure(commands)


def config_server(module):

    state = module.params.get('state')
    local_http_port = module.params.get('local_http_port')
    socket= module.params.get('socket')
    local_http = module.params.get('local_http')
    config = module.from_json(module.execute(['show management api http-commands | json'])[0])
    result = dict(changed=False, _config=config, commands=[])
    commands = [
        'management api http-commands'
    ]

    if not config.get('enabled'):
        if state == 'started':
            # turn on eapi access
            commands.append('no shutdown')
            result['changed'] = True
        else:
            # state is stopped. nothing to do
            return result

    if config.get('enabled') and state == 'stopped':
        # turn off eapi access and exit
        commands.append('shutdown')
        result['changed'] = True
        result['commands'] = commands
        execute_commands(module, commands)
        return result

    # http and https
    for protocol in ['http', 'https']:
        cmds, chg = http_commands(protocol, module.params['{0}_port'.format(protocol)],
                                  module.params['{0}'.format(protocol)], config)
        if chg:
            commands += cmds
            result['changed'] = True

    # local HTTP
    if config.get('localHttpServer').get('running'):
        if not local_http:
            # turn off local http server
            commands.append('no protocol http localhost')
            result['changed'] = True
        elif config.get('localHttpServer').get('port') != local_http_port:
            # update the local http port
            commands.append('protocol http localhost port {0}'.format(local_http_port))
            result['changed'] = True

    if not config.get('localHttpServer').get('running') and local_http:
        # turn on local http server
        commands.append('protocol http localhost port {0}'.format(local_http_port))
        result['changed'] = True

    # socket server
    if config.get('unixSocketServer').get('running') and not socket:
        # turn off unix socket
        commands.append('no protocol unix-socket')
        result['changed'] = True

    if not config.get('unixSocketServer').get('running') and socket:
        # turn on unix socket
        commands.append('protocol unix-socket')
        result['changed'] = True

    if len(commands) > 1:
        # something requires change
        execute_commands(module, commands)
        result['commands'] = commands

    return result

def check_version(module):
    config = module.from_json(module.execute(['show version | json'])[0])
    versions = config['version'].split('.')
    if int(versions[0]) < 4 or int(versions[1]) < 12:
        module.fail_json(msg="Device version {0} does not support eAPI. eAPI was introduced in EOS 4.12.")

def main():
    """ main entry point for module execution
    """

    argument_spec = dict(
        state=dict(default='started', choices=['stopped','started']),
        http_port=dict(default=80, type='int'),
        https_port=dict(default=443, type='int'),
        local_http_port=dict(default=8080, type='int'),
        http=dict(aliases=['enable_http'], default=True, type='bool'),
        https=dict(aliases=['enable_https'], default=True, type='bool'),
        socket=dict(aliases=['enable_socket'], default=False, type='bool'),
        local_http=dict(aliases=['enable_local_http'], default=False, type='bool'),

        # Only allow use of transport cli when coniguring EAPI
        transport=dict(required=True, choices=['cli'])
    )

    module = get_module(argument_spec=argument_spec,
                        supports_check_mode=True)

    check_version(module)

    result = config_server(module)

    return module.exit_json(**result)


from ansible.module_utils.basic import *
from ansible.module_utils.shell import *
from ansible.module_utils.eos import *

if __name__ == '__main__':
    main()
