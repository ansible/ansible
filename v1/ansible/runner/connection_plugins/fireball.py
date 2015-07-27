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
    ''' ZeroMQ accelerated connection '''

    def __init__(self, runner, host, port, *args, **kwargs):

        self.runner = runner
        self.has_pipelining = False

        # attempt to work around shared-memory funness
        if getattr(self.runner, 'aes_keys', None):
            utils.AES_KEYS = self.runner.aes_keys

        self.host = host
        self.key = utils.key_for_hostname(host)
        self.context = None
        self.socket = None

        if  port is None:
            self.port = constants.ZEROMQ_PORT
        else:
            self.port = port

        self.become_methods_supported=[]

    def connect(self):
        ''' activates the connection object '''

        if not HAVE_ZMQ:
            raise errors.AnsibleError("zmq is not installed")
        
        # this is rough/temporary and will likely be optimized later ...
        self.context = zmq.Context()
        socket = self.context.socket(zmq.REQ)
        addr = "tcp://%s:%s" % (self.host, self.port)
        socket.connect(addr)
        self.socket = socket

        return self

    def exec_command(self, cmd, tmp_path, become_user, sudoable=False, executable='/bin/sh', in_data=None):
        ''' run a command on the remote host '''

        if in_data:
            raise errors.AnsibleError("Internal Error: this module does not support optimized module pipelining")

        vvv("EXEC COMMAND %s" % cmd)

        if self.runner.become and sudoable:
            raise errors.AnsibleError(
                "When using fireball, do not specify sudo or su to run your tasks. " +
                "Instead sudo the fireball action with sudo. " +
                "Task will communicate with the fireball already running in sudo mode."
            )

        data = dict(
            mode='command',
            cmd=cmd,
            tmp_path=tmp_path,
            executable=executable,
        )
        data = utils.jsonify(data)
        data = utils.encrypt(self.key, data)
        self.socket.send(data)
        
        response = self.socket.recv()
        response = utils.decrypt(self.key, response)
        response = utils.parse_json(response)

        return (response.get('rc',None), '', response.get('stdout',''), response.get('stderr',''))

    def put_file(self, in_path, out_path):

        ''' transfer a file from local to remote '''
        vvv("PUT %s TO %s" % (in_path, out_path), host=self.host)

        if not os.path.exists(in_path):
            raise errors.AnsibleFileNotFound("file or module does not exist: %s" % in_path)
        data = file(in_path).read()
        data = base64.b64encode(data)

        data = dict(mode='put', data=data, out_path=out_path)
        # TODO: support chunked file transfer
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

        data = dict(mode='fetch', in_path=in_path)
        data = utils.jsonify(data)
        data = utils.encrypt(self.key, data)
        self.socket.send(data)

        response = self.socket.recv()
        response = utils.decrypt(self.key, response)
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
            self.socket.close()
            self.context.term()
        except:
            pass

