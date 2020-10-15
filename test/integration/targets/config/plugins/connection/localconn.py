# (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils._text import to_native
from ansible.plugins.connection import ConnectionBase

DOCUMENTATION = """
    connection: localconn
    short_description: do stuff local
    description:
        - does stuff
    options:
      connectiontimeout:
        aliases:
          - timeout
"""


class Connection(ConnectionBase):
    transport = 'local'
    has_pipelining = True

    def _connect(self):
        return self

    def exec_command(self, cmd, in_data=None, sudoable=True):
        stdout = 'connectiontimeout is {0}'.format(to_native(self.get_option('connectiontimeout')))
        return (0, stdout, '')

    def put_file(self, in_path, out_path):
        raise NotImplementedError('just a test')

    def fetch_file(self, in_path, out_path):
        raise NotImplementedError('just a test')

    def close(self):
        self._connected = False
