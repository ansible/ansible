# (c) 2017 Red Hat Inc.
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    author: Ansible Core Team
    connection: persistent
    short_description: Use a persistent unix socket for connection
    description:
        - This is a helper plugin to allow making other connections persistent.
    version_added: "2.3"
"""

import re
import os
import pty
import subprocess

from ansible.module_utils._text import to_bytes, to_text
from ansible.module_utils.six.moves import cPickle
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

        # Need to force a protocol that is compatible with both py2 and py3.
        # That would be protocol=2 or less.
        # Also need to force a protocol that excludes certain control chars as
        # stdin in this case is a pty and control chars will cause problems.
        # that means only protocol=0 will work.
        src = cPickle.dumps(self._play_context.serialize(), protocol=0)
        stdin.write(src)

        stdin.write(b'\n#END_INIT#\n')
        stdin.write(to_bytes(action))
        stdin.write(b'\n\n')

        (stdout, stderr) = p.communicate()
        stdin.close()

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

    def run(self):
        """Returns the path of the persistent connection socket.

        Attempts to ensure (within playcontext.timeout seconds) that the
        socket path exists. If the path exists (or the timeout has expired),
        returns the socket path.
        """
        socket_path = None
        rc, out, err = self._do_it('RUN:')
        match = re.search(br"#SOCKET_PATH#: (\S+)", out)
        if match:
            socket_path = to_text(match.group(1).strip(), errors='surrogate_or_strict')

        return socket_path
