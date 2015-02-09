# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
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

import traceback
import os
import pipes
import shutil
import subprocess
import select
import fcntl

from ansible.errors import AnsibleError
from ansible.plugins.connections import ConnectionBase

from ansible.utils.debug import debug

class Connection(ConnectionBase):
    ''' Local based connections '''

    def get_transport(self):
        ''' used to identify this connection object '''
        return 'local'

    def connect(self, port=None):
        ''' connect to the local host; nothing to do here '''
        return self

    def exec_command(self, cmd, tmp_path, executable='/bin/sh', in_data=None):
        ''' run a command on the local host '''

        debug("in local.exec_command()")
        # su requires to be run from a terminal, and therefore isn't supported here (yet?)
        if self._connection_info.su:
            raise AnsibleError("Internal Error: this module does not support running commands via su")

        if in_data:
            raise AnsibleError("Internal Error: this module does not support optimized module pipelining")

        # FIXME: su/sudo stuff needs to be generalized
        #if not self.runner.sudo or not sudoable:
        #    if executable:
        #        local_cmd = executable.split() + ['-c', cmd]
        #    else:
        #        local_cmd = cmd
        #else:
        #    local_cmd, prompt, success_key = utils.make_sudo_cmd(self.runner.sudo_exe, sudo_user, executable, cmd)
        if executable:
            local_cmd = executable.split() + ['-c', cmd]
        else:
            local_cmd = cmd

        executable = executable.split()[0] if executable else None

        self._display.vvv("%s EXEC %s" % (self._connection_info.remote_addr, local_cmd))
        # FIXME: cwd= needs to be set to the basedir of the playbook
        debug("opening command with Popen()")
        p = subprocess.Popen(
            local_cmd,
            shell=isinstance(local_cmd, basestring),
            executable=executable, #cwd=...
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        debug("done running command with Popen()")

        # FIXME: more su/sudo stuff
        #if self.runner.sudo and sudoable and self.runner.sudo_pass:
        #    fcntl.fcntl(p.stdout, fcntl.F_SETFL,
        #                fcntl.fcntl(p.stdout, fcntl.F_GETFL) | os.O_NONBLOCK)
        #    fcntl.fcntl(p.stderr, fcntl.F_SETFL,
        #                fcntl.fcntl(p.stderr, fcntl.F_GETFL) | os.O_NONBLOCK)
        #    sudo_output = ''
        #    while not sudo_output.endswith(prompt) and success_key not in sudo_output:
        #        rfd, wfd, efd = select.select([p.stdout, p.stderr], [],
        #                                      [p.stdout, p.stderr], self.runner.timeout)
        #        if p.stdout in rfd:
        #            chunk = p.stdout.read()
        #        elif p.stderr in rfd:
        #            chunk = p.stderr.read()
        #        else:
        #            stdout, stderr = p.communicate()
        #            raise AnsibleError('timeout waiting for sudo password prompt:\n' + sudo_output)
        #        if not chunk:
        #            stdout, stderr = p.communicate()
        #            raise AnsibleError('sudo output closed while waiting for password prompt:\n' + sudo_output)
        #        sudo_output += chunk
        #    if success_key not in sudo_output:
        #        p.stdin.write(self.runner.sudo_pass + '\n')
        #    fcntl.fcntl(p.stdout, fcntl.F_SETFL, fcntl.fcntl(p.stdout, fcntl.F_GETFL) & ~os.O_NONBLOCK)
        #    fcntl.fcntl(p.stderr, fcntl.F_SETFL, fcntl.fcntl(p.stderr, fcntl.F_GETFL) & ~os.O_NONBLOCK)

        debug("getting output with communicate()")
        stdout, stderr = p.communicate()
        debug("done communicating")

        debug("done with local.exec_command()")
        return (p.returncode, '', stdout, stderr)

    def put_file(self, in_path, out_path):
        ''' transfer a file from local to local '''

        #vvv("PUT %s TO %s" % (in_path, out_path), host=self.host)
        self._display.vvv("%s PUT %s TO %s" % (self._connection_info.remote_addr, in_path, out_path))
        if not os.path.exists(in_path):
            #raise AnsibleFileNotFound("file or module does not exist: %s" % in_path)
            raise AnsibleError("file or module does not exist: %s" % in_path)
        try:
            shutil.copyfile(in_path, out_path)
        except shutil.Error:
            traceback.print_exc()
            raise AnsibleError("failed to copy: %s and %s are the same" % (in_path, out_path))
        except IOError:
            traceback.print_exc()
            raise AnsibleError("failed to transfer file to %s" % out_path)

    def fetch_file(self, in_path, out_path):
        #vvv("FETCH %s TO %s" % (in_path, out_path), host=self.host)
        self._display.vvv("%s FETCH %s TO %s" % (self._connection_info.remote_addr, in_path, out_path))
        ''' fetch a file from local to local -- for copatibility '''
        self.put_file(in_path, out_path)

    def close(self):
        ''' terminate the connection; nothing to do here '''
        pass
