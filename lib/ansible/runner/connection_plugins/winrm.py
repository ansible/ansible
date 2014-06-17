# (c) 2014, Chris Church <chris@ninemoreminutes.com>
#
# This file is (not yet) part of Ansible.
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

from __future__ import absolute_import

import base64
import hashlib
import imp
import os
import re
import shlex
import traceback
import urlparse
from ansible import errors
from ansible import utils
from ansible.callbacks import vvv, vvvv

try:
    from winrm import Response
    from winrm.exceptions import WinRMTransportError
    from winrm.protocol import Protocol
except ImportError:
    raise errors.AnsibleError("winrm is not installed")

# When running with unmodified Ansible (1.6.x), load local hacks.
try:
    _winrm_hacks = imp.load_source('_winrm_hacks', os.path.join(os.path.dirname(__file__), '_winrm_hacks.py'))
except (ImportError, IOError):
    _winrm_hacks = None

_winrm_cache = {
    # 'user:pwhash@host:port': <protocol instance>
}

class Connection(object):
    '''WinRM connections over HTTP/HTTPS.'''

    def __init__(self,  runner, host, port, user, password, *args, **kwargs):
        self.runner = runner
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.has_pipelining = False
        self.default_shell = 'powershell'
        self.default_suffixes = ['.ps1', '']
        self.protocol = None
        self.shell_id = None
        self.delegate = None
        if _winrm_hacks:
            _winrm_hacks.patch_module_finder(self)

    def _winrm_connect(self):
        '''
        Establish a WinRM connection over HTTP/HTTPS.
        '''
        if _winrm_hacks:
            port = _winrm_hacks.get_port(self)
        else:
            port = self.port or 5986
        vvv("ESTABLISH WINRM CONNECTION FOR USER: %s on PORT %s TO %s" % \
            (self.user, port, self.host), host=self.host)
        netloc = '%s:%d' % (self.host, port)
        cache_key = '%s:%s@%s:%d' % (self.user, hashlib.md5(self.password).hexdigest(), self.host, port)
        if cache_key in _winrm_cache:
            vvvv('WINRM REUSE EXISTING CONNECTION: %s' % cache_key, host=self.host)
            return _winrm_cache[cache_key]
        transport_schemes = [('plaintext', 'https'), ('plaintext', 'http')] # FIXME: ssl/kerberos
        if port == 5985:
            transport_schemes = reversed(transport_schemes)
        exc = None
        for transport, scheme in transport_schemes:
            endpoint = urlparse.urlunsplit((scheme, netloc, '/wsman', '', ''))
            vvvv('WINRM CONNECT: transport=%s endpoint=%s' % (transport, endpoint),
                 host=self.host)
            protocol = Protocol(endpoint, transport=transport,
                                username=self.user, password=self.password)
            try:
                protocol.send_message('')
                _winrm_cache[cache_key] = protocol
                return protocol
            except WinRMTransportError, exc:
                err_msg = str(exc.args[0])
                if re.search(r'Operation\s+?timed\s+?out', err_msg, re.I):
                    raise
                m = re.search(r'Code\s+?(\d{3})', err_msg)
                if m:
                    code = int(m.groups()[0])
                    if code == 411:
                        _winrm_cache[cache_key] = protocol
                        return protocol
                vvvv('WINRM CONNECTION ERROR: %s' % err_msg, host=self.host)
                continue
        # FIXME: Cache connection!!!
        if exc:
            raise exc

    def _winrm_escape(self, value, include_vars=False):
        '''
        Return value escaped for use in PowerShell command.
        '''
        # http://www.techotopia.com/index.php/Windows_PowerShell_1.0_String_Quoting_and_Escape_Sequences
        # http://stackoverflow.com/questions/764360/a-list-of-string-replacements-in-python
        subs = [('\n', '`n'), ('\r', '`r'), ('\t', '`t'), ('\a', '`a'),
                ('\b', '`b'), ('\f', '`f'), ('\v', '`v'), ('"', '`"'),
                ('\'', '`\''), ('`', '``'), ('\x00', '`0')]
        if include_vars:
            subs.append(('$', '`$'))
        pattern = '|'.join('(%s)' % re.escape(p) for p, s in subs)
        substs = [s for p, s in subs]
        replace = lambda m: substs[m.lastindex - 1]
        return re.sub(pattern, replace, value)

    def _winrm_get_script_cmd(self, script):
        '''
        Convert a PowerShell script to a single base64-encoded command.
        '''
        vvvv('WINRM SCRIPT: %s' % script, host=self.host)
        encoded_script = base64.b64encode(script.encode('utf-16-le'))
        return ['PowerShell', '-NoProfile', '-NonInteractive',
                '-EncodedCommand', encoded_script]

    def _winrm_exec(self, command, args):
        vvvv("WINRM EXEC %r %r" % (command, args), host=self.host)
        if not self.protocol:
            self.protocol = self._winrm_connect()
        if not self.shell_id:
            self.shell_id = self.protocol.open_shell()
        command_id = None
        try:
            command_id = self.protocol.run_command(self.shell_id, command, args)
            response = Response(self.protocol.get_command_output(self.shell_id, command_id))
            vvvv('WINRM RESULT %r' % response, host=self.host)
            vvvv('WINRM STDERR %s' % response.std_err, host=self.host)
            return response
        finally:
            if command_id:
                self.protocol.cleanup_command(self.shell_id, command_id)

    def connect(self):
        if not _winrm_hacks:
            if not self.protocol:
                self.protocol = self._winrm_connect()
        # When using hacks, connect lazily on first command, to allow for
        # runner to set self.delegate, needed if actual host vs. host name are
        # different.
        return self

    def exec_command(self, cmd, tmp_path, sudo_user=None, sudoable=False, executable='/bin/sh', in_data=None, su=None, su_user=None):
        cmd = cmd.encode('utf-8')
        vvv("EXEC %s" % cmd, host=self.host)
        cmd_parts = shlex.split(cmd, posix=False)
        vvvv("WINRM PARTS %r" % cmd_parts, host=self.host)
        # For script/raw support.
        if len(cmd_parts) == 1 and cmd_parts[0].lower().endswith('.ps1'):
            cmd_parts = ['PowerShell', '-ExecutionPolicy', 'Unrestricted', '-File', cmd_parts[0]]
        if _winrm_hacks:
            cmd_parts = _winrm_hacks.filter_cmd_parts(self, cmd_parts)
        if not cmd_parts:
            vvv('WINRM NOOP')
            return (0, '', '', '')
        try:
            result = self._winrm_exec(cmd_parts[0], cmd_parts[1:])
        except Exception, e:
            traceback.print_exc()
            raise errors.AnsibleError("failed to exec cmd %s" % cmd)
        return (result.status_code, '', result.std_out.encode('utf-8'), result.std_err.encode('utf-8'))

    def put_file(self, in_path, out_path):
        if _winrm_hacks:
            out_path = _winrm_hacks.fix_slashes(out_path)
        vvv("PUT %s TO %s" % (in_path, out_path), host=self.host)
        if not os.path.exists(in_path):
            raise errors.AnsibleFileNotFound("file or module does not exist: %s" % in_path)
        buffer_size = 1024 # FIXME: Find max size or optimize.
        with open(in_path) as in_file:
            in_size = os.path.getsize(in_path)
            for offset in xrange(0, in_size, buffer_size):
                try:
                    out_data = in_file.read(buffer_size)
                    if offset == 0:
                        if out_data.lower().startswith('#!powershell') and not out_path.lower().endswith('.ps1'):
                            out_path = out_path + '.ps1'
                    b64_data = base64.b64encode(out_data)
                    script = '''
                        $bufferSize = %d;
                        $stream = [System.IO.File]::OpenWrite("%s");
                        $stream.Seek(%d, [System.IO.SeekOrigin]::Begin) | Out-Null;
                        $data = "%s";
                        $buffer = [System.Convert]::FromBase64String($data);
                        $stream.Write($buffer, 0, $buffer.length) | Out-Null;
                        $stream.SetLength(%d) | Out-Null;
                        $stream.Close() | Out-Null;
                    ''' % (buffer_size, self._winrm_escape(out_path), offset, b64_data, in_size)
                    cmd_parts = self._winrm_get_script_cmd(script)
                    result = self._winrm_exec(cmd_parts[0], cmd_parts[1:])
                    if result.status_code != 0:
                        raise RuntimeError(result.std_err.encode('utf-8'))
                    script = u''
                except Exception: # IOError?
                    traceback.print_exc()
                    raise errors.AnsibleError("failed to transfer file to %s" % out_path)

    def fetch_file(self, in_path, out_path):
        if _winrm_hacks:
            in_path = _winrm_hacks.fix_slashes(in_path)
        out_path = out_path.replace('\\', '/')
        vvv("FETCH %s TO %s" % (in_path, out_path), host=self.host)
        buffer_size = 2**20 # 1MB chunks
        if not os.path.exists(os.path.dirname(out_path)):
            os.makedirs(os.path.dirname(out_path))
        with open(out_path, 'wb') as out_file:
            offset = 0
            while True:
                try:
                    script = '''
                        $bufferSize = %d;
                        $stream = [System.IO.File]::OpenRead("%s");
                        $stream.Seek(%d, [System.IO.SeekOrigin]::Begin) | Out-Null;
                        $buffer = New-Object Byte[] $bufferSize;
                        $bytesRead = $stream.Read($buffer, 0, $bufferSize);
                        $bytes = $buffer[0..($bytesRead-1)];
                        [System.Convert]::ToBase64String($bytes);
                        $stream.Close() | Out-Null;
                    ''' % (buffer_size, self._winrm_escape(in_path), offset)
                    cmd_parts = self._winrm_get_script_cmd(script)
                    result = self._winrm_exec(cmd_parts[0], cmd_parts[1:])
                    data = base64.b64decode(result.std_out.strip())
                    out_file.write(data)
                    if len(data) < buffer_size:
                        break
                    offset += len(data)
                except Exception: # IOError?
                    traceback.print_exc()
                    raise errors.AnsibleError("failed to transfer file to %s" % out_path)

    def close(self):
        if self.protocol and self.shell_id:
            self.protocol.close_shell(self.shell_id)
            self.shell_id = None
