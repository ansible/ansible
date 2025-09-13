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
import re
import shlex
import xml.etree.ElementTree as ET
import ntpath

from ansible.executor.powershell.module_manifest import _bootstrap_powershell_script, _get_powershell_script
from ansible.module_utils.common.text.converters import to_bytes, to_text
from ansible.plugins.shell import ShellBase, _ShellCommand
from ansible.utils.display import Display


display = Display()

# This is weird, we are matching on byte sequences that match the utf-16-be
# matches for '_x(a-fA-F0-9){4}_'. The \x00 and {4} will match the hex sequence
# when it is encoded as utf-16-be byte sequence.
_STRING_DESERIAL_FIND = re.compile(rb"\x00_\x00x((?:\x00[a-fA-F0-9]){4})\x00_")

_common_args = ['PowerShell', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Unrestricted']


def _replace_stderr_clixml(stderr: bytes) -> bytes:
    """Replace CLIXML with stderr data.

    Tries to replace an embedded CLIXML string with the actual stderr data. If
    it fails to parse the CLIXML data, it will return the original data. This
    will replace any line inside the stderr string that contains a valid CLIXML
    sequence.

    :param bytes stderr: The stderr to try and decode.

    :returns: The stderr with the decoded CLIXML data or the original data.
    """
    clixml_header = b"#< CLIXML\r\n"

    if stderr.find(clixml_header) == -1:
        return stderr

    lines: list[bytes] = []
    is_clixml = False
    for line in stderr.splitlines(True):
        if is_clixml:
            is_clixml = False

            # If the line does not contain the closing CLIXML tag, we just
            # add the found header line and this line without trying to parse.
            end_idx = line.find(b"</Objs>")
            if end_idx == -1:
                lines.append(clixml_header)
                lines.append(line)
                continue

            clixml = line[: end_idx + 7]
            remaining = line[end_idx + 7 :]

            # While we expect the stderr to be UTF-8 encoded, we fallback to
            # the most common "ANSI" codepage used by Windows cp437 if it is
            # not valid UTF-8.
            try:
                clixml.decode("utf-8")
            except UnicodeDecodeError:
                # cp427 can decode any sequence and once we have the string, we
                # can encode any cp427 chars to UTF-8.
                clixml_text = clixml.decode("cp437")
                clixml = clixml_text.encode("utf-8")

            try:
                decoded_clixml = _parse_clixml(clixml)
                lines.append(decoded_clixml)
                if remaining:
                    lines.append(remaining)

            except Exception:
                # Any errors and we just add the original CLIXML header and
                # line back in.
                lines.append(clixml_header)
                lines.append(line)

        elif line == clixml_header:
            # The next line should contain the full CLIXML data.
            is_clixml = True

        else:
            lines.append(line)

    # This should never happen but if there was a CLIXML header without a newline
    # following it, we need to add it back.
    if is_clixml:
        lines.append(clixml_header)

    return b"".join(lines)


def _parse_clixml(data: bytes, stream: str = "Error") -> bytes:
    """
    Takes a byte string like '#< CLIXML\r\n<Objs...' and extracts the stream
    message encoded in the XML data. CLIXML is used by PowerShell to encode
    multiple objects in stderr.
    """
    lines: list[str] = []

    # A serialized string will serialize control chars and surrogate pairs as
    # _xDDDD_ values where DDDD is the hex representation of a big endian
    # UTF-16 code unit. As a surrogate pair uses 2 UTF-16 code units, we need
    # to operate our text replacement on the utf-16-be byte encoding of the raw
    # text. This allows us to replace the _xDDDD_ values with the actual byte
    # values and then decode that back to a string from the utf-16-be bytes.
    def rplcr(matchobj: re.Match) -> bytes:
        match_hex = matchobj.group(1)
        hex_string = match_hex.decode("utf-16-be")
        return base64.b16decode(hex_string.upper())

    # There are some scenarios where the stderr contains a nested CLIXML element like
    # '<# CLIXML\r\n<# CLIXML\r\n<Objs>...</Objs><Objs>...</Objs>'.
    # Parse each individual <Objs> element and add the error strings to our stderr list.
    # https://github.com/ansible/ansible/issues/69550
    while data:
        start_idx = data.find(b"<Objs ")
        end_idx = data.find(b"</Objs>")
        if start_idx == -1 or end_idx == -1:
            break

        end_idx += 7
        current_element = data[start_idx:end_idx]
        data = data[end_idx:]

        clixml = ET.fromstring(current_element)
        namespace_match = re.match(r'{(.*)}', clixml.tag)
        namespace = f"{{{namespace_match.group(1)}}}" if namespace_match else ""

        entries = clixml.findall("./%sS" % namespace)
        if not entries:
            continue

        # If this is a new CLIXML element, add a newline to separate the messages.
        if lines:
            lines.append("\r\n")

        for string_entry in entries:
            actual_stream = string_entry.attrib.get('S', None)
            if actual_stream != stream:
                continue

            b_line = (string_entry.text or "").encode("utf-16-be")
            b_escaped = re.sub(_STRING_DESERIAL_FIND, rplcr, b_line)

            lines.append(b_escaped.decode("utf-16-be", errors="surrogatepass"))

    return to_bytes(''.join(lines), errors="surrogatepass")


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
        quoted_path = self._escape(path)
        if recurse:
            return self._encode_script("""Remove-Item '%s' -Force -Recurse;""" % quoted_path)
        else:
            return self._encode_script("""Remove-Item '%s' -Force;""" % quoted_path)

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
        basetmpdir = self._escape(tmpdir if tmpdir else self.get_option('remote_tmp'))

        script = f"""
        {self._CONSOLE_ENCODING}
        $tmp_path = [System.Environment]::ExpandEnvironmentVariables('{basetmpdir}')
        $tmp = New-Item -Type Directory -Path $tmp_path -Name '{basefile}'
        Write-Output -InputObject $tmp.FullName
        """
        return self._encode_script(script.strip())

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

        return _ShellCommand(
            command=self._encode_script(script),
            input_data=stdin,
        )

    def expand_user(
        self,
        user_home_path: str,
        username: str = '',
    ) -> str:
        # This is not called in Ansible anymore but it is kept for backwards
        # compatibility in case other actions plugins outside Ansible called this.
        if user_home_path == '~':
            script = 'Write-Output (Get-Location).Path'
        elif user_home_path.startswith('~\\'):
            script = "Write-Output ((Get-Location).Path + '%s')" % self._escape(user_home_path[1:])
        else:
            script = "Write-Output '%s'" % self._escape(user_home_path)
        return self._encode_script(f"{self._CONSOLE_ENCODING}; {script}")

    def _expand_user2(
        self,
        user_home_path: str,
        username: str = '',
    ) -> _ShellCommand:
        script, stdin = _bootstrap_powershell_script("powershell_expand_user.ps1", {
            'Path': user_home_path,
        })

        return _ShellCommand(
            command=self._encode_script(script),
            input_data=stdin,
        )

    def exists(self, path):
        path = self._escape(path)
        script = """
            If (Test-Path '%s')
            {
                $res = 0;
            }
            Else
            {
                $res = 1;
            }
            Write-Output '$res';
            Exit $res;
         """ % path
        return self._encode_script(script)

    def checksum(self, path, *args, **kwargs):
        display.deprecated(
            msg="The `ShellModule.checksum` method is deprecated.",
            version="2.23",
            help_text="Use `ActionBase._execute_remote_stat()` instead.",
        )
        path = self._escape(path)
        script = """
            If (Test-Path -PathType Leaf '%(path)s')
            {
                $sp = new-object -TypeName System.Security.Cryptography.SHA1CryptoServiceProvider;
                $fp = [System.IO.File]::Open('%(path)s', [System.IO.Filemode]::Open, [System.IO.FileAccess]::Read);
                [System.BitConverter]::ToString($sp.ComputeHash($fp)).Replace("-", "").ToLower();
                $fp.Dispose();
            }
            ElseIf (Test-Path -PathType Container '%(path)s')
            {
                Write-Output "3";
            }
            Else
            {
                Write-Output "1";
            }
        """ % dict(path=path)
        return self._encode_script(script)

    def build_module_command(self, env_string, shebang, cmd, arg_path=None):
        bootstrap_wrapper = _get_powershell_script("bootstrap_wrapper.ps1")

        # pipelining bypass
        if cmd == '':
            return self._encode_script(script=bootstrap_wrapper, strict_mode=False, preserve_rc=False)

        # non-pipelining

        cmd_parts = shlex.split(cmd, posix=False)
        cmd_parts = list(map(to_text, cmd_parts))
        if shebang and shebang.lower() == '#!powershell':
            if arg_path:
                # Running a module without the exec_wrapper and with an argument
                # file.
                script_path = cmd_parts[0]
                if not script_path.lower().endswith('.ps1'):
                    script_path += '.ps1'

                cmd_parts.insert(0, '-File')
                cmd_parts[1] = f'"{script_path}"'
                if arg_path:
                    cmd_parts.append(f'"{arg_path}"')

                wrapper_cmd = " ".join(_common_args + cmd_parts)
                return wrapper_cmd

            else:
                # Running a module with ANSIBLE_KEEP_REMOTE_FILES=true, the script
                # arg is actually the input manifest JSON to provide to the bootstrap
                # wrapper.
                wrapper_cmd = "type " + cmd_parts[0] + " | " + self._encode_script(script=bootstrap_wrapper, strict_mode=False, preserve_rc=False)
                return wrapper_cmd

        elif shebang and shebang.startswith('#!'):
            cmd_parts.insert(0, shebang[2:])
        elif not shebang:
            # The module is assumed to be a binary
            cmd_parts.append(arg_path)
        script = """
            Try
            {
                %s
                %s
            }
            Catch
            {
                $_obj = @{ failed = $true }
                If ($_.Exception.GetType)
                {
                    $_obj.Add('msg', $_.Exception.Message)
                }
                Else
                {
                    $_obj.Add('msg', $_.ToString())
                }
                If ($_.InvocationInfo.PositionMessage)
                {
                    $_obj.Add('exception', $_.InvocationInfo.PositionMessage)
                }
                ElseIf ($_.ScriptStackTrace)
                {
                    $_obj.Add('exception', $_.ScriptStackTrace)
                }
                Try
                {
                    $_obj.Add('error_record', ($_ | ConvertTo-Json | ConvertFrom-Json))
                }
                Catch
                {
                }
                Echo $_obj | ConvertTo-Json -Compress -Depth 99
                Exit 1
            }
        """ % (env_string, ' '.join(cmd_parts))
        return self._encode_script(script, preserve_rc=False)

    def wrap_for_exec(self, cmd):
        super().wrap_for_exec(cmd)
        return '& %s; exit $LASTEXITCODE' % cmd

    def _escape(self, value):
        """Return value escaped for use in PowerShell single quotes."""
        # There are 5 chars that need to be escaped in a single quote.
        # https://github.com/PowerShell/PowerShell/blob/b7cb335f03fe2992d0cbd61699de9d9aafa1d7c1/src/System.Management.Automation/engine/parser/CharTraits.cs#L265-L272
        return re.compile(u"(['\u2018\u2019\u201a\u201b])").sub(u'\\1\\1', value)

    def _encode_script(self, script, as_list=False, strict_mode=True, preserve_rc=True):
        """Convert a PowerShell script to a single base64-encoded command."""
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
