# (c) 2016 RedHat
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import re
import pipes
import ansible.constants as C
import time
import random

from ansible.compat.six import text_type

_USER_HOME_PATH_RE = re.compile(r'^~[_.A-Za-z0-9][-_.A-Za-z0-9]*$')

class ShellBase(object):

    def __init__(self):
        self.env = dict(
            LANG        = C.DEFAULT_MODULE_LANG,
            LC_ALL      = C.DEFAULT_MODULE_LANG,
            LC_MESSAGES = C.DEFAULT_MODULE_LANG,
        )

    def env_prefix(self, **kwargs):
        env = self.env.copy()
        env.update(kwargs)
        return ' '.join(['%s=%s' % (k, pipes.quote(text_type(v))) for k,v in env.items()])

    def join_path(self, *args):
        return os.path.join(*args)

    # some shells (eg, powershell) are snooty about filenames/extensions, this lets the shell plugin have a say
    def get_remote_filename(self, base_name):
        return base_name.strip()

    def path_has_trailing_slash(self, path):
        return path.endswith('/')

    def chmod(self, mode, path):
        path = pipes.quote(path)
        return 'chmod %s %s' % (mode, path)

    def remove(self, path, recurse=False):
        path = pipes.quote(path)
        cmd = 'rm -f '
        if recurse:
            cmd += '-r '
        return cmd + "%s %s" % (path, self._SHELL_REDIRECT_ALLNULL)

    def mkdtemp(self, basefile=None, system=False, mode=None):
        if not basefile:
            basefile = 'ansible-tmp-%s-%s' % (time.time(), random.randint(0, 2**48))
        basetmp = self.join_path(C.DEFAULT_REMOTE_TMP, basefile)
        if system and (basetmp.startswith('$HOME') or basetmp.startswith('~/')):
            basetmp = self.join_path('/tmp', basefile)
        cmd = 'mkdir -p %s echo %s %s' % (self._SHELL_SUB_LEFT, basetmp, self._SHELL_SUB_RIGHT)
        cmd += ' %s echo %s echo %s %s' % (self._SHELL_AND, self._SHELL_SUB_LEFT, basetmp, self._SHELL_SUB_RIGHT)

        # change the umask in a subshell to achieve the desired mode
        # also for directories created with `mkdir -p`
        if mode:
            tmp_umask = 0o777 & ~mode
            cmd = '%s umask %o %s %s %s' % (self._SHELL_GROUP_LEFT, tmp_umask, self._SHELL_AND, cmd, self._SHELL_GROUP_RIGHT)

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

    def build_module_command(self, env_string, shebang, cmd, arg_path=None, rm_tmp=None):
        # don't quote the cmd if it's an empty string, because this will break pipelining mode
        if cmd.strip() != '':
            cmd = pipes.quote(cmd)
        cmd_parts = [env_string.strip(), shebang.replace("#!", "").strip(), cmd]
        if arg_path is not None:
            cmd_parts.append(arg_path)
        new_cmd = " ".join(cmd_parts)
        if rm_tmp:
            new_cmd = '%s; rm -rf "%s" %s' % (new_cmd, rm_tmp, self._SHELL_REDIRECT_ALLNULL)
        return new_cmd
