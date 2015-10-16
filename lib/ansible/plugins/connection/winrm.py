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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import base64
import inspect
import os
import re
import shlex
import traceback

from ansible.compat.six.moves.urllib.parse import urlunsplit

from ansible.errors import AnsibleError
try:
    from winrm import Response
    from winrm.exceptions import WinRMTransportError
    from winrm.protocol import Protocol
except ImportError:
    raise AnsibleError("winrm is not installed")

HAVE_KERBEROS = False
try:
    import kerberos
    HAVE_KERBEROS = True
except ImportError:
    pass

from ansible import constants as C
from ansible.errors import AnsibleConnectionFailure, AnsibleFileNotFound
from ansible.plugins.connection import ConnectionBase
from ansible.plugins import shell_loader
from ansible.utils.path import makedirs_safe
from ansible.utils.unicode import to_bytes, to_unicode

class Connection(ConnectionBase):
    '''WinRM connections over HTTP/HTTPS.'''

    module_implementation_preferences = ('.ps1', '')

    def __init__(self,  *args, **kwargs):

        self.has_pipelining   = False
        self.protocol         = None
        self.shell_id         = None
        self.delegate         = None
        self._shell_type      = 'powershell'

        # TODO: Add runas support
        self.become_methods_supported=[]

        super(Connection, self).__init__(*args, **kwargs)

    @property
    def transport(self):
        ''' used to identify this connection object from other classes '''
        return 'winrm'

    def set_host_overrides(self, host):
        '''
        Override WinRM-specific options from host variables.
        '''
        host_vars = host.get_vars()

        self._winrm_host = self._play_context.remote_addr
        self._winrm_port = int(self._play_context.port or 5986)
        self._winrm_scheme = host_vars.get('ansible_winrm_scheme', 'http' if self._winrm_port == 5985 else 'https')
        self._winrm_path = host_vars.get('ansible_winrm_path', '/wsman')
        self._winrm_user = self._play_context.remote_user
        self._winrm_pass = self._play_context.password

        if '@' in self._winrm_user:
            self._winrm_realm = self._winrm_user.split('@', 1)[1].strip() or None
        else:
            self._winrm_realm = None
        self._winrm_realm = host_vars.get('ansible_winrm_realm', self._winrm_realm) or None

        if HAVE_KERBEROS and ('@' in self._winrm_user or self._winrm_realm):
            self._winrm_transport = 'kerberos,plaintext'
        else:
            self._winrm_transport = 'plaintext'
        self._winrm_transport = host_vars.get('ansible_winrm_transport', self._winrm_transport)
        if isinstance(self._winrm_transport, basestring):
            self._winrm_transport = [x.strip() for x in self._winrm_transport.split(',') if x.strip()]

        self._winrm_kwargs = dict(username=self._winrm_user, password=self._winrm_pass, realm=self._winrm_realm)
        argspec = inspect.getargspec(Protocol.__init__)
        for arg in argspec.args:
            if arg in ('self', 'endpoint', 'transport', 'username', 'password', 'realm'):
                continue
            if 'ansible_winrm_%s' % arg in host_vars:
                self._winrm_kwargs[arg] = host_vars['ansible_winrm_%s' % arg]

    def _winrm_connect(self):
        '''
        Establish a WinRM connection over HTTP/HTTPS.
        '''
        self._display.vvv("ESTABLISH WINRM CONNECTION FOR USER: %s on PORT %s TO %s" % \
            (self._winrm_user, self._winrm_port, self._winrm_host), host=self._winrm_host)
        netloc = '%s:%d' % (self._winrm_host, self._winrm_port)
        endpoint = urlunsplit((self._winrm_scheme, netloc, self._winrm_path, '', ''))
        errors = []
        for transport in self._winrm_transport:
            if transport == 'kerberos' and not HAVE_KERBEROS:
                errors.append('kerberos: the python kerberos library is not installed')
                continue
            self._display.vvvvv('WINRM CONNECT: transport=%s endpoint=%s' % (transport, endpoint), host=self._winrm_host)
            try:
                protocol = Protocol(endpoint, transport=transport, **self._winrm_kwargs)
                protocol.send_message('')
                return protocol
            except Exception as e:
                err_msg = (str(e) or repr(e)).strip()
                if re.search(r'Operation\s+?timed\s+?out', err_msg, re.I):
                    raise AnsibleError('the connection attempt timed out')
                m = re.search(r'Code\s+?(\d{3})', err_msg)
                if m:
                    code = int(m.groups()[0])
                    if code == 401:
                        err_msg = 'the username/password specified for this server was incorrect'
                    elif code == 411:
                        return protocol
                errors.append('%s: %s' % (transport, err_msg))
                self._display.vvvvv('WINRM CONNECTION ERROR: %s\n%s' % (err_msg, traceback.format_exc()), host=self._winrm_host)
        if errors:
            raise AnsibleError(', '.join(errors))
        else:
            raise AnsibleError('No transport found for WinRM connection')

    def _winrm_exec(self, command, args=(), from_exec=False):
        if from_exec:
            self._display.vvvvv("WINRM EXEC %r %r" % (command, args), host=self._winrm_host)
        else:
            self._display.vvvvvv("WINRM EXEC %r %r" % (command, args), host=self._winrm_host)
        if not self.protocol:
            self.protocol = self._winrm_connect()
        if not self.shell_id:
            self.shell_id = self.protocol.open_shell(codepage=65001) # UTF-8
        command_id = None
        try:
            command_id = self.protocol.run_command(self.shell_id, to_bytes(command), map(to_bytes, args))
            response = Response(self.protocol.get_command_output(self.shell_id, command_id))
            if from_exec:
                self._display.vvvvv('WINRM RESULT %r' % to_unicode(response), host=self._winrm_host)
            else:
                self._display.vvvvvv('WINRM RESULT %r' % to_unicode(response), host=self._winrm_host)
            self._display.vvvvvv('WINRM STDOUT %s' % to_unicode(response.std_out), host=self._winrm_host)
            self._display.vvvvvv('WINRM STDERR %s' % to_unicode(response.std_err), host=self._winrm_host)
            return response
        finally:
            if command_id:
                self.protocol.cleanup_command(self.shell_id, command_id)

    def _connect(self):
        if not self.protocol:
            self.protocol = self._winrm_connect()
        return self

    def exec_command(self, cmd, in_data=None, sudoable=True):
        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)
        cmd_parts = shlex.split(to_bytes(cmd), posix=False)
        cmd_parts = map(to_unicode, cmd_parts)
        script = None
        cmd_ext = cmd_parts and self._shell._unquote(cmd_parts[0]).lower()[-4:] or ''
        # Support running .ps1 files (via script/raw).
        if cmd_ext == '.ps1':
            script = '& %s' % cmd
        # Support running .bat/.cmd files; change back to the default system encoding instead of UTF-8.
        elif cmd_ext in ('.bat', '.cmd'):
            script = '[System.Console]::OutputEncoding = [System.Text.Encoding]::Default; & %s' % cmd
        # Encode the command if not already encoded; supports running simple PowerShell commands via raw.
        elif '-EncodedCommand' not in cmd_parts:
            script = cmd
        if script:
            cmd_parts = self._shell._encode_script(script, as_list=True, strict_mode=False)
        if '-EncodedCommand' in cmd_parts:
            encoded_cmd = cmd_parts[cmd_parts.index('-EncodedCommand') + 1]
            decoded_cmd = to_unicode(base64.b64decode(encoded_cmd).decode('utf-16-le'))
            self._display.vvv("EXEC %s" % decoded_cmd, host=self._winrm_host)
        else:
            self._display.vvv("EXEC %s" % cmd, host=self._winrm_host)
        try:
            result = self._winrm_exec(cmd_parts[0], cmd_parts[1:], from_exec=True)
        except Exception as e:
            traceback.print_exc()
            raise AnsibleError("failed to exec cmd %s" % cmd)
        result.std_out = to_unicode(result.std_out)
        result.std_err = to_unicode(result.std_err)
        return (result.status_code, result.std_out, result.std_err)

    def put_file(self, in_path, out_path):
        super(Connection, self).put_file(in_path, out_path)
        out_path = self._shell._unquote(out_path)
        self._display.vvv('PUT "%s" TO "%s"' % (in_path, out_path), host=self._winrm_host)
        if not os.path.exists(in_path):
            raise AnsibleFileNotFound('file or module does not exist: "%s"' % in_path)
        with open(in_path) as in_file:
            in_size = os.path.getsize(in_path)
            script_template = '''
                $s = [System.IO.File]::OpenWrite("%s");
                [void]$s.Seek(%d, [System.IO.SeekOrigin]::Begin);
                $b = [System.Convert]::FromBase64String("%s");
                [void]$s.Write($b, 0, $b.length);
                [void]$s.SetLength(%d);
                [void]$s.Close();
            '''
            # Determine max size of data we can pass per command.
            script = script_template % (self._shell._escape(out_path), in_size, '', in_size)
            cmd = self._shell._encode_script(script)
            # Encode script with no data, subtract its length from 8190 (max
            # windows command length), divide by 2.67 (UTF16LE base64 command
            # encoding), then by 1.35 again (data base64 encoding).
            buffer_size = int(((8190 - len(cmd)) / 2.67) / 1.35)
            for offset in xrange(0, in_size or 1, buffer_size):
                try:
                    out_data = in_file.read(buffer_size)
                    if offset == 0:
                        if out_data.lower().startswith('#!powershell') and not out_path.lower().endswith('.ps1'):
                            out_path = out_path + '.ps1'
                    b64_data = base64.b64encode(out_data)
                    script = script_template % (self._shell._escape(out_path), offset, b64_data, in_size)
                    self._display.vvvvv('WINRM PUT "%s" to "%s" (offset=%d size=%d)' % (in_path, out_path, offset, len(out_data)), host=self._winrm_host)
                    cmd_parts = self._shell._encode_script(script, as_list=True)
                    result = self._winrm_exec(cmd_parts[0], cmd_parts[1:])
                    if result.status_code != 0:
                        raise IOError(to_unicode(result.std_err))
                except Exception:
                    traceback.print_exc()
                    raise AnsibleError('failed to transfer file to "%s"' % out_path)

    def fetch_file(self, in_path, out_path):
        super(Connection, self).fetch_file(in_path, out_path)
        in_path = self._shell._unquote(in_path)
        out_path = out_path.replace('\\', '/')
        self._display.vvv('FETCH "%s" TO "%s"' % (in_path, out_path), host=self._winrm_host)
        buffer_size = 2**19 # 0.5MB chunks
        makedirs_safe(os.path.dirname(out_path))
        out_file = None
        try:
            offset = 0
            while True:
                try:
                    script = '''
                        If (Test-Path -PathType Leaf "%(path)s")
                        {
                            $stream = [System.IO.File]::OpenRead("%(path)s");
                            $stream.Seek(%(offset)d, [System.IO.SeekOrigin]::Begin) | Out-Null;
                            $buffer = New-Object Byte[] %(buffer_size)d;
                            $bytesRead = $stream.Read($buffer, 0, %(buffer_size)d);
                            $bytes = $buffer[0..($bytesRead-1)];
                            [System.Convert]::ToBase64String($bytes);
                            $stream.Close() | Out-Null;
                        }
                        ElseIf (Test-Path -PathType Container "%(path)s")
                        {
                            Write-Host "[DIR]";
                        }
                        Else
                        {
                            Write-Error "%(path)s does not exist";
                            Exit 1;
                        }
                    ''' % dict(buffer_size=buffer_size, path=self._shell._escape(in_path), offset=offset)
                    self._display.vvvvv('WINRM FETCH "%s" to "%s" (offset=%d)' % (in_path, out_path, offset), host=self._winrm_host)
                    cmd_parts = self._shell._encode_script(script, as_list=True)
                    result = self._winrm_exec(cmd_parts[0], cmd_parts[1:])
                    if result.status_code != 0:
                        raise IOError(to_unicode(result.std_err))
                    if result.std_out.strip() == '[DIR]':
                        data = None
                    else:
                        data = base64.b64decode(result.std_out.strip())
                    if data is None:
                        makedirs_safe(out_path)
                        break
                    else:
                        if not out_file:
                            # If out_path is a directory and we're expecting a file, bail out now.
                            if os.path.isdir(out_path):
                                break
                            out_file = open(out_path, 'wb')
                        out_file.write(data)
                        if len(data) < buffer_size:
                            break
                        offset += len(data)
                except Exception:
                    traceback.print_exc()
                    raise AnsibleError('failed to transfer file to "%s"' % out_path)
        finally:
            if out_file:
                out_file.close()

    def close(self):
        if self.protocol and self.shell_id:
            self.protocol.close_shell(self.shell_id)
            self.shell_id = None
