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
import ansible.constants as C
import time
import random

from ansible.module_utils.six import text_type
from ansible.module_utils.six.moves import shlex_quote

_USER_HOME_PATH_RE = re.compile(r'^~[_.A-Za-z0-9][-_.A-Za-z0-9]*$')


class ShellBase(object):

    def __init__(self):
        self.env = dict()
        if C.DEFAULT_MODULE_SET_LOCALE:
            module_locale = C.DEFAULT_MODULE_LANG or os.getenv('LANG', 'en_US.UTF-8')
            self.env.update(
                dict(
                    LANG=module_locale,
                    LC_ALL=module_locale,
                    LC_MESSAGES=module_locale,
                )
            )

    def env_prefix(self, **kwargs):
        env = self.env.copy()
        env.update(kwargs)
        return ' '.join(['%s=%s' % (k, shlex_quote(text_type(v))) for k, v in env.items()])

    def join_path(self, *args):
        return os.path.join(*args)

    # some shells (eg, powershell) are snooty about filenames/extensions, this lets the shell plugin have a say
    def get_remote_filename(self, pathname):
        base_name = os.path.basename(pathname.strip())
        return base_name.strip()

    def path_has_trailing_slash(self, path):
        return path.endswith('/')

    def chmod(self, paths, mode):
        cmd = ['chmod', mode]
        cmd.extend(paths)
        cmd = [shlex_quote(c) for c in cmd]

        return ' '.join(cmd)

    def chown(self, paths, user):
        cmd = ['chown', user]
        cmd.extend(paths)
        cmd = [shlex_quote(c) for c in cmd]

        return ' '.join(cmd)

    def set_user_facl(self, paths, user, mode):
        """Only sets acls for users as that's really all we need"""
        cmd = ['setfacl', '-m', 'u:%s:%s' % (user, mode)]
        cmd.extend(paths)
        cmd = [shlex_quote(c) for c in cmd]

        return ' '.join(cmd)

    def remove(self, path, recurse=False):
        path = shlex_quote(path)
        cmd = 'rm -f '
        if recurse:
            cmd += '-r '
        return cmd + "%s %s" % (path, self._SHELL_REDIRECT_ALLNULL)

    def exists(self, path):
        cmd = ['test', '-e', shlex_quote(path)]
        return ' '.join(cmd)

    def mkdtemp(self, basefile=None, system=False, mode=None, tmpdir=None):
        if not basefile:
            basefile = 'ansible-tmp-%s-%s' % (time.time(), random.randint(0, 2**48))

        # When system is specified we have to create this in a directory where
        # other users can read and access the temp directory.  This is because
        # we use system to create tmp dirs for unprivileged users who are
        # sudo'ing to a second unprivileged user.  The only dirctories where
        # that is standard are the tmp dirs, /tmp and /var/tmp.  So we only
        # allow one of those two locations if system=True.  However, users
        # might want to have some say over which of /tmp or /var/tmp is used
        # (because /tmp may be a tmpfs and want to conserve RAM or persist the
        # tmp files beyond a reboot.  So we check if the user set REMOTE_TMP
        # to somewhere in or below /var/tmp and if so use /var/tmp.  If
        # anything else we use /tmp (because /tmp is specified by POSIX nad
        # /var/tmp is not).

        if system:
            # FIXME: create 'system tmp dirs' config/var and check tmpdir is in those values to allow for /opt/tmp, etc
            if tmpdir.startswith('/var/tmp'):
                basetmpdir = '/var/tmp'
            else:
                basetmpdir = '/tmp'
        else:
            if tmpdir is None:
                basetmpdir = C.DEFAULT_REMOTE_TMP
            else:
                basetmpdir = tmpdir

        basetmp = self.join_path(basetmpdir, basefile)

        cmd = 'mkdir -p %s echo %s %s' % (self._SHELL_SUB_LEFT, basetmp, self._SHELL_SUB_RIGHT)
        cmd += ' %s echo %s=%s echo %s %s' % (self._SHELL_AND, basefile, self._SHELL_SUB_LEFT, basetmp, self._SHELL_SUB_RIGHT)

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
                # shlex_quote will make the shell return the string verbatim
                user_home_path = shlex_quote(user_home_path)
        return 'echo %s' % user_home_path

    def build_module_command(self, env_string, shebang, cmd, arg_path=None, rm_tmp=None):
        # don't quote the cmd if it's an empty string, because this will break pipelining mode
        if cmd.strip() != '':
            cmd = shlex_quote(cmd)

        cmd_parts = []
        if shebang:
            shebang = shebang.replace("#!", "").strip()
        else:
            shebang = ""
        cmd_parts.extend([env_string.strip(), shebang, cmd])
        if arg_path is not None:
            cmd_parts.append(arg_path)
        new_cmd = " ".join(cmd_parts)
        if rm_tmp:
            new_cmd = '%s; rm -rf "%s" %s' % (new_cmd, rm_tmp, self._SHELL_REDIRECT_ALLNULL)
        return new_cmd

    def append_command(self, cmd, cmd_to_append):
        """Append an additional command if supported by the shell"""

        if self._SHELL_AND:
            cmd += ' %s %s' % (self._SHELL_AND, cmd_to_append)

        return cmd

    def wrap_for_exec(self, cmd):
        """wrap script execution with any necessary decoration (eg '&' for quoted powershell script paths)"""
        return cmd
