# Based on local.py (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# Based on chroot.py (c) 2013, Maykel Moya <mmoya@speedyrails.com>
# (c) 2013, Michael Scherer <misc@zarb.org>
# (c) 2015, Toshio Kuratomi <tkuratomi@ansible.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    author: Michael Scherer <misc@zarb.org>
    connection: libvirt_lxc
    short_description: Run tasks in lxc containers via libvirt
    description:
        - Run commands or put/fetch files to an existing lxc container using libvirt
    version_added: "2.0"
    options:
      remote_addr:
        description:
            - Container identifier
        default: The set user as per docker's configuration
        vars:
            - name: ansible_host
            - name: ansible_libvirt_lxc_host
"""

import distutils.spawn
import os
import os.path
import subprocess
import traceback

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.module_utils.six.moves import shlex_quote
from ansible.module_utils._text import to_bytes
from ansible.plugins.connection import ConnectionBase, BUFSIZE


try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class Connection(ConnectionBase):
    ''' Local lxc based connections '''

    transport = 'libvirt_lxc'
    has_pipelining = True
    # su currently has an undiagnosed issue with calculating the file
    # checksums (so copy, for instance, doesn't work right)
    # Have to look into that before re-enabling this
    become_methods = frozenset(C.BECOME_METHODS).difference(('su',))
    default_user = 'root'

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)
        self.lxc = self._play_context.remote_addr

        self.virsh = self._search_executable('virsh')

        self._check_domain(self.lxc)

    def _search_executable(self, executable):
        cmd = distutils.spawn.find_executable(executable)
        if not cmd:
            raise AnsibleError("%s command not found in PATH") % executable
        return cmd

    def _check_domain(self, domain):
        p = subprocess.Popen([self.virsh, '-q', '-c', 'lxc:///', 'dominfo', to_bytes(domain)],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.communicate()
        if p.returncode:
            raise AnsibleError("%s is not a lxc defined in libvirt" % domain)

    def _connect(self):
        ''' connect to the lxc; nothing to do here '''
        super(Connection, self)._connect()
        if not self._connected:
            display.vvv("THIS IS A LOCAL LXC DIR", host=self.lxc)
            self._connected = True

    def _buffered_exec_command(self, cmd, stdin=subprocess.PIPE):
        ''' run a command on the chroot.  This is only needed for implementing
        put_file() get_file() so that we don't have to read the whole file
        into memory.

        compared to exec_command() it looses some niceties like being able to
        return the process's exit code immediately.
        '''
        executable = C.DEFAULT_EXECUTABLE.split()[0] if C.DEFAULT_EXECUTABLE else '/bin/sh'
        local_cmd = [self.virsh, '-q', '-c', 'lxc:///', 'lxc-enter-namespace']

        if C.DEFAULT_LIBVIRT_LXC_NOSECLABEL:
            local_cmd += ['--noseclabel']

        local_cmd += [self.lxc, '--', executable, '-c', cmd]

        display.vvv("EXEC %s" % (local_cmd,), host=self.lxc)
        local_cmd = [to_bytes(i, errors='surrogate_or_strict') for i in local_cmd]
        p = subprocess.Popen(local_cmd, shell=False, stdin=stdin,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        return p

    def exec_command(self, cmd, in_data=None, sudoable=False):
        ''' run a command on the chroot '''
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
        ''' transfer a file from local to lxc '''
        super(Connection, self).put_file(in_path, out_path)
        display.vvv("PUT %s TO %s" % (in_path, out_path), host=self.lxc)

        out_path = shlex_quote(self._prefix_login_path(out_path))
        try:
            with open(to_bytes(in_path, errors='surrogate_or_strict'), 'rb') as in_file:
                try:
                    p = self._buffered_exec_command('dd of=%s bs=%s' % (out_path, BUFSIZE), stdin=in_file)
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
        ''' fetch a file from lxc to local '''
        super(Connection, self).fetch_file(in_path, out_path)
        display.vvv("FETCH %s TO %s" % (in_path, out_path), host=self.lxc)

        in_path = shlex_quote(self._prefix_login_path(in_path))
        try:
            p = self._buffered_exec_command('dd if=%s bs=%s' % (in_path, BUFSIZE))
        except OSError:
            raise AnsibleError("chroot connection requires dd command in the chroot")

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
                raise AnsibleError("failed to transfer file %s to %s:\n%s\n%s" % (in_path, out_path, stdout, stderr))

    def close(self):
        ''' terminate the connection; nothing to do here '''
        super(Connection, self).close()
        self._connected = False
