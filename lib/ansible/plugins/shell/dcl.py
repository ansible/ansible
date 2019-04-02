# Copyright (c) 2014, Chris Church <chris@ninemoreminutes.com>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.six import text_type
from ansible.module_utils.six.moves import shlex_quote
from ansible.plugins.shell.sh import ShellModule as ShModule

DOCUMENTATION = '''
    name: dcl
    plugin_type: shell
    version_added: ""
    short_description: DCL shell OpenVMS COmmand line, no separate command...
    description:
      - This is to support OpenVMS, ( initialy based on fish)
    extends_documentation_fragment:
      - shell_common
'''


class ShellModule(ShModule):

    # Common shell filenames that this plugin handles
    COMPATIBLE_SHELLS = frozenset(('dcl',))
    # Family of shells this has.  Must match the filename without extension
    SHELL_FAMILY = 'dcl'

    _SHELL_EMBEDDED_PY_EOL = '\n'
    # The next can bedone by prepending command with 2 extra lines
    #     $ DEFINE SYS$OUTPUT NL:
    #     $ DEFINE SYS$ERROR NL:
    _SHELL_REDIRECT_ALLNULL =  ''  
    # The next should be prepended to the command
    _SHELL_AND = 'IF $status THEN '
    _SHELL_OR = ''
    _SHELL_SUB_LEFT = ''
    _SHELL_SUB_RIGHT = ''
    _SHELL_GROUP_LEFT = ''
    _SHELL_GROUP_RIGHT = ''

    # can only be done by adding assignment before the command...
    # NOT AFTER IF ... THEN... Quoting will be an issue....
    # strings: "......"
    # variable expansion: 'var' (early, before CLI parsing) &var (late, during CLI parsing)
    #                     ''var'    when variables are inside a string.
    # escaping a "  double up..  "what""ever"""   will show as: what"ever" when printed...
    def env_prefix(self, **kwargs):
        env = self.env.copy()
        env.update(kwargs)
        return ' '.join(['$ %s=%s\n' % (k, shlex_quote(text_type(v))) for k, v in env.items()])

    # This does what/when
    def build_module_command(self, env_string, shebang, cmd, arg_path=None):
        # don't quote the cmd if it's an empty string, because this will break pipelining mode
        #if cmd.strip() != '':
        #    cmd = shlex_quote(cmd)
        #cmd_parts = [env_string.strip(), shebang.replace("#!", "").strip(), cmd]
        #if arg_path is not None:
        #    cmd_parts.append(arg_path)
        #new_cmd = " ".join(cmd_parts)
        new_cmd = cmd
        return new_cmd

    # needed for? if checksums need to be crateds then until now: CRC/MD5 is possible with native tooling
    # I know HPE left something (Maintenance..) out the last few years.
    def checksum(self, path, python_interp):
        # The following test is fish-compliant.
        #
        # In the following test, each condition is a check and logical
        # comparison (or or and) that sets the rc value.  Every check is run so
        # the last check in the series to fail will be the rc that is
        # returned.
        #
        # If a check fails we error before invoking the hash functions because
        # hash functions may successfully take the hash of a directory on BSDs
        # (UFS filesystem?) which is not what the rest of the ansible code
        # expects
        #
        # If all of the available hashing methods fail we fail with an rc of
        # 0.  This logic is added to the end of the cmd at the bottom of this
        # function.

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
        ##shell_escaped_path = shlex_quote(path)
        ##test = "set rc flag; [ -r %(p)s ] %(shell_or)s set rc 2; [ -f %(p)s ] %(shell_or)s set rc 1; [ -d %(p)s ] %(shell_and)s set rc 3; %(i)s -V 2>/dev/null %(shell_or)s set rc 4; [ x\"$rc\" != \"xflag\" ] %(shell_and)s echo \"$rc  \"%(p)s %(shell_and)s exit 0" % dict(p=shell_escaped_path, i=python_interp, shell_and=self._SHELL_AND, shell_or=self._SHELL_OR)  # NOQA
        ##csums = [
        ##    u"({0} -c 'import hashlib; BLOCKSIZE = 65536; hasher = hashlib.sha1();{2}afile = open(\"'{1}'\", \"rb\"){2}buf = afile.read(BLOCKSIZE){2}while len(buf) > 0:{2}\thasher.update(buf){2}\tbuf = afile.read(BLOCKSIZE){2}afile.close(){2}print(hasher.hexdigest())' 2>/dev/null)".format(python_interp, shell_escaped_path, self._SHELL_EMBEDDED_PY_EOL),  # NOQA  Python > 2.4 (including python3)
        ##    u"({0} -c 'import sha; BLOCKSIZE = 65536; hasher = sha.sha();{2}afile = open(\"'{1}'\", \"rb\"){2}buf = afile.read(BLOCKSIZE){2}while len(buf) > 0:{2}\thasher.update(buf){2}\tbuf = afile.read(BLOCKSIZE){2}afile.close(){2}print(hasher.hexdigest())' 2>/dev/null)".format(python_interp, shell_escaped_path, self._SHELL_EMBEDDED_PY_EOL),  # NOQA  Python == 2.4
        ##]

        ##cmd = (" %s " % self._SHELL_OR).join(csums)
        ##cmd = "%s; %s %s (echo \'0  \'%s)" % (test, cmd, self._SHELL_OR, shell_escaped_path)
        ##return cmd
        return ''
