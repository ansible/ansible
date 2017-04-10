# (c) 2016 Matt Clay <matt@mystile.com>
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
from distutils.spawn import find_executable
from subprocess import call, Popen, PIPE

from ansible.errors import AnsibleError, AnsibleConnectionFailure, AnsibleFileNotFound
from ansible.module_utils._text import to_bytes, to_text
from ansible.plugins.connection import ConnectionBase


class Connection(ConnectionBase):
    """ lxd based connections """

    transport = "lxd"
    has_pipelining = True

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        self._host = self._play_context.remote_addr
        self._lxc_cmd = find_executable("lxc")

        if not self._lxc_cmd:
            raise AnsibleError("lxc command not found in PATH")

        if self._play_context.remote_user is not None and self._play_context.remote_user != 'root':
            self._display.warning('lxd does not support remote_user, using container default: root')

    def _connect(self):
        """connect to lxd (nothing to do here) """
        super(Connection, self)._connect()

        if not self._connected:
            self._display.vvv(u"ESTABLISH LXD CONNECTION FOR USER: root", host=self._host)
            self._connected = True

    def exec_command(self, cmd, in_data=None, sudoable=True):
        """ execute a command on the lxd host """
        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        self._display.vvv(u"EXEC {0}".format(cmd), host=self._host)

        local_cmd = [self._lxc_cmd, "exec", self._host, "--", self._play_context.executable, "-c", cmd]

        local_cmd = [to_bytes(i, errors='surrogate_or_strict') for i in local_cmd]
        in_data = to_bytes(in_data, errors='surrogate_or_strict', nonstring='passthru')

        process = Popen(local_cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate(in_data)

        stdout = to_text(stdout)
        stderr = to_text(stderr)

        if stderr == "error: Container is not running.\n":
            raise AnsibleConnectionFailure("container not running: %s" % self._host)

        if stderr == "error: not found\n":
            raise AnsibleConnectionFailure("container not found: %s" % self._host)

        return process.returncode, stdout, stderr

    def put_file(self, in_path, out_path):
        """ put a file from local to lxd """
        super(Connection, self).put_file(in_path, out_path)

        self._display.vvv(u"PUT {0} TO {1}".format(in_path, out_path), host=self._host)

        if not os.path.isfile(to_bytes(in_path, errors='surrogate_or_strict')):
            raise AnsibleFileNotFound("input path is not a file: %s" % in_path)

        local_cmd = [self._lxc_cmd, "file", "push", in_path, self._host + "/" + out_path]

        local_cmd = [to_bytes(i, errors='surrogate_or_strict') for i in local_cmd]

        call(local_cmd)

    def fetch_file(self, in_path, out_path):
        """ fetch a file from lxd to local """
        super(Connection, self).fetch_file(in_path, out_path)

        self._display.vvv(u"FETCH {0} TO {1}".format(in_path, out_path), host=self._host)

        local_cmd = [self._lxc_cmd, "file", "pull", self._host + "/" + in_path, out_path]

        local_cmd = [to_bytes(i, errors='surrogate_or_strict') for i in local_cmd]

        call(local_cmd)

    def close(self):
        """ close the connection (nothing to do here) """
        super(Connection, self).close()

        self._connected = False
