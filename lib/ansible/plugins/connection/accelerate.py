# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
#
# This file is part of Ansible
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
import json
import os
import socket
import struct
import time

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleFileNotFound, AnsibleConnectionFailure
from ansible.parsing.utils.jsonify import jsonify
from ansible.plugins.connection import ConnectionBase
from ansible.utils.encrypt import key_for_hostname, keyczar_encrypt, keyczar_decrypt

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

# the chunk size to read and send, assuming mtu 1500 and
# leaving room for base64 (+33%) encoding and header (8 bytes)
# ((1400-8)/4)*3) = 1044
# which leaves room for the TCP/IP header. We set this to a
# multiple of the value to speed up file reads.
CHUNK_SIZE=1044*20


class Connection(ConnectionBase):
    ''' raw socket accelerated connection '''

    transport = 'accelerate'
    has_pipelining = False
    become_methods = frozenset(C.BECOME_METHODS).difference(['runas'])

    def __init__(self, *args, **kwargs):

        super(Connection, self).__init__(*args, **kwargs)

        self.conn = None
        self.key = key_for_hostname(self._play_context.remote_addr)

    def _connect(self):
        ''' activates the connection object '''

        if not self._connected:
            wrong_user = False
            tries = 3
            self.conn = socket.socket()
            self.conn.settimeout(C.ACCELERATE_CONNECT_TIMEOUT)
            display.vvvv("attempting connection to %s via the accelerated port %d" % (self._play_context.remote_addr,self._play_context.accelerate_port))
            while tries > 0:
                try:
                    self.conn.connect((self._play_context.remote_addr,self._play_context.accelerate_port))
                    break
                except socket.error:
                    display.vvvv("connection to %s failed, retrying..." % self._play_context.remote_addr)
                    time.sleep(0.1)
                    tries -= 1
            if tries == 0:
                display.vvv("Could not connect via the accelerated connection, exceeded # of tries")
                raise AnsibleConnectionFailure("Failed to connect to %s on the accelerated port %s" % (self._play_context.remote_addr, self._play_context.accelerate_port))
            elif wrong_user:
                display.vvv("Restarting daemon with a different remote_user")
                raise AnsibleError("The accelerated daemon was started on the remote with a different user")

            self.conn.settimeout(C.ACCELERATE_TIMEOUT)
            if not self.validate_user():
                # the accelerated daemon was started with a
                # different remote_user. The above command
                # should have caused the accelerate daemon to
                # shutdown, so we'll reconnect.
                wrong_user = True

        self._connected = True
        return self

    def send_data(self, data):
        packed_len = struct.pack('!Q',len(data))
        return self.conn.sendall(packed_len + data)

    def recv_data(self):
        header_len = 8 # size of a packed unsigned long long
        data = b""
        try:
            display.vvvv("%s: in recv_data(), waiting for the header" % self._play_context.remote_addr)
            while len(data) < header_len:
                d = self.conn.recv(header_len - len(data))
                if not d:
                    display.vvvv("%s: received nothing, bailing out" % self._play_context.remote_addr)
                    return None
                data += d
            display.vvvv("%s: got the header, unpacking" % self._play_context.remote_addr)
            data_len = struct.unpack('!Q',data[:header_len])[0]
            data = data[header_len:]
            display.vvvv("%s: data received so far (expecting %d): %d" % (self._play_context.remote_addr,data_len,len(data)))
            while len(data) < data_len:
                d = self.conn.recv(data_len - len(data))
                if not d:
                    display.vvvv("%s: received nothing, bailing out" % self._play_context.remote_addr)
                    return None
                display.vvvv("%s: received %d bytes" % (self._play_context.remote_addr, len(d)))
                data += d
            display.vvvv("%s: received all of the data, returning" % self._play_context.remote_addr)
            return data
        except socket.timeout:
            raise AnsibleError("timed out while waiting to receive data")

    def validate_user(self):
        '''
        Checks the remote uid of the accelerated daemon vs. the
        one specified for this play and will cause the accel
        daemon to exit if they don't match
        '''

        display.vvvv("%s: sending request for validate_user" % self._play_context.remote_addr)
        data = dict(
            mode='validate_user',
            username=self._play_context.remote_user,
        )
        data = jsonify(data)
        data = keyczar_encrypt(self.key, data)
        if self.send_data(data):
            raise AnsibleError("Failed to send command to %s" % self._play_context.remote_addr)

        display.vvvv("%s: waiting for validate_user response" % self._play_context.remote_addr)
        while True:
            # we loop here while waiting for the response, because a
            # long running command may cause us to receive keepalive packets
            # ({"pong":"true"}) rather than the response we want.
            response = self.recv_data()
            if not response:
                raise AnsibleError("Failed to get a response from %s" % self._play_context.remote_addr)
            response = keyczar_decrypt(self.key, response)
            response = json.loads(response)
            if "pong" in response:
                # it's a keepalive, go back to waiting
                display.vvvv("%s: received a keepalive packet" % self._play_context.remote_addr)
                continue
            else:
                display.vvvv("%s: received the validate_user response: %s" % (self._play_context.remote_addr, response))
                break

        if response.get('failed'):
            return False
        else:
            return response.get('rc') == 0

    def exec_command(self, cmd, in_data=None, sudoable=True):

        ''' run a command on the remote host '''

        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        if in_data:
            raise AnsibleError("Internal Error: this module does not support optimized module pipelining")

        display.vvv("EXEC COMMAND %s" % cmd)

        data = dict(
            mode='command',
            cmd=cmd,
            executable=C.DEFAULT_EXECUTABLE,
        )
        data = jsonify(data)
        data = keyczar_encrypt(self.key, data)
        if self.send_data(data):
            raise AnsibleError("Failed to send command to %s" % self._play_context.remote_addr)

        while True:
            # we loop here while waiting for the response, because a
            # long running command may cause us to receive keepalive packets
            # ({"pong":"true"}) rather than the response we want.
            response = self.recv_data()
            if not response:
                raise AnsibleError("Failed to get a response from %s" % self._play_context.remote_addr)
            response = keyczar_decrypt(self.key, response)
            response = json.loads(response)
            if "pong" in response:
                # it's a keepalive, go back to waiting
                display.vvvv("%s: received a keepalive packet" % self._play_context.remote_addr)
                continue
            else:
                display.vvvv("%s: received the response" % self._play_context.remote_addr)
                break

        return (response.get('rc', None), response.get('stdout', ''), response.get('stderr', ''))

    def put_file(self, in_path, out_path):

        ''' transfer a file from local to remote '''
        display.vvv("PUT %s TO %s" % (in_path, out_path), host=self._play_context.remote_addr)

        if not os.path.exists(in_path):
            raise AnsibleFileNotFound("file or module does not exist: %s" % in_path)

        fd = file(in_path, 'rb')
        fstat = os.stat(in_path)
        try:
            display.vvv("PUT file is %d bytes" % fstat.st_size)
            last = False
            while fd.tell() <= fstat.st_size and not last:
                display.vvvv("file position currently %ld, file size is %ld" % (fd.tell(), fstat.st_size))
                data = fd.read(CHUNK_SIZE)
                if fd.tell() >= fstat.st_size:
                    last = True
                data = dict(mode='put', data=base64.b64encode(data), out_path=out_path, last=last)
                if self._play_context.become:
                    data['user'] = self._play_context.become_user
                data = jsonify(data)
                data = keyczar_encrypt(self.key, data)

                if self.send_data(data):
                    raise AnsibleError("failed to send the file to %s" % self._play_context.remote_addr)

                response = self.recv_data()
                if not response:
                    raise AnsibleError("Failed to get a response from %s" % self._play_context.remote_addr)
                response = keyczar_decrypt(self.key, response)
                response = json.loads(response)

                if response.get('failed',False):
                    raise AnsibleError("failed to put the file in the requested location")
        finally:
            fd.close()
            display.vvvv("waiting for final response after PUT")
            response = self.recv_data()
            if not response:
                raise AnsibleError("Failed to get a response from %s" % self._play_context.remote_addr)
            response = keyczar_decrypt(self.key, response)
            response = json.loads(response)

            if response.get('failed',False):
                raise AnsibleError("failed to put the file in the requested location")

    def fetch_file(self, in_path, out_path):
        ''' save a remote file to the specified path '''
        display.vvv("FETCH %s TO %s" % (in_path, out_path), host=self._play_context.remote_addr)

        data = dict(mode='fetch', in_path=in_path)
        data = jsonify(data)
        data = keyczar_encrypt(self.key, data)
        if self.send_data(data):
            raise AnsibleError("failed to initiate the file fetch with %s" % self._play_context.remote_addr)

        fh = open(out_path, "w")
        try:
            bytes = 0
            while True:
                response = self.recv_data()
                if not response:
                    raise AnsibleError("Failed to get a response from %s" % self._play_context.remote_addr)
                response = keyczar_decrypt(self.key, response)
                response = json.loads(response)
                if response.get('failed', False):
                    raise AnsibleError("Error during file fetch, aborting")
                out = base64.b64decode(response['data'])
                fh.write(out)
                bytes += len(out)
                # send an empty response back to signify we
                # received the last chunk without errors
                data = jsonify(dict())
                data = keyczar_encrypt(self.key, data)
                if self.send_data(data):
                    raise AnsibleError("failed to send ack during file fetch")
                if response.get('last', False):
                    break
        finally:
            # we don't currently care about this final response,
            # we just receive it and drop it. It may be used at some
            # point in the future or we may just have the put/fetch
            # operations not send back a final response at all
            response = self.recv_data()
            display.vvv("FETCH wrote %d bytes to %s" % (bytes, out_path))
            fh.close()

    def close(self):
        ''' terminate the connection '''
        # Be a good citizen
        try:
            self.conn.close()
        except:
            pass
