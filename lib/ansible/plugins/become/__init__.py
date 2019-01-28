# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from abc import abstractmethod
from random import choice
from string import ascii_lowercase
from gettext import dgettext

from ansible.module_utils.six.moves import shlex_quote
from ansible.module_utils._text import to_bytes
from ansible.plugins import AnsiblePlugin


def _gen_id(length=32):
    ''' return random string used to identify the current privelege escalation '''
    return ''.join(choice(ascii_lowercase) for x in range(length))


class BecomeBase(AnsiblePlugin):

    name = None

    # messages for detecting prompted password issues
    fail = tuple()
    missing = tuple()

    # many connection plugins cannot provide tty, set to True if your plugin does, i.e su
    require_tty = False

    # prompt to match
    prompt = ''

    def __init__(self):
        super(BecomeBase, self).__init__()
        self._id = ''
        self.success = ''

    def _build_success_command(self, cmd, shell, noexe=False):
        if cmd and shell and self.success:
            cmd = shlex_quote('%s %s %s %s' % (shell.ECHO, self.success, shell.COMMAND_SEP, cmd))
            exe = getattr(shell, 'executable', None)
            if exe and not noexe:
                cmd = '%s -c %s' % (exe, cmd)
        return cmd

    @abstractmethod
    def build_become_command(self, cmd, shell):
        self._id = _gen_id()
        self.success = 'BECOME-SUCCESS-%s' % self._id

    def check_success(self, b_output):
        b_success = to_bytes(self.success)
        return any(b_success in l.rstrip() for l in b_output.splitlines(True))

    def check_password_prompt(self, b_output):
        ''' checks if the expected passwod prompt exists in b_output '''
        found = False
        if self.prompt:
            b_prompt = to_bytes(self.prompt).strip()
            found = any(l.strip().startswith(b_prompt) for l in b_output.splitlines())
        return found

    def _check_password_error(self, b_out, msg):
        ''' returns True/False if domain specific i18n version of msg is found in b_out '''
        b_fail = to_bytes(dgettext(self.name, msg))
        return b_fail and b_fail in b_out

    def check_incorrect_password(self, b_output):
        is_error = False
        for errstring in self.fail:
            if self._check_password_error(b_output, errstring):
                is_error = True
                break
        return is_error

    def check_missing_password(self, b_output):
        is_error = False
        for errstring in self.missing:
            if self._check_password_error(b_output, errstring):
                is_error = True
                break
        return is_error
