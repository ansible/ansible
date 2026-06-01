from __future__ import annotations

DOCUMENTATION = """
    name: unreachable
    short_description: Simulates an unreachable host
    description:
      - This connection plugin fails immediately to simulate an unreachable host.
      - Useful for testing error handling and host failure scenarios.
    author: Ansible Core
  """

from ansible.errors import AnsibleConnectionFailure
from ansible.plugins.connection import ConnectionBase


class Connection(ConnectionBase):
    """Unreachable connection that always fails"""

    transport = 'unreachable'
    has_pipelining = False

    def __init__(self, *args, **kwargs):
        super(Connection, self).__init__(*args, **kwargs)

    def _connect(self):
        """Fail immediately when trying to connect"""
        raise AnsibleConnectionFailure("Host is unreachable")

    def exec_command(self, cmd, in_data=None, sudoable=True):
        """Never executes - connection fails first"""
        raise AnsibleConnectionFailure("Host is unreachable")

    def put_file(self, in_path, out_path):
        """Never executes - connection fails first"""
        raise AnsibleConnectionFailure("Host is unreachable")

    def fetch_file(self, in_path, out_path):
        """Never executes - connection fails first"""
        raise AnsibleConnectionFailure("Host is unreachable")

    def close(self):
        """Nothing to close"""
        self._connected = False
