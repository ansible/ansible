# Copyright (c) 2014, Chris Church <chris@ninemoreminutes.com>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = """
name: sh
short_description: "POSIX shell (/bin/sh)"
version_added: historical
description:
  - This shell plugin is the one you want to use on most Unix systems, it is the most compatible and widely installed shell.
extends_documentation_fragment:
  - shell_common
"""

from ansible.plugins.shell import ShellBase
from ansible.utils.display import Display


display = Display()


class ShellModule(ShellBase):

    # Common shell filenames that this plugin handles.
    # Note: sh is the default shell plugin so this plugin may also be selected
    # This code needs to be SH-compliant. BASH-isms will not work if /bin/sh points to a non-BASH shell.

    # if the filename is not listed in any Shell plugin.
    COMPATIBLE_SHELLS = frozenset(('sh', 'zsh', 'bash', 'dash', 'ksh'))
    # Family of shells this has.  Must match the filename without extension
    SHELL_FAMILY = 'sh'

    # commonly used
    ECHO = 'echo'
    CD = 'cd'
    COMMAND_SEP = ';'

    # How to end lines in a python script one-liner
    _SHELL_EMBEDDED_PY_EOL = '\n'
    _SHELL_REDIRECT_ALLNULL = '> /dev/null 2>&1'
    _SHELL_AND = '&&'
    _SHELL_OR = '||'
    _SHELL_SUB_LEFT = '"`'
    _SHELL_SUB_RIGHT = '`"'
    _SHELL_GROUP_LEFT = '('
    _SHELL_GROUP_RIGHT = ')'

    def checksum(self, path, python_interp):
        display.deprecated(
            msg="The `ShellModule.checksum` method is deprecated.",
            version="2.23",
            help_text="Use `ActionBase._execute_remote_stat()` instead.",
        )
        # In the following test, each condition is a check and logical
        # comparison (|| or &&) that sets the rc value.  Every check is run so
        # the last check in the series to fail will be the rc that is returned.
        #
        # If a check fails we error before invoking the hash functions because
        # hash functions may successfully take the hash of a directory on BSDs
        # (UFS filesystem?) which is not what the rest of the ansible code expects
        #
        # If all of the available hashing methods fail we fail with an rc of 0.
        # This logic is added to the end of the cmd at the bottom of this function.

        # Return codes:
        # checksum: success!
        # 0: Unknown error
        # 1: Remote file does not exist
        # 2: No read permissions on the file
        # 3: File is a directory
        # 4: No python interpreter

        # Quoting gets complex here.  We're writing a python string that's
        # used by a variety of shells on the remote host to invoke a python
        # "one-liner".
        shell_escaped_path = self.quote(path)
        test = "rc=flag; [ -r %(p)s ] %(shell_or)s rc=2; [ -f %(p)s ] %(shell_or)s rc=1; [ -d %(p)s ] %(shell_and)s rc=3; %(i)s -V 2>/dev/null %(shell_or)s rc=4; [ x\"$rc\" != \"xflag\" ] %(shell_and)s echo \"${rc}  \"%(p)s %(shell_and)s exit 0" % dict(p=shell_escaped_path, i=python_interp, shell_and=self._SHELL_AND, shell_or=self._SHELL_OR)  # NOQA
        cmd = "({0} -c 'import hashlib; BLOCKSIZE = 65536; hasher = hashlib.sha1();{2}afile = open(\"'{1}'\", \"rb\"){2}buf = afile.read(BLOCKSIZE){2}while len(buf) > 0:{2}\thasher.update(buf){2}\tbuf = afile.read(BLOCKSIZE){2}afile.close(){2}print(hasher.hexdigest())' 2>/dev/null)".format(python_interp, shell_escaped_path, self._SHELL_EMBEDDED_PY_EOL)  # NOQA

        cmd = "%s; %s %s (echo \'0  \'%s)" % (test, cmd, self._SHELL_OR, shell_escaped_path)
        return cmd
