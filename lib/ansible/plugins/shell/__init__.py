# (c) 2016 RedHat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import dataclasses
import re
import shlex
import uuid

from os.path import isabs, basename, join as path_join

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
        if not all(isabs(d) for d in normalized_paths):
            raise AnsibleError(f'The configured system_tmpdirs contains a relative path: {normalized_paths}. Allsystem_tmpdirs must be absolute')

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
        return f'ansible-tmp-{uuid.uuid4()}'

    def env_prefix(self, **kwargs):
        return ' '.join([f'{k}={self.quote(str(v))}' for k, v in kwargs.items()])

    def join_path(self, *args):
        return path_join(*args)

    # some shells (eg, powershell) are snooty about filenames/extensions, this lets the shell plugin have a say
    def get_remote_filename(self, pathname):
        return basename(pathname.strip())

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
        cmd = ['setfacl', '-m', f'u:{user}:{mode}']
        cmd.extend(paths)
        return self.join(cmd)

    def remove(self, path, recurse=False):
        cmd = ['rm', '-f']
        if recurse:
            cmd.append('-r')
        cmd.extend([self.quote(path), self._SHELL_REDIRECT_ALLNULL])
        return ' '.join(cmd)

    def exists(self, path):
        return ' '.join(['test', '-e', self.quote(path)])

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
        cmd = [
            'mkdir', '-p', self._SHELL_SUB_LEFT, 'echo', basetmpdir, self._SHELL_SUB_RIGHT, self._SHELL_AND,
            'mkdir', self._SHELL_SUB_LEFT, 'echo', basetmp, self._SHELL_SUB_RIGHT, self._SHELL_AND,
            f'echo {basefile}={self._SHELL_SUB_LEFT} echo {basetmp} {self._SHELL_SUB_RIGHT}'
        ]

        # change the umask in a subshell to achieve the desired mode
        # also for directories created with `mkdir -p`
        if mode:
            cmd = [self._SHELL_GROUP_LEFT, 'umask', f'{0o777 & ~mode:o}', self._SHELL_AND] + cmd + [self._SHELL_GROUP_RIGHT]

        return ' '.join(cmd)

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

        return f'echo {user_home_path}'

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
        return f'echo {self._SHELL_SUB_LEFT}pwd{self._SHELL_SUB_RIGHT}'

    def build_module_command(self, env_string, shebang, cmd, arg_path=None):
        if shebang is None:
            shebang = ''

        cmd_parts = [
            env_string,
            shebang.removeprefix('#!'),
            cmd,
            arg_path,
        ]
        return self.join([raw_cmd_part.strip() for raw_cmd_part in cmd_parts if raw_cmd_part])

    def append_command(self, cmd, cmd_to_append):
        """Append an additional command if supported by the shell"""

        if self._SHELL_AND:
            cmd = ' '.join([cmd, self._SHELL_AND, cmd_to_append])

        return cmd

    def wrap_for_exec(self, cmd):
        """wrap script execution with any necessary decoration (eg '&' for quoted powershell script paths)"""
        display.deprecated(
            msg='The Shell.wrap_for_exec method is deprecated.',
            help_text="Contact plugin author to update their plugin to not use this method.",
            version='2.24',
        )
        return cmd

    def quote(self, cmd: str) -> str:
        """Returns a shell-escaped string that can be safely used as one token in a shell command line"""
        return shlex.quote(cmd)

    def join(self, cmd_parts: list[str]) -> str:
        """Returns a shell-escaped string from a list that can be safely used in a shell command line"""
        return shlex.join(cmd_parts)
