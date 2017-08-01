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
import socket
import traceback
import json
import tempfile
import subprocess
import itertools

HAVE_KERBEROS = False
try:
    import kerberos
    HAVE_KERBEROS = True
except ImportError:
    pass

from ansible.errors import AnsibleError, AnsibleConnectionFailure
from ansible.errors import AnsibleFileNotFound
from ansible.module_utils.six import string_types
from ansible.module_utils.six.moves.urllib.parse import urlunsplit
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.module_utils.six import binary_type
from ansible.plugins.connection import ConnectionBase
from ansible.plugins.shell.powershell import exec_wrapper, become_wrapper, leaf_exec
from ansible.utils.hashing import secure_hash
from ansible.utils.path import makedirs_safe

try:
    import winrm
    from winrm import Response
    from winrm.protocol import Protocol
    HAS_WINRM = True
except ImportError as e:
    HAS_WINRM = False

try:
    import xmltodict
    HAS_XMLTODICT = True
except ImportError as e:
    HAS_XMLTODICT = False

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class Connection(ConnectionBase):
    '''WinRM connections over HTTP/HTTPS.'''

    transport = 'winrm'
    module_implementation_preferences = ('.ps1', '.exe', '')
    become_methods = ['runas']
    allow_executable = False

    def __init__(self, *args, **kwargs):

        self.has_pipelining = True
        self.always_pipeline_modules = True
        self.has_native_async = True
        self.protocol = None
        self.shell_id = None
        self.delegate = None
        self._shell_type = 'powershell'
        # FUTURE: Add runas support

        super(Connection, self).__init__(*args, **kwargs)

    def transport_test(self, connect_timeout):
        ''' Test the transport mechanism, if available '''
        host = self._winrm_host
        port = int(self._winrm_port)
        display.vvv("attempting transport test to %s:%s" % (host, port))
        sock = socket.create_connection((host, port), connect_timeout)
        sock.close()

    def set_host_overrides(self, host, hostvars=None):
        '''
        Override WinRM-specific options from host variables.
        '''
        if not HAS_WINRM:
            return

        self._winrm_host = self._play_context.remote_addr
        self._winrm_port = int(self._play_context.port or 5986)
        self._winrm_scheme = hostvars.get('ansible_winrm_scheme', 'http' if self._winrm_port == 5985 else 'https')
        self._winrm_path = hostvars.get('ansible_winrm_path', '/wsman')
        self._winrm_user = self._play_context.remote_user
        self._winrm_pass = self._play_context.password
        self._become_method = self._play_context.become_method
        self._become_user = self._play_context.become_user
        self._become_pass = self._play_context.become_pass

        self._kinit_cmd = hostvars.get('ansible_winrm_kinit_cmd', 'kinit')

        if hasattr(winrm, 'FEATURE_SUPPORTED_AUTHTYPES'):
            self._winrm_supported_authtypes = set(winrm.FEATURE_SUPPORTED_AUTHTYPES)
        else:
            # for legacy versions of pywinrm, use the values we know are supported
            self._winrm_supported_authtypes = set(['plaintext', 'ssl', 'kerberos'])

        # TODO: figure out what we want to do with auto-transport selection in the face of NTLM/Kerb/CredSSP/Cert/Basic
        transport_selector = 'ssl' if self._winrm_scheme == 'https' else 'plaintext'

        if HAVE_KERBEROS and ((self._winrm_user and '@' in self._winrm_user)):
            self._winrm_transport = 'kerberos,%s' % transport_selector
        else:
            self._winrm_transport = transport_selector
        self._winrm_transport = hostvars.get('ansible_winrm_transport', self._winrm_transport)
        if isinstance(self._winrm_transport, string_types):
            self._winrm_transport = [x.strip() for x in self._winrm_transport.split(',') if x.strip()]

        unsupported_transports = set(self._winrm_transport).difference(self._winrm_supported_authtypes)

        if unsupported_transports:
            raise AnsibleError('The installed version of WinRM does not support transport(s) %s' % list(unsupported_transports))

        # if kerberos is among our transports and there's a password specified, we're managing the tickets
        kinit_mode = to_text(hostvars.get('ansible_winrm_kinit_mode', '')).strip()
        if kinit_mode == "":
            # HACK: ideally, remove multi-transport stuff
            self._kerb_managed = "kerberos" in self._winrm_transport and self._winrm_pass
        elif kinit_mode == "managed":
            self._kerb_managed = True
        elif kinit_mode == "manual":
            self._kerb_managed = False
        else:
            raise AnsibleError('Unknown ansible_winrm_kinit_mode value: "%s" (must be "managed" or "manual")' % kinit_mode)

        # arg names we're going passing directly
        internal_kwarg_mask = set(['self', 'endpoint', 'transport', 'username', 'password', 'scheme', 'path', 'kinit_mode', 'kinit_cmd'])

        self._winrm_kwargs = dict(username=self._winrm_user, password=self._winrm_pass)
        argspec = inspect.getargspec(Protocol.__init__)
        supported_winrm_args = set(argspec.args)
        supported_winrm_args.update(internal_kwarg_mask)
        passed_winrm_args = set([v.replace('ansible_winrm_', '') for v in hostvars if v.startswith('ansible_winrm_')])
        unsupported_args = passed_winrm_args.difference(supported_winrm_args)

        # warn for kwargs unsupported by the installed version of pywinrm
        for arg in unsupported_args:
            display.warning("ansible_winrm_{0} unsupported by pywinrm (is an up-to-date version of pywinrm installed?)".format(arg))

        # pass through matching kwargs, excluding the list we want to treat specially
        for arg in passed_winrm_args.difference(internal_kwarg_mask).intersection(supported_winrm_args):
            self._winrm_kwargs[arg] = hostvars['ansible_winrm_%s' % arg]

    # Until pykerberos has enough goodies to implement a rudimentary kinit/klist, simplest way is to let each connection
    # auth itself with a private CCACHE.
    def _kerb_auth(self, principal, password):
        if password is None:
            password = ""
        self._kerb_ccache = tempfile.NamedTemporaryFile()
        display.vvvvv("creating Kerberos CC at %s" % self._kerb_ccache.name)
        krb5ccname = "FILE:%s" % self._kerb_ccache.name
        krbenv = dict(KRB5CCNAME=krb5ccname)
        os.environ["KRB5CCNAME"] = krb5ccname
        kinit_cmdline = [self._kinit_cmd, principal]

        display.vvvvv("calling kinit for principal %s" % principal)
        p = subprocess.Popen(kinit_cmdline, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=krbenv)

        # TODO: unicode/py3
        stdout, stderr = p.communicate(password + b'\n')

        if p.returncode != 0:
            raise AnsibleConnectionFailure("Kerberos auth failure: %s" % stderr.strip())

        display.vvvvv("kinit succeeded for principal %s" % principal)

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
            if transport == 'kerberos':
                if not HAVE_KERBEROS:
                    errors.append('kerberos: the python kerberos library is not installed')
                    continue
                if self._kerb_managed:
                    self._kerb_auth(self._winrm_user, self._winrm_pass)
            display.vvvvv('WINRM CONNECT: transport=%s endpoint=%s' % (transport, endpoint), host=self._winrm_host)
            try:
                protocol = Protocol(endpoint, transport=transport, **self._winrm_kwargs)

                # open the shell from connect so we know we're able to talk to the server
                if not self.shell_id:
                    self.shell_id = protocol.open_shell(codepage=65001)  # UTF-8
                    display.vvvvv('WINRM OPEN SHELL: %s' % self.shell_id, host=self._winrm_host)

                return protocol
            except Exception as e:
                err_msg = to_text(e).strip()
                if re.search(to_text(r'Operation\s+?timed\s+?out'), err_msg, re.I):
                    raise AnsibleError('the connection attempt timed out')
                m = re.search(to_text(r'Code\s+?(\d{3})'), err_msg)
                if m:
                    code = int(m.groups()[0])
                    if code == 401:
                        err_msg = 'the specified credentials were rejected by the server'
                    elif code == 411:
                        return protocol
                errors.append(u'%s: %s' % (transport, err_msg))
                display.vvvvv(u'WINRM CONNECTION ERROR: %s\n%s' % (err_msg, to_text(traceback.format_exc())), host=self._winrm_host)
        if errors:
            raise AnsibleConnectionFailure(', '.join(map(to_native, errors)))
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
        protocol.send_message(xmltodict.unparse(rq))

    def _winrm_exec(self, command, args=(), from_exec=False, stdin_iterator=None):
        if not self.protocol:
            self.protocol = self._winrm_connect()
            self._connected = True
        if from_exec:
            display.vvvvv("WINRM EXEC %r %r" % (command, args), host=self._winrm_host)
        else:
            display.vvvvvv("WINRM EXEC %r %r" % (command, args), host=self._winrm_host)
        command_id = None
        try:
            stdin_push_failed = False
            command_id = self.protocol.run_command(self.shell_id, to_bytes(command), map(to_bytes, args), console_mode_stdin=(stdin_iterator is None))

            # TODO: try/except around this, so we can get/return the command result on a broken pipe or other failure (probably more useful than the 500 that
            # comes from this)
            try:
                if stdin_iterator:
                    for (data, is_last) in stdin_iterator:
                        self._winrm_send_input(self.protocol, self.shell_id, command_id, data, eof=is_last)

            except Exception as ex:
                from traceback import format_exc
                display.warning("FATAL ERROR DURING FILE TRANSFER: %s" % format_exc(ex))
                stdin_push_failed = True

            if stdin_push_failed:
                raise AnsibleError('winrm send_input failed')

            # NB: this can hang if the receiver is still running (eg, network failed a Send request but the server's still happy).
            # FUTURE: Consider adding pywinrm status check/abort operations to see if the target is still running after a failure.
            resptuple = self.protocol.get_command_output(self.shell_id, command_id)
            # ensure stdout/stderr are text for py3
            # FUTURE: this should probably be done internally by pywinrm
            response = Response(tuple(to_text(v) if isinstance(v, binary_type) else v for v in resptuple))

            # TODO: check result from response and set stdin_push_failed if we have nonzero
            if from_exec:
                display.vvvvv('WINRM RESULT %r' % to_text(response), host=self._winrm_host)
            else:
                display.vvvvvv('WINRM RESULT %r' % to_text(response), host=self._winrm_host)

            display.vvvvvv('WINRM STDOUT %s' % to_text(response.std_out), host=self._winrm_host)
            display.vvvvvv('WINRM STDERR %s' % to_text(response.std_err), host=self._winrm_host)

            if stdin_push_failed:
                raise AnsibleError('winrm send_input failed; \nstdout: %s\nstderr %s' % (response.std_out, response.std_err))

            return response
        finally:
            if command_id:
                self.protocol.cleanup_command(self.shell_id, command_id)

    def _connect(self):

        if not HAS_WINRM:
            raise AnsibleError("winrm or requests is not installed: %s" % to_text(e))
        elif not HAS_XMLTODICT:
            raise AnsibleError("xmltodict is not installed: %s" % to_text(e))

        super(Connection, self)._connect()
        if not self.protocol:
            self.protocol = self._winrm_connect()
            self._connected = True
        return self

    def _reset(self):  # used by win_reboot (and any other action that might need to bounce the state)
        self.protocol = None
        self.shell_id = None
        self._connect()

    def _create_raw_wrapper_payload(self, cmd, environment=dict()):
        payload = {
            'module_entry': to_text(base64.b64encode(to_bytes(cmd))),
            'powershell_modules': {},
            'actions': ['exec'],
            'exec': to_text(base64.b64encode(to_bytes(leaf_exec))),
            'environment': environment
        }

        return json.dumps(payload)

    def _wrapper_payload_stream(self, payload, buffer_size=200000):
        payload_bytes = to_bytes(payload)
        byte_count = len(payload_bytes)
        for i in range(0, byte_count, buffer_size):
            yield payload_bytes[i:i + buffer_size], i + buffer_size >= byte_count

    def exec_command(self, cmd, in_data=None, sudoable=True):
        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)
        cmd_parts = self._shell._encode_script(cmd, as_list=True, strict_mode=False, preserve_rc=False)

        # TODO: display something meaningful here
        display.vvv("EXEC (via pipeline wrapper)")

        stdin_iterator = None

        if in_data:
            stdin_iterator = self._wrapper_payload_stream(in_data)

        result = self._winrm_exec(cmd_parts[0], cmd_parts[1:], from_exec=True, stdin_iterator=stdin_iterator)

        result.std_out = to_bytes(result.std_out)
        result.std_err = to_bytes(result.std_err)

        # parse just stderr from CLIXML output
        if self.is_clixml(result.std_err):
            try:
                result.std_err = self.parse_clixml_stream(result.std_err)
            except:
                # unsure if we're guaranteed a valid xml doc- use raw output in case of error
                pass

        return (result.status_code, result.std_out, result.std_err)

    def exec_command_old(self, cmd, in_data=None, sudoable=True):
        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)
        cmd_parts = shlex.split(to_bytes(cmd), posix=False)
        cmd_parts = map(to_text, cmd_parts)
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
            decoded_cmd = to_text(base64.b64decode(encoded_cmd).decode('utf-16-le'))
            display.vvv("EXEC %s" % decoded_cmd, host=self._winrm_host)
        else:
            display.vvv("EXEC %s" % cmd, host=self._winrm_host)
        try:
            result = self._winrm_exec(cmd_parts[0], cmd_parts[1:], from_exec=True)
        except Exception:
            traceback.print_exc()
            raise AnsibleConnectionFailure("failed to exec cmd %s" % cmd)
        result.std_out = to_bytes(result.std_out)
        result.std_err = to_bytes(result.std_err)

        # parse just stderr from CLIXML output
        if self.is_clixml(result.std_err):
            try:
                result.std_err = self.parse_clixml_stream(result.std_err)
            except:
                # unsure if we're guaranteed a valid xml doc- use raw output in case of error
                pass

        return (result.status_code, result.std_out, result.std_err)

    def is_clixml(self, value):
        return value.startswith(b"#< CLIXML")

    # hacky way to get just stdout- not always sure of doc framing here, so use with care
    def parse_clixml_stream(self, clixml_doc, stream_name='Error'):
        clear_xml = clixml_doc.replace(b'#< CLIXML\r\n', b'')
        doc = xmltodict.parse(clear_xml)
        lines = [l.get('#text', '').replace('_x000D__x000A_', '') for l in doc.get('Objs', {}).get('S', {}) if l.get('@S') == stream_name]
        return '\r\n'.join(lines)

    # FUTURE: determine buffer size at runtime via remote winrm config?
    def _put_file_stdin_iterator(self, in_path, out_path, buffer_size=250000):
        in_size = os.path.getsize(to_bytes(in_path, errors='surrogate_or_strict'))
        offset = 0
        with open(to_bytes(in_path, errors='surrogate_or_strict'), 'rb') as in_file:
            for out_data in iter((lambda: in_file.read(buffer_size)), b''):
                offset += len(out_data)
                self._display.vvvvv('WINRM PUT "%s" to "%s" (offset=%d size=%d)' % (in_path, out_path, offset, len(out_data)), host=self._winrm_host)
                # yes, we're double-encoding over the wire in this case- we want to ensure that the data shipped to the end PS pipeline is still b64-encoded
                b64_data = base64.b64encode(out_data) + b'\r\n'
                # cough up the data, as well as an indicator if this is the last chunk so winrm_send knows to set the End signal
                yield b64_data, (in_file.tell() == in_size)

            if offset == 0:  # empty file, return an empty buffer + eof to close it
                yield "", True

    def put_file(self, in_path, out_path):
        super(Connection, self).put_file(in_path, out_path)
        out_path = self._shell._unquote(out_path)
        display.vvv('PUT "%s" TO "%s"' % (in_path, out_path), host=self._winrm_host)
        if not os.path.exists(to_bytes(in_path, errors='surrogate_or_strict')):
            raise AnsibleFileNotFound('file or module does not exist: "%s"' % in_path)

        script_template = u'''
            begin {{
                $path = '{0}'

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
        cmd_parts = self._shell._encode_script(script, as_list=True, strict_mode=False, preserve_rc=False)

        result = self._winrm_exec(cmd_parts[0], cmd_parts[1:], stdin_iterator=self._put_file_stdin_iterator(in_path, out_path))
        # TODO: improve error handling
        if result.status_code != 0:
            raise AnsibleError(to_native(result.std_err))

        put_output = json.loads(result.std_out)
        remote_sha1 = put_output.get("sha1")

        if not remote_sha1:
            raise AnsibleError("Remote sha1 was not returned")

        local_sha1 = secure_hash(in_path)

        if not remote_sha1 == local_sha1:
            raise AnsibleError("Remote sha1 hash {0} does not match local hash {1}".format(to_native(remote_sha1), to_native(local_sha1)))

    def fetch_file(self, in_path, out_path):
        super(Connection, self).fetch_file(in_path, out_path)
        in_path = self._shell._unquote(in_path)
        out_path = out_path.replace('\\', '/')
        display.vvv('FETCH "%s" TO "%s"' % (in_path, out_path), host=self._winrm_host)
        buffer_size = 2**19  # 0.5MB chunks
        makedirs_safe(os.path.dirname(out_path))
        out_file = None
        try:
            offset = 0
            while True:
                try:
                    script = '''
                        If (Test-Path -PathType Leaf "%(path)s")
                        {
                            $stream = New-Object IO.FileStream("%(path)s", [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [IO.FileShare]::ReadWrite);
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
                    cmd_parts = self._shell._encode_script(script, as_list=True, preserve_rc=False)
                    result = self._winrm_exec(cmd_parts[0], cmd_parts[1:])
                    if result.status_code != 0:
                        raise IOError(to_native(result.std_err))
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
                            if os.path.isdir(to_bytes(out_path, errors='surrogate_or_strict')):
                                break
                            out_file = open(to_bytes(out_path, errors='surrogate_or_strict'), 'wb')
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
