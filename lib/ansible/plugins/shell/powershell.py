# Copyright (c) 2014, Chris Church <chris@ninemoreminutes.com>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = """
name: powershell
version_added: historical
short_description: Windows PowerShell
description:
- The only option when using 'winrm' or 'psrp' as a connection plugin.
- Can also be used when using 'ssh' as a connection plugin and the C(DefaultShell) has been configured to PowerShell.
extends_documentation_fragment:
- shell_windows
"""

import base64
import os
import shlex
import ntpath

from ansible._internal._powershell import _script
from ansible.executor.powershell.module_manifest import _bootstrap_powershell_script
from ansible.module_utils.common.text.converters import to_text
from ansible.plugins.shell import ShellBase, _ShellCommand
from ansible.utils.display import Display


display = Display()

_common_args = ['PowerShell', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Unrestricted']


class ShellModule(ShellBase):

    # Common shell filenames that this plugin handles
    # Powershell is handled differently.  It's selected when winrm is the
    # connection
    COMPATIBLE_SHELLS = frozenset()  # type: frozenset[str]
    # Family of shells this has.  Must match the filename without extension
    SHELL_FAMILY = 'powershell'

    # We try catch as some connection plugins don't have a console (PSRP).
    _CONSOLE_ENCODING = "try { [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding } catch {}"
    _SHELL_REDIRECT_ALLNULL = '> $null'
    _SHELL_AND = ';'

    # Used by various parts of Ansible to do Windows specific changes
    _IS_WINDOWS = True

    # TODO: add binary module support

    def env_prefix(self, **kwargs):
        # powershell/winrm env handling is handled in the exec wrapper
        return ""

    def join_path(self, *args):
        # use normpath() to remove doubled slashed and convert forward to backslashes
        parts = [ntpath.normpath(arg) for arg in args]

        # Because ntpath.join treats any component that begins with a backslash as an absolute path,
        # we have to strip slashes from at least the beginning, otherwise join will ignore all previous
        # path components except for the drive.
        return ntpath.join(parts[0], *[part.strip('\\') for part in parts[1:]])

    def get_remote_filename(self, pathname):
        # powershell requires that script files end with .ps1
        base_name = os.path.basename(pathname.strip())
        name, ext = os.path.splitext(base_name.strip())
        if ext.lower() not in ['.ps1', '.exe']:
            return name + '.ps1'

        return base_name.strip()

    def path_has_trailing_slash(self, path):
        # Allow Windows paths to be specified using either slash.
        return path.endswith('/') or path.endswith('\\')

    def chmod(self, paths, mode):
        raise NotImplementedError('chmod is not implemented for Powershell')

    def chown(self, paths, user):
        raise NotImplementedError('chown is not implemented for Powershell')

    def set_user_facl(self, paths, user, mode):
        raise NotImplementedError('set_user_facl is not implemented for Powershell')

    def remove(self, path, recurse=False):
        path = _script.quote_pwsh_argument(path)
        script = f"Remove-Item {path} -Force"
        if recurse:
            script += " -Recurse"

        return self._encode_pwsh_script_as_command(script)

    def mkdtemp(
        self,
        basefile: str | None = None,
        system: bool = False,
        mode: int = 0o700,
        tmpdir: str | None = None,
    ) -> str:
        # This is not called in Ansible anymore but it is kept for backwards
        # compatibility in case other action plugins outside Ansible calls this.
        if not basefile:
            basefile = self.__class__._generate_temp_dir_name()
        basefile = _script.quote_pwsh_argument(basefile)
        basetmpdir = _script.quote_pwsh_argument(tmpdir if tmpdir else self.get_option('remote_tmp'))

        script = f"""
        {self._CONSOLE_ENCODING}
        $tmp_path = [System.Environment]::ExpandEnvironmentVariables({basetmpdir})
        $tmp = New-Item -Type Directory -Path $tmp_path -Name {basefile}
        Write-Output -InputObject $tmp.FullName
        """
        return self._encode_pwsh_script_as_command(script)

    def _mkdtemp2(
        self,
        basefile: str | None = None,
        system: bool = False,
        mode: int = 0o700,
        tmpdir: str | None = None,
    ) -> _ShellCommand:
        # Windows does not have an equivalent for the system temp files, so
        # the param is ignored
        if not basefile:
            basefile = self.__class__._generate_temp_dir_name()

        basetmpdir = tmpdir if tmpdir else self.get_option('remote_tmp')

        script, stdin = _bootstrap_powershell_script("powershell_mkdtemp.ps1", {
            'Directory': basetmpdir,
            'Name': basefile,
        })
        command = self._encode_pwsh_script_as_command(script)

        return _ShellCommand(
            command=command,
            input_data=stdin,
        )

    def expand_user(
        self,
        user_home_path: str,
        username: str = '',
    ) -> str:
        # This is not called in Ansible anymore but it is kept for backwards
        # compatibility in case other actions plugins outside Ansible called this.

        script = self._CONSOLE_ENCODING
        if user_home_path == '~':
            script += "; (Get-Location).Path"
        elif user_home_path.startswith('~\\'):
            script += f"; ((Get-Location).Path + {_script.quote_pwsh_argument(user_home_path[1:])})"
        else:
            script += f"; {_script.quote_pwsh_argument(user_home_path)}"

        return self._encode_pwsh_script_as_command(script)

    def _expand_user2(
        self,
        user_home_path: str,
        username: str = '',
    ) -> _ShellCommand:
        script, stdin = _bootstrap_powershell_script("powershell_expand_user.ps1", {
            'Path': user_home_path,
        })
        command = self._encode_pwsh_script_as_command(script)

        return _ShellCommand(
            command=command,
            input_data=stdin,
        )

    def exists(self, path):
        path = _script.quote_pwsh_argument(path)
        script = f"exit -not (Test-Path -LiteralPath {path})"

        return self._encode_pwsh_script_as_command(script)

    def checksum(self, path, *args, **kwargs):
        display.deprecated(
            msg="The `ShellModule.checksum` method is deprecated.",
            version="2.23",
            help_text="Use `ActionBase._execute_remote_stat()` instead.",
        )
        path = _script.quote_pwsh_argument(path)
        script = """
            If (Test-Path -PathType Leaf %(path)s)
            {
                $sp = new-object -TypeName System.Security.Cryptography.SHA1CryptoServiceProvider;
                $fp = [System.IO.File]::Open(%(path)s, [System.IO.Filemode]::Open, [System.IO.FileAccess]::Read);
                [System.BitConverter]::ToString($sp.ComputeHash($fp)).Replace("-", "").ToLower();
                $fp.Dispose();
            }
            ElseIf (Test-Path -PathType Container %(path)s)
            {
                Write-Output "3";
            }
            Else
            {
                Write-Output "1";
            }
        """ % dict(path=path)

        return self._encode_pwsh_script_as_command(script)

    def build_module_command(self, env_string, shebang, cmd, arg_path=None):
        # This will be called when executing modules not covered by the pwsh
        # exec wrapper. For example module replacer, binary or basic shell
        # modules.
        # The env_string is never used in PowerShell.
        cmd_parts = shlex.split(cmd, posix=False)

        if shebang and shebang.startswith('#!'):
            cmd = shebang[2:]
        elif not shebang:
            # The module is assumed to be a binary
            cmd = cmd_parts.pop(0)

        if arg_path:
            cmd_parts.append(arg_path)

        script = _script.build_pwsh_cmd_statement(cmd, cmd_parts)
        return self._encode_pwsh_script_as_command(script)

    def wrap_for_exec(self, cmd):
        super().wrap_for_exec(cmd)
        return '& %s; exit $LASTEXITCODE' % cmd

    def join(self, cmd_parts: list[str]) -> str:
        if not cmd_parts:
            return ""

        cmd = cmd_parts[0]
        args = []
        if len(cmd_parts) > 1:
            args = cmd_parts[1:]

        return _script.build_pwsh_cmd_statement(cmd, args)

    def quote(self, cmd: str) -> str:
        return _script.quote_pwsh_argument(cmd)

    def _encode_pwsh_script_as_command(self, script: str) -> str:
        """Wraps the provided PowerShell script as a command line string for the current shell plugin."""
        cmd_args = _script.get_pwsh_encoded_cmdline(script, override_execution_policy=True)
        return self.join(cmd_args)

    def _encode_script(self, script, as_list=False, strict_mode=True, preserve_rc=True):
        """Convert a PowerShell script to a single base64-encoded command."""
        # Needs a deprecation as ansible.windows uses this in the reboot plugin.
        display.deprecated(
            msg="The `PowerShell._encode_script` method is deprecated.",
            version="2.24",
            help_text="Contact plugin author to update their plugin to use an alternative method.",
        )
        script = to_text(script)

        if script == u'-':
            cmd_parts = _common_args + ['-Command', '-']

        else:
            if strict_mode:
                script = u'Set-StrictMode -Version Latest\r\n%s' % script
            # try to propagate exit code if present- won't work with begin/process/end-style scripts (ala put_file)
            # NB: the exit code returned may be incorrect in the case of a successful command followed by an invalid command
            if preserve_rc:
                script = u'%s\r\nIf (-not $?) { If (Get-Variable LASTEXITCODE -ErrorAction SilentlyContinue) { exit $LASTEXITCODE } Else { exit 1 } }\r\n'\
                    % script
            script = '\n'.join([x.strip() for x in script.splitlines() if x.strip()])
            encoded_script = to_text(base64.b64encode(script.encode('utf-16-le')), 'utf-8')
            cmd_parts = _common_args + ['-EncodedCommand', encoded_script]

        if as_list:
            return cmd_parts
        return ' '.join(cmd_parts)
