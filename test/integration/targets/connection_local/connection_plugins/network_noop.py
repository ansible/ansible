# (c) 2024 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = """
connection: network_noop
author: ansible-core
short_description: legacy-ish connection plugin with only minimal config
description:
  - A wrapper around NetworkConnectionBase to test that the default attributes don't cause internal errors in TE.
options:
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
extends_documentation_fragment:
  - connection_pipelining
"""

from ansible.plugins.connection import NetworkConnectionBase, ensure_connect
from ansible.utils.display import Display

display = Display()


class Connection(NetworkConnectionBase):
    transport = 'network_noop'
    has_pipelining = True

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

    @ensure_connect
    def exec_command(self, *args, **kwargs):
        return super(Connection, self).exec_command(*args, **kwargs)

    @ensure_connect
    def put_file(self, *args, **kwargs):
        return super(Connection, self).put_file(*args, **kwargs)

    @ensure_connect
    def fetch_file(self, *args, **kwargs):
        return super(Connection, self).fetch_file(*args, **kwargs)

    def _connect(self):
        if not self.connected:
            self._connected = True
            display.vvv("ESTABLISH NEW CONNECTION")

    def close(self):
        if self.connected:
            display.vvv("CLOSING CONNECTION")
        super(Connection, self).close()
