# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    name: su
    short_description: Substitute User
    description:
        - This become plugin allows your remote/login user to execute commands as another user via the su utility.
    author: ansible (@core)
    version_added: "2.8"
    options:
        become_user:
            description: User you 'become' to execute the task
            default: root
            ini:
              - section: privilege_escalation
                key: become_user
              - section: su_become_plugin
                key: user
            vars:
              - name: ansible_become_user
              - name: ansible_su_user
            env:
              - name: ANSIBLE_BECOME_USER
              - name: ANSIBLE_SU_USER
            keyword:
              - name: become_user
        become_exe:
            description: Su executable
            default: su
            ini:
              - section: privilege_escalation
                key: become_exe
              - section: su_become_plugin
                key: executable
            vars:
              - name: ansible_become_exe
              - name: ansible_su_exe
            env:
              - name: ANSIBLE_BECOME_EXE
              - name: ANSIBLE_SU_EXE
            keyword:
              - name: become_exe
        become_flags:
            description: Options to pass to su
            default: ''
            ini:
              - section: privilege_escalation
                key: become_flags
              - section: su_become_plugin
                key: flags
            vars:
              - name: ansible_become_flags
              - name: ansible_su_flags
            env:
              - name: ANSIBLE_BECOME_FLAGS
              - name: ANSIBLE_SU_FLAGS
            keyword:
              - name: become_flags
        become_pass:
            description: Password to pass to su
            required: False
            vars:
              - name: ansible_become_password
              - name: ansible_become_pass
              - name: ansible_su_pass
            env:
              - name: ANSIBLE_BECOME_PASS
              - name: ANSIBLE_SU_PASS
            ini:
              - section: su_become_plugin
                key: password
        prompt_l10n:
            description:
                - List of localized strings to match for prompt detection
                - If empty we'll use the built in one
                - Do NOT add a colon (:) to your custom entries. Ansible adds a colon at the end of each prompt;
                  if you add another one in your string, your prompt will fail with a "Timeout" error.
            default: []
            type: list
            elements: string
            ini:
              - section: su_become_plugin
                key: localized_prompts
            vars:
              - name: ansible_su_prompt_l10n
            env:
              - name: ANSIBLE_SU_PROMPT_L10N
"""

import re
import shlex

from ansible.module_utils._text import to_bytes
from ansible.plugins.become import BecomeBase


class BecomeModule(BecomeBase):

    name = 'su'

    # messages for detecting prompted password issues
    fail = ('Authentication failure',)

    SU_PROMPT_LOCALIZATIONS = [
        'Password',
        '암호',
        'パスワード',
        'Adgangskode',
        'Contraseña',
        'Contrasenya',
        'Hasło',
        'Heslo',
        'Jelszó',
        'Lösenord',
        'Mật khẩu',
        'Mot de passe',
        'Parola',
        'Parool',
        'Pasahitza',
        'Passord',
        'Passwort',
        'Salasana',
        'Sandi',
        'Senha',
        'Wachtwoord',
        'ססמה',
        'Лозинка',
        'Парола',
        'Пароль',
        'गुप्तशब्द',
        'शब्दकूट',
        'సంకేతపదము',
        'හස්පදය',
        '密码',
        '密碼',
        '口令',
    ]

    def check_password_prompt(self, b_output):
        ''' checks if the expected password prompt exists in b_output '''

        prompts = self.get_option('prompt_l10n') or self.SU_PROMPT_LOCALIZATIONS
        b_password_string = b"|".join((br'(\w+\'s )?' + to_bytes(p)) for p in prompts)
        # Colon or unicode fullwidth colon
        b_password_string = b_password_string + to_bytes(u' ?(:|：) ?')
        b_su_prompt_localizations_re = re.compile(b_password_string, flags=re.IGNORECASE)
        return bool(b_su_prompt_localizations_re.match(b_output))

    def build_become_command(self, cmd, shell):
        super(BecomeModule, self).build_become_command(cmd, shell)

        # Prompt handling for ``su`` is more complicated, this
        # is used to satisfy the connection plugin
        self.prompt = True

        if not cmd:
            return cmd

        exe = self.get_option('become_exe') or self.name
        flags = self.get_option('become_flags') or ''
        user = self.get_option('become_user') or ''
        success_cmd = self._build_success_command(cmd, shell)

        return "%s %s %s -c %s" % (exe, flags, user, shlex.quote(success_cmd))
