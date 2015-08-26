# Based on local.py (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2013, Maykel Moya <mmoya@speedyrails.com>
# (c) 2015, Toshio Kuratomi <tkuratomi@ansible.com>
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

import distutils.spawn
import os
import shlex
import subprocess
import traceback

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.plugins.connections import ConnectionBase
from ansible.utils.path import is_executable
from ansible.utils.unicode import to_bytes


class Connection(ConnectionBase):
    ''' Local chroot based connections '''

    BUFSIZE = 65536
    has_pipelining = False

    def __init__(self, *args, **kwargs):

        super(Connection, self).__init__(*args, **kwargs)

        self.chroot = self._play_context.remote_addr

        if os.geteuid() != 0:
            raise AnsibleError("chroot connection requires running as root")

        # we're running as root on the local system so do some
        # trivial checks for ensuring 'host' is actually a chroot'able dir
        if not os.path.isdir(self.chroot):
            raise AnsibleError("%s is not a directory" % self.chroot)

        chrootsh = os.path.join(self.chroot, 'bin/sh')
        if not is_executable(chrootsh):
            raise AnsibleError("%s does not look like a chrootable dir (/bin/sh missing)" % self.chroot)

        self.chroot_cmd = distutils.spawn.find_executable('chroot')
        if not self.chroot_cmd:
            raise AnsibleError("chroot command not found in PATH")

    @property
    def transport(self):
        ''' used to identify this connection object '''
        return 'chroot'

    def _connect(self, port=None):
        ''' connect to the chroot; nothing to do here '''

        self._display.vvv("THIS IS A LOCAL CHROOT DIR", host=self.chroot)

        return self

    def _generate_cmd(self, executable, cmd):
        if executable:
            local_cmd = [self.chroot_cmd, self.chroot, executable, '-c', cmd]
        else:
            # Prev to python2.7.3, shlex couldn't handle unicode type strings
            cmd = to_bytes(cmd)
            cmd = shlex.split(cmd)
            local_cmd = [self.chroot_cmd, self.chroot]
            local_cmd += cmd
        return local_cmd

    def _buffered_exec_command(self, cmd, tmp_path, become_user=None, sudoable=False, executable='/bin/sh', in_data=None, stdin=subprocess.PIPE):
        ''' run a command on the chroot.  This is only needed for implementing
        put_file() get_file() so that we don't have to read the whole file
        into memory.

        compared to exec_command() it looses some niceties like being able to
        return the process's exit code immediately.
        '''

        if sudoable and self._play_context.become and self._play_context.become_method not in self.become_methods_supported:
            raise AnsibleError("Internal Error: this module does not support running commands via %s" % self._play_context.become_method)

        if in_data:
            raise AnsibleError("Internal Error: this module does not support optimized module pipelining")

        # We enter zone as root so we ignore privilege escalation (probably need to fix in case we have to become a specific used [ex: postgres admin])?
        local_cmd = self._generate_cmd(executable, cmd)

        self._display.vvv("EXEC %s" % (local_cmd), host=self.chroot)
        # FIXME: cwd= needs to be set to the basedir of the playbook, which
        #        should come from loader, but is not in the connection plugins
        p = subprocess.Popen(local_cmd, shell=False,
                             stdin=stdin,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        return p

    def exec_command(self, cmd, tmp_path, become_user=None, sudoable=False, executable='/bin/sh', in_data=None):
        ''' run a command on the chroot '''

        p = self._buffered_exec_command(cmd, tmp_path, become_user, sudoable, executable, in_data)

        stdout, stderr = p.communicate()
        return (p.returncode, '', stdout, stderr)

    def put_file(self, in_path, out_path):
        ''' transfer a file from local to chroot '''

        self._display.vvv("PUT %s TO %s" % (in_path, out_path), host=self.chroot)

        try:
            with open(in_path, 'rb') as in_file:
                try:
                    p = self._buffered_exec_command('dd of=%s bs=%s' % (out_path, self.BUFSIZE), None, stdin=in_file)
                except OSError:
                    raise AnsibleError("chroot connection requires dd command in the chroot")
                try:
                    stdout, stderr = p.communicate()
                except:
                    traceback.print_exc()
                    raise AnsibleError("failed to transfer file %s to %s" % (in_path, out_path))
                if p.returncode != 0:
                    raise AnsibleError("failed to transfer file %s to %s:\n%s\n%s" % (in_path, out_path, stdout, stderr))
        except IOError:
            raise AnsibleError("file or module does not exist at: %s" % in_path)

    def fetch_file(self, in_path, out_path):
        ''' fetch a file from chroot to local '''

        self._display.vvv("FETCH %s TO %s" % (in_path, out_path), host=self.chroot)

        try:
            p = self._buffered_exec_command('dd if=%s bs=%s' % (in_path, self.BUFSIZE), None)
        except OSError:
            raise AnsibleError("chroot connection requires dd command in the chroot")

        with open(out_path, 'wb+') as out_file:
            try:
                chunk = p.stdout.read(self.BUFSIZE)
                while chunk:
                    out_file.write(chunk)
                    chunk = p.stdout.read(self.BUFSIZE)
            except:
                traceback.print_exc()
                raise AnsibleError("failed to transfer file %s to %s" % (in_path, out_path))
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                raise AnsibleError("failed to transfer file %s to %s:\n%s\n%s" % (in_path, out_path, stdout, stderr))

    def close(self):
        ''' terminate the connection; nothing to do here '''
        pass
