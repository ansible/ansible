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
This module adds shared support for Arista EOS devices using eAPI over
HTTP/S transport.   It is built on module_utils/urls.py which is required
for proper operation.

In order to use this module, include it as part of a custom
module as shown below.

** Note: The order of the import statements does matter. **

from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.eapi import *

The eapi module provides the following common argument spec:

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

    * enable_mode (bool) - Specifies whether or not to enter `enable` mode
        prior to executing the command list.  The default value is True

    * enable_password (str) - The password for entering `enable` mode
        on the switch if configured.

In order to communicate with Arista EOS devices, the eAPI feature
must be enabled and configured on the device.

"""
def eapi_argument_spec(spec=None):
    """Creates an argument spec for working with eAPI
    """
    arg_spec = url_argument_spec()
    arg_spec.update(dict(
        host=dict(required=True),
        port=dict(),
        url_username=dict(required=True, aliases=['username']),
        url_password=dict(required=True, aliases=['password']),
        use_ssl=dict(default=True, type='bool'),
        enable_mode=dict(default=True, type='bool'),
        enable_password=dict()
    ))
    if spec:
        arg_spec.update(spec)
    return arg_spec

def eapi_url(module):
    """Construct a valid Arist eAPI URL
    """
    if module.params['use_ssl']:
        proto = 'https'
    else:
        proto = 'http'
    host = module.params['host']
    url = '{}://{}'.format(proto, host)
    if module.params['port']:
        url = '{}:{}'.format(url, module.params['port'])
    return '{}/command-api'.format(url)

def to_list(arg):
    """Convert the argument to a list object
    """
    if isinstance(arg, (list, tuple)):
        return list(arg)
    elif arg is not None:
        return [arg]
    else:
        return []

def eapi_body(commands, encoding, reqid=None):
    """Create a valid eAPI JSON-RPC request message
    """
    params = dict(version=1, cmds=to_list(commands), format=encoding)
    return dict(jsonrpc='2.0', id=reqid, method='runCmds', params=params)

def eapi_enable_mode(module):
    """Build commands for entering `enable` mode on the switch
    """
    if module.params['enable_mode']:
        passwd = module.params['enable_password']
        if passwd:
            return dict(cmd='enable', input=passwd)
        else:
            return 'enable'

def eapi_command(module, commands, encoding='json'):
    """Send an ordered list of commands to the device over eAPI
    """
    commands = to_list(commands)
    url = eapi_url(module)

    enable = eapi_enable_mode(module)
    if enable:
        commands.insert(0, enable)

    data = eapi_body(commands, encoding)
    data = module.jsonify(data)

    headers = {'Content-Type': 'application/json-rpc'}

    response, headers = fetch_url(module, url, data=data, headers=headers,
                                  method='POST')

    if headers['status'] != 200:
        module.fail_json(**headers)

    response = module.from_json(response.read())
    if 'error' in response:
        err = response['error']
        module.fail_json(msg='json-rpc error', **err)

    if enable:
        response['result'].pop(0)

    return response['result'], headers

def eapi_configure(module, commands):
    """Send configuration commands to the device over eAPI
    """
    commands.insert(0, 'configure')
    response, headers = eapi_command(module, commands)
    response.pop(0)
    return response, headers


