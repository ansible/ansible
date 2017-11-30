# (c) 2016 Red Hat Inc.
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = """
---
author: Ansible Networking Team
connection: netconf
short_description: Provides a persistent connection using the netconf protocol
description:
  - This plugin actually forces use of 'local' execution but uses paramiko to
    establish a remote ssh netconf session on the network device.  This connection
    plugin will load an additional plugin to manage the session.  It will
    load a netconf plugin to handle serializing requests to the remote device.
version_added: "2.3"
options:
  host:
    description:
      - Specifies the remote device FQDN or IP address to establish the SSH
        connection to.
    default: inventory_hostname
    vars:
      - name: ansible_host
      - name: ansible_ssh_host
  port:
    type: int
    description:
      - Specifies the port on the remote device to listening for connections
        when establishing the SSH connection.
    default: 830
    ini:
      - section: defaults
        key: remote_port
    env:
      - name: ANSIBLE_REMOTE_PORT
    vars:
      - name: ansible_port
      - name: ansible_ssh_port
  network_os:
    description:
      - Configures the device platform network operating system.  This value is
        used to load a device specific netconf plugin.  If this option is not
        configured, then the default netconf plugin will be used.
    default: null
    vars:
      - name: ansible_network_os
  remote_user:
    description:
      - The username used to authenticate to the remote device when the SSH
        connection is first established.  If the remote_user is not specified,
        the connection will use the username of the logged in user.
      - Can be configured form the CLI via the ``--user`` or ``-u`` options
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
        when first establishing the SSH connection.
    vars:
      - name: ansible_pass
  private_key_file:
    description:
      - The private SSH key or certificate file used to to authenticate to the
        remote device when first establishing the SSH connection.
    ini:
     section: defaults
     key: private_key_file
    env:
      - name: ANSIBLE_PRIVATE_KEY_FILE
    vars:
      - name: ansible_private_key_file
  timeout:
    type: int
    description:
      - Sets the connection time for the communicating with the remote device.
        This timeout is used as the default timeout value when awaiting a
        response after issuing a call to a RPC.  If the RPC does not return in
        timeout seconds, an error is generated.
        type: int
    default: 120
  connect_timeout:
    type: int
    description:
      - Configures the connect timeout for when the connection is initially
        established to the remote device.  The connect_timeout value should
        be specified in seconds.
    ini:
      section: persistent_connection
      key: connect_timeout
  host_key_auto_add:
    type: boolean
    description:
      - By default, Ansible will prompt the user before adding SSH keys to the
        known hosts file.  Since persistent connections such as network_cli run
        in background processes, the user will never be prompted.  By enabling
        this option, unknown host keys will automatically be added to the
        known hosts file.
      - Be sure to fully understand the security implications of enabling this
        option on production systems as it could create a security vulnerability.
    default: False
    ini:
      section: paramiko_connection
      key: host_key_auto_add
    env:
      - name: ANSIBLE_HOST_KEY_AUTO_ADD


# TODO:
# persistent_connection/connect_retry_timeout
# persistent_connection/command_timeout
"""

import os
import logging
import json

from ansible import constants as C
from ansible.errors import AnsibleConnectionFailure, AnsibleError
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.module_utils.parsing.convert_bool import BOOLEANS_TRUE
from ansible.plugins.loader import netconf_loader
from ansible.plugins.connection import ConnectionBase, ensure_connect
from ansible.plugins.connection.local import Connection as LocalConnection

try:
    from ncclient import manager
    from ncclient.operations import RPCError
    from ncclient.transport.errors import SSHUnknownHostError
    from ncclient.xml_ import to_ele, to_xml
except ImportError:
    raise AnsibleError("ncclient is not installed")

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

logging.getLogger('ncclient').setLevel(logging.INFO)


class Connection(ConnectionBase):
    """NetConf connections"""

    transport = 'netconf'
    has_pipelining = False
    force_persistence = True

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        self._network_os = self._play_context.network_os or 'default'
        display.display('network_os is set to %s' % self._network_os, log_only=True)

        self._netconf = None
        self._manager = None
        self._connected = False

        self._local = LocalConnection(play_context, new_stdin, *args, **kwargs)

    def __getattr__(self, name):
        try:
            return self.__dict__[name]
        except KeyError:
            if name.startswith('_'):
                raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, name))
            return getattr(self._netconf, name)

    def exec_command(self, request, in_data=None, sudoable=True):
        """Sends the request to the node and returns the reply
        The method accepts two forms of request.  The first form is as a byte
        string that represents xml string be send over netconf session.
        The second form is a json-rpc (2.0) byte string.
        """
        if self._manager:
            # to_ele operates on native strings
            request = to_ele(to_native(request, errors='surrogate_or_strict'))

            if request is None:
                return 'unable to parse request'

            try:
                reply = self._manager.rpc(request)
            except RPCError as exc:
                error = self.internal_error(data=to_text(to_xml(exc.xml), errors='surrogate_or_strict'))
                return json.dumps(error)

            return reply.data_xml
        else:
            return self._local.exec_command(request, in_data, sudoable)

    def put_file(self, in_path, out_path):
        """Transfer a file from local to remote"""
        return self._local.put_file(in_path, out_path)

    def fetch_file(self, in_path, out_path):
        """Fetch a file from remote to local"""
        return self._local.fetch_file(in_path, out_path)

    def _connect(self):
        super(Connection, self)._connect()

        display.display('ssh connection done, starting ncclient', log_only=True)

        allow_agent = True
        if self._play_context.password is not None:
            allow_agent = False
        setattr(self._play_context, 'allow_agent', allow_agent)

        key_filename = None
        if self._play_context.private_key_file:
            key_filename = os.path.expanduser(self._play_context.private_key_file)

        network_os = self._play_context.network_os

        if not network_os:
            for cls in netconf_loader.all(class_only=True):
                network_os = cls.guess_network_os(self)
                if network_os:
                    display.display('discovered network_os %s' % network_os, log_only=True)

        if not network_os:
            raise AnsibleConnectionFailure('Unable to automatically determine host network os. Please ansible_network_os value')

        ssh_config = os.getenv('ANSIBLE_NETCONF_SSH_CONFIG', False)
        if ssh_config in BOOLEANS_TRUE:
            ssh_config = True
        else:
            ssh_config = None

        try:
            self._manager = manager.connect(
                host=self._play_context.remote_addr,
                port=self._play_context.port or 830,
                username=self._play_context.remote_user,
                password=self._play_context.password,
                key_filename=str(key_filename),
                hostkey_verify=C.HOST_KEY_CHECKING,
                look_for_keys=C.PARAMIKO_LOOK_FOR_KEYS,
                allow_agent=self._play_context.allow_agent,
                timeout=self._play_context.timeout,
                device_params={'name': network_os},
                ssh_config=ssh_config
            )
        except SSHUnknownHostError as exc:
            raise AnsibleConnectionFailure(str(exc))
        except ImportError as exc:
            raise AnsibleError("connection=netconf is not supported on {0}".format(network_os))

        if not self._manager.connected:
            return 1, b'', b'not connected'

        display.display('ncclient manager object created successfully', log_only=True)

        self._connected = True

        self._netconf = netconf_loader.get(network_os, self)
        if self._netconf:
            display.display('loaded netconf plugin for network_os %s' % network_os, log_only=True)
        else:
            display.display('unable to load netconf for network_os %s' % network_os)

        return 0, to_bytes(self._manager.session_id, errors='surrogate_or_strict'), b''

    def reset(self):
        '''
        Reset the connection
        '''
        if self._socket_path:
            display.vvvv('resetting persistent connection for socket_path %s' % self._socket_path, host=self._play_context.remote_addr)
            self.close()
        display.vvvv('reset call on connection instance', host=self._play_context.remote_addr)

    def close(self):
        if self._manager:
            self._manager.close_session()
            self._connected = False
        super(Connection, self).close()
