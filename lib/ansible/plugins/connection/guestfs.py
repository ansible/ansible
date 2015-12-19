# Based on local.py (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2013, Maykel Moya <mmoya@speedyrails.com>
# (c) 2015, Toshio Kuratomi <tkuratomi@ansible.com>
# (c) 2015, Michael Scherer <mscherer@redhat.com>
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

import os
import os.path
try:
    import guestfs
except ImportError:
    raise AnsibleError("guestfs python bindings are not installed")

import json
import re

from ansible.errors import AnsibleError
from ansible.plugins.connection import ConnectionBase
from ansible.module_utils._text import to_native

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

# keep that code python2 and python3 compliant
# we need to set $HOME so we are not left with
# .ansible directory on /
# also, I kept it {} free for clarity, hence the use of
# disct instead of the short form with brackets.
EXECUTION_SCRIPT = """
import sys
import json
import os
from subprocess import PIPE, Popen

os.environ['HOME'] = '{}'

cmd_file = sys.argv[1]
if not os.path.exists(cmd_file):
    sys.exit(1)

cmd = json.loads(open(cmd_file).read())
if type(cmd) == type(u''):
    cmd = cmd.encode('UTF-8')
r = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
(stdout, stderr) = r.communicate()

output = dict()
output['rc'] = r.returncode
output['stdout'] = stdout.decode('UTF-8')
output['stderr'] = stderr.decode('UTF-8')

json.dump(output, open(cmd_file + '.out', 'w'))
"""


class Connection(ConnectionBase):
    ''' Libguestfs based connections '''

    transport = 'guestfs'
    # not sure how it would react, so better disable it
    has_pipelining = False

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin,
                                         *args, **kwargs)

        self.disk = self._play_context.remote_addr

        if not os.path.isfile(self.disk):
            raise AnsibleError("%s is not a file, aborting" % self.disk)

        self.guestfs = guestfs.GuestFS(python_return_dict=True)

        self.guestfs.add_drive_opts(self.disk)

    def _find_python(self):
        ''' find what python to use '''
        self._python = None
        for p in ('python', 'python3'):
            try:
                python_version = self.guestfs.sh('%s -V' % p)
                self._python = p
                break
            except RuntimeError:
                pass

        if self._python is None:
            raise AnsibleError("No python found on the image, aborting")

    def _mount_tmp(self):
        ''' mount a tmpfs over /tmp or /run to store various artefacts '''
        self._tmp = None
        for tmp in ('/run', '/tmp'):
            if self.guestfs.is_dir(tmp):
                self.guestfs.sh("mount -t tmpfs -o size=4M tmpfs %s" % tmp)
                self._tmp = tmp
                break

        if self._tmp is None:
            raise AnsibleError("Cannot mount tmpfs, aborting")

    def _enable_selinux(self):
        ''' check if we can load a policy and load it '''
        # man pages indicate this may not work on older system, not sure
        #how old they have to be
        if self.guestfs.is_file('/usr/sbin/load_policy'):
            self.guestfs.sh('/usr/sbin/load_policy')

    def _start_guestfs(self):
        ''' start the guestfs appliance '''
        self.guestfs.set_network(True)
        self.guestfs.set_selinux(True)
        self.guestfs.launch()
        # code taken from the manpages
        roots = self.guestfs.inspect_os()
        if len(roots) != 1:
            # TODO handle the case a bit better ?
            raise AnsibleError("%s has more than one OS,"
                               "aborting" % self.disk)

        mps = self.guestfs.inspect_get_mountpoints(roots[0])

        def compare(a, b):
            return len(a) - len(b)

        for device in sorted(mps.keys(), compare):
            try:
                self.guestfs.mount(mps[device], device)
            except RuntimeError as msg:
                print("%s (ignored)" % msg)
        self._enable_selinux()

    def _connect(self):
        ''' connect to the disk image '''
        super(Connection, self)._connect()
        if not self._connected:
            self._start_guestfs()
            self._mount_tmp()
            self._find_python()
            self.guestfs.write(self._script_name(), EXECUTION_SCRIPT.format(self._tmp))

            self._connected = True

    # no need to randomize the filename since that's on a controlled
    # tmpfs, with a offline system
    def _script_name(self):
        ''' return the filename for the execution script '''
        return '%s/script' % self._tmp

    def _cmd_name(self):
        ''' return the filename for the command to execute '''
        return '%s/cmd' % self._tmp

    def _cmd_result_name(self):
        ''' return the filename for the command output '''
        return '%s/cmd.out' % self._tmp

    def exec_command(self, cmd, in_data=None, sudoable=False):
        #TODO handle sudo ?
        ''' run a command on the image '''
        super(Connection, self).exec_command(cmd, in_data=in_data,
                                             sudoable=sudoable)

        self.guestfs.write(self._cmd_name(), json.dumps(cmd))
        display.vvv(u"EXECUTING RPC WITH {0}".format(self._python), host=self.disk)
        result = self.guestfs.sh('%s %s %s' % (self._python,
                                               self._script_name(),
                                               self._cmd_name()))
        if result:
            print(result)
            raise AnsibleError("Execution error on the guest: %s" % result)

        r = json.loads(self.guestfs.read_file(self._cmd_result_name()))
        self.guestfs.rm(self._cmd_result_name())
        return (r['rc'], r['stdout'], r['stderr'])

    def put_file(self, in_path, out_path):
        ''' transfer a file from local to the image '''
        super(Connection, self).put_file(in_path, out_path)
        display.vvv(u"PUT {0} TO {1}".format(in_path, out_path), host=self.disk)
        self.guestfs.upload(to_native(in_path), to_native(out_path))

    def fetch_file(self, in_path, out_path):
        ''' fetch a file from the image to local '''
        super(Connection, self).fetch_file(in_path, out_path)
        display.vvv(u"FETCH {0} TO {1}".format(in_path, out_path), host=self.disk)
        self.guestfs.download(to_native(in_path), to_native(out_path))

    def close(self):
        ''' terminate the connection; nothing to do here '''
        super(Connection, self).close()
        # not sure if all is needed
        self.guestfs.shutdown()
        self.guestfs.umount_all()
        self.guestfs.close()
        self._connected = False
