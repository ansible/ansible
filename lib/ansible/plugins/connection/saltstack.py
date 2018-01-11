# Based on local.py (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# Based on chroot.py (c) 2013, Maykel Moya <mmoya@speedyrails.com>
# Based on func.py
# (c) 2014, Michael Scherer <misc@zarb.org>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    author: Michael Scherer <misc@zarb.org>
    connection: saltstack
    short_description: Allow ansible to piggyback on salt minions
    description:
        - This allows you to use existing Saltstack infrastructure to connect to targets.
    version_added: "2.2"
"""

import re
import os
import pty
import subprocess

from ansible.module_utils._text import to_bytes, to_text
from ansible.module_utils.six.moves import cPickle

HAVE_SALTSTACK = False
try:
    import salt.client as sc
    HAVE_SALTSTACK = True
except ImportError:
    pass

import os
from ansible import errors
from ansible.plugins.connection import ConnectionBase


class Connection(ConnectionBase):
    ''' Salt-based connections '''

    has_pipelining = False
    # while the name of the product is salt, naming that module salt cause
    # trouble with module import
    transport = 'saltstack'

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)
        self.host = self._play_context.remote_addr

    def _connect(self):
        if not HAVE_SALTSTACK:
            raise errors.AnsibleError("saltstack is not installed")

        self.client = sc.LocalClient()
        self._connected = True
        return self

    def exec_command(self, cmd, sudoable=False, in_data=None):
        ''' run a command on the remote minion '''
        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        if in_data:
            raise errors.AnsibleError("Internal Error: this module does not support optimized module pipelining")

        self._display.vvv("EXEC %s" % (cmd), host=self.host)
        # need to add 'true;' to work around https://github.com/saltstack/salt/issues/28077
        res = self.client.cmd(self.host, 'cmd.exec_code_all', ['bash', 'true;' + cmd])
        if self.host not in res:
            raise errors.AnsibleError("Minion %s didn't answer, check if salt-minion is running and the name is correct" % self.host)

        p = res[self.host]
        return (p['retcode'], p['stdout'], p['stderr'])

    def _normalize_path(self, path, prefix):
        if not path.startswith(os.path.sep):
            path = os.path.join(os.path.sep, path)
        normpath = os.path.normpath(path)
        return os.path.join(prefix, normpath[1:])

    def put_file(self, in_path, out_path):
        ''' transfer a file from local to remote '''

        super(Connection, self).put_file(in_path, out_path)

        out_path = self._normalize_path(out_path, '/')
        self._display.vvv("PUT %s TO %s" % (in_path, out_path), host=self.host)
        content = open(in_path).read()
        self.client.cmd(self.host, 'file.write', [out_path, content])

    # TODO test it
    def fetch_file(self, in_path, out_path):
        ''' fetch a file from remote to local '''

        super(Connection, self).fetch_file(in_path, out_path)

        in_path = self._normalize_path(in_path, '/')
        self._display.vvv("FETCH %s TO %s" % (in_path, out_path), host=self.host)
        content = self.client.cmd(self.host, 'cp.get_file_str', [in_path])[self.host]
        open(out_path, 'wb').write(content)

    def close(self):
        ''' terminate the connection; nothing to do here '''
        pass
