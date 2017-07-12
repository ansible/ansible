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

import signal
import socket
import struct
import os
import uuid

from functools import partial

from ansible.module_utils.basic import get_exception
from ansible.module_utils._text import to_bytes, to_native, to_text


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
    try:
        sf = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sf.connect(module._socket_path)

        data = "EXEC: %s" % command
        send_data(sf, to_bytes(data.strip()))

        rc = int(recv_data(sf), 10)
        stdout = recv_data(sf)
        stderr = recv_data(sf)
    except socket.error:
        exc = get_exception()
        sf.close()
        module.fail_json(msg='unable to connect to socket', err=str(exc))

    sf.close()

    return rc, to_native(stdout, errors='surrogate_or_strict'), to_native(stderr, errors='surrogate_or_strict')


def request_builder(method, *args, **kwargs):
    reqid = str(uuid.uuid4())
    req = {'jsonrpc': '2.0', 'method': method, 'id': reqid}

    params = list(args) or kwargs or None
    if params:
        req['params'] = params

    return req


class Connection:

    def __init__(self, module):
        self._module = module

    def __getattr__(self, name):
        try:
            return self.__dict__[name]
        except KeyError:
            if name.startswith('_'):
                raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, name))
            return partial(self.__rpc__, name)

    def __rpc__(self, name, *args, **kwargs):
        """Executes the json-rpc and returns the output received
           from remote device.
           :name: rpc method to be executed over connection plugin that implements jsonrpc 2.0
           :args: Ordered list of params passed as arguments to rpc method
           :kwargs: Dict of valid key, value pairs passed as arguments to rpc method

           For usage refer the respective connection plugin docs.
        """
        req = request_builder(name, *args, **kwargs)
        reqid = req['id']

        if not self._module._socket_path:
            self._module.fail_json(msg='provider support not available for this host')

        if not os.path.exists(self._module._socket_path):
            self._module.fail_json(msg='provider socket does not exist, is the provider running?')

        try:
            data = self._module.jsonify(req)
            rc, out, err = exec_command(self._module, data)

        except socket.error:
            exc = get_exception()
            self._module.fail_json(msg='unable to connect to socket', err=str(exc))

        try:
            response = self._module.from_json(to_text(out, errors='surrogate_then_replace'))
        except ValueError as exc:
            self._module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))

        if response['id'] != reqid:
            self._module.fail_json(msg='invalid id received')

        if 'error' in response:
            msg = response['error'].get('data') or response['error']['message']
            self._module.fail_json(msg=to_text(msg, errors='surrogate_then_replace'))

        return response['result']
