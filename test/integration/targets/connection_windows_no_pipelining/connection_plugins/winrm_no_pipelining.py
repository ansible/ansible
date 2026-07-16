# Copyright (c) 2026 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""
author: Ansible Core Team
name: winrm_no_pipelining
short_description: Testing Windows over non pipelined connection plugin
description:
- Used for testing only
options:
  remote_addr:
    description:
    - Address of the windows machine
    vars:
    - name: ansible_host
    type: str
  remote_user:
    description:
    - The user to log in as to the Windows machine
    vars:
    - name: ansible_user
    type: str
  remote_password:
    description: Authentication password.
    vars:
    - name: ansible_password
    type: str
  port:
    description:
    - WinRM port.
    vars:
    - name: ansible_port
    default: 5986
    type: integer
  transport:
    description:
    - WinRM transport to use.
    vars:
    - name: ansible_winrm_transport
    type: list
    elements: str
  server_cert_validation:
    description:
    - WinRM server certificate validation mode to use.
    vars:
    - name: ansible_winrm_server_cert_validation
    type: str
"""


from ansible.plugins.connection.winrm import Connection as WinRMBase


class Connection(WinRMBase):

    transport = 'winrm_no_pipelining'

    def _build_winrm_kwargs(self) -> None:
        # Stub out just enough of what the base class needs from known input options.
        self._winrm_host = self.get_option('remote_addr')
        self._winrm_user = self.get_option('remote_user')
        self._winrm_pass = self.get_option('remote_password')
        self._winrm_port = self.get_option('port')
        self._winrm_transport = self.get_option('transport')

        self._winrm_scheme = 'http' if self._winrm_port == 5985 else 'https'
        self._winrm_path = '/wsman'
        self._winrm_connection_timeout = None

        self._winrm_kwargs = {
            'username': self._winrm_user,
            'password': self._winrm_pass,
            'server_cert_validation': self.get_option('server_cert_validation'),
        }

    def exec_command(self, cmd, in_data=None, sudoable=False):
        if in_data:
            raise Exception(f"Pipelining should be disabled but in_data was provided for {cmd}")

        return super().exec_command(cmd, in_data=in_data, sudoable=sudoable)

    def is_pipelining_enabled(self, wrap_async: bool = False) -> bool:
        return False
