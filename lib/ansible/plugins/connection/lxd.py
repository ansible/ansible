# (c) 2016 Matt Clay <matt@mystile.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    author: Matt Clay <matt@mystile.com>
    connection: lxd
    short_description: Run tasks in lxc containers via lxc CLI
    description:
        - Run commands or put/fetch files to an existing lxc container using lxc CLI
    version_added: "2.0"
    options:
      remote_addr:
        description:
            - Container identifier
        default: inventory_hostname
        vars:
            - name: ansible_host
            - name: ansible_lxd_host
      executable:
        description:
            - shell to use for execution inside container
        default: /bin/sh
        vars:
            - name: ansible_executable
            - name: ansible_lxd_executable
"""

import os
from distutils.spawn import find_executable
from subprocess import call, Popen, PIPE

from ansible.errors import AnsibleError, AnsibleConnectionFailure, AnsibleFileNotFound
from ansible.module_utils._text import to_bytes, to_text
from ansible.plugins.connection import ConnectionBase


class Connection(ConnectionBase):
    """ lxd based connections """

    transport = "lxd"
    has_pipelining = True
    default_user = 'root'

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        self._host = self._play_context.remote_addr
        self._lxc_cmd = find_executable("lxc")

        if not self._lxc_cmd:
            raise AnsibleError("lxc command not found in PATH")

        if self._play_context.remote_user is not None and self._play_context.remote_user != 'root':
            self._display.warning('lxd does not support remote_user, using container default: root')

    def _connect(self):
        """connect to lxd (nothing to do here) """
        super(Connection, self)._connect()

        if not self._connected:
            self._display.vvv(u"ESTABLISH LXD CONNECTION FOR USER: root", host=self._host)
            self._connected = True

    def exec_command(self, cmd, in_data=None, sudoable=True):
        """ execute a command on the lxd host """
        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        self._display.vvv(u"EXEC {0}".format(cmd), host=self._host)

        local_cmd = [self._lxc_cmd, "exec", self._host, "--", self._play_context.executable, "-c", cmd]

        local_cmd = [to_bytes(i, errors='surrogate_or_strict') for i in local_cmd]
        in_data = to_bytes(in_data, errors='surrogate_or_strict', nonstring='passthru')

        process = Popen(local_cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate(in_data)

        stdout = to_text(stdout)
        stderr = to_text(stderr)

        if stderr == "error: Container is not running.\n":
            raise AnsibleConnectionFailure("container not running: %s" % self._host)

        if stderr == "error: not found\n":
            raise AnsibleConnectionFailure("container not found: %s" % self._host)

        return process.returncode, stdout, stderr

    def put_file(self, in_path, out_path):
        """ put a file from local to lxd """
        super(Connection, self).put_file(in_path, out_path)

        self._display.vvv(u"PUT {0} TO {1}".format(in_path, out_path), host=self._host)

        if not os.path.isfile(to_bytes(in_path, errors='surrogate_or_strict')):
            raise AnsibleFileNotFound("input path is not a file: %s" % in_path)

        local_cmd = [self._lxc_cmd, "file", "push", in_path, self._host + "/" + out_path]

        local_cmd = [to_bytes(i, errors='surrogate_or_strict') for i in local_cmd]

        call(local_cmd)

    def fetch_file(self, in_path, out_path):
        """ fetch a file from lxd to local """
        super(Connection, self).fetch_file(in_path, out_path)

        self._display.vvv(u"FETCH {0} TO {1}".format(in_path, out_path), host=self._host)

        local_cmd = [self._lxc_cmd, "file", "pull", self._host + "/" + in_path, out_path]

        local_cmd = [to_bytes(i, errors='surrogate_or_strict') for i in local_cmd]

        call(local_cmd)

    def close(self):
        """ close the connection (nothing to do here) """
        super(Connection, self).close()

        self._connected = False
