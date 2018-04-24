# (c) 2018 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    author: Ansible Networking Team
    connection: httpapi
    short_description: Use httpapi to run command on Arista EOS devices using httpapi
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
            - name: ansible_httpapi_pass
      use_ssl:
        description:
            - Whether to connect using SSL (HTTPS) or not (HTTP)
        vars:
            - name: ansible_httpapi_use_ssl
      timeout:
        type: int
        description:
          - Connection timeout in seconds
        default: 120
"""

import os

from ansible import constants as C
from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_bytes
from ansible.module_utils.six import PY3
from ansible.module_utils.six.moves import cPickle
from ansible.module_utils.urls import open_url
from ansible.playbook.play_context import PlayContext
from ansible.plugins.loader import cliconf_loader, connection_loader, httpapi_loader
from ansible.plugins.connection import ConnectionBase
from ansible.utils.path import unfrackpath

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class Connection(ConnectionBase):
    '''Network API connection'''

    transport = 'httpapi'
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

        self._httpapi = httpapi_loader.get(network_os, self)
        if self._httpapi:
            display.vvvv('loaded API plugin for network_os %s' % network_os, host=self._play_context.remote_addr)
        else:
            raise AnsibleConnectionFailure('unable to load API plugin for network_os %s' % network_os)

        protocol = 'https' if getattr(play_context, 'use_ssl', True) else 'http'
        port = play_context.port or 443 if protocol == 'https' else 80
        self._url = '%s://%s:%s' % (protocol, play_context.remote_addr, port)
        self._auth = None

        # reconstruct the socket_path and set instance values accordingly
        self._update_connection_state()

    def __getattr__(self, name):
        try:
            return self.__dict__[name]
        except KeyError:
            if not name.startswith('_'):
                for plugin in (self._httpapi, self._cliconf):
                    method = getattr(plugin, name, None)
                    if method:
                        return method
            raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, name))

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

    def send(self, path, data, **kwargs):
        '''
        Sends the command to the device over api
        '''
        url_kwargs = dict(url_username=self._play_context.remote_user, url_password=self._play_context.password)
        url_kwargs.update(kwargs)
        response = open_url(self._url + path, data=data, **url_kwargs)
        self._auth = response.info().get('Set-Cookie')

        return response
