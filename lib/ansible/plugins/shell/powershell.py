# Copyright (c) 2014, Chris Church <chris@ninemoreminutes.com>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
name: powershell
plugin_type: shell
version_added: historical
short_description: Windows PowerShell
description:
- The only option when using 'winrm' or 'psrp' as a connection plugin.
- Can also be used when using 'ssh' as a connection plugin and the C(DefaultShell) has been configured to PowerShell.
extends_documentation_fragment:
- shell_windows
'''

import base64
import os
import re
import shlex
import pkgutil
import xml.etree.ElementTree as ET
import ntpath

from ansible.module_utils._text import to_bytes, to_text
from ansible.plugins.shell import ShellBase


_common_args = ['PowerShell', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Unrestricted']


def _parse_clixml(data, stream="Error"):
    """
    Takes a byte string like '#< CLIXML\r\n<Objs...' and extracts the stream
    message encoded in the XML data. CLIXML is used by PowerShell to encode
    multiple objects in stderr.
    """
    lines = []

    # There are some scenarios where the stderr contains a nested CLIXML element like
    # '<# CLIXML\r\n<# CLIXML\r\n<Objs>...</Objs><Objs>...</Objs>'.
    # Parse each individual <Objs> element and add the error strings to our stderr list.
    # https://github.com/ansible/ansible/issues/69550
    while data:
        end_idx = data.find(b"</Objs>") + 7
        current_element = data[data.find(b"<Objs "):end_idx]
        data = data[end_idx:]

        clixml = ET.fromstring(current_element)
        namespace_match = re.match(r'{(.*)}', clixml.tag)
        namespace = "{%s}" % namespace_match.group(1) if namespace_match else ""

        strings = clixml.findall("./%sS" % namespace)
        lines.extend([e.text.replace('_x000D__x000A_', '') for e in strings if e.attrib.get('S') == stream])

    return to_bytes('\r\n'.join(lines))


class ShellModule(ShellBase):

    # Common shell filenames that this plugin handles
    # Powershell is handled differently.  It's selected when winrm is the
    # connection
    COMPATIBLE_SHELLS = frozenset()
    # Family of shells this has.  Must match the filename without extension
    SHELL_FAMILY = 'powershell'

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
        parts = [ntpath.normpath(self._unquote(arg)) for arg in args]

        # Becuase ntpath.join treats any component that begins with a backslash as an absolute path,
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
        path = self._unquote(path)
        return path.endswith('/') or path.endswith('\\')

    def chmod(self, paths, mode):
        raise NotImplementedError('chmod is not implemented for Powershell')

    def chown(self, paths, user):
        raise NotImplementedError('chown is not implemented for Powershell')

    def set_user_facl(self, paths, user, mode):
        raise NotImplementedError('set_user_facl is not implemented for Powershell')

    def remove(self, path, recurse=False):
        path = self._escape(self._unquote(path))
        if recurse:
            return self._encode_script('''Remove-Item '%s' -Force -Recurse;''' % path)
        else:
            return self._encode_script('''Remove-Item '%s' -Force;''' % path)

    def mkdtemp(self, basefile=None, system=False, mode=None, tmpdir=None):
        # Windows does not have an equivalent for the system temp files, so
        # the param is ignored
        if not basefile:
            basefile = self.__class__._generate_temp_dir_name()
        basefile = self._escape(self._unquote(basefile))
        basetmpdir = tmpdir if tmpdir else self.get_option('remote_tmp')

        script = '''
        $tmp_path = [System.Environment]::ExpandEnvironmentVariables('%s')
        $tmp = New-Item -Type Directory -Path $tmp_path -Name '%s'
        Write-Output -InputObject $tmp.FullName
        ''' % (basetmpdir, basefile)
        return self._encode_script(script.strip())

    def expand_user(self, user_home_path, username=''):
        # PowerShell only supports "~" (not "~username").  Resolve-Path ~ does
        # not seem to work remotely, though by default we are always starting
        # in the user's home directory.
        user_home_path = self._unquote(user_home_path)
        if user_home_path == '~':
            script = 'Write-Output (Get-Location).Path'
        elif user_home_path.startswith('~\\'):
            script = "Write-Output ((Get-Location).Path + '%s')" % self._escape(user_home_path[1:])
        else:
            script = "Write-Output '%s'" % self._escape(user_home_path)
        return self._encode_script(script)

    def exists(self, path):
        path = self._escape(self._unquote(path))
        script = '''
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
         ''' % path
        return self._encode_script(script)

    def checksum(self, path, *args, **kwargs):
        path = self._escape(self._unquote(path))
        script = '''
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
        ''' % dict(path=path)
        return self._encode_script(script)

    def build_module_command(self, env_string, shebang, cmd, arg_path=None):
        bootstrap_wrapper = pkgutil.get_data("ansible.executor.powershell", "bootstrap_wrapper.ps1")

        # pipelining bypass
        if cmd == '':
            return self._encode_script(script=bootstrap_wrapper, strict_mode=False, preserve_rc=False)

        # non-pipelining

        cmd_parts = shlex.split(cmd, posix=False)
        cmd_parts = list(map(to_text, cmd_parts))
        if shebang and shebang.lower() == '#!powershell':
            if not self._unquote(cmd_parts[0]).lower().endswith('.ps1'):
                # we're running a module via the bootstrap wrapper
                cmd_parts[0] = '"%s.ps1"' % self._unquote(cmd_parts[0])
            wrapper_cmd = "type " + cmd_parts[0] + " | " + self._encode_script(script=bootstrap_wrapper, strict_mode=False, preserve_rc=False)
            return wrapper_cmd
        elif shebang and shebang.startswith('#!'):
            cmd_parts.insert(0, shebang[2:])
        elif not shebang:
            # The module is assumed to be a binary
            cmd_parts[0] = self._unquote(cmd_parts[0])
            cmd_parts.append(arg_path)
        script = '''
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
        ''' % (env_string, ' '.join(cmd_parts))
        return self._encode_script(script, preserve_rc=False)

    def wrap_for_exec(self, cmd):
        return '& %s; exit $LASTEXITCODE' % cmd

    def _unquote(self, value):
        '''Remove any matching quotes that wrap the given value.'''
        value = to_text(value or '')
        m = re.match(r'^\s*?\'(.*?)\'\s*?$', value)
        if m:
            return m.group(1)
        m = re.match(r'^\s*?"(.*?)"\s*?$', value)
        if m:
            return m.group(1)
        return value

    def _escape(self, value):
        '''Return value escaped for use in PowerShell single quotes.'''
        # There are 5 chars that need to be escaped in a single quote.
        # https://github.com/PowerShell/PowerShell/blob/b7cb335f03fe2992d0cbd61699de9d9aafa1d7c1/src/System.Management.Automation/engine/parser/CharTraits.cs#L265-L272
        return re.compile(u"(['\u2018\u2019\u201a\u201b])").sub(u'\\1\\1', value)

    def _encode_script(self, script, as_list=False, strict_mode=True, preserve_rc=True):
        '''Convert a PowerShell script to a single base64-encoded command.'''
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
