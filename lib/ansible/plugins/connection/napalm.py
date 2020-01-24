# (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = """
---
author: Ansible Networking Team
connection: napalm
short_description: Provides persistent connection using NAPALM
description:
  - This connection plugin provides connectivity to network devices using
    the NAPALM network device abstraction library.  This library requires
    certain features to be enabled on network devices depending on the
    destination device operating system.  The connection plugin requires
    C(napalm) to be installed locally on the Ansible controller.
version_added: "2.8"
requirements:
  - napalm
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
      - Specifies the port on the remote device that listens for connections
        when establishing the SSH connection.
    default: 22
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
        used to load a napalm device abstraction.
    vars:
      - name: ansible_network_os
  remote_user:
    description:
      - The username used to authenticate to the remote device when the SSH
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
        when first establishing the SSH connection.
    vars:
      - name: ansible_password
      - name: ansible_ssh_pass
      - name: ansible_ssh_password
  private_key_file:
    description:
      - The private SSH key or certificate file used to authenticate to the
        remote device when first establishing the SSH connection.
    ini:
      - section: defaults
        key: private_key_file
    env:
      - name: ANSIBLE_PRIVATE_KEY_FILE
    vars:
      - name: ansible_private_key_file
  timeout:
    type: int
    description:
      - Sets the connection time, in seconds, for communicating with the
        remote device.  This timeout is used as the default timeout value for
        commands when issuing a command to the network CLI.  If the command
        does not return in timeout seconds, an error is generated.
    default: 120
  host_key_auto_add:
    type: boolean
    description:
      - By default, Ansible will prompt the user before adding SSH keys to the
        known hosts file. By enabling this option, unknown host keys will
        automatically be added to the known hosts file.
      - Be sure to fully understand the security implications of enabling this
        option on production systems as it could create a security vulnerability.
    default: False
    ini:
      - section: paramiko_connection
        key: host_key_auto_add
    env:
      - name: ANSIBLE_HOST_KEY_AUTO_ADD
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
"""

from ansible.errors import AnsibleConnectionFailure, AnsibleError
from ansible.plugins.connection import NetworkConnectionBase

try:
    from napalm import get_network_driver
    from napalm.base import ModuleImportError
    HAS_NAPALM = True
except ImportError:
    HAS_NAPALM = False


class Connection(NetworkConnectionBase):
    """Napalm connections"""

    transport = 'napalm'
    has_pipelining = False

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        self.napalm = None

    def _connect(self):
        if not HAS_NAPALM:
            raise AnsibleError('The "napalm" python library is required to use the napalm connection type.\n')

        super(Connection, self)._connect()

        if not self.connected:
            if not self._network_os:
                raise AnsibleConnectionFailure(
                    'Unable to automatically determine host network os. Please '
                    'manually configure ansible_network_os value for this host'
                )
            self.queue_message('log', 'network_os is set to %s' % self._network_os)

            try:
                driver = get_network_driver(self._network_os)
            except ModuleImportError:
                raise AnsibleConnectionFailure('Failed to import napalm driver for {0}'.format(self._network_os))

            host = self.get_option('host')
            self.napalm = driver(
                hostname=host,
                username=self.get_option('remote_user'),
                password=self.get_option('password'),
                timeout=self.get_option('persistent_command_timeout'),
            )

            self.napalm.open()

            self._sub_plugin = {'name': 'napalm', 'obj': self.napalm}
            self.queue_message('vvvv', 'created napalm device for network_os %s' % self._network_os)
            self._connected = True

    def close(self):
        if self.napalm:
            self.napalm.close()
            self.napalm = None

        super(Connection, self).close()
