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

    * host (str) - [Required] The IPv4 address or FQDN of the network device

    * port (str) - Overrides the default port to use for the HTTP/S
        connection.  The default values are 80 for HTTP and
        443 for HTTPS

    * url_username (str) - [Required] The username to use to authenticate
        the HTTP/S connection.  Aliases: username

    * url_password (str) - [Required] The password to use to authenticate
        the HTTP/S connection.  Aliases: password

    * use_ssl (bool) - Specifies whether or not to use an encrypted (HTTPS)
        connection or not.  The default value is False.

    * command_type (str) - The type of command to send to the remote
        device.  Valid values in `cli_show`, `cli_show_ascii`, 'cli_conf`
        and `bash`.  The default value is `cli_show_ascii`

In order to communicate with Cisco NXOS devices, the NXAPI feature
must be enabled and configured on the device.

"""

NXAPI_COMMAND_TYPES = ['cli_show', 'cli_show_ascii', 'cli_conf', 'bash']

def nxapi_argument_spec(spec=None):
    """Creates an argument spec for working with NXAPI
    """
    arg_spec = url_argument_spec()
    arg_spec.update(dict(
        host=dict(required=True),
        port=dict(),
        url_username=dict(required=True, aliases=['username']),
        url_password=dict(required=False, aliases=['password']),
        use_ssl=dict(default=False, type='bool'),
        command_type=dict(default='cli_show_ascii', choices=NXAPI_COMMAND_TYPES)
    ))
    if spec:
        arg_spec.update(spec)
    return arg_spec

def nxapi_url(module):
    """Constructs a valid NXAPI url
    """
    proto = 'https' if module.params['use_ssl'] else 'http'
    host = module.params['host']
    url = '{}://{}'.format(proto, host)
    port = module.params['port']
    if module.params['port']:
        url = '{}:{}'.format(url, module.params['port'])
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
    url = nxapi_url(module)

    command_type = command_type or module.params['command_type']

    data = nxapi_body(commands, command_type)
    data = module.jsonify(data)

    headers = {'Content-Type': 'text/json'}

    response, headers = fetch_url(module, url, data=data, headers=headers,
                                  method='POST')

    status = kwargs.get('status') or 200
    if headers['status'] != status:
        module.fail_json(**headers)

    response = module.from_json(response.read())
    return response, headers

