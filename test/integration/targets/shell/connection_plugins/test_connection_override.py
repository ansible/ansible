# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = '''
connection: test_connection_override
short_description: test connection plugin used in tests
description:
- This is a test connection plugin used for shell testing
author: ansible (@core)
version_added: historical
options:
'''

from ansible.plugins.connection import ConnectionBase


class Connection(ConnectionBase):
    ''' test connection '''

    transport = 'test_connection_override'

    def __init__(self, *args, **kwargs):
        self._shell_type = 'powershell'  # Set a shell type that is not sh
        super(Connection, self).__init__(*args, **kwargs)

    def _connect(self):
        pass

    def exec_command(self, cmd, in_data=None, sudoable=True):
        pass

    def put_file(self, in_path, out_path):
        pass

    def fetch_file(self, in_path, out_path):
        pass

    def close(self):
        pass
