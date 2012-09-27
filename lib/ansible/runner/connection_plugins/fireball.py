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
from ansible.callbacks import vvv
from ansible import utils
from ansible import errors
from ansible import constants

HAVE_ZMQ=False

try:
    import zmq
    HAVE_ZMQ=True
except ImportError:
    pass

class Connection(object):
    ''' SSH based connections with Paramiko '''

    def __init__(self, runner, host, port=None):

        self.runner = runner

        # attempt to work around shared-memory funness
        if getattr(self.runner, 'aes_keys', None):
            utils.AES_KEYS = self.runner.aes_keys

        self.host = host
        self.key = utils.key_for_hostname(host)
        self.socket = None
        # port passed in is the SSH port, which we ignore
        self.port = constants.ZEROMQ_PORT
  
    def connect(self):
        ''' activates the connection object '''

        if not HAVE_ZMQ:
            raise errors.AnsibleError("zmq is not installed")
        
        # this is rough/temporary and will likely be optimized later ...
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        addr = "tcp://%s:%s" % (self.host, self.port)
        socket.connect(addr)
        self.socket = socket    

        return self

    def exec_command(self, cmd, tmp_path, sudo_user, sudoable=False):
        ''' run a command on the remote host '''

        vvv("EXEC COMMAND %s" % cmd)

        if self.runner.sudo and sudoable:
            raise errors.AnsibleError("fireball does not use sudo, but runs as whoever it was initiated as.  (That itself is where to use sudo).")

        data = dict(
            mode='command',
            cmd=cmd,
            tmp_path=tmp_path,
        )
        data = utils.jsonify(data)
        data = utils.encrypt(self.key, data)
        self.socket.send(data)
        
        response = self.socket.recv()
        response = utils.decrypt(self.key, response)
        response = utils.parse_json(response)

        return ('', response.get('stdout',''), response.get('stderr',''))

    def put_file(self, in_path, out_path):

        ''' transfer a file from local to remote '''
        vvv("PUT %s TO %s" % (in_path, out_path), host=self.host)

        if not os.path.exists(in_path):
            raise errors.AnsibleFileNotFound("file or module does not exist: %s" % in_path)
        data = file(in_path).read()
        
        data = dict(mode='put', data=data, out_path=out_path)
        data = utils.jsonify(data)
        data = utils.encrypt(self.key, data)
        self.socket.send(data)

        response = self.socket.recv()
        response = utils.decrypt(self.key, response)
        response = utils.parse_json(response)

        # no meaningful response needed for this

    def fetch_file(self, in_path, out_path):
        ''' save a remote file to the specified path '''
        vvv("FETCH %s TO %s" % (in_path, out_path), host=self.host)

        data = dict(mode='fetch', file=in_path)
        data = utils.jsonify(data)
        data = utils.encrypt(self.key, data)
        self.socket.send(data)

        response = self.socket.recv()
        response = utils.decrypt(self.key, response)
        response = utils.parse_json(response)
        response = response['data']

        fh = open(out_path, "w")
        fh.write(response)
        fh.close()

    def close(self):
        ''' terminate the connection '''
        # no need for this

