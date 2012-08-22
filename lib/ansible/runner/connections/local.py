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
import shutil
import subprocess
from ansible import errors
from ansible.callback import vvv

class Connection(object):
    ''' Local based connections '''

    def __init__(self, runner, host, port):
        self.runner = runner
        self.host = host
        # port is unused, since this is local
        self.port = port 

    def connect(self, port=None):
        ''' connect to the local host; nothing to do here '''

        return self

    def exec_command(self, cmd, tmp_path, sudo_user, sudoable=False):
        ''' run a command on the local host '''

        if self.runner.sudo and sudoable:
            if self.runner.sudo_pass:
                # NOTE: if someone wants to add sudo w/ password to the local connection type, they are welcome
                # to do so.  The primary usage of the local connection is for crontab and kickstart usage however
                # so this doesn't seem to be a huge priority
                raise errors.AnsibleError("sudo with password is presently only supported on the 'paramiko' (SSH) and native 'ssh' connection types")
            cmd = "sudo -u {0} -s {1}".format(sudo_user, cmd)

        vvv("EXEC %s" % cmd, host=self.host)
        p = subprocess.Popen(cmd, shell=True, stdin=None,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        return ("", stdout, stderr)

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
