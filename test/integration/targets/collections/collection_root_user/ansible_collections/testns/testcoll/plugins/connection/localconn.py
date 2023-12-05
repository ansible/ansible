from __future__ import annotations

from ansible.module_utils.common.text.converters import to_native
from ansible.plugins.connection import ConnectionBase

DOCUMENTATION = """
    connection: localconn
    short_description: do stuff local
    description:
        - does stuff
    options:
      connectionvar:
        description:
            - something we set
        default: the_default
        vars:
            - name: ansible_localconn_connectionvar
"""


class Connection(ConnectionBase):
    transport = 'local'
    has_pipelining = True

    def _connect(self):
        return self

    def exec_command(self, cmd, in_data=None, sudoable=True):
        stdout = 'localconn ran {0}'.format(to_native(cmd))
        stderr = 'connectionvar is {0}'.format(to_native(self.get_option('connectionvar')))
        return (0, stdout, stderr)

    def put_file(self, in_path, out_path):
        raise NotImplementedError('just a test')

    def fetch_file(self, in_path, out_path):
        raise NotImplementedError('just a test')

    def close(self):
        self._connected = False
