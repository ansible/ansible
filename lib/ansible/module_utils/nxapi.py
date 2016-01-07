#
# (c) 2015 Peter Sprygada, <psprygada@ansible.com>
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
"""
This module adds support for Cisco NXAPI to Ansible shared
module_utils.  It builds on module_utils/urls.py to provide
NXAPI support over HTTP/S which is required for proper operation.

In order to use this module, include it as part of a custom
module as shown below.

** Note: The order of the import statements does matter. **

from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.nxapi import *

The nxapi module provides the following common argument spec:

    * host (str) - The IPv4 address or FQDN of the network device

    * port (str) - Overrides the default port to use for the HTTP/S
        connection.  The default values are 80 for HTTP and
        443 for HTTPS

    * username (str) - The username to use to authenticate
        the HTTP/S connection.  Aliases: username

    * password (str) - The password to use to authenticate
        the HTTP/S connection.  Aliases: password

    * use_ssl (bool) - Specifies whether or not to use an encrypted (HTTPS)
        connection or not.  The default value is False.

    * command_type (str) - The type of command to send to the remote
        device.  Valid values in `cli_show`, `cli_show_ascii`, 'cli_conf`
        and `bash`.  The default value is `cli_show_ascii`

    * device (dict) - Used to send the entire set of connection parameters
        as a dict object.  This argument is mutually exclusive with the
        host argument

In order to communicate with Cisco NXOS devices, the NXAPI feature
must be enabled and configured on the device.

"""

NXAPI_COMMAND_TYPES = ['cli_show', 'cli_show_ascii', 'cli_conf', 'bash']

NXAPI_COMMON_ARGS = dict(
    host=dict(),
    port=dict(),
    username=dict(),
    password=dict(),
    use_ssl=dict(default=False, type='bool'),
    device=dict(),
    command_type=dict(default='cli_show_ascii', choices=NXAPI_COMMAND_TYPES)
)

def nxapi_module(**kwargs):
    """Append the common args to the argument_spec
    """
    spec = kwargs.get('argument_spec') or dict()

    argument_spec = url_argument_spec()
    argument_spec.update(NXAPI_COMMON_ARGS)
    if kwargs.get('argument_spec'):
        argument_spec.update(kwargs['argument_spec'])
    kwargs['argument_spec'] = argument_spec

    module = AnsibleModule(**kwargs)

    device = module.params.get('device') or dict()
    for key, value in device.iteritems():
        if key in NXAPI_COMMON_ARGS:
            module.params[key] = value

    params = json_dict_unicode_to_bytes(json.loads(MODULE_COMPLEX_ARGS))
    for key, value in params.iteritems():
        if key != 'device':
            module.params[key] = value

    return module

def nxapi_url(params):
    """Constructs a valid NXAPI url
    """
    if params['use_ssl']:
        proto = 'https'
    else:
        proto = 'http'
    host = params['host']
    url = '{}://{}'.format(proto, host)
    if params['port']:
        url = '{}:{}'.format(url, params['port'])
    url = '{}/ins'.format(url)
    return url

def nxapi_body(commands, command_type, **kwargs):
    """Encodes a NXAPI JSON request message
    """
    if isinstance(commands, (list, set, tuple)):
        commands = ' ;'.join(commands)

    msg = {
        'version': kwargs.get('version') or '1.2',
        'type': command_type,
        'chunk': kwargs.get('chunk') or '0',
        'sid': kwargs.get('sid'),
        'input': commands,
        'output_format': 'json'
    }

    return dict(ins_api=msg)

def nxapi_command(module, commands, command_type=None, **kwargs):
    """Sends the list of commands to the device over NXAPI
    """
    url = nxapi_url(module.params)

    command_type = command_type or module.params['command_type']

    data = nxapi_body(commands, command_type)
    data = module.jsonify(data)

    headers = {'Content-Type': 'text/json'}

    module.params['url_username'] = module.params['username']
    module.params['url_password'] = module.params['password']

    response, headers = fetch_url(module, url, data=data, headers=headers,
                                  method='POST')

    status = kwargs.get('status') or 200
    if headers['status'] != status:
        module.fail_json(**headers)

    response = module.from_json(response.read())
    return response, headers

