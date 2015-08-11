# Based on the chroot connection plugin by Maykel Moya
#
# Connection plugin for configuring docker containers
# (c) 2014, Lorin Hochstein
# (c) 2015, Leendert Brouwer
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

import os
import subprocess
import time

from ansible import errors
from ansible.plugins.connections import ConnectionBase

BUFSIZE = 65536

class Connection(ConnectionBase):

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        if 'docker_command' in kwargs:
            self.docker_cmd = kwargs['docker_command']
        else:
            self.docker_cmd = 'docker'

    @property
    def transport(self):
        return 'docker'

    def _connect(self, port=None):
        """ Connect to the container. Nothing to do """
        return self

    def exec_command(self, cmd, tmp_path, sudo_user=None, sudoable=False,
                     executable='/bin/sh', in_data=None, su=None,
                     su_user=None):

        """ Run a command on the local host """

        # Don't currently support su
        if su or su_user:
            raise errors.AnsibleError("Internal Error: this module does not "
                                      "support running commands via su")

        if in_data:
            raise errors.AnsibleError("Internal Error: this module does not "
                                      "support optimized module pipelining")

        if sudoable and sudo_user:
            raise errors.AnsibleError("Internal Error: this module does not "
                                      "support running commands via sudo")

        if executable:
            local_cmd = [self.docker_cmd, "exec", self._play_context.remote_addr, executable,
                         '-c', cmd]
        else:
            local_cmd = '%s exec "%s" %s' % (self.docker_cmd, self._play_context.remote_addr, cmd)

        self._display.vvv("EXEC %s" % (local_cmd), host=self._play_context.remote_addr)
        p = subprocess.Popen(local_cmd,
                             shell=isinstance(local_cmd, basestring),
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = p.communicate()
        return (p.returncode, '', stdout, stderr)

    # Docker doesn't have native support for copying files into running
    # containers, so we use docker exec to implement this
    def put_file(self, in_path, out_path):
        """ Transfer a file from local to container """
        args = [self.docker_cmd, "exec", "-i", self._play_context.remote_addr, "bash", "-c",
                "dd of=%s bs=%s" % (format(out_path), BUFSIZE)]

        self._display.vvv("PUT %s TO %s" % (in_path, out_path), host=self._play_context.remote_addr)

        if not os.path.exists(in_path):
            raise errors.AnsibleFileNotFound(
                "file or module does not exist: %s" % in_path)
        p = subprocess.Popen(args, stdin=open(in_path),
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.communicate()

    def fetch_file(self, in_path, out_path):
        """ Fetch a file from container to local. """
        # out_path is the final file path, but docker takes a directory, not a
        # file path
        out_dir = os.path.dirname(out_path)

        args = [self.docker_cmd, "cp", "%s:%s" % (self._play_context.remote_addr, in_path), out_dir]

        self._display.vvv("FETCH %s TO %s" % (in_path, out_path), host=self._play_context.remote_addr)
        p = subprocess.Popen(args, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.communicate()

        # Rename if needed
        actual_out_path = os.path.join(out_dir, os.path.basename(in_path))
        if actual_out_path != out_path:
            os.rename(actual_out_path, out_path)

    def close(self):
        """ Terminate the connection. Nothing to do for Docker"""
        pass
