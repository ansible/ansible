# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = """
    name: connection_test
    short_description: register secrets and prove Display egress redacts them immediately
    description:
        - Test helper connection that registers secrets via the public
          C(ansible.module_utils.secrets) API while connecting and proves a subsequent
          C(Display) egress redacts them without any propagation delay.
        - Does not execute anything remote; C(exec_command) returns a canned result.
    author: ansible (@core)
"""

from ansible.module_utils.secrets import register_secret, register_secrets, mask_secrets
from ansible.plugins.connection import ConnectionBase
from ansible.utils.display import Display

display = Display()


class Connection(ConnectionBase):
    """ probe connection that registers secrets while connecting """

    transport = 'connection_test'
    has_pipelining = True

    def _connect(self):
        if not self._connected:
            secrets = ['ConnectionSecret1', 'ConnectionSecret2', 'ConnectionSecret3']

            register_secret(secrets[0])
            display.display(f"MARKER connection_register: {secrets[0]}")

            register_secrets(secrets)
            display.display(f"MARKER connection_registers: {secrets[0]} {secrets[1]} {secrets[2]}")

            if mask_secrets(f"{secrets[0]} {secrets[1]} {secrets[2]}") != '$REDACTED$ $REDACTED$ $REDACTED$':
                raise Exception("mask_secrets did not redact all the registered secrets")

            display.warning(f"MARKER connection_warning: {secrets[1]}")
            display.deprecated(f"MARKER connection_deprecated: {secrets[2]}", version='9999.9')

            self._connected = True
        return self

    def exec_command(self, cmd, in_data=None, sudoable=True):
        super().exec_command(cmd, in_data=in_data, sudoable=sudoable)
        return 0, b'ALL IS GOOD', b''

    def put_file(self, in_path, out_path):
        super().put_file(in_path, out_path)

    def fetch_file(self, in_path, out_path):
        super().fetch_file(in_path, out_path)

    def close(self):
        self._connected = False
