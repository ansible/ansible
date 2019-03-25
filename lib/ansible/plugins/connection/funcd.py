# Based on local.py (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# Based on chroot.py (c) 2013, Maykel Moya <mmoya@speedyrails.com>
# Copyright (c) 2013, Michael Scherer <misc@zarb.org>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    author: Michael Scherer (@msherer) <misc@zarb.org>
    connection: funcd
    short_description: Use funcd to connect to target
    description:
        - This transport permits you to use Ansible over Func.
        - For people who have already setup func and that wish to play with ansible,
          this permit to move gradually to ansible without having to redo completely the setup of the network.
    version_added: "1.1"
    options:
      remote_addr:
        description:
            - The path of the chroot you want to access.
        default: inventory_hostname
        vars:
            - name: ansible_host
            - name: ansible_func_host
"""

HAVE_FUNC = False
try:
    import func.overlord.client as fc
    HAVE_FUNC = True
except ImportError:
    pass

import os
import tempfile
import shutil

from ansible.errors import AnsibleError
from ansible.utils.display import Display

display = Display()


class Connection(object):
    ''' Func-based connections '''

    has_pipelining = False

    def __init__(self, runner, host, port, *args, **kwargs):
        self.runner = runner
        self.host = host
        # port is unused, this go on func
        self.port = port

    def connect(self, port=None):
        if not HAVE_FUNC:
            raise AnsibleError("func is not installed")

        self.client = fc.Client(self.host)
        return self

    def exec_command(self, cmd, become_user=None, sudoable=False, executable='/bin/sh', in_data=None):
        ''' run a command on the remote minion '''

        if in_data:
            raise AnsibleError("Internal Error: this module does not support optimized module pipelining")

        # totally ignores privlege escalation
        display.vvv("EXEC %s" % (cmd), host=self.host)
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
        display.vvv("PUT %s TO %s" % (in_path, out_path), host=self.host)
        self.client.local.copyfile.send(in_path, out_path)

    def fetch_file(self, in_path, out_path):
        ''' fetch a file from remote to local '''

        in_path = self._normalize_path(in_path, '/')
        display.vvv("FETCH %s TO %s" % (in_path, out_path), host=self.host)
        # need to use a tmp dir due to difference of semantic for getfile
        # ( who take a # directory as destination) and fetch_file, who
        # take a file directly
        tmpdir = tempfile.mkdtemp(prefix="func_ansible")
        self.client.local.getfile.get(in_path, tmpdir)
        shutil.move(os.path.join(tmpdir, self.host, os.path.basename(in_path)), out_path)
        shutil.rmtree(tmpdir)

    def close(self):
        ''' terminate the connection; nothing to do here '''
        pass
