# Based on local.py (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# and chroot.py     (c) 2013, Maykel Moya <mmoya@speedyrails.com>
# (c) 2013, Michael Scherer <misc@zarb.org>
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

import distutils.spawn
import traceback
import os
import shutil
import subprocess
from ansible import errors
from ansible.callbacks import vvv

class Connection(object):
    ''' Local chroot based connections '''

    def _search_executable(self, executable):
        cmd = distutils.spawn.find_executable(executable)
        if not cmd:
            raise errors.AnsibleError("%s command not found in PATH") % executable
        return cmd

    def list_jails(self):
        p = subprocess.Popen([self.jls_cmd, '-q', 'name'],
                             cwd=self.runner.basedir,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = p.communicate()

        return stdout.split()

    def get_jail_path(self):
        p = subprocess.Popen([self.jls_cmd, '-j', self.jail, '-q', 'path'],
                             cwd=self.runner.basedir,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = p.communicate()
        # remove \n
        return stdout[:-1]

 
        
    def __init__(self, runner, host, port, *args, **kwargs):
        self.jail = host
        self.runner = runner
        self.host = host
        self.has_pipelining = False

        if os.geteuid() != 0:
            raise errors.AnsibleError("jail connection requires running as root")

        self.jls_cmd = self._search_executable('jls')
        self.jexec_cmd = self._search_executable('jexec')
        
        if not self.jail in self.list_jails():
            raise errors.AnsibleError("incorrect jail name %s" % self.jail)


        self.host = host
        # port is unused, since this is local
        self.port = port

    def connect(self, port=None):
        ''' connect to the chroot; nothing to do here '''

        vvv("THIS IS A LOCAL CHROOT DIR", host=self.jail)

        return self

    # a modifier
    def _generate_cmd(self, executable, cmd):
        if executable:
            local_cmd = [self.jexec_cmd, self.jail, executable, '-c', cmd]
        else:
            local_cmd = '%s "%s" %s' % (self.jexec_cmd, self.jail, cmd)
        return local_cmd

    def exec_command(self, cmd, tmp_path, sudo_user=None, sudoable=False, executable='/bin/sh', in_data=None, su=None, su_user=None):
        ''' run a command on the chroot '''

        if su or su_user:
            raise errors.AnsibleError("Internal Error: this module does not support running commands via su")

        if in_data:
            raise errors.AnsibleError("Internal Error: this module does not support optimized module pipelining")

        # We enter chroot as root so sudo stuff can be ignored
        local_cmd = self._generate_cmd(executable, cmd)

        vvv("EXEC %s" % (local_cmd), host=self.jail)
        p = subprocess.Popen(local_cmd, shell=isinstance(local_cmd, basestring),
                             cwd=self.runner.basedir,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = p.communicate()
        return (p.returncode, '', stdout, stderr)

    def _normalize_path(self, path, prefix):
        if not path.startswith(os.path.sep):
            path = os.path.join(os.path.sep, path)
        normpath = os.path.normpath(path)
        return os.path.join(prefix, normpath[1:])

    def _copy_file(self, in_path, out_path):
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

    def put_file(self, in_path, out_path):
        ''' transfer a file from local to chroot '''

        out_path = self._normalize_path(out_path, self.get_jail_path())
        vvv("PUT %s TO %s" % (in_path, out_path), host=self.jail)

        self._copy_file(in_path, out_path)

    def fetch_file(self, in_path, out_path):
        ''' fetch a file from chroot to local '''

        in_path = self._normalize_path(in_path, self.get_jail_path())
        vvv("FETCH %s TO %s" % (in_path, out_path), host=self.jail)

        self._copy_file(in_path, out_path)

    def close(self):
        ''' terminate the connection; nothing to do here '''
        pass
