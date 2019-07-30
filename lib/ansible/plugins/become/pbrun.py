# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    become: pbrun
    short_description: PowerBroker run
    description:
        - This become plugins allows your remote/login user to execute commands as another user via the pbrun utility.
    author: ansible (@core)
    version_added: "2.8"
    options:
        become_user:
            description: User you 'become' to execute the task
            default: ''
            ini:
              - section: privilege_escalation
                key: become_user
              - section: pbrun_become_plugin
                key: user
            vars:
              - name: ansible_become_user
              - name: ansible_pbrun_user
            env:
              - name: ANSIBLE_BECOME_USER
              - name: ANSIBLE_PBRUN_USER
        become_exe:
            description: Sudo executable
            default: pbrun
            ini:
              - section: privilege_escalation
                key: become_exe
              - section: pbrun_become_plugin
                key: executable
            vars:
              - name: ansible_become_exe
              - name: ansible_pbrun_exe
            env:
              - name: ANSIBLE_BECOME_EXE
              - name: ANSIBLE_PBRUN_EXE
        become_flags:
            description: Options to pass to pbrun
            ini:
              - section: privilege_escalation
                key: become_flags
              - section: pbrun_become_plugin
                key: flags
            vars:
              - name: ansible_become_flags
              - name: ansible_pbrun_flags
            env:
              - name: ANSIBLE_BECOME_FLAGS
              - name: ANSIBLE_PBRUN_FLAGS
        become_pass:
            description: Password for pbrun
            required: False
            vars:
              - name: ansible_become_password
              - name: ansible_become_pass
              - name: ansible_pbrun_pass
            env:
              - name: ANSIBLE_BECOME_PASS
              - name: ANSIBLE_PBRUN_PASS
            ini:
              - section: pbrun_become_plugin
                key: password
        wrap_exe:
            description: Toggle to wrap the command pbrun calls in 'shell -c' or not
            default: False
            type: bool
            ini:
              - section: pbrun_become_plugin
                key: wrap_execution
            vars:
              - name: ansible_pbrun_wrap_execution
            env:
              - name: ANSIBLE_PBRUN_WRAP_EXECUTION
"""

from ansible.plugins.become import BecomeBase


class BecomeModule(BecomeBase):

    name = 'pbrun'

    prompt = 'Password:'

    def build_become_command(self, cmd, shell):
        super(BecomeModule, self).build_become_command(cmd, shell)

        if not cmd:
            return cmd

        become_exe = self.get_option('become_exe') or self.name
        flags = self.get_option('become_flags') or ''
        user = self.get_option('become_user') or ''
        if user:
            user = '-u %s' % (user)
        noexe = not self.get_option('wrap_exe')

        return ' '.join([become_exe, flags, user, self._build_success_command(cmd, shell, noexe=noexe)])
