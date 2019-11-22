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
      - Specifies the port on the remote device that listens for connections
        when establishing the HTTP(S) connection.
      - When unspecified, will pick 80 or 443 based on the value of use_ssl.
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
        used to load the correct httpapi plugin to communicate with the remote
        device
    vars:
      - name: ansible_network_os
  remote_user:
    description:
      - The username used to authenticate to the remote device when the API
        connection is first established.  If the remote_user is not specified,
        the connection will use the username of the logged in user.
      - Can be configured from the CLI via the C(--user) or C(-u) options.
    ini:
      - section: defaults
        key: remote_user
    env:
      - name: ANSIBLE_REMOTE_USER
    vars:
      - name: ansible_user
  password:
    description:
      - Configures the user password used to authenticate to the remote device
        when needed for the device API.
    vars:
      - name: ansible_password
      - name: ansible_httpapi_pass
      - name: ansible_httpapi_password
  use_ssl:
    type: boolean
    description:
      - Whether to connect using SSL (HTTPS) or not (HTTP).
    default: False
    vars:
      - name: ansible_httpapi_use_ssl
  validate_certs:
    type: boolean
    version_added: '2.7'
    description:
      - Whether to validate SSL certificates
    default: True
    vars:
      - name: ansible_httpapi_validate_certs
  use_proxy:
    type: boolean
    version_added: "2.9"
    description:
      - Whether to use https_proxy for requests.
    default: True
    vars:
      - name: ansible_httpapi_use_proxy
  timeout:
    type: int
    description:
      - Sets the connection time, in seconds, for communicating with the
        remote device.  This timeout is used as the default timeout value for
        commands when issuing a command to the network CLI.  If the command
        does not return in timeout seconds, an error is generated.
    default: 120
  become:
    type: boolean
    description:
      - The become option will instruct the CLI session to attempt privilege
        escalation on platforms that support it.  Normally this means
        transitioning from user mode to C(enable) mode in the CLI session.
        If become is set to True and the remote device does not support
        privilege escalation or the privilege has already been elevated, then
        this option is silently ignored.
      - Can be configured from the CLI via the C(--become) or C(-b) options.
    default: False
    ini:
      - section: privilege_escalation
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
      - section: privilege_escalation
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
        will fail.
    default: 30
    ini:
      - section: persistent_connection
        key: connect_timeout
    env:
      - name: ANSIBLE_PERSISTENT_CONNECT_TIMEOUT
    vars:
      - name: ansible_connect_timeout
  persistent_command_timeout:
    type: int
    description:
      - Configures, in seconds, the amount of time to wait for a command to
        return from the remote device.  If this timer is exceeded before the
        command returns, the connection plugin will raise an exception and
        close.
    default: 30
    ini:
      - section: persistent_connection
        key: command_timeout
    env:
      - name: ANSIBLE_PERSISTENT_COMMAND_TIMEOUT
    vars:
      - name: ansible_command_timeout
  persistent_log_messages:
    type: boolean
    description:
      - This flag will enable logging the command executed and response received from
        target device in the ansible log file. For this option to work 'log_path' ansible
        configuration option is required to be set to a file path with write access.
      - Be sure to fully understand the security implications of enabling this
        option as it could create a security vulnerability by logging sensitive information in log file.
    default: False
    ini:
      - section: persistent_connection
        key: log_messages
    env:
      - name: ANSIBLE_PERSISTENT_LOG_MESSAGES
    vars:
      - name: ansible_persistent_log_messages
"""

from io import BytesIO

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_bytes
from ansible.module_utils.six import PY3
from ansible.module_utils.six.moves import cPickle
from ansible.module_utils.six.moves.urllib.error import HTTPError, URLError
from ansible.module_utils.urls import open_url
from ansible.playbook.play_context import PlayContext
from ansible.plugins.loader import httpapi_loader
from ansible.plugins.connection import NetworkConnectionBase, ensure_connect


class Connection(NetworkConnectionBase):
    '''Network API connection'''

    transport = 'httpapi'
    has_pipelining = True

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        self._url = None
        self._auth = None

        if self._network_os:

            self.httpapi = httpapi_loader.get(self._network_os, self)
            if self.httpapi:
                self._sub_plugin = {'type': 'httpapi', 'name': self.httpapi._load_name, 'obj': self.httpapi}
                self.queue_message('vvvv', 'loaded API plugin %s from path %s for network_os %s' %
                                   (self.httpapi._load_name, self.httpapi._original_path, self._network_os))
            else:
                raise AnsibleConnectionFailure('unable to load API plugin for network_os %s' % self._network_os)

        else:
            raise AnsibleConnectionFailure(
                'Unable to automatically determine host network os. Please '
                'manually configure ansible_network_os value for this host'
            )
        self.queue_message('log', 'network_os is set to %s' % self._network_os)

    def update_play_context(self, pc_data):
        """Updates the play context information for the connection"""
        pc_data = to_bytes(pc_data)
        if PY3:
            pc_data = cPickle.loads(pc_data, encoding='bytes')
        else:
            pc_data = cPickle.loads(pc_data)
        play_context = PlayContext()
        play_context.deserialize(pc_data)

        self.queue_message('vvvv', 'updating play_context for connection')
        if self._play_context.become ^ play_context.become:
            self.set_become(play_context)
            if play_context.become is True:
                self.queue_message('vvvv', 'authorizing connection')
            else:
                self.queue_message('vvvv', 'deauthorizing connection')

        self._play_context = play_context

    def _connect(self):
        if not self.connected:
            protocol = 'https' if self.get_option('use_ssl') else 'http'
            host = self.get_option('host')
            port = self.get_option('port') or (443 if protocol == 'https' else 80)
            self._url = '%s://%s:%s' % (protocol, host, port)

            self.queue_message('vvv', "ESTABLISH HTTP(S) CONNECTFOR USER: %s TO %s" %
                               (self._play_context.remote_user, self._url))
            self.httpapi.set_become(self._play_context)
            self._connected = True

            self.httpapi.login(self.get_option('remote_user'), self.get_option('password'))

    def close(self):
        '''
        Close the active session to the device
        '''
        # only close the connection if its connected.
        if self._connected:
            self.queue_message('vvvv', "closing http(s) connection to device")
            self.logout()

        super(Connection, self).close()

    @ensure_connect
    def send(self, path, data, **kwargs):
        '''
        Sends the command to the device over api
        '''
        url_kwargs = dict(
            timeout=self.get_option('timeout'), validate_certs=self.get_option('validate_certs'),
            use_proxy=self.get_option("use_proxy"),
            headers={},
        )
        url_kwargs.update(kwargs)
        if self._auth:
            # Avoid modifying passed-in headers
            headers = dict(kwargs.get('headers', {}))
            headers.update(self._auth)
            url_kwargs['headers'] = headers
        else:
            url_kwargs['force_basic_auth'] = True
            url_kwargs['url_username'] = self.get_option('remote_user')
            url_kwargs['url_password'] = self.get_option('password')

        try:
            url = self._url + path
            self._log_messages("send url '%s' with data '%s' and kwargs '%s'" % (url, data, url_kwargs))
            response = open_url(url, data=data, **url_kwargs)
        except HTTPError as exc:
            is_handled = self.handle_httperror(exc)
            if is_handled is True:
                return self.send(path, data, **kwargs)
            elif is_handled is False:
                raise
            else:
                response = is_handled
        except URLError as exc:
            raise AnsibleConnectionFailure('Could not connect to {0}: {1}'.format(self._url + path, exc.reason))

        response_buffer = BytesIO()
        resp_data = response.read()
        self._log_messages("received response: '%s'" % resp_data)
        response_buffer.write(resp_data)

        # Try to assign a new auth token if one is given
        self._auth = self.update_auth(response, response_buffer) or self._auth

        response_buffer.seek(0)

        return response, response_buffer
