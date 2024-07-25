# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import shlex

from abc import abstractmethod
from secrets import choice
from string import ascii_lowercase
from gettext import dgettext

from ansible.errors import AnsibleError
from ansible.module_utils.common.text.converters import to_bytes
from ansible.plugins import AnsiblePlugin


def _gen_id(length=32):
    ''' return random string used to identify the current privilege escalation '''
    return ''.join(choice(ascii_lowercase) for x in range(length))


class BecomeBase(AnsiblePlugin):

    name = None  # type: str | None

    # messages for detecting prompted password issues
    fail = tuple()  # type: tuple[str, ...]
    missing = tuple()  # type: tuple[str, ...]

    # many connection plugins cannot provide tty, set to True if your become
    # plugin requires a tty, i.e su
    require_tty = False

    # prompt to match
    prompt = ''

    def __init__(self):
        super(BecomeBase, self).__init__()
        self._id = ''
        self.success = ''

    def get_option(self, option, hostvars=None, playcontext=None):
        """ Overrides the base get_option to provide a fallback to playcontext vars in case a 3rd party plugin did not
        implement the base become options required in Ansible. """
        # TODO: add deprecation warning for ValueError in devel that removes the playcontext fallback
        try:
            return super(BecomeBase, self).get_option(option, hostvars=hostvars)
        except KeyError:
            pc_fallback = ['become_user', 'become_pass', 'become_flags', 'become_exe']
            if option not in pc_fallback:
                raise

            return getattr(playcontext, option, None)

    def expect_prompt(self):
        """This function assists connection plugins in determining if they need to wait for
        a prompt. Both a prompt and a password are required.
        """
        return self.prompt and self.get_option('become_pass')

    def _build_success_command(self, cmd, shell, noexe=False):
        if not all((cmd, shell, self.success)):
            return cmd

        try:
            cmd = shlex.quote('%s %s %s %s' % (shell.ECHO, self.success, shell.COMMAND_SEP, cmd))
        except AttributeError:
            # TODO: This should probably become some more robust functionality used to detect incompat
            raise AnsibleError('The %s shell family is incompatible with the %s become plugin' % (shell.SHELL_FAMILY, self.name))
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
        ''' checks if the expected password prompt exists in b_output '''
        if self.prompt:
            b_prompt = to_bytes(self.prompt).strip()
            return any(l.strip().startswith(b_prompt) for l in b_output.splitlines())
        return False

    def _check_password_error(self, b_out, msg):
        ''' returns True/False if domain specific i18n version of msg is found in b_out '''
        b_fail = to_bytes(dgettext(self.name, msg))
        return b_fail and b_fail in b_out

    def check_incorrect_password(self, b_output):
        for errstring in self.fail:
            if self._check_password_error(b_output, errstring):
                return True
        return False

    def check_missing_password(self, b_output):
        for errstring in self.missing:
            if self._check_password_error(b_output, errstring):
                return True
        return False
