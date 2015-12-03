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
Adds shared module support for connecting to and configuring Cisco
IOS devices.  This shared module builds on module_utils/ssh.py and
implements the Shell object.

** Note: The order of the import statements does matter. **

from ansible.module_utils.basic import *
from ansible.module_utils.ssh import *
from ansible.module_utils.ios import *

This module provides the following common argument spec for creating
ios connections:

    * enable_mode (bool) - Forces the shell connection into IOS enable mode

    * enable_password (str) - Configures the IOS enable mode password to be
        send to the device to authorize the session

    * device (dict) - Accepts the set of configuration parameters as a
        dict object

Note: These shared arguments are in addition to the arguments provided by
the module_utils/ssh.py shared module

"""
import socket

IOS_PROMPTS_RE = [
    re.compile(r'[\r\n]?[a-zA-Z]{1}[a-zA-Z0-9-]*[>|#](?:\s*)$'),
    re.compile(r'[\r\n]?[a-zA-Z]{1}[a-zA-Z0-9-]*\(.+\)#$'),
    re.compile(r'\x1b.*$')
]

IOS_ERRORS_RE = [
    re.compile(r"% ?Error"),
    re.compile(r"^% \w+", re.M),
    re.compile(r"% ?Bad secret"),
    re.compile(r"invalid input", re.I),
    re.compile(r"(?:incomplete|ambiguous) command", re.I),
    re.compile(r"connection timed out", re.I),
    re.compile(r"[^\r\n]+ not found", re.I),
    re.compile(r"'[^']' +returned error code: ?\d+"),
]

IOS_PASSWD_RE = re.compile(r"[\r\n]?password: $", re.I)

IOS_COMMON_ARGS = dict(
    host=dict(),
    port=dict(type='int', default=22),
    username=dict(),
    password=dict(),
    enable_mode=dict(default=False, type='bool'),
    enable_password=dict(),
    connect_timeout=dict(type='int', default=10),
    device=dict()
)


def ios_module(**kwargs):
    """Append the common args to the argument_spec
    """
    spec = kwargs.get('argument_spec') or dict()

    argument_spec = shell_argument_spec()
    argument_spec.update(IOS_COMMON_ARGS)
    if kwargs.get('argument_spec'):
        argument_spec.update(kwargs['argument_spec'])
    kwargs['argument_spec'] = argument_spec

    module = AnsibleModule(**kwargs)

    device = module.params.get('device') or dict()
    for key, value in device.iteritems():
        if key in IOS_COMMON_ARGS:
            module.params[key] = value

    params = json_dict_unicode_to_bytes(json.loads(MODULE_COMPLEX_ARGS))
    for key, value in params.iteritems():
        if key != 'device':
            module.params[key] = value

    return module

def to_list(arg):
    """Try to force the arg to a list object
    """
    if isinstance(arg, (list, tuple)):
        return list(arg)
    elif arg is not None:
        return [arg]
    else:
        return []

class IosShell(object):

    def __init__(self):
        self.connection = None

    def connect(self, host, username, password, **kwargs):
        port = kwargs.get('port') or 22
        timeout = kwargs.get('timeout') or 10

        self.connection = Shell()

        self.connection.prompts.extend(IOS_PROMPTS_RE)
        self.connection.errors.extend(IOS_ERRORS_RE)

        self.connection.open(host, port=port, username=username,
                             password=password, timeout=timeout)

    def authorize(self, passwd=None):
        command = Command('enable', prompt=IOS_PASSWD_RE, response=passwd)
        self.send(command)

    def configure(self, commands):
        commands = to_list(commands)

        commands.insert(0, 'configure terminal')
        commands.append('end')

        resp = self.send(commands)
        resp.pop(0)
        resp.pop()

        return resp

    def send(self, commands):
        responses = list()
        for cmd in to_list(commands):
            response = self.connection.send(cmd)
            responses.append(response)
        return responses

def ios_connection(module):
    """Creates a connection to an IOS device based on the module arguments
    """
    host = module.params['host']
    port = module.params['port']

    username = module.params['username']
    password = module.params['password']

    timeout = module.params['connect_timeout']

    try:
        shell = IosShell()
        shell.connect(host, port=port, username=username, password=password,
                    timeout=timeout)
        shell.send('terminal length 0')
    except paramiko.ssh_exception.AuthenticationException, exc:
        module.fail_json(msg=exc.message)
    except socket.error, exc:
        module.fail_json(msg=exc.strerror, errno=exc.errno)

    if module.params['enable_mode']:
        shell.authorize(module.params['enable_password'])

    return shell



