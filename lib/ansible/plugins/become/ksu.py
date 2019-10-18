# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    become: ksu
    short_description: Kerberos substitute user
    description:
        - This become plugins allows your remote/login user to execute commands as another user via the ksu utility.
    author: ansible (@core)
    version_added: "2.8"
    options:
        become_user:
            description: User you 'become' to execute the task
            ini:
              - section: privilege_escalation
                key: become_user
              - section: ksu_become_plugin
                key: user
            vars:
              - name: ansible_become_user
              - name: ansible_ksu_user
            env:
              - name: ANSIBLE_BECOME_USER
              - name: ANSIBLE_KSU_USER
            required: True
        become_exe:
            description: Su executable
            default: ksu
            ini:
              - section: privilege_escalation
                key: become_exe
              - section: ksu_become_plugin
                key: executable
            vars:
              - name: ansible_become_exe
              - name: ansible_ksu_exe
            env:
              - name: ANSIBLE_BECOME_EXE
              - name: ANSIBLE_KSU_EXE
        become_flags:
            description: Options to pass to ksu
            default: ''
            ini:
              - section: privilege_escalation
                key: become_flags
              - section: ksu_become_plugin
                key: flags
            vars:
              - name: ansible_become_flags
              - name: ansible_ksu_flags
            env:
              - name: ANSIBLE_BECOME_FLAGS
              - name: ANSIBLE_KSU_FLAGS
        become_pass:
            description: ksu password
            required: False
            vars:
              - name: ansible_ksu_pass
              - name: ansible_become_pass
              - name: ansible_become_password
            env:
              - name: ANSIBLE_BECOME_PASS
              - name: ANSIBLE_KSU_PASS
            ini:
              - section: ksu_become_plugin
                key: password
        prompt_l10n:
            description:
                - List of localized strings to match for prompt detection
                - If empty we'll use the built in one
            default: []
            ini:
              - section: ksu_become_plugin
                key: localized_prompts
            vars:
              - name: ansible_ksu_prompt_l10n
            env:
              - name: ANSIBLE_KSU_PROMPT_L10N
"""

import re

from ansible.module_utils._text import to_bytes
from ansible.plugins.become import BecomeBase


class BecomeModule(BecomeBase):

    name = 'ksu'

    # messages for detecting prompted password issues
    fail = ('Password incorrect',)
    missing = ('No password given',)

    def check_password_prompt(self, b_output):
        ''' checks if the expected password prompt exists in b_output '''

        prompts = self.get_option('prompt_l10n') or ["Kerberos password for .*@.*:"]
        b_prompt = b"|".join(to_bytes(p) for p in prompts)

        return bool(re.match(b_prompt, b_output))

    def build_become_command(self, cmd, shell):

        super(BecomeModule, self).build_become_command(cmd, shell)

        # Prompt handling for ``ksu`` is more complicated, this
        # is used to satisfy the connection plugin
        self.prompt = True

        if not cmd:
            return cmd

        exe = self.get_option('become_exe') or self.name
        flags = self.get_option('become_flags') or ''
        user = self.get_option('become_user') or ''
        return '%s %s %s -e %s ' % (exe, user, flags, self._build_success_command(cmd, shell))
