# (c) 2015, Joerg Thalheim <joerg@higgsboson.tk>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    author: Joerg Thalheim <joerg@higgsboson.tk>
    connection: lxc
    short_description: Run tasks in lxc containers via lxc python library
    description:
        - Run commands or put/fetch files to an existing lxc container using lxc python library
    version_added: "2.0"
    options:
      remote_addr:
        description:
            - Container identifier
        default: inventory_hostname
        vars:
            - name: ansible_host
            - name: ansible_lxc_host
      executable:
        default: /bin/sh
        description:
            - Shell executable
        vars:
            - name: ansible_executable
            - name: ansible_lxc_executable
"""

import os
import shutil
import traceback
import select
import fcntl
import errno

HAS_LIBLXC = False
try:
    import lxc as _lxc
    HAS_LIBLXC = True
except ImportError:
    pass

from ansible import constants as C
from ansible import errors
from ansible.module_utils._text import to_bytes, to_native
from ansible.plugins.connection import ConnectionBase


class Connection(ConnectionBase):
    ''' Local lxc based connections '''

    transport = 'lxc'
    has_pipelining = True
    default_user = 'root'

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        self.container_name = self._play_context.remote_addr
        self.container = None

    def _connect(self):
        ''' connect to the lxc; nothing to do here '''
        super(Connection, self)._connect()

        if not HAS_LIBLXC:
            msg = "lxc bindings for python2 are not installed"
            raise errors.AnsibleError(msg)

        if self.container:
            return

        self._display.vvv("THIS IS A LOCAL LXC DIR", host=self.container_name)
        self.container = _lxc.Container(self.container_name)
        if self.container.state == "STOPPED":
            raise errors.AnsibleError("%s is not running" % self.container_name)

    def _communicate(self, pid, in_data, stdin, stdout, stderr):
        buf = {stdout: [], stderr: []}
        read_fds = [stdout, stderr]
        if in_data:
            write_fds = [stdin]
        else:
            write_fds = []
        while len(read_fds) > 0 or len(write_fds) > 0:
            try:
                ready_reads, ready_writes, _ = select.select(read_fds, write_fds, [])
            except select.error as e:
                if e.args[0] == errno.EINTR:
                    continue
                raise
            for fd in ready_writes:
                in_data = in_data[os.write(fd, in_data):]
                if len(in_data) == 0:
                    write_fds.remove(fd)
            for fd in ready_reads:
                data = os.read(fd, 32768)
                if not data:
                    read_fds.remove(fd)
                buf[fd].append(data)

        (pid, returncode) = os.waitpid(pid, 0)

        return returncode, b"".join(buf[stdout]), b"".join(buf[stderr])

    def _set_nonblocking(self, fd):
        flags = fcntl.fcntl(fd, fcntl.F_GETFL) | os.O_NONBLOCK
        fcntl.fcntl(fd, fcntl.F_SETFL, flags)
        return fd

    def exec_command(self, cmd, in_data=None, sudoable=False):
        ''' run a command on the chroot '''
        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        # python2-lxc needs bytes. python3-lxc needs text.
        executable = to_native(self._play_context.executable, errors='surrogate_or_strict')
        local_cmd = [executable, '-c', to_native(cmd, errors='surrogate_or_strict')]

        read_stdout, write_stdout = None, None
        read_stderr, write_stderr = None, None
        read_stdin, write_stdin = None, None

        try:
            read_stdout, write_stdout = os.pipe()
            read_stderr, write_stderr = os.pipe()

            kwargs = {
                'stdout': self._set_nonblocking(write_stdout),
                'stderr': self._set_nonblocking(write_stderr),
                'env_policy': _lxc.LXC_ATTACH_CLEAR_ENV
            }

            if in_data:
                read_stdin, write_stdin = os.pipe()
                kwargs['stdin'] = self._set_nonblocking(read_stdin)

            self._display.vvv("EXEC %s" % (local_cmd), host=self.container_name)
            pid = self.container.attach(_lxc.attach_run_command, local_cmd, **kwargs)
            if pid == -1:
                msg = "failed to attach to container %s" % self.container_name
                raise errors.AnsibleError(msg)

            write_stdout = os.close(write_stdout)
            write_stderr = os.close(write_stderr)
            if read_stdin:
                read_stdin = os.close(read_stdin)

            return self._communicate(pid,
                                     in_data,
                                     write_stdin,
                                     read_stdout,
                                     read_stderr)
        finally:
            fds = [read_stdout,
                   write_stdout,
                   read_stderr,
                   write_stderr,
                   read_stdin,
                   write_stdin]
            for fd in fds:
                if fd:
                    os.close(fd)

    def put_file(self, in_path, out_path):
        ''' transfer a file from local to lxc '''
        super(Connection, self).put_file(in_path, out_path)
        self._display.vvv("PUT %s TO %s" % (in_path, out_path), host=self.container_name)
        in_path = to_bytes(in_path, errors='surrogate_or_strict')
        out_path = to_bytes(out_path, errors='surrogate_or_strict')

        if not os.path.exists(in_path):
            msg = "file or module does not exist: %s" % in_path
            raise errors.AnsibleFileNotFound(msg)
        try:
            src_file = open(in_path, "rb")
        except IOError:
            traceback.print_exc()
            raise errors.AnsibleError("failed to open input file to %s" % in_path)
        try:
            def write_file(args):
                with open(out_path, 'wb+') as dst_file:
                    shutil.copyfileobj(src_file, dst_file)
            try:
                self.container.attach_wait(write_file, None)
            except IOError:
                traceback.print_exc()
                msg = "failed to transfer file to %s" % out_path
                raise errors.AnsibleError(msg)
        finally:
            src_file.close()

    def fetch_file(self, in_path, out_path):
        ''' fetch a file from lxc to local '''
        super(Connection, self).fetch_file(in_path, out_path)
        self._display.vvv("FETCH %s TO %s" % (in_path, out_path), host=self.container_name)
        in_path = to_bytes(in_path, errors='surrogate_or_strict')
        out_path = to_bytes(out_path, errors='surrogate_or_strict')

        try:
            dst_file = open(out_path, "wb")
        except IOError:
            traceback.print_exc()
            msg = "failed to open output file %s" % out_path
            raise errors.AnsibleError(msg)
        try:
            def write_file(args):
                try:
                    with open(in_path, 'rb') as src_file:
                        shutil.copyfileobj(src_file, dst_file)
                finally:
                    # this is needed in the lxc child process
                    # to flush internal python buffers
                    dst_file.close()
            try:
                self.container.attach_wait(write_file, None)
            except IOError:
                traceback.print_exc()
                msg = "failed to transfer file from %s to %s" % (in_path, out_path)
                raise errors.AnsibleError(msg)
        finally:
            dst_file.close()

    def close(self):
        ''' terminate the connection; nothing to do here '''
        super(Connection, self).close()
        self._connected = False
