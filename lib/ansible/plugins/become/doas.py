# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    become: doas
    short_description: Do As user
    description:
        - This become plugins allows your remote/login user to execute commands as another user via the doas utility.
    author: ansible (@core)
    version_added: "2.8"
    options:
        become_user:
            description: User you 'become' to execute the task
            ini:
              - section: privilege_escalation
                key: become_user
              - section: doas_become_plugin
                key: user
            vars:
              - name: ansible_become_user
              - name: ansible_doas_user
            env:
              - name: ANSIBLE_BECOME_USER
              - name: ANSIBLE_DOAS_USER
        become_exe:
            description: Doas executable
            default: doas
            ini:
              - section: privilege_escalation
                key: become_exe
              - section: doas_become_plugin
                key: executable
            vars:
              - name: ansible_become_exe
              - name: ansible_doas_exe
            env:
              - name: ANSIBLE_BECOME_EXE
              - name: ANSIBLE_DOAS_EXE
        become_flags:
            description: Options to pass to doas
            default:
            ini:
              - section: privilege_escalation
                key: become_flags
              - section: doas_become_plugin
                key: flags
            vars:
              - name: ansible_become_flags
              - name: ansible_doas_flags
            env:
              - name: ANSIBLE_BECOME_FLAGS
              - name: ANSIBLE_DOAS_FLAGS
        become_pass:
            description: password for doas prompt
            required: False
            vars:
              - name: ansible_become_password
              - name: ansible_become_pass
              - name: ansible_doas_pass
            env:
              - name: ANSIBLE_BECOME_PASS
              - name: ANSIBLE_DOAS_PASS
            ini:
              - section: doas_become_plugin
                key: password
        prompt_l10n:
            description:
                - List of localized strings to match for prompt detection
                - If empty we'll use the built in one
            default: []
            ini:
              - section: doas_become_plugin
                key: localized_prompts
            vars:
              - name: ansible_doas_prompt_l10n
            env:
              - name: ANSIBLE_DOAS_PROMPT_L10N
"""

import re

from ansible.module_utils._text import to_bytes
from ansible.plugins.become import BecomeBase


class BecomeModule(BecomeBase):

    name = 'doas'

    # messages for detecting prompted password issues
    fail = ('Permission denied',)
    missing = ('Authorization required',)

    def check_password_prompt(self, b_output):
        ''' checks if the expected password prompt exists in b_output '''

        # FIXME: more accurate would be: 'doas (%s@' % remote_user
        # however become plugins don't have that information currently
        b_prompts = [to_bytes(p) for p in self.get_option('prompt_l10n')] or [br'doas \(', br'Password:']
        b_prompt = b"|".join(b_prompts)

        return bool(re.match(b_prompt, b_output))

    def build_become_command(self, cmd, shell):
        super(BecomeModule, self).build_become_command(cmd, shell)

        if not cmd:
            return cmd

        self.prompt = True

        become_exe = self.get_option('become_exe') or self.name

        flags = self.get_option('become_flags') or ''
        if not self.get_option('become_pass') and '-n' not in flags:
            flags += ' -n'

        user = self.get_option('become_user') or ''
        if user:
            user = '-u %s' % (user)

        success_cmd = self._build_success_command(cmd, shell, noexe=True)
        executable = getattr(shell, 'executable', shell.SHELL_FAMILY)

        return '%s %s %s %s -c %s' % (become_exe, flags, user, executable, success_cmd)
