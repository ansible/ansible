# Based on local.py by Michael DeHaan <michael.dehaan@gmail.com>
# and chroot.py by  Maykel Moya <mmoya@speedyrails.com>
# Copyright (c) 2013, Michael Scherer <misc@zarb.org>
# Copyright (c) 2015, Toshio Kuratomi <tkuratomi@ansible.com>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    author: Ansible Core Team
    connection: jail
    short_description: Run tasks in jails
    description:
        - Run commands or put/fetch files to an existing jail
    version_added: "2.0"
    options:
      remote_addr:
        description:
            - Path to the jail
        default: inventory_hostname
        vars:
            - name: ansible_host
            - name: ansible_jail_host
      remote_user:
        description:
            - User to execute as inside the jail
        vars:
            - name: ansible_user
            - name: ansible_jail_user
"""

import distutils.spawn
import os
import os.path
import subprocess
import traceback
import ansible.constants as C

from ansible.errors import AnsibleError
from ansible.module_utils.six.moves import shlex_quote
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.plugins.connection import ConnectionBase, BUFSIZE

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class Connection(ConnectionBase):
    ''' Local BSD Jail based connections '''

    modified_jailname_key = 'conn_jail_name'

    transport = 'jail'
    # Pipelining may work.  Someone needs to test by setting this to True and
    # having pipelining=True in their ansible.cfg
    has_pipelining = True

    become_methods = frozenset(C.BECOME_METHODS)

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        self.jail = self._play_context.remote_addr
        if self.modified_jailname_key in kwargs:
            self.jail = kwargs[self.modified_jailname_key]

        if os.geteuid() != 0:
            raise AnsibleError("jail connection requires running as root")

        self.jls_cmd = self._search_executable('jls')
        self.jexec_cmd = self._search_executable('jexec')

        if self.jail not in self.list_jails():
            raise AnsibleError("incorrect jail name %s" % self.jail)

    @staticmethod
    def _search_executable(executable):
        cmd = distutils.spawn.find_executable(executable)
        if not cmd:
            raise AnsibleError("%s command not found in PATH" % executable)
        return cmd

    def list_jails(self):
        p = subprocess.Popen([self.jls_cmd, '-q', 'name'],
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = p.communicate()

        return to_text(stdout, errors='surrogate_or_strict').split()

    def _connect(self):
        ''' connect to the jail; nothing to do here '''
        super(Connection, self)._connect()
        if not self._connected:
            display.vvv(u"ESTABLISH JAIL CONNECTION FOR USER: {0}".format(self._play_context.remote_user), host=self.jail)
            self._connected = True

    def _buffered_exec_command(self, cmd, stdin=subprocess.PIPE):
        ''' run a command on the jail.  This is only needed for implementing
        put_file() get_file() so that we don't have to read the whole file
        into memory.

        compared to exec_command() it looses some niceties like being able to
        return the process's exit code immediately.
        '''

        local_cmd = [self.jexec_cmd]
        set_env = ''

        if self._play_context.remote_user is not None:
            local_cmd += ['-U', self._play_context.remote_user]
            # update HOME since -U does not update the jail environment
            set_env = 'HOME=~' + self._play_context.remote_user + ' '

        local_cmd += [self.jail, self._play_context.executable, '-c', set_env + cmd]

        display.vvv("EXEC %s" % (local_cmd,), host=self.jail)
        local_cmd = [to_bytes(i, errors='surrogate_or_strict') for i in local_cmd]
        p = subprocess.Popen(local_cmd, shell=False, stdin=stdin,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        return p

    def exec_command(self, cmd, in_data=None, sudoable=False):
        ''' run a command on the jail '''
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
        ''' transfer a file from local to jail '''
        super(Connection, self).put_file(in_path, out_path)
        display.vvv("PUT %s TO %s" % (in_path, out_path), host=self.jail)

        out_path = shlex_quote(self._prefix_login_path(out_path))
        try:
            with open(to_bytes(in_path, errors='surrogate_or_strict'), 'rb') as in_file:
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
                    raise AnsibleError("failed to transfer file %s to %s:\n%s\n%s" % (in_path, out_path, to_native(stdout), to_native(stderr)))
        except IOError:
            raise AnsibleError("file or module does not exist at: %s" % in_path)

    def fetch_file(self, in_path, out_path):
        ''' fetch a file from jail to local '''
        super(Connection, self).fetch_file(in_path, out_path)
        display.vvv("FETCH %s TO %s" % (in_path, out_path), host=self.jail)

        in_path = shlex_quote(self._prefix_login_path(in_path))
        try:
            p = self._buffered_exec_command('dd if=%s bs=%s' % (in_path, BUFSIZE))
        except OSError:
            raise AnsibleError("jail connection requires dd command in the jail")

        with open(to_bytes(out_path, errors='surrogate_or_strict'), 'wb+') as out_file:
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
                raise AnsibleError("failed to transfer file %s to %s:\n%s\n%s" % (in_path, out_path, to_native(stdout), to_native(stderr)))

    def close(self):
        ''' terminate the connection; nothing to do here '''
        super(Connection, self).close()
        self._connected = False
