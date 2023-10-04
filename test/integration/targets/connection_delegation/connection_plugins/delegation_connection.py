from __future__ import annotations

DOCUMENTATION = """
author: Ansible Core Team
connection: delegation_connection
short_description: Test connection for delegated host check
description:
- Some further description that you don't care about.
options:
  remote_password:
    description: The remote password
    type: str
    vars:
    - name: ansible_password
    # Tests that an aliased key gets the -k option which hardcodes the value to password
    aliases:
    - password
"""

from ansible.plugins.connection import ConnectionBase


class Connection(ConnectionBase):

    transport = 'delegation_connection'
    has_pipelining = True

    def __init__(self, *args, **kwargs):
        super(Connection, self).__init__(*args, **kwargs)

    def _connect(self):
        super(Connection, self)._connect()

    def exec_command(self, cmd, in_data=None, sudoable=True):
        super(Connection, self).exec_command(cmd, in_data, sudoable)

    def put_file(self, in_path, out_path):
        super(Connection, self).put_file(in_path, out_path)

    def fetch_file(self, in_path, out_path):
        super(Connection, self).fetch_file(in_path, out_path)

    def close(self):
        super(Connection, self).close()
