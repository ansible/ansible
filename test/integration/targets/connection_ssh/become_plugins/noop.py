# Copyright: (c) 2026, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = """
    name: noop
    short_description: Test become plugin attributes.
    description: Test become plugin attributes that modulate pipelining.
    options:
      become_pass:
        description: Password option required by BecomeBase.
        default: pass
"""

import os

from ansible.module_utils.parsing.convert_bool import boolean
from ansible.plugins.become import BecomeBase


class BecomeModule(BecomeBase):
    name = 'noop'
    prompt = 'testing become plugin attributes via ansible-test'

    require_tty = boolean(os.environ.get("ANSIBLE_TEST_BECOME_REQUIRE_TTY", BecomeBase.require_tty))
    pipelining = boolean(os.environ.get("ANSIBLE_TEST_BECOME_PIPELINING", BecomeBase.pipelining))

    def build_become_command(self, cmd, shell):
        super(BecomeModule, self).build_become_command(cmd, shell)

        if not cmd:
            return cmd

        return f'echo "{self.prompt}"; read PASS; echo {self.success}; exec {cmd}'
