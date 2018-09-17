# (c) 2018 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
---
author: Ansible Networking Team
connection: httpapi
short_description: Use httpapi to run command on network appliances
description:
  - This connection plugin provides a connection to remote devices over a
    HTTP(S)-based api.
version_added: "2.6"
options:
  host:
    description:
      - Specifies the remote device FQDN or IP address to establish the HTTP(S)
        connection to.
    default: inventory_hostname
    vars:
      - name: ansible_host
  port:
    type: int
    description:
      - Specifies the port on the remote device to listening for connections
        when establishing the HTTP(S) connection.
        When unspecified, will pick 80 or 443 based on the value of use_ssl
    ini:
      - section: defaults
        key: remote_port
    env:
      - name: ANSIBLE_REMOTE_PORT
    vars:
      - name: ansible_httpapi_port
  network_os:
    description:
      - Configures the device platform network operating system.  This value is
        used to load the correct httpapi and cliconf plugins to communicate
        with the remote device
    vars:
      - name: ansible_network_os
  remote_user:
    description:
      - The username used to authenticate to the remote device when the API
        connection is first established.  If the remote_user is not specified,
        the connection will use the username of the logged in user.
      - Can be configured form the CLI via the C(--user) or C(-u) options
    ini:
      - section: defaults
        key: remote_user
    env:
      - name: ANSIBLE_REMOTE_USER
    vars:
      - name: ansible_user
  password:
    description:
      - Secret used to authenticate
    vars:
      - name: ansible_password
      - name: ansible_httpapi_pass
  use_ssl:
    type: boolean
    description:
      - Whether to connect using SSL (HTTPS) or not (HTTP)
    default: False
    vars:
      - name: ansible_httpapi_use_ssl
  timeout:
    type: int
    description:
      - Sets the connection time, in seconds, for the communicating with the
        remote device.  This timeout is used as the default timeout value for
        commands when issuing a command to the network CLI.  If the command
        does not return in timeout seconds, the an error is generated.
    default: 120
  become:
    type: boolean
    description:
      - The become option will instruct the CLI session to attempt privilege
        escalation on platforms that support it.  Normally this means
        transitioning from user mode to C(enable) mode in the CLI session.
        If become is set to True and the remote device does not support
        privilege escalation or the privilege has already been elevated, then
        this option is silently ignored
      - Can be configured form the CLI via the C(--become) or C(-b) options
    default: False
    ini:
      section: privilege_escalation
      key: become
    env:
      - name: ANSIBLE_BECOME
    vars:
      - name: ansible_become
  become_method:
    description:
      - This option allows the become method to be specified in for handling
        privilege escalation.  Typically the become_method value is set to
        C(enable) but could be defined as other values.
    default: sudo
    ini:
      section: privilege_escalation
      key: become_method
    env:
      - name: ANSIBLE_BECOME_METHOD
    vars:
      - name: ansible_become_method
  persistent_connect_timeout:
    type: int
    description:
      - Configures, in seconds, the amount of time to wait when trying to
        initially establish a persistent connection.  If this value expires
        before the connection to the remote device is completed, the connection
        will fail
    default: 30
    ini:
      - section: persistent_connection
        key: connect_timeout
    env:
      - name: ANSIBLE_PERSISTENT_CONNECT_TIMEOUT
  persistent_command_timeout:
    type: int
    description:
      - Configures, in seconds, the amount of time to wait for a command to
        return from the remote device.  If this timer is exceeded before the
        command returns, the connection plugin will raise an exception and
        close
    default: 10
    ini:
      - section: persistent_connection
        key: command_timeout
    env:
      - name: ANSIBLE_PERSISTENT_COMMAND_TIMEOUT
"""

import os

from ansible import constants as C
from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_bytes
from ansible.module_utils.six import PY3
from ansible.module_utils.six.moves import cPickle
from ansible.module_utils.six.moves.urllib.error import URLError
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
    # Do not use _remote_is_local in other connections
    _remote_is_local = True

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
            if hasattr(self._httpapi, 'set_become'):
                self._httpapi.set_become(play_context)
            display.vvvv('loaded API plugin for network_os %s' % network_os, host=self._play_context.remote_addr)
        else:
            raise AnsibleConnectionFailure('unable to load API plugin for network_os %s' % network_os)

        self._url = None
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
        if self._play_context.become ^ play_context.become:
            self._httpapi.set_become(play_context)

        self._play_context = play_context
        return messages

    def _connect(self):
        if self.connected:
            return
        network_os = self._play_context.network_os

        protocol = 'https' if self.get_option('use_ssl') else 'http'
        host = self.get_option('host')
        port = self.get_option('port') or (443 if protocol == 'https' else 80)
        self._url = '%s://%s:%s' % (protocol, host, port)

        self._cliconf = cliconf_loader.get(network_os, self)
        if self._cliconf:
            display.vvvv('loaded cliconf plugin for network_os %s' % network_os, host=host)
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
        url_kwargs = dict(
            url_username=self.get_option('remote_user'), url_password=self.get_option('password'),
            timeout=self.get_option('timeout'),
        )
        url_kwargs.update(kwargs)

        try:
            response = open_url(self._url + path, data=data, **url_kwargs)
        except URLError as exc:
            raise AnsibleConnectionFailure('Could not connect to {0}: {1}'.format(self._url, exc.reason))

        self._auth = response.info().get('Set-Cookie')

        return response
