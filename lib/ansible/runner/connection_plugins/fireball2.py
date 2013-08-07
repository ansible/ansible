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

import json
import os
import base64
import socket
from ansible.callbacks import vvv
from ansible import utils
from ansible import errors
from ansible import constants

class Connection(object):
    ''' raw socket accelerated connection '''

    def __init__(self, runner, host, port, *args, **kwargs):

        self.runner = runner

        # attempt to work around shared-memory funness
        if getattr(self.runner, 'aes_keys', None):
            utils.AES_KEYS = self.runner.aes_keys

        self.host = host
        self.context = None
        self.conn = None
        self.cipher = AES256Cipher()

        if  port is None:
            self.port = constants.FIREBALL2_PORT
        else:
            self.port = port

    def connect(self):
        ''' activates the connection object '''

        self.conn = socket.socket()
        self.conn.connect((self.host,self.port))

        return self

    def exec_command(self, cmd, tmp_path, sudo_user, sudoable=False, executable='/bin/sh'):
        ''' run a command on the remote host '''

        vvv("EXEC COMMAND %s" % cmd)

        data = dict(
            mode='command',
            cmd=cmd,
            tmp_path=tmp_path,
            executable=executable,
        )
        data = utils.jsonify(data)
        data = self.cipher.encrypt(data)
        if self.conn.sendall(data):
            raise errors.AnisbleError("Failed to send command to %s:%s" % (self.host,self.port))
        
        response = self.conn.recv(2048)
        response = self.cipher.decrypt(response)
        response = utils.parse_json(response)

        return (response.get('rc',None), '', response.get('stdout',''), response.get('stderr',''))

    def put_file(self, in_path, out_path):

        ''' transfer a file from local to remote '''
        vvv("PUT %s TO %s" % (in_path, out_path), host=self.host)

        if not os.path.exists(in_path):
            raise errors.AnsibleFileNotFound("file or module does not exist: %s" % in_path)

        data = base64.file(in_path).read()
        data = base64.b64encode(data)
        data = dict(mode='put', data=data, out_path=out_path)

        # TODO: support chunked file transfer
        data = utils.jsonify(data)
        data = self.cipher.encrypt(data)
        if self.conn.sendall(data):
            raise errors.AnsibleError("failed to send the file to %s:%s" % (self.host,self.port))

        response = self.conn.recv(2048)
        response = self.cipher.decrypt(response)
        response = utils.parse_json(response)

        # no meaningful response needed for this

    def fetch_file(self, in_path, out_path):
        ''' save a remote file to the specified path '''
        vvv("FETCH %s TO %s" % (in_path, out_path), host=self.host)

        data = dict(mode='fetch', in_path=in_path)
        data = utils.jsonify(data)
        data = self.cipher.encrypt(data)
        if self.conn.sendall(data):
            raise errors.AnsibleError("failed to initiate the file fetch with %s:%s" % (self.host,self.port))

        response = self.socket.recv(2048)
        response = self.cipher.decrypt(response)
        response = utils.parse_json(response)
        response = response['data']
        response = base64.b64decode(response)        

        fh = open(out_path, "w")
        fh.write(response)
        fh.close()

    def close(self):
        ''' terminate the connection '''
        # Be a good citizen
        try:
            self.conn.close()
        except:
            pass

