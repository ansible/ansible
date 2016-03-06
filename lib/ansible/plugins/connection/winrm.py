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
import json
import xmltodict

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

from ansible.errors import AnsibleFileNotFound
from ansible.plugins.connection import ConnectionBase
from ansible.utils.hashing import secure_hash
from ansible.utils.path import makedirs_safe
from ansible.utils.unicode import to_bytes, to_unicode, to_str
from ansible.utils.vars import combine_vars

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class Connection(ConnectionBase):
    '''WinRM connections over HTTP/HTTPS.'''

    module_implementation_preferences = ('.ps1', '')
    become_methods = []
    allow_executable = False

    def __init__(self,  *args, **kwargs):

        self.has_pipelining   = False
        self.protocol         = None
        self.shell_id         = None
        self.delegate         = None
        self._shell_type      = 'powershell'

        # TODO: Add runas support

        super(Connection, self).__init__(*args, **kwargs)

    @property
    def transport(self):
        ''' used to identify this connection object from other classes '''
        return 'winrm'

    def set_host_overrides(self, host):
        '''
        Override WinRM-specific options from host variables.
        '''
        host_vars = combine_vars(host.get_group_vars(), host.get_vars())

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

        transport_selector = 'ssl' if self._winrm_scheme == 'https' else 'plaintext'

        if HAVE_KERBEROS and ('@' in self._winrm_user or self._winrm_realm):
            self._winrm_transport = 'kerberos,%s' % transport_selector
        else:
            self._winrm_transport = transport_selector
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
        display.vvv("ESTABLISH WINRM CONNECTION FOR USER: %s on PORT %s TO %s" %
            (self._winrm_user, self._winrm_port, self._winrm_host), host=self._winrm_host)
        netloc = '%s:%d' % (self._winrm_host, self._winrm_port)
        endpoint = urlunsplit((self._winrm_scheme, netloc, self._winrm_path, '', ''))
        errors = []
        for transport in self._winrm_transport:
            if transport == 'kerberos' and not HAVE_KERBEROS:
                errors.append('kerberos: the python kerberos library is not installed')
                continue
            display.vvvvv('WINRM CONNECT: transport=%s endpoint=%s' % (transport, endpoint), host=self._winrm_host)
            try:
                protocol = Protocol(endpoint, transport=transport, **self._winrm_kwargs)
                protocol.send_message('')
                return protocol
            except Exception as e:
                err_msg = to_unicode(e).strip()
                if re.search(to_unicode(r'Operation\s+?timed\s+?out'), err_msg, re.I):
                    raise AnsibleError('the connection attempt timed out')
                m = re.search(to_unicode(r'Code\s+?(\d{3})'), err_msg)
                if m:
                    code = int(m.groups()[0])
                    if code == 401:
                        err_msg = 'the username/password specified for this server was incorrect'
                    elif code == 411:
                        return protocol
                errors.append(u'%s: %s' % (transport, err_msg))
                display.vvvvv(u'WINRM CONNECTION ERROR: %s\n%s' % (err_msg, to_unicode(traceback.format_exc())), host=self._winrm_host)
        if errors:
            raise AnsibleError(', '.join(map(to_str, errors)))
        else:
            raise AnsibleError('No transport found for WinRM connection')

    def _winrm_send_input(self, protocol, shell_id, command_id, stdin, eof=False):
        rq = {'env:Envelope': protocol._get_soap_header(
            resource_uri='http://schemas.microsoft.com/wbem/wsman/1/windows/shell/cmd',
            action='http://schemas.microsoft.com/wbem/wsman/1/windows/shell/Send',
            shell_id=shell_id)}
        stream = rq['env:Envelope'].setdefault('env:Body', {}).setdefault('rsp:Send', {})\
            .setdefault('rsp:Stream', {})
        stream['@Name'] = 'stdin'
        stream['@CommandId'] = command_id
        stream['#text'] = base64.b64encode(to_bytes(stdin))
        if eof:
            stream['@End'] = 'true'
        rs = protocol.send_message(xmltodict.unparse(rq))

    def _winrm_exec(self, command, args=(), from_exec=False, stdin_iterator=None):
        if not self.protocol:
            self.protocol = self._winrm_connect()
            self._connected = True
        if not self.shell_id:
            self.shell_id = self.protocol.open_shell(codepage=65001) # UTF-8
            display.vvvvv('WINRM OPEN SHELL: %s' % self.shell_id, host=self._winrm_host)
        if from_exec:
            display.vvvvv("WINRM EXEC %r %r" % (command, args), host=self._winrm_host)
        else:
            display.vvvvvv("WINRM EXEC %r %r" % (command, args), host=self._winrm_host)
        command_id = None
        try:
            stdin_push_failed = False
            command_id = self.protocol.run_command(self.shell_id, to_bytes(command), map(to_bytes, args), console_mode_stdin=(stdin_iterator == None))

            # TODO: try/except around this, so we can get/return the command result on a broken pipe or other failure (probably more useful than the 500 that comes from this)
            try:
                if stdin_iterator:
                    for (data, is_last) in stdin_iterator:
                        self._winrm_send_input(self.protocol, self.shell_id, command_id, data, eof=is_last)
            except:
                stdin_push_failed = True

            # NB: this could hang if the receiver is still running (eg, network failed a Send request but the server's still happy).
            # FUTURE: Consider adding pywinrm status check/abort operations to see if the target is still running after a failure.
            response = Response(self.protocol.get_command_output(self.shell_id, command_id))
            if from_exec:
                display.vvvvv('WINRM RESULT %r' % to_unicode(response), host=self._winrm_host)
            else:
                display.vvvvvv('WINRM RESULT %r' % to_unicode(response), host=self._winrm_host)
            display.vvvvvv('WINRM STDOUT %s' % to_unicode(response.std_out), host=self._winrm_host)
            display.vvvvvv('WINRM STDERR %s' % to_unicode(response.std_err), host=self._winrm_host)

            if stdin_push_failed:
                raise AnsibleError('winrm send_input failed; \nstdout: %s\nstderr %s' % (response.std_out, response.std_err))

            return response
        finally:
            if command_id:
                self.protocol.cleanup_command(self.shell_id, command_id)

    def _connect(self):
        if not self.protocol:
            self.protocol = self._winrm_connect()
            self._connected = True
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
            display.vvv("EXEC %s" % decoded_cmd, host=self._winrm_host)
        else:
            display.vvv("EXEC %s" % cmd, host=self._winrm_host)
        try:
            result = self._winrm_exec(cmd_parts[0], cmd_parts[1:], from_exec=True)
        except Exception:
            traceback.print_exc()
            raise AnsibleError("failed to exec cmd %s" % cmd)
        result.std_out = to_bytes(result.std_out)
        result.std_err = to_bytes(result.std_err)
        return (result.status_code, result.std_out, result.std_err)

    # FUTURE: determine buffer size at runtime via remote winrm config?
    def _put_file_stdin_iterator(self, in_path, out_path, buffer_size=250000):
        in_size = os.path.getsize(in_path)
        offset = 0
        with open(in_path, 'rb') as in_file:
            for out_data in iter((lambda:in_file.read(buffer_size)), ''):
                offset += len(out_data)
                self._display.vvvvv('WINRM PUT "%s" to "%s" (offset=%d size=%d)' % (in_path, out_path, offset, len(out_data)), host=self._winrm_host)
                # yes, we're double-encoding over the wire in this case- we want to ensure that the data shipped to the end PS pipeline is still b64-encoded
                b64_data = base64.b64encode(out_data) + '\r\n'
                # cough up the data, as well as an indicator if this is the last chunk so winrm_send knows to set the End signal
                yield b64_data, (in_file.tell() == in_size)

            if offset == 0: # empty file, return an empty buffer + eof to close it
                yield "", True

    def put_file(self, in_path, out_path):
        super(Connection, self).put_file(in_path, out_path)
        out_path = self._shell._unquote(out_path)
        display.vvv('PUT "%s" TO "%s"' % (in_path, out_path), host=self._winrm_host)
        if not os.path.exists(in_path):
            raise AnsibleFileNotFound('file or module does not exist: "%s"' % in_path)

        script_template = u'''
            begin {{
                $path = "{0}"

                $DebugPreference = "Continue"
                $ErrorActionPreference = "Stop"
                Set-StrictMode -Version 2

                $fd = [System.IO.File]::Create($path)

                $sha1 = [System.Security.Cryptography.SHA1CryptoServiceProvider]::Create()

                $bytes = @() #initialize for empty file case
            }}
            process {{
               $bytes = [System.Convert]::FromBase64String($input)
               $sha1.TransformBlock($bytes, 0, $bytes.Length, $bytes, 0) | Out-Null
               $fd.Write($bytes, 0, $bytes.Length)
            }}
            end {{
                $sha1.TransformFinalBlock($bytes, 0, 0) | Out-Null

                $hash = [System.BitConverter]::ToString($sha1.Hash).Replace("-", "").ToLowerInvariant()

                $fd.Close()

                Write-Output "{{""sha1"":""$hash""}}"
            }}
        '''

        script = script_template.format(self._shell._escape(out_path))
        cmd_parts = self._shell._encode_script(script, as_list=True, strict_mode=False)

        result = self._winrm_exec(cmd_parts[0], cmd_parts[1:], stdin_iterator=self._put_file_stdin_iterator(in_path, out_path))
        # TODO: improve error handling
        if result.status_code != 0:
            raise AnsibleError(to_str(result.std_err))

        put_output = json.loads(result.std_out)
        remote_sha1 = put_output.get("sha1")

        if not remote_sha1:
            raise AnsibleError("Remote sha1 was not returned")

        local_sha1 = secure_hash(in_path)

        if not remote_sha1 == local_sha1:
            raise AnsibleError("Remote sha1 hash {0} does not match local hash {1}".format(to_str(remote_sha1), to_str(local_sha1)))


    def fetch_file(self, in_path, out_path):
        super(Connection, self).fetch_file(in_path, out_path)
        in_path = self._shell._unquote(in_path)
        out_path = out_path.replace('\\', '/')
        display.vvv('FETCH "%s" TO "%s"' % (in_path, out_path), host=self._winrm_host)
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
                    display.vvvvv('WINRM FETCH "%s" to "%s" (offset=%d)' % (in_path, out_path, offset), host=self._winrm_host)
                    cmd_parts = self._shell._encode_script(script, as_list=True)
                    result = self._winrm_exec(cmd_parts[0], cmd_parts[1:])
                    if result.status_code != 0:
                        raise IOError(to_str(result.std_err))
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
            display.vvvvv('WINRM CLOSE SHELL: %s' % self.shell_id, host=self._winrm_host)
            self.protocol.close_shell(self.shell_id)
        self.shell_id = None
        self.protocol = None
        self._connected = False
