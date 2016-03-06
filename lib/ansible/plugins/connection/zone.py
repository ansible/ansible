# Based on local.py (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# and chroot.py     (c) 2013, Maykel Moya <mmoya@speedyrails.com>
# and jail.py       (c) 2013, Michael Scherer <misc@zarb.org>
# (c) 2015, Dagobert Michelsen <dam@baltic-online.de>
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
import os.path
import pipes
import subprocess
import traceback

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.plugins.connection import ConnectionBase
from ansible.utils import to_bytes

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

BUFSIZE = 65536


class Connection(ConnectionBase):
    ''' Local zone based connections '''

    transport = 'zone'
    has_pipelining = True
    become_methods = frozenset(C.BECOME_METHODS).difference(('su',))

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        self.zone = self._play_context.remote_addr

        if os.geteuid() != 0:
            raise AnsibleError("zone connection requires running as root")

        self.zoneadm_cmd = to_bytes(self._search_executable('zoneadm'))
        self.zlogin_cmd = to_bytes(self._search_executable('zlogin'))

        if self.zone not in self.list_zones():
            raise AnsibleError("incorrect zone name %s" % self.zone)

    @staticmethod
    def _search_executable(executable):
        cmd = distutils.spawn.find_executable(executable)
        if not cmd:
            raise AnsibleError("%s command not found in PATH") % executable
        return cmd

    def list_zones(self):
        process = subprocess.Popen([self.zoneadm_cmd, 'list', '-ip'],
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        zones = []
        for l in process.stdout.readlines():
            # 1:work:running:/zones/work:3126dc59-9a07-4829-cde9-a816e4c5040e:native:shared
            s = l.split(':')
            if s[1] != 'global':
                zones.append(s[1])

        return zones

    def get_zone_path(self):
        #solaris10vm# zoneadm -z cswbuild list -p
        #-:cswbuild:installed:/zones/cswbuild:479f3c4b-d0c6-e97b-cd04-fd58f2c0238e:native:shared
        process = subprocess.Popen([self.zoneadm_cmd, '-z', to_bytes(self.zone), 'list', '-p'],
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        #stdout, stderr = p.communicate()
        path = process.stdout.readlines()[0].split(':')[3]
        return path + '/root'

    def _connect(self):
        ''' connect to the zone; nothing to do here '''
        super(Connection, self)._connect()
        if not self._connected:
            display.vvv("THIS IS A LOCAL ZONE DIR", host=self.zone)
            self._connected = True

    def _buffered_exec_command(self, cmd, stdin=subprocess.PIPE):
        ''' run a command on the zone.  This is only needed for implementing
        put_file() get_file() so that we don't have to read the whole file
        into memory.

        compared to exec_command() it looses some niceties like being able to
        return the process's exit code immediately.
        '''
        # Note: zlogin invokes a shell (just like ssh does) so we do not pass
        # this through /bin/sh -c here.  Instead it goes through the shell
        # that zlogin selects.
        local_cmd = [self.zlogin_cmd, self.zone, cmd]
        local_cmd = map(to_bytes, local_cmd)

        display.vvv("EXEC %s" % (local_cmd), host=self.zone)
        p = subprocess.Popen(local_cmd, shell=False, stdin=stdin,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        return p

    def exec_command(self, cmd, in_data=None, sudoable=False):
        ''' run a command on the zone '''
        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        p = self._buffered_exec_command(cmd)

        stdout, stderr = p.communicate(in_data)
        return (p.returncode, stdout, stderr)

    def _prefix_login_path(self, remote_path):
        ''' Make sure that we put files into a standard path

            If a path is relative, then we need to choose where to put it.
            ssh chooses $HOME but we aren't guaranteed that a home dir will
            exist in any given chroot.  So for now we're choosing "/" instead.
            This also happens to be the former default.

            Can revisit using $HOME instead if it's a problem
        '''
        if not remote_path.startswith(os.path.sep):
            remote_path = os.path.join(os.path.sep, remote_path)
        return os.path.normpath(remote_path)

    def put_file(self, in_path, out_path):
        ''' transfer a file from local to zone '''
        super(Connection, self).put_file(in_path, out_path)
        display.vvv("PUT %s TO %s" % (in_path, out_path), host=self.zone)

        out_path = pipes.quote(self._prefix_login_path(out_path))
        try:
            with open(in_path, 'rb') as in_file:
                try:
                    p = self._buffered_exec_command('dd of=%s bs=%s' % (out_path, BUFSIZE), stdin=in_file)
                except OSError:
                    raise AnsibleError("jail connection requires dd command in the jail")
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
        ''' fetch a file from zone to local '''
        super(Connection, self).fetch_file(in_path, out_path)
        display.vvv("FETCH %s TO %s" % (in_path, out_path), host=self.zone)

        in_path = pipes.quote(self._prefix_login_path(in_path))
        try:
            p = self._buffered_exec_command('dd if=%s bs=%s' % (in_path, BUFSIZE))
        except OSError:
            raise AnsibleError("zone connection requires dd command in the zone")

        with open(out_path, 'wb+') as out_file:
            try:
                chunk = p.stdout.read(BUFSIZE)
                while chunk:
                    out_file.write(chunk)
                    chunk = p.stdout.read(BUFSIZE)
            except:
                traceback.print_exc()
                raise AnsibleError("failed to transfer file %s to %s" % (in_path, out_path))
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                raise AnsibleError("failed to transfer file %s to %s:\n%s\n%s" % (in_path, out_path, stdout, stderr))

    def close(self):
        ''' terminate the connection; nothing to do here '''
        super(Connection, self).close()
        self._connected = False
