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

    return rc, to_native(stdout), to_native(stderr)


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
           rpc method can be executed over cliconf or netconf based on connection type
          Spec for cliconf rpc:
            :name: name of rpc method to be executed
              List of supported rpc names:
                :get_config: Retrieves the specified configuration from the device
                :edit_config: Loads the specified commands into the remote device
                :get: Execute specified command on remote device
                :get_capabilities: Retrieves device information and supported rpc methods
                :commit: Load configuration from candidate to running
                :discard_changes: Discard changes to candidate datastore

              Note: List of supported rpc's for remote device can be extracted from
                    output of get_capabilities()

            :arg: It is positional list passed as arguments to rpc method.
                get_config: arg[0] source: Datastore from which configuration should be retrieved
                                   eg: running/candidate/startup. (optional)
                                   Default is running.
                            arg[1] format: Output format in which configuration is retrieved
                                   Note: Specified datastore should be supported by remote device.
                edit_config: arg[0] command: List of configuration commands
                get: arg[0] command: command in string format to be executed on remote device
                     arg[1] prompt: the expected prompt generated by executing command.
                                    This can be a string or a list of strings (optional)
                     arg[2] answer: the string to respond to the prompt with (optional)
                     arg[3] sendonly: bool to disable waiting for response, default is false (optional)
                commit: arg[0] comment: Commit comment
            :kwargs: It is dictionary passed as argument to rpc method.
                :command: the command string to execute
                :prompt: the expected prompt generated by executing command.
                    This can be a string or a list of strings
                :answer: the string to respond to the prompt with
                :sendonly: bool to disable waiting for response
                :source: Datastore from which configuration should be retrieved (applicable for get_config())
                :comment: Commit comment (applicable for commit())
                :format: Output format in which configuration is retrieved (applicable for get_config())
            :returns: Returns output received from remote device as byte string

            Usage:
            conn = Connection()
            conn.get('show lldp neighbors detail'')
            conn.get_config('running')
            conn.edit_config(['hostname test', 'netconf ssh'])

       Spec for netconf rpc:
        :name: name of rpc method to be executed
          List of supported rpc names:
            :get_config: Retrieves the specified configuration from the device
            :edit_config: Loads the specified commands into the remote device
            :get: Execute specified command on remote device
            :get_capabilities: Retrieves device information and supported rpc methods
            :commit: Load configuration from candidate to running
            :discard_changes: Discard changes to candidate datastore
            :validate: Validate the contents of the specified configuration.
            :lock: Allows the client to lock the configuration system of a device.
            :unlock: Release a configuration lock, previously obtained with the lock operation.
            :copy_config: create or replace an entire configuration datastore with the contents of another complete
                          configuration datastore.
            For JUNOS:
            :execute_rpc: RPC to be execute on remote device
            :load_configuration: Loads given configuration on device

        Note: rpc support depends on the capabilites of remote device.

        :returns: Returns output received from remote device as byte string
        Note: the 'result' or 'error' from response should to be converted to object
              of ElementTree using 'fromstring' to parse output from device as xml doc
              'get_capabilities()' returns 'result' as a json string.
            Usage:
            conn = Connection()
            data = conn.execute_rpc(rpc)
            reply = fromstring(reply)

            data = conn.get_capabilities()
            json.loads(data)

            conn.load_configuration(config=[''set system ntp server 1.1.1.1''], action='set', format='text')
        """

        reqid = str(uuid.uuid4())
        req = {'jsonrpc': '2.0', 'method': name, 'id': reqid}

        params = list(args) or kwargs or None
        if params:
            req['params'] = params

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
