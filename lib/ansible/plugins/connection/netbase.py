# (c) 2018 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible import constants as C
from ansible.plugins.connection import ConnectionBase
from ansible.plugins.loader import connection_loader
from ansible.utils.path import unfrackpath

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class NetworkConnectionBase(ConnectionBase):
    """
    A base class for network-style connections.
    """

    force_persistence = True
    # Do not use _remote_is_local in other connections
    _remote_is_local = True

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(NetworkConnectionBase, self).__init__(play_context, new_stdin, *args, **kwargs)

        self._network_os = self._play_context.network_os

        self._local = connection_loader.get('local', play_context, '/dev/null')
        self._local.set_options()

        self._implementation_plugins = []

        # reconstruct the socket_path and set instance values accordingly
        self._ansible_playbook_pid = kwargs.get('ansible_playbook_pid')
        self._update_connection_state()

    def __getattr__(self, name):
        try:
            return self.__dict__[name]
        except KeyError:
            if not name.startswith('_'):
                for plugin in self._implementation_plugins:
                    method = getattr(plugin, name, None)
                    if method is not None:
                        return method
            raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, name))

    def put_file(self, in_path, out_path):
        """Transfer a file from local to remote"""
        return self._local.put_file(in_path, out_path)

    def fetch_file(self, in_path, out_path):
        """Fetch a file from remote to local"""
        return self._local.fetch_file(in_path, out_path)

    def reset(self):
        '''
        Reset the connection
        '''
        if self._socket_path:
            display.vvvv('resetting persistent connection for socket_path %s' % self._socket_path, host=self._play_context.remote_addr)
            self.close()
        display.vvvv('reset call on connection instance', host=self._play_context.remote_addr)

    def close(self):
        if self._connected:
            self._connected = False
        self._implementation_plugins = []

    def _update_connection_state(self):
        '''
        Reconstruct the connection socket_path and check if it exists

        If the socket path exists then the connection is active and set
        both the _socket_path value to the path and the _connected value
        to True.  If the socket path doesn't exist, leave the socket path
        value to None and the _connected value to False
        '''
        ssh = connection_loader.get('ssh', class_only=True)
        control_path = ssh._create_control_path(
            self._play_context.remote_addr, self._play_context.port,
            self._play_context.remote_user, self._play_context.connection,
            self._ansible_playbook_pid
        )

        tmp_path = unfrackpath(C.PERSISTENT_CONTROL_PATH_DIR)
        socket_path = unfrackpath(control_path % dict(directory=tmp_path))

        if os.path.exists(socket_path):
            self._connected = True
            self._socket_path = socket_path
