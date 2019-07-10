# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    become: sudo
    short_description: Substitute User DO
    description:
        - This become plugins allows your remote/login user to execute commands as another user via the sudo utility.
    author: ansible (@core)
    version_added: "2.8"
    extends_documentation_fragment:
        - become_matches
    options:
        become_user:
            description: User you 'become' to execute the task
            default: root
            ini:
              - section: privilege_escalation
                key: become_user
              - section: sudo_become_plugin
                key: user
            vars:
              - name: ansible_become_user
              - name: ansible_sudo_user
            env:
              - name: ANSIBLE_BECOME_USER
              - name: ANSIBLE_SUDO_USER
        become_exe:
            description: Sudo executable
            default: sudo
            ini:
              - section: privilege_escalation
                key: become_exe
              - section: sudo_become_plugin
                key: executable
            vars:
              - name: ansible_become_exe
              - name: ansible_sudo_exe
            env:
              - name: ANSIBLE_BECOME_EXE
              - name: ANSIBLE_SUDO_EXE
        become_flags:
            description: Options to pass to sudo
            default: -H -S -n
            ini:
              - section: privilege_escalation
                key: become_flags
              - section: sudo_become_plugin
                key: flags
            vars:
              - name: ansible_become_flags
              - name: ansible_sudo_flags
            env:
              - name: ANSIBLE_BECOME_FLAGS
              - name: ANSIBLE_SUDO_FLAGS
        become_pass:
            description: Password to pass to sudo
            required: False
            vars:
              - name: ansible_become_password
              - name: ansible_become_pass
              - name: ansible_sudo_pass
            env:
              - name: ANSIBLE_BECOME_PASS
              - name: ANSIBLE_SUDO_PASS
            ini:
              - section: sudo_become_plugin
                key: password
        become_fail_match:
            version_added: '2.9'
            default: ['Sorry, try again.']
            ini:
              - section: sudo_become_plugin
                key: fail_match
            env:
              - name: ANSIBLE_SUDO_FAIL_MATCH
            vars:
              - name: ansible_sudo_fail_match
        become_missing_password_match:
            version_added: '2.9'
            default: ['Sorry, a password is required to run sudo', 'sudo: a password is required']
            ini:
              - section: sudo_become_plugin
                key: missing_password_match
            env:
              - name: ANSIBLE_SUDO_MISSING_PASSWORD_MATCH
            vars:
              - name: ansible_sudo_missing_passowrd_match
"""


from ansible.plugins.become import BecomeBase


class BecomeModule(BecomeBase):

    # me
    name = 'sudo'

    # messages for detecting prompted password issues
    fail = None
    missing = None

    def build_become_command(self, cmd, shell):
        super(BecomeModule, self).build_become_command(cmd, shell)

        if not cmd:
            return cmd

        becomecmd = self.get_option('become_exe') or self.name

        flags = self.get_option('become_flags') or ''
        prompt = ''
        if self.get_option('become_pass'):
            self.prompt = '[sudo via ansible, key=%s] password:' % self._id
            if flags:  # this could be simplified, but kept as is for now for backwards string matching
                flags = flags.replace('-n', '')
            prompt = '-p "%s"' % (self.prompt)

        user = self.get_option('become_user') or ''
        if user:
            user = '-u %s' % (user)

        return ' '.join([becomecmd, flags, prompt, user, self._build_success_command(cmd, shell)])
