# (c) 2014, Chris Church <chris@ninemoreminutes.com>
#
# This file is part of Ansible.
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import os
import re
import pipes
import ansible.constants as C

_USER_HOME_PATH_RE = re.compile(r'^~[_.A-Za-z0-9][-_.A-Za-z0-9]*$')

class ShellModule(object):

    # How to end lines in a python script one-liner
    _SHELL_EMBEDDED_PY_EOL = '\n'

    def env_prefix(self, **kwargs):
        '''Build command prefix with environment variables.'''
        env = dict(
            LANG     = C.DEFAULT_MODULE_LANG,
            LC_CTYPE = C.DEFAULT_MODULE_LANG,
        )
        env.update(kwargs)
        return ' '.join(['%s=%s' % (k, pipes.quote(unicode(v))) for k,v in env.items()])

    def join_path(self, *args):
        return os.path.join(*args)

    def path_has_trailing_slash(self, path):
        return path.endswith('/')

    def chmod(self, mode, path):
        path = pipes.quote(path)
        return 'chmod %s %s' % (mode, path)

    def remove(self, path, recurse=False):
        path = pipes.quote(path)
        if recurse:
            return "rm -rf %s >/dev/null 2>&1" % path
        else:
            return "rm -f %s >/dev/null 2>&1" % path

    def mkdtemp(self, basefile=None, system=False, mode=None):
        if not basefile:
            basefile = 'ansible-tmp-%s-%s' % (time.time(), random.randint(0, 2**48))
        basetmp = self.join_path(C.DEFAULT_REMOTE_TMP, basefile)
        if system and basetmp.startswith('$HOME'):
            basetmp = self.join_path('/tmp', basefile)
        cmd = 'mkdir -p %s' % basetmp
        if mode:
            cmd += ' && chmod %s %s' % (mode, basetmp)
        cmd += ' && echo %s' % basetmp
        return cmd

    def expand_user(self, user_home_path):
        ''' Return a command to expand tildes in a path

        It can be either "~" or "~username".  We use the POSIX definition of
        a username:
            http://pubs.opengroup.org/onlinepubs/000095399/basedefs/xbd_chap03.html#tag_03_426
            http://pubs.opengroup.org/onlinepubs/000095399/basedefs/xbd_chap03.html#tag_03_276
        '''

        # Check that the user_path to expand is safe
        if user_home_path != '~':
            if not _USER_HOME_PATH_RE.match(user_home_path):
                # pipes.quote will make the shell return the string verbatim
                user_home_path = pipes.quote(user_home_path)
        return 'echo %s' % user_home_path

    def checksum(self, path, python_interp):
        # The following test needs to be SH-compliant.  BASH-isms will
        # not work if /bin/sh points to a non-BASH shell.
        #
        # In the following test, each condition is a check and logical
        # comparison (|| or &&) that sets the rc value.  Every check is run so
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
        shell_escaped_path = pipes.quote(path)
        test = "rc=flag; [ -r %(p)s ] || rc=2; [ -f %(p)s ] || rc=1; [ -d %(p)s ] && rc=3; %(i)s -V 2>/dev/null || rc=4; [ x\"$rc\" != \"xflag\" ] && echo \"${rc}  \"%(p)s && exit 0" % dict(p=shell_escaped_path, i=python_interp)
        csums = [
            "({0} -c 'import hashlib; BLOCKSIZE = 65536; hasher = hashlib.sha1();{2}afile = open(\"'{1}'\", \"rb\"){2}buf = afile.read(BLOCKSIZE){2}while len(buf) > 0:{2}\thasher.update(buf){2}\tbuf = afile.read(BLOCKSIZE){2}afile.close(){2}print(hasher.hexdigest())' 2>/dev/null)".format(python_interp, shell_escaped_path, self._SHELL_EMBEDDED_PY_EOL),      # Python > 2.4 (including python3)
            "({0} -c 'import sha; BLOCKSIZE = 65536; hasher = sha.sha();{2}afile = open(\"'{1}'\", \"rb\"){2}buf = afile.read(BLOCKSIZE){2}while len(buf) > 0:{2}\thasher.update(buf){2}\tbuf = afile.read(BLOCKSIZE){2}afile.close(){2}print(hasher.hexdigest())' 2>/dev/null)".format(python_interp, shell_escaped_path, self._SHELL_EMBEDDED_PY_EOL),      # Python == 2.4
        ]

        cmd = " || ".join(csums)
        cmd = "%s; %s || (echo \'0  \'%s)" % (test, cmd, shell_escaped_path)
        return cmd

    def build_module_command(self, env_string, shebang, cmd, rm_tmp=None):
        cmd_parts = [env_string.strip(), shebang.replace("#!", "").strip(), cmd]
        new_cmd = " ".join(cmd_parts)
        if rm_tmp:
            new_cmd = '%s; rm -rf %s >/dev/null 2>&1' % (new_cmd, rm_tmp)
        return new_cmd
