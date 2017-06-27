# Based on the docker connection plugin
#
# Connection plugin for building container images using buildah tool
#   https://github.com/projectatomic/buildah
#
# Written by: Tomas Tomecek (https://github.com/TomasTomecek)
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

import shlex

import subprocess

import ansible.constants as C
from ansible.module_utils._text import to_bytes
from ansible.plugins.connection import ConnectionBase, ensure_connect


try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


__metaclass__ = type


# this _has to be_ named Connection
class Connection(ConnectionBase):
    """
    This is a connection plugin for buildah: it uses buildah binary to interact with the containers
    """

    # String used to identify this Connection class from other classes
    transport = 'buildah'
    has_pipelining = True
    # TODO: add support to change user which initiates commands inside the container,
    #       seems like buildah doesn't support changing users
    become_methods = frozenset(C.BECOME_METHODS)

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        self._container_id = self._play_context.remote_addr
        self._connected = False
        # TODO: save actual user and print it

    def _connect(self):
        """ no persistent connection is being maintained; just set _connected to True """
        super(Connection, self)._connect()
        self._connected = True

    @ensure_connect
    def exec_command(self, cmd, in_data=None, sudoable=False):
        """ run specified command in a running OCI container using buildah """
        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        cmd_bytes = to_bytes(cmd, errors='surrogate_or_strict')
        cmd_args_list = shlex.split(cmd_bytes)

        local_cmd = ['buildah', 'run', '--', self._container_id]
        local_cmd += cmd_args_list
        local_cmd = [to_bytes(i, errors='surrogate_or_strict') for i in local_cmd]

        display.vvv("RUN %s" % (local_cmd,), host=self._container_id)
        p = subprocess.Popen(local_cmd, shell=False, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = p.communicate(in_data)
        stdout = to_bytes(stdout, errors='surrogate_or_strict')
        stderr = to_bytes(stderr, errors='surrogate_or_strict')
        display.vvvvv("STDOUT %s STDERR %s" % (stderr, stderr))
        return p.returncode, stdout, stderr

    def put_file(self, in_path, out_path):
        """ Place a local file located in 'in_path' inside container at 'out_path' """
        super(Connection, self).put_file(in_path, out_path)
        display.vvv("PUT %s TO %s" % (in_path, out_path), host=self._container_id)

        local_cmd = ['buildah', 'copy', '--', self._container_id, in_path, out_path]
        local_cmd = [to_bytes(i, errors='surrogate_or_strict') for i in local_cmd]

        display.vvv("RUN %s" % (local_cmd,), host=self._container_id)
        p = subprocess.Popen(local_cmd, shell=False, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = p.communicate()
        stdout = to_bytes(stdout, errors='surrogate_or_strict')
        stderr = to_bytes(stderr, errors='surrogate_or_strict')
        display.vvvvv("STDOUT %s STDERR %s" % (stdout, stderr))

    def fetch_file(self, in_path, out_path):
        """ obtain file specified via 'in_path' from the container and place it at 'out_path' """
        super(Connection, self).fetch_file(in_path, out_path)
        display.vvv("FETCH %s TO %s" % (in_path, out_path), host=self._container_id)
        local_cmd = ['buildah', 'run', '--', self._container_id, 'cat',
                     to_bytes(in_path, errors='surrogate_or_strict')]

        display.vvv("RUN %s" % (local_cmd,), host=self._container_id)
        with open(to_bytes(out_path, errors='surrogate_or_strict'), 'wb') as out_file:
            p = subprocess.Popen(local_cmd, shell=False, stdin=subprocess.PIPE,
                                 stdout=out_file, stderr=subprocess.PIPE)
            _, stderr = p.communicate()

        stderr = to_bytes(stderr, errors='surrogate_or_strict')
        display.vvvvv("STDERR %s" % (stderr, ))

    def close(self):
        """ no persistent connection is being maintained; just flip _connected to False """
        super(Connection, self).close()
        # TODO: we should probably get rid of ~/.ansible directory in the container
        self._connected = False
