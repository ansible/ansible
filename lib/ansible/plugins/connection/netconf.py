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
  - This connection plugin provides a connection to remote devices over the
    SSH NETCONF subsystem.  This connection plugin is typically used by
    network devices for sending and receiving RPC calls over NETCONF.
  - Note this connection plugin requires ncclient to be installed on the
    local Ansible controller.
version_added: "2.3"
requirements:
  - ncclient
options:
  host:
    description:
      - Specifies the remote device FQDN or IP address to establish the SSH
        connection to.
    default: inventory_hostname
    vars:
      - name: ansible_host
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
  network_os:
    description:
      - Configures the device platform network operating system.  This value is
        used to load a device specific netconf plugin.  If this option is not
        configured, then the default netconf plugin will be used.
    vars:
      - name: ansible_network_os
  remote_user:
    description:
      - The username used to authenticate to the remote device when the SSH
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
      - Configures the user password used to authenticate to the remote device
        when first establishing the SSH connection.
    vars:
      - name: ansible_password
      - name: ansible_ssh_pass
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
    default: 120
  host_key_auto_add:
    type: bool
    description:
      - By default, Ansible will prompt the user before adding SSH keys to the
        known hosts file.  Enabling this option, unknown host keys will
        automatically be added to the known hosts file.
      - Be sure to fully understand the security implications of enabling this
        option on production systems as it could create a security vulnerability.
    default: 'no'
    ini:
      section: paramiko_connection
      key: host_key_auto_add
    env:
      - name: ANSIBLE_HOST_KEY_AUTO_ADD
  look_for_keys:
    default: True
    description: 'TODO: write it'
    env:
      - name: ANSIBLE_PARAMIKO_LOOK_FOR_KEYS
    ini:
      - section: paramiko_connection
        key: look_for_keys
    type: boolean
  host_key_checking:
    description: 'Set this to "False" if you want to avoid host key checking by the underlying tools Ansible uses to connect to the host'
    type: boolean
    default: True
    env:
      - name: ANSIBLE_HOST_KEY_CHECKING
      - name: ANSIBLE_SSH_HOST_KEY_CHECKING
      - name: ANSIBLE_NETCONF_HOST_KEY_CHECKING
    ini:
      - section: defaults
        key: host_key_checking
      - section: paramiko_connection
        key: host_key_checking
    vars:
      - name: ansible_host_key_checking
      - name: ansible_ssh_host_key_checking
      - name: ansible_netconf_host_key_checking
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
    vars:
      - name: ansible_command_timeout
  netconf_ssh_config:
    description:
      - This variable is used to enable bastion/jump host with netconf connection. If set to
        True the bastion/jump host ssh settings should be present in ~/.ssh/config file,
        alternatively it can be set to custom ssh configuration file path to read the
        bastion/jump host settings.
    ini:
      - section: netconf_connection
        key: ssh_config
        version_added: '2.7'
    env:
      - name: ANSIBLE_NETCONF_SSH_CONFIG
    vars:
      - name: ansible_netconf_ssh_config
        version_added: '2.7'
"""

import os
import logging
import json

from ansible.errors import AnsibleConnectionFailure, AnsibleError
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.module_utils.parsing.convert_bool import BOOLEANS_TRUE, BOOLEANS_FALSE
from ansible.plugins.loader import netconf_loader
from ansible.plugins.connection import NetworkConnectionBase

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

NETWORK_OS_DEVICE_PARAM_MAP = {
    "nxos": "nexus",
    "ios": "default",
    "sros": "alu",
    "ce": "huawei"
}


class Connection(NetworkConnectionBase):
    """NetConf connections"""

    transport = 'netconf'
    has_pipelining = False

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        self._network_os = self._network_os or 'default'
        display.display('network_os is set to %s' % self._network_os, log_only=True)

        self._manager = None

    def exec_command(self, cmd, in_data=None, sudoable=True):
        """Sends the request to the node and returns the reply
        The method accepts two forms of request.  The first form is as a byte
        string that represents xml string be send over netconf session.
        The second form is a json-rpc (2.0) byte string.
        """
        if self._manager:
            # to_ele operates on native strings
            request = to_ele(to_native(cmd, errors='surrogate_or_strict'))

            if request is None:
                return 'unable to parse request'

            try:
                reply = self._manager.rpc(request)
            except RPCError as exc:
                error = self.internal_error(data=to_text(to_xml(exc.xml), errors='surrogate_or_strict'))
                return json.dumps(error)

            return reply.data_xml
        else:
            return super(Connection, self).exec_command(cmd, in_data, sudoable)

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

        if self._network_os == 'default':
            for cls in netconf_loader.all(class_only=True):
                network_os = cls.guess_network_os(self)
                if network_os:
                    display.display('discovered network_os %s' % network_os, log_only=True)
                    self._network_os = network_os

        device_params = {'name': NETWORK_OS_DEVICE_PARAM_MAP.get(self._network_os) or self._network_os}

        ssh_config = self.get_option('netconf_ssh_config')
        if ssh_config in BOOLEANS_TRUE:
            ssh_config = True
        elif ssh_config in BOOLEANS_FALSE:
            ssh_config = None

        try:
            self._manager = manager.connect(
                host=self._play_context.remote_addr,
                port=self._play_context.port or 830,
                username=self._play_context.remote_user,
                password=self._play_context.password,
                key_filename=str(key_filename),
                hostkey_verify=self.get_option('host_key_checking'),
                look_for_keys=self.get_option('look_for_keys'),
                device_params=device_params,
                allow_agent=self._play_context.allow_agent,
                timeout=self._play_context.timeout,
                ssh_config=ssh_config
            )
        except SSHUnknownHostError as exc:
            raise AnsibleConnectionFailure(str(exc))
        except ImportError as exc:
            raise AnsibleError("connection=netconf is not supported on {0}".format(self._network_os))

        if not self._manager.connected:
            return 1, b'', b'not connected'

        display.display('ncclient manager object created successfully', log_only=True)

        self._connected = True

        netconf = netconf_loader.get(self._network_os, self)
        if netconf:
            display.display('loaded netconf plugin for network_os %s' % self._network_os, log_only=True)
        else:
            netconf = netconf_loader.get("default", self)
            display.display('unable to load netconf plugin for network_os %s, falling back to default plugin' % self._network_os)
        self._implementation_plugins.append(netconf)

        return 0, to_bytes(self._manager.session_id, errors='surrogate_or_strict'), b''

    def close(self):
        if self._manager:
            self._manager.close_session()
        super(Connection, self).close()
