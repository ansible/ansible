# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = '''
name: cmd
version_added: '2.8'
short_description: Windows Command Prompt
description:
- Used with the 'ssh' connection plugin and no C(DefaultShell) has been set on the Windows host.
extends_documentation_fragment:
- shell_windows
'''

import re

from ansible.plugins.shell.powershell import ShellModule as PSShellModule

# these are the metachars that have a special meaning in cmd that we want to escape when quoting
_find_unsafe = re.compile(r'[\s\(\)\%\!^\"\<\>\&\|]').search


class ShellModule(PSShellModule):

    # Common shell filenames that this plugin handles
    COMPATIBLE_SHELLS = frozenset()  # type: frozenset[str]
    # Family of shells this has.  Must match the filename without extension
    SHELL_FAMILY = 'cmd'

    _SHELL_REDIRECT_ALLNULL = '>nul 2>&1'
    _SHELL_AND = '&&'

    # Used by various parts of Ansible to do Windows specific changes
    _IS_WINDOWS = True

    def quote(self, cmd):
        # cmd does not support single quotes that the shlex_quote uses. We need to override the quoting behaviour to
        # better match cmd.exe.
        # https://blogs.msdn.microsoft.com/twistylittlepassagesallalike/2011/04/23/everyone-quotes-command-line-arguments-the-wrong-way/

        # Return an empty argument
        if not cmd:
            return '""'

        if _find_unsafe(cmd) is None:
            return cmd

        # Escape the metachars as we are quoting the string to stop cmd from interpreting that metachar. For example
        # 'file &whoami.exe' would result in 'file $(whoami.exe)' instead of the literal string
        # https://stackoverflow.com/questions/3411771/multiple-character-replace-with-python
        for c in '^()%!"<>&|':  # '^' must be the first char that we scan and replace
            if c in cmd:
                # I can't find any docs that explicitly say this but to escape ", it needs to be prefixed with \^.
                cmd = cmd.replace(c, ("\\^" if c == '"' else "^") + c)

        return '^"' + cmd + '^"'
