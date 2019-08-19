# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    become: machinectl
    short_description: Systemd's machinectl privilege escalation
    description:
        - This become plugins allows your remote/login user to execute commands as another user via the machinectl utility.
    author: ansible (@core)
    version_added: "2.8"
    options:
        become_user:
            description: User you 'become' to execute the task
            ini:
              - section: privilege_escalation
                key: become_user
              - section: machinectl_become_plugin
                key: user
            vars:
              - name: ansible_become_user
              - name: ansible_machinectl_user
            env:
              - name: ANSIBLE_BECOME_USER
              - name: ANSIBLE_MACHINECTL_USER
        become_exe:
            description: Machinectl executable
            default: machinectl
            ini:
              - section: privilege_escalation
                key: become_exe
              - section: machinectl_become_plugin
                key: executable
            vars:
              - name: ansible_become_exe
              - name: ansible_machinectl_exe
            env:
              - name: ANSIBLE_BECOME_EXE
              - name: ANSIBLE_MACHINECTL_EXE
        become_flags:
            description: Options to pass to machinectl
            default: ''
            ini:
              - section: privilege_escalation
                key: become_flags
              - section: machinectl_become_plugin
                key: flags
            vars:
              - name: ansible_become_flags
              - name: ansible_machinectl_flags
            env:
              - name: ANSIBLE_BECOME_FLAGS
              - name: ANSIBLE_MACHINECTL_FLAGS
        become_pass:
            description: Password for machinectl
            required: False
            vars:
              - name: ansible_become_password
              - name: ansible_become_pass
              - name: ansible_machinectl_pass
            env:
              - name: ANSIBLE_BECOME_PASS
              - name: ANSIBLE_MACHINECTL_PASS
            ini:
              - section: machinectl_become_plugin
                key: password
"""

from ansible.plugins.become import BecomeBase


class BecomeModule(BecomeBase):

    name = 'machinectl'

    def build_become_command(self, cmd, shell):
        super(BecomeModule, self).build_become_command(cmd, shell)

        if not cmd:
            return cmd

        become = self.get_option('become_exe') or self.name
        flags = self.get_option('become_flags') or ''
        user = self.get_option('become_user') or ''
        return '%s -q shell %s %s@ %s' % (become, flags, user, cmd)
