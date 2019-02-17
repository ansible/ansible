# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2015, 2017 Toshio Kuratomi <tkuratomi@ansible.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    connection: local
    short_description: execute on controller
    description:
        - This connection plugin allows ansible to execute tasks on the Ansible 'controller' instead of on a remote host.
    author: ansible (@core)
    version_added: historical
    notes:
        - The remote user is ignored, the user with which the ansible CLI was executed is used instead.
'''

import os
import shutil
import subprocess
import fcntl
import getpass

import ansible.constants as C
from ansible.compat import selectors
from ansible.errors import AnsibleError, AnsibleFileNotFound
from ansible.module_utils.six import text_type, binary_type
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.plugins.connection import ConnectionBase
from ansible.utils.display import Display

display = Display()


class Connection(ConnectionBase):
    ''' Local based connections '''

    transport = 'local'
    has_pipelining = True

    def _connect(self):
        ''' connect to the local host; nothing to do here '''

        # Because we haven't made any remote connection we're running as
        # the local user, rather than as whatever is configured in
        # remote_user.
        self._play_context.remote_user = getpass.getuser()

        if not self._connected:
            display.vvv(u"ESTABLISH LOCAL CONNECTION FOR USER: {0}".format(self._play_context.remote_user), host=self._play_context.remote_addr)
            self._connected = True
        return self

    def exec_command(self, cmd, in_data=None, sudoable=True):
        ''' run a command on the local host '''

        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        display.debug("in local.exec_command()")

        executable = C.DEFAULT_EXECUTABLE.split()[0] if C.DEFAULT_EXECUTABLE else None

        if not os.path.exists(to_bytes(executable, errors='surrogate_or_strict')):
            raise AnsibleError("failed to find the executable specified %s."
                               " Please verify if the executable exists and re-try." % executable)

        display.vvv(u"EXEC {0}".format(to_text(cmd)), host=self._play_context.remote_addr)
        display.debug("opening command with Popen()")

        if isinstance(cmd, (text_type, binary_type)):
            cmd = to_bytes(cmd)
        else:
            cmd = map(to_bytes, cmd)

        p = subprocess.Popen(
            cmd,
            shell=isinstance(cmd, (text_type, binary_type)),
            executable=executable,  # cwd=...
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        display.debug("done running command with Popen()")

        if self.become and self.become.expect_prompt() and sudoable:
            fcntl.fcntl(p.stdout, fcntl.F_SETFL, fcntl.fcntl(p.stdout, fcntl.F_GETFL) | os.O_NONBLOCK)
            fcntl.fcntl(p.stderr, fcntl.F_SETFL, fcntl.fcntl(p.stderr, fcntl.F_GETFL) | os.O_NONBLOCK)
            selector = selectors.DefaultSelector()
            selector.register(p.stdout, selectors.EVENT_READ)
            selector.register(p.stderr, selectors.EVENT_READ)

            become_output = b''
            try:
                while not self.become.check_success(become_output) and not self.become.check_password_prompt(become_output):
                    events = selector.select(self._play_context.timeout)
                    if not events:
                        stdout, stderr = p.communicate()
                        raise AnsibleError('timeout waiting for privilege escalation password prompt:\n' + to_native(become_output))

                    for key, event in events:
                        if key.fileobj == p.stdout:
                            chunk = p.stdout.read()
                        elif key.fileobj == p.stderr:
                            chunk = p.stderr.read()

                    if not chunk:
                        stdout, stderr = p.communicate()
                        raise AnsibleError('privilege output closed while waiting for password prompt:\n' + to_native(become_output))
                    become_output += chunk
            finally:
                selector.close()

            if not self.become.check_success(become_output):
                p.stdin.write(to_bytes(self._play_context.become_pass, errors='surrogate_or_strict') + b'\n')
            fcntl.fcntl(p.stdout, fcntl.F_SETFL, fcntl.fcntl(p.stdout, fcntl.F_GETFL) & ~os.O_NONBLOCK)
            fcntl.fcntl(p.stderr, fcntl.F_SETFL, fcntl.fcntl(p.stderr, fcntl.F_GETFL) & ~os.O_NONBLOCK)

        display.debug("getting output with communicate()")
        stdout, stderr = p.communicate(in_data)
        display.debug("done communicating")

        display.debug("done with local.exec_command()")
        return (p.returncode, stdout, stderr)

    def put_file(self, in_path, out_path):
        ''' transfer a file from local to local '''

        super(Connection, self).put_file(in_path, out_path)

        display.vvv(u"PUT {0} TO {1}".format(in_path, out_path), host=self._play_context.remote_addr)
        if not os.path.exists(to_bytes(in_path, errors='surrogate_or_strict')):
            raise AnsibleFileNotFound("file or module does not exist: {0}".format(to_native(in_path)))
        try:
            shutil.copyfile(to_bytes(in_path, errors='surrogate_or_strict'), to_bytes(out_path, errors='surrogate_or_strict'))
        except shutil.Error:
            raise AnsibleError("failed to copy: {0} and {1} are the same".format(to_native(in_path), to_native(out_path)))
        except IOError as e:
            raise AnsibleError("failed to transfer file to {0}: {1}".format(to_native(out_path), to_native(e)))

    def fetch_file(self, in_path, out_path):
        ''' fetch a file from local to local -- for compatibility '''

        super(Connection, self).fetch_file(in_path, out_path)

        display.vvv(u"FETCH {0} TO {1}".format(in_path, out_path), host=self._play_context.remote_addr)
        self.put_file(in_path, out_path)

    def close(self):
        ''' terminate the connection; nothing to do here '''
        self._connected = False
