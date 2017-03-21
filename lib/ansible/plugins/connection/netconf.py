#
# (c) 2016 Red Hat Inc.
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

import os
import re
import socket
import json
import signal
import logging

from ansible import constants as C
from ansible.errors import AnsibleConnectionFailure, AnsibleError
from ansible.plugins.connection import ConnectionBase, ensure_connect
from ansible.module_utils.six.moves import StringIO

try:
    from ncclient import manager
    from ncclient.operations import RPCError
    from ncclient.transport.errors import SSHUnknownHostError
    from ncclient.xml_ import to_ele, to_xml
except ImportError:
    raise AnsibleError("ncclient is not installed")

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

logging.getLogger('ncclient').setLevel(logging.INFO)

class Connection(ConnectionBase):
    ''' NetConf connections '''

    transport = 'netconf'
    has_pipelining = False

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        self._network_os = self._play_context.network_os or 'default'
        display.display('network_os is set to %s' % self._network_os, log_only=True)

        self._manager = None
        self._connected = False

    def log(self, msg):
        msg = 'h=%s u=%s %s' % (self._play_context.remote_addr, self._play_context.remote_user, msg)
        logger.debug(msg)

    def _connect(self):
        super(Connection, self)._connect()

        display.display('ssh connection done, stating ncclient', log_only=True)

        allow_agent = True
        if self._play_context.password is not None:
            allow_agent = False

        key_filename = None
        if self._play_context.private_key_file:
            key_filename = os.path.expanduser(self._play_context.private_key_file)

        if not self._network_os:
            raise AnsibleConnectionError('network_os must be set for netconf connections')

        try:
            self._manager = manager.connect(
                host=self._play_context.remote_addr,
                port=self._play_context.port or 830,
                username=self._play_context.remote_user,
                password=self._play_context.password,
                key_filename=str(key_filename),
                hostkey_verify=C.HOST_KEY_CHECKING,
                look_for_keys=C.PARAMIKO_LOOK_FOR_KEYS,
                allow_agent=allow_agent,
                timeout=self._play_context.timeout,
                device_params={'name': self._network_os}
            )
        except SSHUnknownHostError as exc:
            raise AnsibleConnectionFailure(str(exc))

        if not self._manager.connected:
            return (1, '', 'not connected')

        display.display('ncclient manager object created successfully', log_only=True)

        self._connected = True
        return (0, self._manager.session_id, '')

    def close(self):
        if self._manager:
            self._manager.close_session()
            self._connected = False
        super(Connection, self).close()

    @ensure_connect
    def exec_command(self, request):
        """Sends the request to the node and returns the reply
        """
        if request == 'open_session()':
            return (0, 'ok', '')

        req = to_ele(request)
        if req is None:
            return (1, '', 'unable to parse request')

        try:
            reply = self._manager.rpc(req)
        except RPCError as exc:
            return (1, '', to_xml(exc.xml))

        return (0, reply.data_xml, '')

    def put_file(self, in_path, out_path):
        """Transfer a file from local to remote"""
        pass

    def fetch_file(self, in_path, out_path):
        """Fetch a file from remote to local"""
        pass

