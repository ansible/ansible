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
      connectionvar:
        description:
            - something we set
        default: the_default
        vars:
            - name: ansible_localconn_connectionvar
      count_commands:
        description:
          - include the number of commands the connection has run in stdout
        default: false
        type: bool
        vars:
          - name: ansible_localconn_command_count
"""


class Connection(ConnectionBase):
    transport = 'local'
    has_pipelining = True

    def __init__(self, *args, **kwargs):
        self._cmds_run = 0
        super().__init__(*args, **kwargs)

    @property
    def connected(self):
        return True

    def _connect(self):
        return self

    def exec_command(self, cmd, in_data=None, sudoable=True):
        if self.get_option('count_commands'):
            self._cmds_run += 1
            stdout = 'localconn ran {0} ({1})'.format(to_native(cmd), self._cmds_run)
        else:
            stdout = 'localconn ran {0}'.format(to_native(cmd))
        stderr = 'connectionvar is {0}'.format(to_native(self.get_option('connectionvar')))
        return (0, stdout, stderr)

    def put_file(self, in_path, out_path):
        raise NotImplementedError('just a test')

    def fetch_file(self, in_path, out_path):
        raise NotImplementedError('just a test')

    def close(self):
        self._connected = False
