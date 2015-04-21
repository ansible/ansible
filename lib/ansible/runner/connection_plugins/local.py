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
from ansible import errors
from ansible import utils
from ansible.callbacks import vvv


class Connection(object):
    ''' Local based connections '''

    def __init__(self, runner, host, port, *args, **kwargs):
        self.runner = runner
        self.host = host
        # port is unused, since this is local
        self.port = port
        self.has_pipelining = False

        # TODO: add su(needs tty), pbrun, pfexec
        self.become_methods_supported=['sudo']

    def connect(self, port=None):
        ''' connect to the local host; nothing to do here '''

        return self

    def exec_command(self, cmd, tmp_path, become_user=None, sudoable=False, executable='/bin/sh', in_data=None):
        ''' run a command on the local host '''

        # su requires to be run from a terminal, and therefore isn't supported here (yet?)
        if sudoable and self.runner.become and self.runner.become_method not in self.become_methods_supported:
            raise errors.AnsibleError("Internal Error: this module does not support running commands via %s" % self.runner.become_method)

        if in_data:
            raise errors.AnsibleError("Internal Error: this module does not support optimized module pipelining")

        if self.runner.become and sudoable:
            local_cmd, prompt, success_key = utils.make_become_cmd(cmd, become_user, executable, self.runner.become_method, '-H', self.runner.become_exe)
        else:
            if executable:
                local_cmd = executable.split() + ['-c', cmd]
            else:
                local_cmd = cmd
        executable = executable.split()[0] if executable else None

        vvv("EXEC %s" % (local_cmd), host=self.host)
        p = subprocess.Popen(local_cmd, shell=isinstance(local_cmd, basestring),
                             cwd=self.runner.basedir, executable=executable,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if self.runner.become and sudoable and self.runner.become_pass:
            fcntl.fcntl(p.stdout, fcntl.F_SETFL,
                        fcntl.fcntl(p.stdout, fcntl.F_GETFL) | os.O_NONBLOCK)
            fcntl.fcntl(p.stderr, fcntl.F_SETFL,
                        fcntl.fcntl(p.stderr, fcntl.F_GETFL) | os.O_NONBLOCK)
            become_output = ''
            while success_key not in become_output:

                if prompt and become_output.endswith(prompt):
                    break
                if utils.su_prompts.check_su_prompt(become_output):
                    break

                rfd, wfd, efd = select.select([p.stdout, p.stderr], [],
                                              [p.stdout, p.stderr], self.runner.timeout)
                if p.stdout in rfd:
                    chunk = p.stdout.read()
                elif p.stderr in rfd:
                    chunk = p.stderr.read()
                else:
                    stdout, stderr = p.communicate()
                    raise errors.AnsibleError('timeout waiting for %s password prompt:\n' % self.runner.become_method + become_output)
                if not chunk:
                    stdout, stderr = p.communicate()
                    raise errors.AnsibleError('%s output closed while waiting for password prompt:\n' % self.runner.become_method + become_output)
                become_output += chunk
            if success_key not in become_output:
                p.stdin.write(self.runner.become_pass + '\n')
            fcntl.fcntl(p.stdout, fcntl.F_SETFL, fcntl.fcntl(p.stdout, fcntl.F_GETFL) & ~os.O_NONBLOCK)
            fcntl.fcntl(p.stderr, fcntl.F_SETFL, fcntl.fcntl(p.stderr, fcntl.F_GETFL) & ~os.O_NONBLOCK)

        stdout, stderr = p.communicate()
        return (p.returncode, '', stdout, stderr)

    def put_file(self, in_path, out_path):
        ''' transfer a file from local to local '''

        vvv("PUT %s TO %s" % (in_path, out_path), host=self.host)
        if not os.path.exists(in_path):
            raise errors.AnsibleFileNotFound("file or module does not exist: %s" % in_path)
        try:
            shutil.copyfile(in_path, out_path)
        except shutil.Error:
            traceback.print_exc()
            raise errors.AnsibleError("failed to copy: %s and %s are the same" % (in_path, out_path))
        except IOError:
            traceback.print_exc()
            raise errors.AnsibleError("failed to transfer file to %s" % out_path)

    def fetch_file(self, in_path, out_path):
        vvv("FETCH %s TO %s" % (in_path, out_path), host=self.host)
        ''' fetch a file from local to local -- for copatibility '''
        self.put_file(in_path, out_path)

    def close(self):
        ''' terminate the connection; nothing to do here '''
        pass
