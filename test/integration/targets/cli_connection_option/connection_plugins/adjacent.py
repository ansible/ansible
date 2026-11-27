from __future__ import annotations

DOCUMENTATION = """
connection: adjacent
author: ansible-core
short_description: playbook-adjacent connection plugin
description:
  - Only needs to be resolvable, to verify C(-c) accepts plugins next to the playbook.
"""

from ansible.plugins.connection.local import Connection as LocalConnection


class Connection(LocalConnection):
    transport = 'adjacent'
