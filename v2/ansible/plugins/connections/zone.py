# Based on local.py (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# and chroot.py     (c) 2013, Maykel Moya <mmoya@speedyrails.com>
# and jail.py       (c) 2013, Michael Scherer <misc@zarb.org>
# (c) 2015, Dagobert Michelsen <dam@baltic-online.de>
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
import traceback
import os
import shutil
import subprocess
from subprocess import Popen,PIPE
from ansible import errors
from ansible.callbacks import vvv
import ansible.constants as C

class Connection(object):
    ''' Local zone based connections '''

    def _search_executable(self, executable):
        cmd = distutils.spawn.find_executable(executable)
        if not cmd:
            raise errors.AnsibleError("%s command not found in PATH") % executable
        return cmd

    def list_zones(self):
        pipe = subprocess.Popen([self.zoneadm_cmd, 'list', '-ip'],
                             cwd=self.runner.basedir,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #stdout, stderr = p.communicate()
        zones = []
        for l in pipe.stdout.readlines():
          # 1:work:running:/zones/work:3126dc59-9a07-4829-cde9-a816e4c5040e:native:shared
          s = l.split(':')
          if s[1] != 'global':
            zones.append(s[1])

        return zones

    def get_zone_path(self):
        #solaris10vm# zoneadm -z cswbuild list -p         
        #-:cswbuild:installed:/zones/cswbuild:479f3c4b-d0c6-e97b-cd04-fd58f2c0238e:native:shared
        pipe = subprocess.Popen([self.zoneadm_cmd, '-z', self.zone, 'list', '-p'],
                             cwd=self.runner.basedir,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        #stdout, stderr = p.communicate()
        path = pipe.stdout.readlines()[0].split(':')[3]
        return path + '/root'
        
    def __init__(self, runner, host, port, *args, **kwargs):
        self.zone = host
        self.runner = runner
        self.host = host
        self.has_pipelining = False
        self.become_methods_supported=C.BECOME_METHODS

        if os.geteuid() != 0:
            raise errors.AnsibleError("zone connection requires running as root")

        self.zoneadm_cmd = self._search_executable('zoneadm')
        self.zlogin_cmd = self._search_executable('zlogin')
        
        if not self.zone in self.list_zones():
            raise errors.AnsibleError("incorrect zone name %s" % self.zone)


        self.host = host
        # port is unused, since this is local
        self.port = port

    def connect(self, port=None):
        ''' connect to the zone; nothing to do here '''

        vvv("THIS IS A LOCAL ZONE DIR", host=self.zone)

        return self

    # a modifier
    def _generate_cmd(self, executable, cmd):
        if executable:
            local_cmd = [self.zlogin_cmd, self.zone, executable, cmd]
        else:
            local_cmd = '%s "%s" %s' % (self.zlogin_cmd, self.zone, cmd)
        return local_cmd

    def exec_command(self, cmd, tmp_path, become_user=None, sudoable=False, executable=None, in_data=None):
        ''' run a command on the zone '''

        if sudoable and self.runner.become and self.runner.become_method not in self.become_methods_supported:
            raise errors.AnsibleError("Internal Error: this module does not support running commands via %s" % self.runner.become_method)

        if in_data:
            raise errors.AnsibleError("Internal Error: this module does not support optimized module pipelining")

        # We happily ignore privelege escalation
        if executable == '/bin/sh':
          executable = None
        local_cmd = self._generate_cmd(executable, cmd)

        vvv("EXEC %s" % (local_cmd), host=self.zone)
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
        ''' transfer a file from local to zone '''

        out_path = self._normalize_path(out_path, self.get_zone_path())
        vvv("PUT %s TO %s" % (in_path, out_path), host=self.zone)

        self._copy_file(in_path, out_path)

    def fetch_file(self, in_path, out_path):
        ''' fetch a file from zone to local '''

        in_path = self._normalize_path(in_path, self.get_zone_path())
        vvv("FETCH %s TO %s" % (in_path, out_path), host=self.zone)

        self._copy_file(in_path, out_path)

    def close(self):
        ''' terminate the connection; nothing to do here '''
        pass
