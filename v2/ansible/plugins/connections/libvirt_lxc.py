# Based on local.py (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# Based on chroot.py (c) 2013, Maykel Moya <mmoya@speedyrails.com>
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
import os
import subprocess
from ansible import errors
from ansible.callbacks import vvv
import ansible.constants as C

class Connection(object):
    ''' Local lxc based connections '''

    def _search_executable(self, executable):
        cmd = distutils.spawn.find_executable(executable)
        if not cmd:
            raise errors.AnsibleError("%s command not found in PATH") % executable
        return cmd

    def _check_domain(self, domain):
        p = subprocess.Popen([self.cmd, '-q', '-c', 'lxc:///', 'dominfo', domain],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.communicate()
        if p.returncode:
            raise errors.AnsibleError("%s is not a lxc defined in libvirt" % domain)

    def __init__(self, runner, host, port, *args, **kwargs):
        self.lxc = host

        self.cmd = self._search_executable('virsh')

        self._check_domain(host)

        self.runner = runner
        self.host = host
        # port is unused, since this is local
        self.port = port
        self.become_methods_supported=C.BECOME_METHODS

    def connect(self, port=None):
        ''' connect to the lxc; nothing to do here '''

        vvv("THIS IS A LOCAL LXC DIR", host=self.lxc)

        return self

    def _generate_cmd(self, executable, cmd):
        if executable:
            local_cmd = [self.cmd, '-q', '-c', 'lxc:///', 'lxc-enter-namespace', self.lxc, '--', executable , '-c', cmd]
        else:
            local_cmd = '%s -q -c lxc:/// lxc-enter-namespace %s -- %s' % (self.cmd, self.lxc, cmd)
        return local_cmd

    def exec_command(self, cmd, tmp_path, become_user, sudoable=False, executable='/bin/sh', in_data=None):
        ''' run a command on the chroot '''

        if sudoable and self.runner.become and self.runner.become_method not in self.become_methods_supported:
            raise errors.AnsibleError("Internal Error: this module does not support running commands via %s" % self.runner.become_method)

        if in_data:
            raise errors.AnsibleError("Internal Error: this module does not support optimized module pipelining")

        # We ignore privelege escalation!
        local_cmd = self._generate_cmd(executable, cmd)

        vvv("EXEC %s" % (local_cmd), host=self.lxc)
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

    def put_file(self, in_path, out_path):
        ''' transfer a file from local to lxc '''

        out_path = self._normalize_path(out_path, '/')
        vvv("PUT %s TO %s" % (in_path, out_path), host=self.lxc)
        
        local_cmd = [self.cmd, '-q', '-c', 'lxc:///', 'lxc-enter-namespace', self.lxc, '--', '/bin/tee', out_path]
        vvv("EXEC %s" % (local_cmd), host=self.lxc)

        p = subprocess.Popen(local_cmd, cwd=self.runner.basedir,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE) 
        stdout, stderr = p.communicate(open(in_path,'rb').read())
 
    def fetch_file(self, in_path, out_path):
        ''' fetch a file from lxc to local '''

        in_path = self._normalize_path(in_path, '/')
        vvv("FETCH %s TO %s" % (in_path, out_path), host=self.lxc)

        local_cmd = [self.cmd, '-q', '-c', 'lxc:///', 'lxc-enter-namespace', self.lxc, '--', '/bin/cat', in_path]
        vvv("EXEC %s" % (local_cmd), host=self.lxc)

        p = subprocess.Popen(local_cmd, cwd=self.runner.basedir,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        open(out_path,'wb').write(stdout)


    def close(self):
        ''' terminate the connection; nothing to do here '''
        pass
