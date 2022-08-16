# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = '''
name: annotations
short_description: validate-modules test with annotations import
description:
- This connection plugin tests out a plugin with an annotations import
author: ansible (@core)
'''

from ansible.plugins.connection import ConnectionBase


class Connection(ConnectionBase):

    transport = 'annotations'

    def exec_command(self, cmd, in_data=None, sudoable=True):
        return 0, b"", b""

    def put_file(self, in_path, out_path):
        return

    def fetch_file(self, in_path, out_path):
        return

    def close(self):
        return
