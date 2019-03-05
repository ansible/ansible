# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
---
author: Ansible Team
connection: grpc
short_description: Provides a persistent connection using the gRPC protocol
description:
  - This connection plugin provides a connection to remote devices over gRPC and
    is typically used with devices for sending and receiving RPC calls
    over gRPC framework.
  - Note this connection plugin requires the grpcio python library to be installed on the
    local Ansible controller.
version_added: "2.8"
requirements:
  - grpcio
  - protobuf
options:
  host:
    description:
      - Specifies the remote device FQDN or IP address to establish the gRPC
        connection to.
    default: inventory_hostname
    vars:
      - name: ansible_host
  port:
    type: int
    description:
      - Specifies the port on the remote device that listens for connections
        when establishing the GRPC connection. If None only the C(host) part will
        be used
    ini:
      - section: defaults
        key: remote_port
    env:
      - name: ANSIBLE_REMOTE_PORT
    vars:
      - name: ansible_port
  network_os:
    description:
      - Configures the device platform network operating system. This value is
        used to load a device specific grpc plugin to communicate with the remote
        device.
    vars:
      - name: ansible_network_os
  remote_user:
    description:
      - The username used to authenticate to the remote device when the grpc
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
        when first establishing the gRPC connection.
    vars:
      - name: ansible_password
      - name: ansible_ssh_pass
  private_key_file:
    description:
      - The PEM encoded private key file used to authenticate to the
        remote device when first establishing the grpc connection.
    ini:
      - section: grpc_connection
        key: private_key_file
    env:
      - name: ANSIBLE_PRIVATE_KEY_FILE
    vars:
      - name: ansible_private_key_file
  root_certificates_file:
    description:
      - The PEM encoded root certificate file used to create a SSL-enabled
        channel, if the value is None it reads the root certificates from
        a default location chosen by gRPC runtime.
    ini:
      - section: grpc_connection
        key: root_certificates_file
    env:
      - name: ANSIBLE_ROOT_CERTIFICATES_FILE
    vars:
      - name: ansible_root_certificates_file
  certificate_chain_file:
    description:
      - The PEM encoded certificate chain file used to create a SSL-enabled
        channel, if the value is None in that case no certificate chain is used.
    ini:
      - section: grpc_connection
        key: certificate_chain_file
    env:
      - name: ANSIBLE_CERTIFICATE_CHAIN_FILE
    vars:
      - name: ansible_certificate_chain_file
  ssl_target_name_override:
    description:
      - The option overrides SSL target name used for SSL host name checking.
        The name used for SSL host name checking will be the target parameter
        (assuming that the secure channel is an SSL channel). If this parameter is
        specified and the underlying secure channel is not an SSL channel, it will just be ignored.
    ini:
      - section: grpc_connection
        key: ssl_target_name_override
    env:
      - name: ANSIBLE_GPRC_SSL_TARGET_NAME_OVERRIDE
    vars:
      - name: ansible_grpc_ssl_target_name_override
  persistent_connect_timeout:
    type: int
    description:
      - Configures, in seconds, the amount of time to wait when trying to
        initially establish a persistent connection. If this value expires
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
      - Configures, in seconds,  the default timeout
        value when awaiting a response after issuing a call to a RPC. If the RPC
        does not return in timeout seconds, an error is generated and the connection is
        closed.
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
        target device in the ansible log file. For this option to work the 'log_path' ansible
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

from ansible.errors import AnsibleConnectionFailure, AnsibleError
from ansible.plugins.loader import grpc_loader
from ansible.plugins.connection import NetworkConnectionBase

try:
    from grpc import ssl_channel_credentials, secure_channel, insecure_channel
    from grpc.beta import implementations
    HAS_GRPC = True
except ImportError:
    HAS_GRPC = False

try:
    from google import protobuf
    HAS_PROTOBUF = True
except ImportError:
    HAS_PROTOBUF = False


class Connection(NetworkConnectionBase):
    """GRPC connections"""

    transport = 'grpc'
    has_pipelining = False

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        # TODO: Need to add support to make grpc connection work with non-network target host.
        # Currently this works only with network target host.
        if self._network_os:
            if not HAS_PROTOBUF:
                raise AnsibleError(
                    "protobuf is required to use the grpc connection type. Please run 'pip install protobuf'"
                )

            grpc = grpc_loader.get(self._network_os, self)
            if grpc:
                self._sub_plugin = {'type': 'grpc', 'name': self._network_os, 'obj': grpc}
                self.queue_message('log', 'loaded gRPC plugin for network_os %s' % self._network_os)
                self.queue_message('log', 'network_os is set to %s' % self._network_os)
            else:
                raise AnsibleConnectionFailure('unable to load API plugin for network_os %s' % self._network_os)
        else:
            self._sub_plugin['type'] = 'external'
            self.queue_message('warning', 'Unable to automatically determine gRPC implementation type.'
                                          ' Please manually configure ansible_network_os value for this host')

    def _connect(self):
        """
        Create GRPC connection to target host
        :return: None
        """
        if not HAS_GRPC:
            raise AnsibleError(
                "grpcio is required to use the gRPC connection type. Please run 'pip install grpcio'"
            )

        host = self.get_option('host')
        if self.connected:
            self.queue_message('log', 'gRPC connection to host %s already exist' % host)
            return

        port = self.get_option('port')
        self._target = host if port is None else '%s:%d' % (host, port)
        self._timeout = self.get_option('persistent_command_timeout')
        self._login_credentials = [('username', self.get_option('remote_user')), ('password', self.get_option('password'))]
        ssl_target_name_override = self.get_option('ssl_target_name_override')
        if ssl_target_name_override:
            self._channel_options = [('grpc.ssl_target_name_override', ssl_target_name_override), ]
        else:
            self._channel_options = None

        certs = {}
        private_key_file = self.get_option('private_key_file')
        root_certificates_file = self.get_option('root_certificates_file')
        certificate_chain_file = self.get_option('certificate_chain_file')

        try:
            if root_certificates_file:
                with open(root_certificates_file, 'rb') as f:
                    certs['root_certificates'] = f.read()
            if private_key_file:
                with open(private_key_file, 'rb') as f:
                    certs['private_key'] = f.read()
            if certificate_chain_file:
                with open(certificate_chain_file, 'rb') as f:
                    certs['certificate_chain'] = f.read()
        except Exception as e:
            raise AnsibleConnectionFailure('Failed to read certificate keys: %s' % e)

        if certs:
            creds = ssl_channel_credentials(**certs)
            channel = secure_channel(self._target, creds, options=self._channel_options)
        else:
            channel = insecure_channel(self._target, options=self._channel_options)
        self.queue_message('vvv', "ESTABLISH GRPC CONNECTION FOR USER: %s on PORT %s TO %s" %
                                 (self.get_option('remote_user'), port, host))
        self._channel = implementations.Channel(channel)
        self.queue_message('vvvv', 'grpc connection has completed successfully')
        self._connected = True

    def close(self):
        """
        Close the active session to the device
        :return: None
        """
        if self._connected:
            self.queue_message('vvvv', "closing gRPC connection to target host")
            self._channel.close()
        super(Connection, self).close()
