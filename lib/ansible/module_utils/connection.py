#
# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2017 Red Hat Inc.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import annotations

import os
import json
import pickle
import socket
import struct
import traceback
import uuid

from functools import partial
from ansible.module_utils.common.text.converters import to_bytes, to_text
from ansible.module_utils.common.json import AnsibleJSONEncoder
from ansible.module_utils.six import iteritems


def write_to_stream(stream, obj):
    """Write a length+newline-prefixed pickled object to a stream."""
    src = pickle.dumps(obj)

    stream.write(b'%d\n' % len(src))
    stream.write(src)


def send_data(s, data):
    packed_len = struct.pack('!Q', len(data))
    return s.sendall(packed_len + data)


def recv_data(s):
    header_len = 8  # size of a packed unsigned long long
    data = to_bytes("")
    while len(data) < header_len:
        d = s.recv(header_len - len(data))
        if not d:
            return None
        data += d
    data_len = struct.unpack('!Q', data[:header_len])[0]
    data = data[header_len:]
    while len(data) < data_len:
        d = s.recv(data_len - len(data))
        if not d:
            return None
        data += d
    return data


def exec_command(module, command):
    connection = Connection(module._socket_path)
    try:
        out = connection.exec_command(command)
    except ConnectionError as exc:
        code = getattr(exc, 'code', 1)
        message = getattr(exc, 'err', exc)
        return code, '', to_text(message, errors='surrogate_then_replace')
    return 0, out, ''


def request_builder(method_, *args, **kwargs):
    reqid = str(uuid.uuid4())
    req = {'jsonrpc': '2.0', 'method': method_, 'id': reqid}
    req['params'] = (args, kwargs)

    return req


class ConnectionError(Exception):

    def __init__(self, message, *args, **kwargs):
        super(ConnectionError, self).__init__(message)
        for k, v in iteritems(kwargs):
            setattr(self, k, v)


class Connection(object):

    def __init__(self, socket_path):
        if socket_path is None:
            raise AssertionError('socket_path must be a value')
        self.socket_path = socket_path

    def __getattr__(self, name):
        try:
            return self.__dict__[name]
        except KeyError:
            if name.startswith('_'):
                raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, name))
            return partial(self.__rpc__, name)

    def _exec_jsonrpc(self, name, *args, **kwargs):

        req = request_builder(name, *args, **kwargs)
        reqid = req['id']

        if not os.path.exists(self.socket_path):
            raise ConnectionError(
                'socket path %s does not exist or cannot be found. See Troubleshooting socket '
                'path issues in the Network Debug and Troubleshooting Guide' % self.socket_path
            )

        try:
            data = json.dumps(req, cls=AnsibleJSONEncoder, vault_to_text=True)
        except TypeError as exc:
            raise ConnectionError(
                "Failed to encode some variables as JSON for communication with the persistent connection helper. "
                "The original exception was: %s" % to_text(exc)
            )

        try:
            out = self.send(data)
        except socket.error as e:
            raise ConnectionError(
                'unable to connect to socket %s. See Troubleshooting socket path issues '
                'in the Network Debug and Troubleshooting Guide' % self.socket_path,
                err=to_text(e, errors='surrogate_then_replace'), exception=traceback.format_exc()
            )

        try:
            response = json.loads(out)
        except ValueError:
            # set_option(s) has sensitive info, and the details are unlikely to matter anyway
            if name.startswith("set_option"):
                raise ConnectionError(
                    "Unable to decode JSON from response to {0}. Received '{1}'.".format(name, out)
                )
            params = [repr(arg) for arg in args] + ['{0}={1!r}'.format(k, v) for k, v in iteritems(kwargs)]
            params = ', '.join(params)
            raise ConnectionError(
                "Unable to decode JSON from response to {0}({1}). Received '{2}'.".format(name, params, out)
            )

        if response['id'] != reqid:
            raise ConnectionError('invalid json-rpc id received')
        if "result_type" in response:
            response["result"] = pickle.loads(to_bytes(response["result"], errors="surrogateescape"))

        return response

    def __rpc__(self, name, *args, **kwargs):
        """Executes the json-rpc and returns the output received
           from remote device.
           :name: rpc method to be executed over connection plugin that implements jsonrpc 2.0
           :args: Ordered list of params passed as arguments to rpc method
           :kwargs: Dict of valid key, value pairs passed as arguments to rpc method

           For usage refer the respective connection plugin docs.
        """

        response = self._exec_jsonrpc(name, *args, **kwargs)

        if 'error' in response:
            err = response.get('error')
            msg = err.get('data') or err['message']
            code = err['code']
            raise ConnectionError(to_text(msg, errors='surrogate_then_replace'), code=code)

        return response['result']

    def send(self, data):
        try:
            sf = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sf.connect(self.socket_path)

            send_data(sf, to_bytes(data))
            response = recv_data(sf)

        except socket.error as e:
            sf.close()
            raise ConnectionError(
                'unable to connect to socket %s. See the socket path issue category in '
                'Network Debug and Troubleshooting Guide' % self.socket_path,
                err=to_text(e, errors='surrogate_then_replace'), exception=traceback.format_exc()
            )

        sf.close()

        return to_text(response, errors='surrogate_or_strict')
