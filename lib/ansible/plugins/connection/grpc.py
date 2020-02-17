# (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
---
author:
  - "Ansible Team"
  - "Hans Thienpondt (@HansThienpondt)"
  - "Sven Wisotzky (@wisotzky)"
connection: grpc
short_description: Provides a persistent connection using the gRPC protocol
description:
  - This connection plugin provides a persistent communication channel to
    remote devices using gRPC.
  - The plugin is responsible for the underlying transport (TLS) and
    the gRPC communication channel.
  - The plugin does not bind to any gRPC service. Sub-plugins must be
    registered using the `register_service()` method to bind to specific
    gRPC services required.
version_added: "2.10"
requirements:
  - grpcio
  - protobuf
options:
  host:
    description:
      - Target host FQDN or IP address to establish gRPC connection.
    default: inventory_hostname
    vars:
      - name: ansible_host
  port:
    type: int
    description:
      - Specifies the port on the remote device that listens for connections
        when establishing the gRPC connection. If None only the C(host) part
        will be used.
    ini:
      - section: defaults
        key: remote_port
    env:
      - name: ANSIBLE_REMOTE_PORT
    vars:
      - name: ansible_port
  remote_user:
    description:
      - The username used to authenticate to the remote device when the gRPC
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
        a default location chosen by gRPC at runtime.
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
        channel. If the value is None, no certificate chain is used.
    ini:
      - section: grpc_connection
        key: certificate_chain_file
    env:
      - name: ANSIBLE_CERTIFICATE_CHAIN_FILE
    vars:
      - name: ansible_certificate_chain_file
  grpc_channel_options:
    description:
      - Key/Value pairs (dict) to define gRPC channel options to be used
      - gRPC reference
        U(https://grpc.github.io/grpc/core/group__grpc__arg__keys.html)
      - Provide the I(ssl_target_name_override) option to override the TLS
        subject or subjectAltName (only in the case secure connections are
        used). The option must be provided in cases, when the FQDN or IPv4
        address that is used to connect to the device is different from the
        subject name that is provided in the host certificate. This is
        needed, because the TLS validates hostname or IP address to avoid
        man-in-the-middle attacks.
    vars:
      - name: ansible_grpc_channel_options
  grpc_environment:
    description:
      - Key/Value pairs (dict) to define environment settings specific to gRPC
      - The standard mechanism to provide/set the environment in Ansible
        cannot be used, because those environment settings are not passed to
        the client process that establishes the gRPC connection.
      - Set C(GRPC_VERBOSITY) and C(GRPC_TRACE) to setup gRPC logging. Need to
        add code for log forwarding of gRPC related log messages to the
        persistent messages log (see below).
      - Set C(HTTPS_PROXY) to specify your proxy settings (if needed).
      - Set C(GRPC_SSL_CIPHER_SUITES) in case the default TLS ciphers do not match
        what is offered by the gRPC server.
    vars:
      - name: ansible_grpc_environment
  persistent_connect_timeout:
    type: int
    description:
      - Configures, in seconds, the amount of time to wait when trying to
        initially establish a persistent connection. If this value expires
        before the connection to the remote device is completed, the connection
        will fail.
    default: 5
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
      - Configures the default timeout value (in seconds) when awaiting a
        response after issuing a call to a RPC. If the RPC does not return
        before the timeout exceed, an error is generated and the connection
        is closed.
    default: 300
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
      - This flag will enable logging the command executed and response received
        from target device in the ansible log file. For this option to work the
        'log_path' ansible configuration option is required to be set to a file
        path with write access.
      - Be sure to fully understand the security implications of enabling this
        option as it could create a security vulnerability by logging sensitive
        information in log file.
    default: False
    ini:
      - section: persistent_connection
        key: log_messages
    env:
      - name: ANSIBLE_PERSISTENT_LOG_MESSAGES
    vars:
      - name: ansible_persistent_log_messages
"""

import os
from ansible.errors import AnsibleConnectionFailure, AnsibleError
from ansible.plugins.loader import grpc_loader
from ansible.plugins.connection import NetworkConnectionBase

try:
    import grpc
    HAS_GRPC = True
except ImportError:
    HAS_GRPC = False

try:
    from google import protobuf
    HAS_PROTOBUF = True
except ImportError:
    HAS_PROTOBUF = False


class Connection(NetworkConnectionBase):
    """
    Connection plugin for gRPC

    To use gRPC connections in Ansible one (or more) sub-plugin(s) for the
    required gRPC service(s) must be loaded. To load gRPC sub-plugins use the
    method `register_service()` with the name of the sub-plugin to be
    registered.

    After loading the sub-plugin, Ansible modules can call methods provided by
    that sub-plugin. There is a wrapper available that consumes the attribute
    name {sub-plugin name}__{method name} to call a specific method of that
    sub-plugin.
    """

    transport = 'grpc'
    has_pipelining = False

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)
        self._connected = False
        self._grpc_services = {}

        if not HAS_PROTOBUF:
            raise AnsibleError(
                "protobuf is required to use gRPC connection type. " +
                "Please run 'pip install protobuf'"
            )
        if not HAS_GRPC:
            raise AnsibleError(
                "grpcio is required to use gRPC connection type. " +
                "Please run 'pip install grpcio'"
            )

    def register_service(self, grpcService):
        """
        Loads the gRPC sub-plugin with the name {grpcService}

        Example implementation to load 'gnmi' service:
        def get_connection(module):
            if not hasattr(module, '_grpc_connection'):
                module._grpc_connection = Connection(module._socket_path)
                module._grpc_connection.register_service('gnmi')
            return module._grpc_connection

        For collections full qualified names must be used:
            [...]
            module._grpc_connection.register_service('nokia.gnmi.gnmi')

        Parameters:
            grpcService (str): Name of the sub-plugin to be loaded

        Returns:
            None
        """
        registryName = grpcService.split('.')[-1]

        if registryName not in self._grpc_services:
            newService = grpc_loader.get(grpcService, self)
            if newService:
                self._grpc_services[registryName] = newService
                self.queue_message('v', 'loaded gRPC API plugin for %s service' % registryName)
            else:
                raise AnsibleConnectionFailure('unable to load gRPC API plugin for %s service' % registryName)

    def __getattr__(self, name):
        """
        Wrapper to call a sub-plugin method

        The wrapper will first try to resolve the attribute name as usual.
        If it can not be resolved, it will check if it follows the syntax
        {sub plugin}__{method} and tries to resolve it.

        Example implementation to call method Set() from 'gnmi' service:
        response = get_connection(module).gnmi__Set(*args, **kwargs)

        Parameters:
            name (str): Name of attribute or method

        Returns:
            (ANY): resolved attribute or method
        """
        try:
            return super(Connection, self).__getattr__(name)
        except AttributeError:
            if '__' in name:
                (grpcService, rpc) = name.split('__', 2)
                plugin = self._grpc_services[grpcService]
                if plugin:
                    method = getattr(plugin, rpc, None)
                    if method is not None:
                        return method
            raise

    def _connect(self):
        """
        Creates a gRPC connection to the target host

        Parameters:
            None

        Returns:
            None
        """
        host = self.get_option('host')
        port = self.get_option('port')

        if self.connected:
            self.queue_message('v', 'gRPC connection to host %s already exist' % host)
            return

        self._target = host if port is None else '%s:%d' % (host, port)
        self._timeout = self.get_option('persistent_command_timeout')
        self._login_credentials = [
            ('username', self.get_option('remote_user')),
            ('password', self.get_option('password'))
        ]

        grpcEnv = self.get_option('grpc_environment')
        for key in grpcEnv:
            if grpcEnv[key]:
                os.environ[key] = str(grpcEnv[key])
            else:
                try:
                    del os.environ[key]
                except KeyError:
                    # no such setting in current environment, but thats ok
                    pass

        certs = {}
        try:
            filename = self.get_option('root_certificates_file')
            if filename:
                with open(filename, 'rb') as f:
                    certs['root_certificates'] = f.read()

            filename = self.get_option('private_key_file')
            if filename:
                with open(filename, 'rb') as f:
                    certs['private_key'] = f.read()

            filename = self.get_option('certificate_chain_file')
            if filename:
                with open(filename, 'rb') as f:
                    certs['certificate_chain'] = f.read()

        except Exception as e:
            raise AnsibleConnectionFailure('Failed to read certificate keys: %s' % e)

        options = self.get_option('grpc_channel_options')
        options = options.items() if options else None

        if certs:
            creds = grpc.ssl_channel_credentials(**certs)
            channel = grpc.secure_channel(self._target, creds, options=options)
        else:
            channel = grpc.insecure_channel(self._target, options=options)

        self.queue_message('v', "ESTABLISH GRPC CONNECTION FOR USER: %s on PORT %s TO %s" %
                           (self.get_option('remote_user'), port, host))
        self._channel = channel
        self.queue_message('v', 'grpc connection has completed successfully')
        self._connected = True

    def close(self):
        """
        Closes the active gRPC connection to the target host

        Parameters:
            None

        Returns:
            None
        """

        if self._connected:
            self.queue_message('v', "closing gRPC connection to target host")
            self._channel.close()
        super(Connection, self).close()
