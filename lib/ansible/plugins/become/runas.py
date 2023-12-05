# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = """
    name: runas
    short_description: Run As user
    description:
        - This become plugin allows your remote/login user to execute commands as another user via the windows runas facility.
    author: ansible (@core)
    version_added: "2.8"
    options:
        become_user:
            description: User you 'become' to execute the task
            ini:
              - section: privilege_escalation
                key: become_user
              - section: runas_become_plugin
                key: user
            vars:
              - name: ansible_become_user
              - name: ansible_runas_user
            env:
              - name: ANSIBLE_BECOME_USER
              - name: ANSIBLE_RUNAS_USER
            keyword:
              - name: become_user
            required: True
        become_flags:
            description: Options to pass to runas, a space delimited list of k=v pairs
            default: ''
            ini:
              - section: privilege_escalation
                key: become_flags
              - section: runas_become_plugin
                key: flags
            vars:
              - name: ansible_become_flags
              - name: ansible_runas_flags
            env:
              - name: ANSIBLE_BECOME_FLAGS
              - name: ANSIBLE_RUNAS_FLAGS
            keyword:
              - name: become_flags
        become_pass:
            description: password
            ini:
              - section: runas_become_plugin
                key: password
            vars:
              - name: ansible_become_password
              - name: ansible_become_pass
              - name: ansible_runas_pass
            env:
              - name: ANSIBLE_BECOME_PASS
              - name: ANSIBLE_RUNAS_PASS
    notes:
        - runas is really implemented in the powershell module handler and as such can only be used with winrm connections.
        - This plugin ignores the 'become_exe' setting as it uses an API and not an executable.
        - The Secondary Logon service (seclogon) must be running to use runas
"""

from ansible.plugins.become import BecomeBase


class BecomeModule(BecomeBase):

    name = 'runas'

    def build_become_command(self, cmd, shell):
        # this is a noop, the 'real' runas is implemented
        # inside the windows powershell execution subsystem
        return cmd
