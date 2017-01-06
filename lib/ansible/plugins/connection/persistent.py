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
import pty
import subprocess
import sys

from ansible.module_utils._text import to_bytes
from ansible.module_utils.six.moves import cPickle, StringIO
from ansible.plugins.connection import ConnectionBase

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class Connection(ConnectionBase):
    ''' Local based connections '''

    transport = 'persistent'
    has_pipelining = False

    def _connect(self):

        self._connected = True
        return self

    def _do_it(self, action):

        master, slave = pty.openpty()
        p = subprocess.Popen(["ansible-connection"], stdin=slave, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdin = os.fdopen(master, 'wb', 0)
        os.close(slave)

        src = StringIO()
        cPickle.dump(self._play_context.serialize(), src)
        stdin.write(src.getvalue())
        src.close()

        stdin.write(b'\n#END_INIT#\n')
        stdin.write(to_bytes(action))
        stdin.write(b'\n\n')
        stdin.close()
        (stdout, stderr) = p.communicate()

        return (p.returncode, stdout, stderr)

    def exec_command(self, cmd, in_data=None, sudoable=True):
        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)
        return self._do_it('EXEC: ' + cmd)

    def put_file(self, in_path, out_path):
        super(Connection, self).put_file(in_path, out_path)
        self._do_it('PUT: %s %s' % (in_path, out_path))

    def fetch_file(self, in_path, out_path):
        super(Connection, self).fetch_file(in_path, out_path)
        self._do_it('FETCH: %s %s' % (in_path, out_path))

    def close(self):
        self._connected = False
