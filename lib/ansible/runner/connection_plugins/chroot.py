# Based on local.py (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2013, Maykel Moya <mmoya@speedyrails.com>
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
from ansible import utils
from ansible.callbacks import vvv

class Connection(object):
    ''' Local chroot based connections '''

    def __init__(self, runner, host, port, *args, **kwargs):
        self.chroot = host
        self.has_pipelining = False

        if os.geteuid() != 0:
            raise errors.AnsibleError("chroot connection requires running as root")

        # we're running as root on the local system so do some
        # trivial checks for ensuring 'host' is actually a chroot'able dir
        if not os.path.isdir(self.chroot):
            raise errors.AnsibleError("%s is not a directory" % self.chroot)

        chrootsh = os.path.join(self.chroot, 'bin/sh')
        if not utils.is_executable(chrootsh):
            raise errors.AnsibleError("%s does not look like a chrootable dir (/bin/sh missing)" % self.chroot)

        self.chroot_cmd = distutils.spawn.find_executable('chroot')
        if not self.chroot_cmd:
            raise errors.AnsibleError("chroot command not found in PATH")

        self.runner = runner
        self.host = host
        # port is unused, since this is local
        self.port = port

    def connect(self, port=None):
        ''' connect to the chroot; nothing to do here '''

        vvv("THIS IS A LOCAL CHROOT DIR", host=self.chroot)

        return self

    def exec_command(self, cmd, tmp_path, sudo_user=None, sudoable=False, executable='/bin/sh', in_data=None, su=None, su_user=None):
        ''' run a command on the chroot '''

        if su or su_user:
            raise errors.AnsibleError("Internal Error: this module does not support running commands via su")

        if in_data:
            raise errors.AnsibleError("Internal Error: this module does not support optimized module pipelining")

        # We enter chroot as root so sudo stuff can be ignored

        if executable:
            local_cmd = [self.chroot_cmd, self.chroot, executable, '-c', cmd]
        else:
            local_cmd = '%s "%s" %s' % (self.chroot_cmd, self.chroot, cmd)

        vvv("EXEC %s" % (local_cmd), host=self.chroot)
        p = subprocess.Popen(local_cmd, shell=isinstance(local_cmd, basestring),
                             cwd=self.runner.basedir,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = p.communicate()
        return (p.returncode, '', stdout, stderr)

    def put_file(self, in_path, out_path):
        ''' transfer a file from local to chroot '''

        if not out_path.startswith(os.path.sep):
            out_path = os.path.join(os.path.sep, out_path)
        normpath = os.path.normpath(out_path)
        out_path = os.path.join(self.chroot, normpath[1:])

        vvv("PUT %s TO %s" % (in_path, out_path), host=self.chroot)
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
        ''' fetch a file from chroot to local '''

        if not in_path.startswith(os.path.sep):
            in_path = os.path.join(os.path.sep, in_path)
        normpath = os.path.normpath(in_path)
        in_path = os.path.join(self.chroot, normpath[1:])

        vvv("FETCH %s TO %s" % (in_path, out_path), host=self.chroot)
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

    def close(self):
        ''' terminate the connection; nothing to do here '''
        pass
