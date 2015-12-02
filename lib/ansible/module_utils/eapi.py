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

    * host (str) - The IPv4 address or FQDN of the network device
    * port (str) - Overrides the default port to use for the HTTP/S
        connection.  The default values are 80 for HTTP and
        443 for HTTPS
    * username (str) - The username to use to authenticate the HTTP/S
        connection.
    * password (str) - The password to use to authenticate the HTTP/S
        connection.
    * use_ssl (bool) - Specifies whether or not to use an encrypted (HTTPS)
        connection or not.  The default value is False.
    * enable_mode (bool) - Specifies whether or not to enter `enable` mode
        prior to executing the command list.  The default value is True
    * enable_password (str) - The password for entering `enable` mode
        on the switch if configured.
    * device (dict) - Used to send the entire set of connectin parameters
        as a dict object.  This argument is mutually exclusive with the
        host argument

In order to communicate with Arista EOS devices, the eAPI feature
must be enabled and configured on the device.

"""
EAPI_COMMON_ARGS = dict(
    host=dict(),
    port=dict(),
    username=dict(),
    password=dict(no_log=True),
    use_ssl=dict(default=True, type='bool'),
    enable_mode=dict(default=True, type='bool'),
    enable_password=dict(no_log=True),
    device=dict()
)

def eapi_module(**kwargs):
    """Append the common args to the argument_spec
    """
    spec = kwargs.get('argument_spec') or dict()

    argument_spec = url_argument_spec()
    argument_spec.update(EAPI_COMMON_ARGS)
    if kwargs.get('argument_spec'):
        argument_spec.update(kwargs['argument_spec'])
    kwargs['argument_spec'] = argument_spec

    module = AnsibleModule(**kwargs)

    device = module.params.get('device') or dict()
    for key, value in device.iteritems():
        if key in EAPI_COMMON_ARGS:
            module.params[key] = value

    params = json_dict_unicode_to_bytes(json.loads(MODULE_COMPLEX_ARGS))
    for key, value in params.iteritems():
        if key != 'device':
            module.params[key] = value

    return module

def eapi_url(params):
    """Construct a valid Arista eAPI URL
    """
    if params['use_ssl']:
        proto = 'https'
    else:
        proto = 'http'
    host = params['host']
    url = '{}://{}'.format(proto, host)
    if params['port']:
        url = '{}:{}'.format(url, params['port'])
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

def eapi_enable_mode(params):
    """Build commands for entering `enable` mode on the switch
    """
    if params['enable_mode']:
        passwd = params['enable_password']
        if passwd:
            return dict(cmd='enable', input=passwd)
        else:
            return 'enable'

def eapi_command(module, commands, encoding='json'):
    """Send an ordered list of commands to the device over eAPI
    """
    commands = to_list(commands)
    url = eapi_url(module.params)

    enable = eapi_enable_mode(module.params)
    if enable:
        commands.insert(0, enable)

    data = eapi_body(commands, encoding)
    data = module.jsonify(data)

    headers = {'Content-Type': 'application/json-rpc'}

    module.params['url_username'] = module.params['username']
    module.params['url_password'] = module.params['password']

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


