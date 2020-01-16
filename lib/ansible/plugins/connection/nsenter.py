# Based on the kubectl connection plugin
#
# Connection plugin for configuring process namespaces with nsenter
# (c) 2020, kvaps <kvapss@gmail.com>
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

DOCUMENTATION = """
    author: kvaps <kvapss@gmail.com>
    connection: nsenter
    short_description: Run tasks in process namespace via nsenter
    description:
      - Run commands or put/fetch files to an existing process namespace using nsenter on the Ansible controller.
    version_added: "2.10"
    options:
      remote_addr:
        description:
          - Target process id which namespaces you want to access
        type: int
        vars:
          - name: ansible_host
        default: 1
      executable:
        description:
          - User specified executable shell
        ini:
          - section: defaults
            key: executable
        env:
          - name: ANSIBLE_EXECUTABLE
        vars:
          - name: ansible_executable
        default: /bin/sh
      nsenter_mount:
        description:
          - Enter the mount namespace.
        type: boolean
        ini:
          - section: nsenter_connection
            key: mount
        env:
          - name: ANSIBLE_NSENTER_MOUNT
        vars:
          - name: ansible_nsenter_mount
        default: 'yes'
      nsenter_utc:
        description:
          - Enter the UTC namespace.
        type: boolean
        ini:
          - section: nsenter_connection
            key: utc
        env:
          - name: ANSIBLE_NSENTER_UTC
        vars:
          - name: ansible_nsenter_utc
        default: 'yes'
      nsenter_ipc:
        description:
            - Enter the IPC namespace.
        type: boolean
        ini:
          - section: nsenter_connection
            key: ipc
        env:
          - name: ANSIBLE_NSENTER_IPC
        vars:
          - name: ansible_nsenter_ipc
        default: 'yes'
      nsenter_net:
        description:
          - Enter the network namespace.
        type: boolean
        ini:
          - section: nsenter_connection
            key: network
        env:
          - name: ANSIBLE_NSENTER_NET
        vars:
          - name: ansible_nsenter_net
        default: 'yes'
      nsenter_pid:
        description:
          - Enter the PID namespace.
        type: boolean
        ini:
          - section: nsenter_connection
            key: pid
        env:
          - name: ANSIBLE_NSENTER_PID
        vars:
          - name: ansible_nsenter_pid
        default: 'yes'
      nsenter_user:
        description:
          - Enter the user namespace.
        type: boolean
        ini:
          - section: nsenter_connection
            key: user
        env:
          - name: ANSIBLE_NSENTER_USER
        vars:
          - name: ansible_nsenter_user
        default: 'no'
      nsenter_uid:
        description:
          - Set the user ID which will be used in the entered namespace.
          - If no user ID is supplied, Ansible will let the nsenter binary choose the user ID as it normally
        type: integer
        ini:
          - section: nsenter_connection
            key: uid
        env:
          - name: ANSIBLE_NSENTER_UID
        vars:
          - name: ansible_nsenter_uid
      nsenter_gid:
        description:
          - Set the group ID which will be used in the entered namespace and drop supplementary groups.
          - If no group ID is supplied, Ansible will let the nsenter binary choose the group ID as it normally
        type: integer
        ini:
          - section: nsenter_connection
            key: gid
        env:
          - name: ANSIBLE_NSENTER_GID
        vars:
          - name: ansible_nsenter_gid
"""

import distutils.spawn
import os
import os.path
import subprocess

import ansible.constants as C
from ansible.parsing.yaml.loader import AnsibleLoader
from ansible.errors import AnsibleError, AnsibleFileNotFound
from ansible.module_utils.six.moves import shlex_quote
from ansible.module_utils._text import to_bytes
from ansible.plugins.connection import ConnectionBase, BUFSIZE
from ansible.utils.display import Display

display = Display()


CONNECTION_TRANSPORT = 'nsenter'

CONNECTION_OPTIONS = {
    'nsenter_mount': '-m',
    'nsenter_utc': '-u',
    'nsenter_ipc': '-i',
    'nsenter_net': '-n',
    'nsenter_pid': '-p',
    'nsenter_user': '-U',
    'nsenter_uid': '-S',
    'nsenter_gid': '-G',
}


class Connection(ConnectionBase):
    ''' Local nsenter based connections '''

    transport = CONNECTION_TRANSPORT
    connection_options = CONNECTION_OPTIONS
    connection_options = CONNECTION_OPTIONS
    documentation = DOCUMENTATION
    has_pipelining = True
    transport_cmd = None
    has_tty = False

    default_user = 'root'

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        self.target = self._play_context.remote_addr

        cmd_arg = '{0}_command'.format(self.transport)
        if cmd_arg in kwargs:
            self.transport_cmd = kwargs[cmd_arg]
        else:
            self.transport_cmd = distutils.spawn.find_executable(self.transport)
            if not self.transport_cmd:
                raise AnsibleError("{0} command not found in PATH".format(self.transport))

        # do some trivial checks for ensuring 'host' is actually a process ID
        if not self.target.isdigit():
            raise AnsibleError("specified target (%s) is not valid pid" % self.target)

        try:
            os.kill(int(self.target), 0)
        except OSError:
            raise AnsibleError("a target pid (%d) does not exist" % self.target)

    def _build_exec_cmd(self, cmd):
        """ Build the local nsenter command to run cmd on remote_host
        """
        local_cmd = [self.transport_cmd, '-t', self.target]
        executable = self.get_option('executable')

        # Build command options based on doc string
        doc_yaml = AnsibleLoader(self.documentation).get_single_data()
        for key in doc_yaml.get('options'):
            if key in ['nsenter_uid', 'nsenter_gid'] and self.get_option(key) is not None:
                cmd_arg = self.connection_options[key]
                local_cmd += [cmd_arg, self.get_option(key)]
            elif self.get_option(key) and self.connection_options.get(key):
                cmd_arg = self.connection_options[key]
                local_cmd += [cmd_arg]

        local_cmd += ['-F', '--'] + cmd

        return local_cmd

    def _connect(self):
        ''' connect to the nsenter '''

        super(Connection, self)._connect()
        if not self._connected:
            display.vvv(u"ESTABLISH {0} CONNECTION".format(self.transport), host=self.target)
            self._connected = True

    def exec_command(self, cmd, in_data=None, sudoable=False):
        ''' run a command on the process namespace '''
        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        local_cmd = self._build_exec_cmd([self._play_context.executable, '-c', cmd])

        display.vvv("EXEC %s" % (local_cmd,), host=self.target)
        local_cmd = [to_bytes(i, errors='surrogate_or_strict') for i in local_cmd]
        p = subprocess.Popen(local_cmd, shell=False, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = p.communicate(in_data)
        return (p.returncode, stdout, stderr)

    def _prefix_login_path(self, remote_path):
        ''' Make sure that we put files into a standard path

            If a path is relative, then we need to choose where to put it.
            ssh chooses $HOME but we aren't guaranteed that a home dir will
            exist in any given nsenter.  So for now we're choosing "/" instead.
            This also happens to be the former default.

            Can revisit using $HOME instead if it's a problem
        '''
        if not remote_path.startswith(os.path.sep):
            remote_path = os.path.join(os.path.sep, remote_path)
        return os.path.normpath(remote_path)

    def put_file(self, in_path, out_path):
        ''' Transfer a file from local to process namespace '''
        super(Connection, self).put_file(in_path, out_path)
        display.vvv("PUT %s TO %s" % (in_path, out_path), host=self._play_context.remote_addr)

        out_path = self._prefix_login_path(out_path)
        if not os.path.exists(to_bytes(in_path, errors='surrogate_or_strict')):
            raise AnsibleFileNotFound(
                "file or module does not exist: %s" % in_path)

        out_path = shlex_quote(out_path)
        with open(to_bytes(in_path, errors='surrogate_or_strict'), 'rb') as in_file:
            if not os.fstat(in_file.fileno()).st_size:
                count = ' count=0'
            else:
                count = ''
            args = self._build_exec_cmd([self._play_context.executable, "-c", "dd of=%s bs=%s%s" % (out_path, BUFSIZE, count)])
            args = [to_bytes(i, errors='surrogate_or_strict') for i in args]
            try:
                p = subprocess.Popen(args, stdin=in_file,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except OSError:
                raise AnsibleError("nsenter connection requires dd command in the container to put files")
            stdout, stderr = p.communicate()

            if p.returncode != 0:
                raise AnsibleError("failed to transfer file %s to %s:\n%s\n%s" % (in_path, out_path, stdout, stderr))

    def fetch_file(self, in_path, out_path):
        ''' Fetch a file from process namespace to local '''
        super(Connection, self).fetch_file(in_path, out_path)
        display.vvv("FETCH %s TO %s" % (in_path, out_path), host=self.target)

        in_path = self._prefix_login_path(in_path)
        out_dir = os.path.dirname(out_path)

        args = self._build_exec_cmd([self._play_context.executable, "-c", "dd if=%s bs=%s" % (in_path, BUFSIZE)])
        args = [to_bytes(i, errors='surrogate_or_strict') for i in args]
        actual_out_path = os.path.join(out_dir, os.path.basename(in_path))
        with open(to_bytes(actual_out_path, errors='surrogate_or_strict'), 'wb') as out_file:
            try:
                p = subprocess.Popen(args, stdin=subprocess.PIPE,
                                     stdout=out_file, stderr=subprocess.PIPE)
            except OSError:
                raise AnsibleError(
                    "{0} connection requires dd command in the container to fetch files".format(self.transport)
                )
            stdout, stderr = p.communicate()

            if p.returncode != 0:
                raise AnsibleError("failed to fetch file %s to %s:\n%s\n%s" % (in_path, out_path, stdout, stderr))

        if actual_out_path != out_path:
            os.rename(to_bytes(actual_out_path, errors='strict'), to_bytes(out_path, errors='strict'))

    def close(self):
        ''' Terminate the connection; Nothing to do here '''
        super(Connection, self).close()
        self._connected = False
