# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    become: pfexec
    short_description: profile based execution
    description:
        - This become plugins allows your remote/login user to execute commands as another user via the pfexec utility.
    author: ansible (@core)
    version_added: "2.8"
    options:
        become_user:
            description:
                - User you 'become' to execute the task
                - This plugin ignores this setting as pfexec uses it's own ``exec_attr`` to figure this out,
                  but it is supplied here for Ansible to make decisions needed for the task execution, like file permissions.
            default: root
            ini:
              - section: privilege_escalation
                key: become_user
              - section: pfexec_become_plugin
                key: user
            vars:
              - name: ansible_become_user
              - name: ansible_pfexec_user
            env:
              - name: ANSIBLE_BECOME_USER
              - name: ANSIBLE_PFEXEC_USER
        become_exe:
            description: Sudo executable
            default: pfexec
            ini:
              - section: privilege_escalation
                key: become_exe
              - section: pfexec_become_plugin
                key: executable
            vars:
              - name: ansible_become_exe
              - name: ansible_pfexec_exe
            env:
              - name: ANSIBLE_BECOME_EXE
              - name: ANSIBLE_PFEXEC_EXE
        become_flags:
            description: Options to pass to pfexec
            default: -H -S -n
            ini:
              - section: privilege_escalation
                key: become_flags
              - section: pfexec_become_plugin
                key: flags
            vars:
              - name: ansible_become_flags
              - name: ansible_pfexec_flags
            env:
              - name: ANSIBLE_BECOME_FLAGS
              - name: ANSIBLE_PFEXEC_FLAGS
        become_pass:
            description: pfexec password
            required: False
            vars:
              - name: ansible_become_password
              - name: ansible_become_pass
              - name: ansible_pfexec_pass
            env:
              - name: ANSIBLE_BECOME_PASS
              - name: ANSIBLE_PFEXEC_PASS
            ini:
              - section: pfexec_become_plugin
                key: password
        wrap_exe:
            description: Toggle to wrap the command pfexec calls in 'shell -c' or not
            default: False
            type: bool
            ini:
              - section: pfexec_become_plugin
                key: wrap_execution
            vars:
              - name: ansible_pfexec_wrap_execution
            env:
              - name: ANSIBLE_PFEXEC_WRAP_EXECUTION
    note:
      - This plugin ignores ``become_user`` as pfexec uses it's own ``exec_attr`` to figure this out.
"""

from ansible.plugins.become import BecomeBase


class BecomeModule(BecomeBase):

    name = 'pfexec'

    def build_become_command(self, cmd, shell):
        super(BecomeModule, self).build_become_command(cmd, shell)

        if not cmd:
            return cmd

        exe = self.get_option('become_exe') or self.name
        flags = self.get_option('become_flags')
        noexe = not self.get_option('wrap_exe')
        return '%s %s "%s"' % (exe, flags, self._build_success_command(cmd, shell, noexe=noexe))
