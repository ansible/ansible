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

# ---
# The func transport permit to use ansible over func. For people who have already setup
# func and that wish to play with ansible, this permit to move gradually to ansible
# without having to redo completely the setup of the network.
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

HAVE_FUNC=False
try:
    import func.overlord.client as fc
    HAVE_FUNC=True
except ImportError:
    pass

import os
from ansible.callbacks import vvv
from ansible import errors
import tempfile
import shutil


class Connection(object):
    ''' Func-based connections '''

    def __init__(self, runner, host, port, *args, **kwargs):
        self.runner = runner
        self.host = host
        self.has_pipelining = False
        # port is unused, this go on func
        self.port = port

    def connect(self, port=None):
        if not HAVE_FUNC:
            raise errors.AnsibleError("func is not installed")

        self.client = fc.Client(self.host)
        return self

    def exec_command(self, cmd, become_user=None, sudoable=False,
                     executable='/bin/sh', in_data=None):
        ''' run a command on the remote minion '''

        if in_data:
            raise errors.AnsibleError("Internal Error: this module does not support optimized module pipelining")

        # totally ignores privlege escalation
        vvv("EXEC %s" % (cmd), host=self.host)
        p = self.client.command.run(cmd)[self.host]
        return (p[0], p[1], p[2])

    def _normalize_path(self, path, prefix):
        if not path.startswith(os.path.sep):
            path = os.path.join(os.path.sep, path)
        normpath = os.path.normpath(path)
        return os.path.join(prefix, normpath[1:])

    def put_file(self, in_path, out_path):
        ''' transfer a file from local to remote '''

        out_path = self._normalize_path(out_path, '/')
        vvv("PUT %s TO %s" % (in_path, out_path), host=self.host)
        self.client.local.copyfile.send(in_path, out_path)

    def fetch_file(self, in_path, out_path):
        ''' fetch a file from remote to local '''

        in_path = self._normalize_path(in_path, '/')
        vvv("FETCH %s TO %s" % (in_path, out_path), host=self.host)
        # need to use a tmp dir due to difference of semantic for getfile
        # ( who take a # directory as destination) and fetch_file, who
        # take a file directly
        tmpdir = tempfile.mkdtemp(prefix="func_ansible")
        self.client.local.getfile.get(in_path, tmpdir)
        shutil.move(os.path.join(tmpdir, self.host, os.path.basename(in_path)),
                    out_path)
        shutil.rmtree(tmpdir)

    def close(self):
        ''' terminate the connection; nothing to do here '''
        pass
