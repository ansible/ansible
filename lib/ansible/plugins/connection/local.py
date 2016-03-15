# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2015 Toshio Kuratomi <tkuratomi@ansible.com>
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
import shutil
import subprocess
import select
import fcntl
import getpass

from ansible.compat.six import text_type, binary_type

import ansible.constants as C

from ansible.errors import AnsibleError, AnsibleFileNotFound
from ansible.plugins.connection import ConnectionBase
from ansible.utils.unicode import to_bytes, to_str

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class Connection(ConnectionBase):
    ''' Local based connections '''

    @property
    def transport(self):
        ''' used to identify this connection object '''
        return 'local'

    def _connect(self):
        ''' connect to the local host; nothing to do here '''

        # Because we haven't made any remote connection we're running as
        # the local user, rather than as whatever is configured in
        # remote_user.
        self._play_context.remote_user = getpass.getuser()

        if not self._connected:
            display.vvv(u"ESTABLISH LOCAL CONNECTION FOR USER: {0}".format(self._play_context.remote_user, host=self._play_context.remote_addr))
            self._connected = True
        return self

    def exec_command(self, cmd, in_data=None, sudoable=True):
        ''' run a command on the local host '''

        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        display.debug("in local.exec_command()")

        if in_data:
            raise AnsibleError("Internal Error: this module does not support optimized module pipelining")
        executable = C.DEFAULT_EXECUTABLE.split()[0] if C.DEFAULT_EXECUTABLE else None

        display.vvv(u"{0} EXEC {1}".format(self._play_context.remote_addr, cmd))
        # FIXME: cwd= needs to be set to the basedir of the playbook
        display.debug("opening command with Popen()")

        if isinstance(cmd, (text_type, binary_type)):
            cmd = to_bytes(cmd)
        else:
            cmd = map(to_bytes, cmd)

        p = subprocess.Popen(
            cmd,
            shell=isinstance(cmd, basestring),
            executable=executable, #cwd=...
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        display.debug("done running command with Popen()")

        if self._play_context.prompt and sudoable:
            fcntl.fcntl(p.stdout, fcntl.F_SETFL, fcntl.fcntl(p.stdout, fcntl.F_GETFL) | os.O_NONBLOCK)
            fcntl.fcntl(p.stderr, fcntl.F_SETFL, fcntl.fcntl(p.stderr, fcntl.F_GETFL) | os.O_NONBLOCK)
            become_output = ''
            while not self.check_become_success(become_output) and not self.check_password_prompt(become_output):

                rfd, wfd, efd = select.select([p.stdout, p.stderr], [], [p.stdout, p.stderr], self._play_context.timeout)
                if p.stdout in rfd:
                    chunk = p.stdout.read()
                elif p.stderr in rfd:
                    chunk = p.stderr.read()
                else:
                    stdout, stderr = p.communicate()
                    raise AnsibleError('timeout waiting for privilege escalation password prompt:\n' + become_output)
                if not chunk:
                    stdout, stderr = p.communicate()
                    raise AnsibleError('privilege output closed while waiting for password prompt:\n' + become_output)
                become_output += chunk
            if not self.check_become_success(become_output):
                p.stdin.write(self._play_context.become_pass + '\n')
            fcntl.fcntl(p.stdout, fcntl.F_SETFL, fcntl.fcntl(p.stdout, fcntl.F_GETFL) & ~os.O_NONBLOCK)
            fcntl.fcntl(p.stderr, fcntl.F_SETFL, fcntl.fcntl(p.stderr, fcntl.F_GETFL) & ~os.O_NONBLOCK)

        display.debug("getting output with communicate()")
        stdout, stderr = p.communicate()
        display.debug("done communicating")

        display.debug("done with local.exec_command()")
        return (p.returncode, stdout, stderr)

    def put_file(self, in_path, out_path):
        ''' transfer a file from local to local '''

        super(Connection, self).put_file(in_path, out_path)

        display.vvv(u"{0} PUT {1} TO {2}".format(self._play_context.remote_addr, in_path, out_path))
        if not os.path.exists(to_bytes(in_path, errors='strict')):
            raise AnsibleFileNotFound("file or module does not exist: {0}".format(to_str(in_path)))
        try:
            shutil.copyfile(to_bytes(in_path, errors='strict'), to_bytes(out_path, errors='strict'))
        except shutil.Error:
            raise AnsibleError("failed to copy: {0} and {1} are the same".format(to_str(in_path), to_str(out_path)))
        except IOError as e:
            raise AnsibleError("failed to transfer file to {0}: {1}".format(to_str(out_path), to_str(e)))

    def fetch_file(self, in_path, out_path):
        ''' fetch a file from local to local -- for copatibility '''

        super(Connection, self).fetch_file(in_path, out_path)

        display.vvv(u"{0} FETCH {1} TO {2}".format(self._play_context.remote_addr, in_path, out_path))
        self.put_file(in_path, out_path)

    def close(self):
        ''' terminate the connection; nothing to do here '''
        self._connected = False
