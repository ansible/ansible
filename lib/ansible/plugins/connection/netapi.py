# (c) 2018 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    author: Ansible Networking Team
    connection: netapi
    short_description: Use netapi to run command on Arista EOS devices using netapi
    description:
        - This plugin actually forces use of 'local' execution but using paramiko to establish a remote ssh shell on the appliance.
        - Also this plugin ignores the become_method but still uses the becoe_user and become_pass to
          do privilege escalation.
    version_added: "2.5"
    options:
      password:
        description:
            - Secret used to authenticate
        vars:
            - name: ansible_password
            - name: ansible_netapi_pass
      protocol:
        description:
            - Protocol to connect to netapit with (eg, 'http' or 'https')
        vars:
            - name: ansible_netapi_protocol
      timeout:
        type: int
        description:
          - Connection timeout in seconds
        default: 120
"""

import json
import os

from ansible import constants as C
from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_bytes, to_text
from ansible.module_utils.six import PY3
from ansible.module_utils.six.moves import cPickle
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.urls import open_url
from ansible.playbook.play_context import PlayContext
from ansible.plugins.loader import cliconf_loader, connection_loader
from ansible.plugins.connection import ConnectionBase
from ansible.utils.path import unfrackpath

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class Connection(ConnectionBase):
    '''Network API connection'''

    transport = 'netapi'
    has_pipelining = True
    force_persistence = True

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        self._matched_prompt = None
        self._matched_pattern = None
        self._last_response = None
        self._history = list()

        self._local = connection_loader.get('local', play_context, '/dev/null')
        self._local.set_options()

        self._cliconf = None

        self._ansible_playbook_pid = kwargs.get('ansible_playbook_pid')

        network_os = self._play_context.network_os
        if not network_os:
            raise AnsibleConnectionFailure(
                'Unable to automatically determine host network os. Please '
                'manually configure ansible_network_os value for this host'
            )

        self._request_builder = getattr(self, '_request_builder_%s' % network_os)
        self._handle_response = getattr(self, '_handle_response_%s' % network_os)
        protocol = getattr(play_context, 'protocol', 'http')
        if network_os == 'eos':
            self._url = '%s://%s:%s/command-api' % (protocol, play_context.remote_addr, play_context.port or 80)
        elif network_os == 'nxos':
            self._url = '%s://%s:%s/ins' % (protocol, play_context.remote_addr, play_context.port or 80)

        # reconstruct the socket_path and set instance values accordingly
        self._update_connection_state()

    def __getattr__(self, name):
        try:
            return self.__dict__[name]
        except KeyError:
            if name.startswith('_'):
                raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, name))
            return getattr(self._cliconf, name)

    def _request_builder_eos(self, commands, output, reqid=None):
        params = dict(version=1, cmds=commands, format=output)
        headers = {'Content-Type': 'application/json-rpc'}

        return dict(jsonrpc='2.0', id=reqid, method='runCmds', params=params), headers

    def _request_builder_nxos(self, commands, output, version='1.0', chunk='0', sid=None):
        """Encodes a NXAPI JSON request message
        """
        output_to_command_type = {
            'text': 'cli_show_ascii',
            'json': 'cli_show',
            'bash': 'bash',
            'config': 'cli_conf'
        }

        maybe_output = commands[0].split('|')[-1].strip()
        if maybe_output in output_to_command_type:
            command_type = output_to_command_type[maybe_output]
            commands = [command.split('|')[0].strip() for command in commands]
        else:
            try:
                command_type = output_to_command_type[output]
            except KeyError:
                msg = 'invalid format, received %s, expected one of %s' % \
                    (output, ','.join(output_to_command_type.keys()))
                self._error(msg=msg)

        if isinstance(commands, (list, set, tuple)):
            commands = ' ;'.join(commands)

        msg = {
            'version': version,
            'type': command_type,
            'chunk': chunk,
            'sid': sid,
            'input': commands,
            'output_format': 'json'
        }
        headers = {'Content-Type': 'application/json'}

        return dict(ins_api=msg), headers

    def _handle_response_eos(self, response):
        if 'error' in response:
            raise AnsibleConnectionFailure(response['error'])

        result = response['result'][0]
        if 'messages' in result:
            result = result['messages'][0]
        else:
            result = json.dumps(result)
        return result.strip()

    def _handle_response_nxos(self, response):
        if response['ins_api'].get('outputs'):
            output = response['ins_api']['outputs']['output']
            if output['code'] != '200':
                raise AnsibleConnectionFailure('%s: %s' % (output['input'], output['msg']))
            elif 'body' in output:
                return json.dumps(output['body']).strip()


    def exec_command(self, cmd, in_data=None, sudoable=True):
        return self._local.exec_command(cmd, in_data, sudoable)

    def put_file(self, in_path, out_path):
        return self._local.put_file(in_path, out_path)

    def fetch_file(self, in_path, out_path):
        return self._local.fetch_file(in_path, out_path)

    def update_play_context(self, pc_data):
        """Updates the play context information for the connection"""
        pc_data = to_bytes(pc_data)
        if PY3:
            pc_data = cPickle.loads(pc_data, encoding='bytes')
        else:
            pc_data = cPickle.loads(pc_data)
        play_context = PlayContext()
        play_context.deserialize(pc_data)

        messages = ['updating play_context for connection']
        if self._play_context.become is False and play_context.become is True:
            self._enable = True
            messages.append('authorizing connection')

        elif self._play_context.become is True and not play_context.become:
            self._enable = False
            messages.append('deauthorizing connection')

        self._play_context = play_context
        return messages

    def _connect(self):
        if self.connected:
            return
        network_os = self._play_context.network_os

        self._cliconf = cliconf_loader.get(network_os, self)
        if self._cliconf:
            display.vvvv('loaded cliconf plugin for network_os %s' % network_os, host=self._play_context.remote_addr)
        else:
            display.vvvv('unable to load cliconf for network_os %s' % network_os)

        self._connected = True

        return self

    def _update_connection_state(self):
        '''
        Reconstruct the connection socket_path and check if it exists

        If the socket path exists then the connection is active and set
        both the _socket_path value to the path and the _connected value
        to True.  If the socket path doesn't exist, leave the socket path
        value to None and the _connected value to False
        '''
        ssh = connection_loader.get('ssh', class_only=True)
        cp = ssh._create_control_path(
            self._play_context.remote_addr, self._play_context.port,
            self._play_context.remote_user, self._play_context.connection,
            self._ansible_playbook_pid
        )

        tmp_path = unfrackpath(C.PERSISTENT_CONTROL_PATH_DIR)
        socket_path = unfrackpath(cp % dict(directory=tmp_path))

        if os.path.exists(socket_path):
            self._connected = True
            self._socket_path = socket_path

    def reset(self):
        '''
        Reset the connection
        '''
        if self._socket_path:
            display.vvvv('resetting persistent connection for socket_path %s' % self._socket_path, host=self._play_context.remote_addr)
            self.close()
        display.vvvv('reset call on connection instance', host=self._play_context.remote_addr)

    def close(self):
        if self._connected:
            self._connected = False

    def send(self, command, **kwargs):
        '''
        Sends the command to the device over api
        '''
        if self._play_context.become and self._play_context.become_method == 'enable':
            display.vvvv('firing event: on_become', host=self._play_context.remote_addr)
            auth_pass = self._play_context.become_pass
            #TODO ??? self._terminal.on_become(passwd=auth_pass)

        command = to_text(command)
        try:
            command = json.loads(command)
            output = cmd['output']
        except ValueError:
            output = 'json'
        request, headers = self._request_builder(to_list(command), output)
        data = json.dumps(request)

        response = open_url(
            self._url, data=data, headers=headers, method='POST',
            url_username=self._play_context.remote_user, url_password=self._play_context.password
        )
        self._auth = response.info().get('Set-Cookie')

        try:
            data = to_text(response.read())
            response = json.loads(data)
        except ValueError:
            raise

        return self._handle_response(response)
