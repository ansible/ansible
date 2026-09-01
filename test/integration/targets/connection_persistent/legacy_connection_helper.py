# Copyright: (c) 2026, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

from ansible.cli.scripts import ansible_connection_cli_stub as connection_helper
from ansible.utils.jsonrpc import JsonRpcServer


class LegacyJsonRpcServer(JsonRpcServer):
    """Simulate a daemon created before the compound synchronization RPC existed."""

    def register(self, obj: object) -> None:
        if isinstance(obj, connection_helper._ConnectionProcessRpc):
            return

        super().register(obj)


connection_helper.JsonRpcServer = LegacyJsonRpcServer


if __name__ == '__main__':
    connection_helper.main()
