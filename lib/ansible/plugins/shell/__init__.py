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
from __future__ import annotations

import dataclasses
import os
import os.path
import re
import secrets
import shlex
import time

from ansible.errors import AnsibleError
from ansible.module_utils.common.text.converters import to_native
from ansible.plugins import AnsiblePlugin
from ansible.utils.display import Display

display = Display()

_USER_HOME_PATH_RE = re.compile(r'^~[_.A-Za-z0-9][-_.A-Za-z0-9]*$')


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class _ShellCommand:
    """Internal type returned by shell subsystems that may require both an execution payload and a command (eg powershell)."""
    command: str
    input_data: bytes | None = None


class ShellBase(AnsiblePlugin):
    def __init__(self):

        super(ShellBase, self).__init__()

        # Not used but here for backwards compatibility.
        # ansible.posix.fish uses (but does not actually use) this value.
        # https://github.com/ansible-collections/ansible.posix/blob/f41f08e9e3d3129e709e122540b5ae6bc19932be/plugins/shell/fish.py#L38-L39
        self.env = {}
        self.tmpdir = None
        self.executable = None

    def _normalize_system_tmpdirs(self):
        # Normalize the tmp directory strings. We don't use expanduser/expandvars because those
        # can vary between remote user and become user.  Therefore the safest practice will be for
        # this to always be specified as full paths)
        normalized_paths = [d.rstrip('/') for d in self.get_option('system_tmpdirs')]

        # Make sure all system_tmpdirs are absolute otherwise they'd be relative to the login dir
        # which is almost certainly going to fail in a cornercase.
        if not all(os.path.isabs(d) for d in normalized_paths):
            raise AnsibleError('The configured system_tmpdirs contains a relative path: {0}. All'
                               ' system_tmpdirs must be absolute'.format(to_native(normalized_paths)))

        self.set_option('system_tmpdirs', normalized_paths)

    def set_options(self, task_keys=None, var_options=None, direct=None):

        super(ShellBase, self).set_options(task_keys=task_keys, var_options=var_options, direct=direct)

        # We can remove the try: except in the future when we make ShellBase a proper subset of
        # *all* shells.  Right now powershell and third party shells which do not use the
        # shell_common documentation fragment (and so do not have system_tmpdirs) will fail
        try:
            self._normalize_system_tmpdirs()
        except KeyError:
            pass

    @staticmethod
    def _generate_temp_dir_name():
        return 'ansible-tmp-%s-%s-%s' % (time.time(), os.getpid(), secrets.randbelow(2**48))

    def env_prefix(self, **kwargs):
        return ' '.join(['%s=%s' % (k, self.quote(str(v))) for k, v in kwargs.items()])

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
        return self.join(cmd)

    def chown(self, paths, user):
        cmd = ['chown', user]
        cmd.extend(paths)
        return self.join(cmd)

    def chgrp(self, paths, group):
        cmd = ['chgrp', group]
        cmd.extend(paths)
        return self.join(cmd)

    def set_user_facl(self, paths, user, mode):
        """Only sets acls for users as that's really all we need"""
        cmd = ['setfacl', '-m', 'u:%s:%s' % (user, mode)]
        cmd.extend(paths)
        return self.join(cmd)

    def remove(self, path, recurse=False):
        path = self.quote(path)
        cmd = 'rm -f '
        if recurse:
            cmd += '-r '
        return cmd + "%s %s" % (path, self._SHELL_REDIRECT_ALLNULL)

    def exists(self, path):
        cmd = ['test', '-e', self.quote(path)]
        return ' '.join(cmd)

    def mkdtemp(
        self,
        basefile: str | None = None,
        system: bool = False,
        mode: int = 0o700,
        tmpdir: str | None = None,
    ) -> str:
        if not basefile:
            basefile = self.__class__._generate_temp_dir_name()

        # When system is specified we have to create this in a directory where
        # other users can read and access the tmp directory.
        # This is because we use system to create tmp dirs for unprivileged users who are
        # sudo'ing to a second unprivileged user.
        # The 'system_tmpdirs' setting defines directories we can use for this purpose
        # the default are, /tmp and /var/tmp.
        # So we only allow one of those locations if system=True, using the
        # passed in tmpdir if it is valid or the first one from the setting if not.

        if system:
            if tmpdir:
                tmpdir = tmpdir.rstrip('/')

            if tmpdir in self.get_option('system_tmpdirs'):
                basetmpdir = tmpdir
            else:
                basetmpdir = self.get_option('system_tmpdirs')[0]
        else:
            if tmpdir is None:
                basetmpdir = self.get_option('remote_tmp')
            else:
                basetmpdir = tmpdir

        basetmp = self.join_path(basetmpdir, basefile)

        # use mkdir -p to ensure parents exist, but mkdir fullpath to ensure last one is created by us
        cmd = 'mkdir -p %s echo %s %s' % (self._SHELL_SUB_LEFT, basetmpdir, self._SHELL_SUB_RIGHT)
        cmd += '%s mkdir %s echo %s %s' % (self._SHELL_AND, self._SHELL_SUB_LEFT, basetmp, self._SHELL_SUB_RIGHT)
        cmd += ' %s echo %s=%s echo %s %s' % (self._SHELL_AND, basefile, self._SHELL_SUB_LEFT, basetmp, self._SHELL_SUB_RIGHT)

        # change the umask in a subshell to achieve the desired mode
        # also for directories created with `mkdir -p`
        if mode:
            tmp_umask = 0o777 & ~mode
            cmd = '%s umask %o %s %s %s' % (self._SHELL_GROUP_LEFT, tmp_umask, self._SHELL_AND, cmd, self._SHELL_GROUP_RIGHT)

        return cmd

    def _mkdtemp2(
        self,
        basefile: str | None = None,
        system: bool = False,
        mode: int = 0o700,
        tmpdir: str | None = None,
    ) -> _ShellCommand:
        """Gets command info to create a temporary directory.

        This is an internal API that should not be used publicly.

        :args basefile: The base name of the temporary directory.
        :args system: If True, create the directory in a system-wide location.
        :args mode: The permissions mode for the directory.
        :args tmpdir: The directory in which to create the temporary directory.
        :returns: The shell command to run to create the temp directory.
        """
        cmd = self.mkdtemp(basefile=basefile, system=system, mode=mode, tmpdir=tmpdir)
        return _ShellCommand(command=cmd, input_data=None)

    def expand_user(
        self,
        user_home_path: str,
        username: str = '',
    ) -> str:
        """ Return a command to expand tildes in a path

        It can be either "~" or "~username". We just ignore $HOME
        We use the POSIX definition of a username:
            http://pubs.opengroup.org/onlinepubs/000095399/basedefs/xbd_chap03.html#tag_03_426
            http://pubs.opengroup.org/onlinepubs/000095399/basedefs/xbd_chap03.html#tag_03_276

            Falls back to 'current working directory' as we assume 'home is where the remote user ends up'
        """

        # Check that the user_path to expand is safe
        if user_home_path != '~':
            if not _USER_HOME_PATH_RE.match(user_home_path):
                user_home_path = self.quote(user_home_path)
        elif username:
            # if present the user name is appended to resolve "that user's home"
            user_home_path += username

        return 'echo %s' % user_home_path

    def _expand_user2(
        self,
        user_home_path: str,
        username: str = '',
    ) -> _ShellCommand:
        """Gets command to expand user path.

        This is an internal API that should not be used publicly.

        :args user_home_path: The path to expand.
        :args username: The username to use for expansion.
        :returns: The shell command to run to get the expanded user path.
        """
        cmd = self.expand_user(user_home_path, username=username)
        return _ShellCommand(command=cmd, input_data=None)

    def pwd(self):
        """Return the working directory after connecting"""
        return 'echo %spwd%s' % (self._SHELL_SUB_LEFT, self._SHELL_SUB_RIGHT)

    def build_module_command(self, env_string, shebang, cmd, arg_path=None):
        env_string = env_string.strip()
        if env_string:
            env_string += ' '

        if shebang is None:
            shebang = ''

        cmd_parts = [
            shebang.removeprefix('#!').strip(),
            cmd.strip(),
            arg_path,
        ]

        cleaned_up_cmd = self.join(
            stripped_cmd_part for raw_cmd_part in cmd_parts
            if raw_cmd_part and (stripped_cmd_part := raw_cmd_part.strip())
        )
        return ''.join((env_string, cleaned_up_cmd))

    def append_command(self, cmd, cmd_to_append):
        """Append an additional command if supported by the shell"""

        if self._SHELL_AND:
            cmd += ' %s %s' % (self._SHELL_AND, cmd_to_append)

        return cmd

    def wrap_for_exec(self, cmd):
        """wrap script execution with any necessary decoration (eg '&' for quoted powershell script paths)"""
        display.deprecated(
            msg='The Shell.wrap_for_exec method is deprecated.',
            help_text="Contact plugin author to update their plugin to not use this method.",
            version='2.24',
        )
        return cmd

    def quote(self, cmd):
        """Returns a shell-escaped string that can be safely used as one token in a shell command line"""
        return shlex.quote(cmd)

    def join(self, cmd_parts):
        """Returns a shell-escaped string from a list that can be safely used in a shell command line"""
        return shlex.join(cmd_parts)
