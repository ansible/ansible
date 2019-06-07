# Based on the docker connection plugin
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Connection plugin for building container images using buildah tool
#   https://github.com/projectatomic/buildah
#
# Written by: Tomas Tomecek (https://github.com/TomasTomecek)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = """
    connection: buildah
    short_description: Interact with an existing buildah container
    description:
        - Run commands or put/fetch files to an existing container using buildah tool.
    author: Tomas Tomecek (ttomecek@redhat.com)
    version_added: 2.4
    options:
      remote_addr:
        description:
            - The ID of the container you want to access.
        default: inventory_hostname
        vars:
            - name: ansible_host
#        keyword:
#            - name: hosts
      remote_user:
        description:
            - User specified via name or ID which is used to execute commands inside the container.
        ini:
          - section: defaults
            key: remote_user
        env:
          - name: ANSIBLE_REMOTE_USER
        vars:
          - name: ansible_user
#        keyword:
#            - name: remote_user
"""

import os
import shlex
import shutil
import subprocess
import traceback

import ansible.constants as C
from ansible.errors import AnsibleError
from ansible.module_utils._text import to_bytes, to_native
from ansible.module_utils.six.moves import shlex_quote
from ansible.plugins.connection import ConnectionBase, BUFSIZE
from ansible.utils.display import Display

display = Display()


# this _has to be_ named Connection
class Connection(ConnectionBase):
    """
    This is a connection plugin for buildah: it uses buildah binary to interact with the containers
    """

    # String used to identify this Connection class from other classes
    transport = 'buildah'
    has_pipelining = True

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        self._container_id = self._play_context.remote_addr
        self._connected = False
        # container filesystem will be mounted here on host
        self._mount_point = None
        # `buildah inspect` doesn't contain info about what the default user is -- if it's not
        # set, it's empty
        self.user = self._play_context.remote_user

    def _set_user(self):
        self._buildah(b"config", [b"--user=" + to_bytes(self.user, errors='surrogate_or_strict')])

    def _buffered_buildah(self, cmd, cmd_args=None, stdin=subprocess.PIPE):
        """
        run buildah executable

        :param cmd: buildah's command to execute (str)
        :param cmd_args: list of arguments to pass to the command (list of str/bytes)
        :param stdin: passed to subproces.Popen
        :return: subprocess.Popen object
        """
        local_cmd = ['buildah', cmd, '--', self._container_id]
        if cmd_args:
            local_cmd += cmd_args
        local_cmd = [to_bytes(i, errors='surrogate_or_strict') for i in local_cmd]

        display.vvv("RUN %s" % (local_cmd,), host=self._container_id)
        p = subprocess.Popen(local_cmd, shell=False, stdin=stdin,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        return p

    def _buildah(self, cmd, cmd_args=None, in_data=None):
        """
        run buildah executable

        :param cmd: buildah's command to execute (str)
        :param cmd_args: list of arguments to pass to the command (list of str/bytes)
        :param in_data: data passed to buildah's stdin
        :return: return code, stdout, stderr
        """
        p = self._buffered_buildah(cmd, cmd_args)

        stdout, stderr = p.communicate(input=in_data)
        stdout = to_bytes(stdout, errors='surrogate_or_strict')
        stderr = to_bytes(stderr, errors='surrogate_or_strict')
        return p.returncode, stdout, stderr

    def _connect(self):
        """
        no persistent connection is being maintained
        """
        super(Connection, self)._connect()
        if not self._connected:
            display.vvv("THIS IS A BUILDAH CONTAINER", host=self._container_id)
            self._connected = True

    def exec_command(self, cmd, in_data=None, sudoable=False):
        """ run specified command in a running OCI container using buildah """
        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        # shlex.split has a bug with text strings on Python-2.6 and can only handle text strings on Python-3
        cmd_args_list = shlex.split(to_native(cmd, errors='surrogate_or_strict'))

        rc, stdout, stderr = self._buildah("run", cmd_args_list, in_data)

        display.vvvvv("STDOUT %r STDERR %r" % (stderr, stderr))
        return rc, stdout, stderr

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
        """ Place a local file located in 'in_path' inside container at 'out_path' """
        super(Connection, self).put_file(in_path, out_path)
        display.vvv("PUT %s TO %s" % (in_path, out_path), host=self._container_id)

        rc, stdout, stderr = self._buildah(
            "copy",
            [to_bytes(in_path, errors='surrogate_or_strict'),
             to_bytes(self._prefix_login_path(out_path), errors='surrogate_or_strict')]
        )

        if rc != 0:
            raise AnsibleError("failed to transfer file %s to %s:\n%s\n%s" % (in_path, out_path, stdout, stderr))

    def fetch_file(self, in_path, out_path):
        """ obtain file specified via 'in_path' from the container and place it at 'out_path' """
        super(Connection, self).fetch_file(in_path, out_path)
        display.vvv("FETCH %s TO %s" % (in_path, out_path), host=self._container_id)

        in_path = shlex_quote(self._prefix_login_path(in_path))
        p = self._buffered_buildah("run", ['dd', 'if=%s' % in_path, 'bs=%s' % BUFSIZE])

        with open(to_bytes(out_path, errors='surrogate_or_strict'), 'wb+') as out_file:
            try:
                chunk = p.stdout.read(BUFSIZE)
                while chunk:
                    out_file.write(chunk)
                    chunk = p.stdout.read(BUFSIZE)
            except Exception:
                traceback.print_exc()
                raise AnsibleError("failed to transfer file %s to %s" % (in_path, out_path))
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                raise AnsibleError("failed to transfer file %s to %s:\n%s\n%s" % (in_path, out_path, stdout, stderr))

    def close(self):
        """ unmount container's filesystem """
        super(Connection, self).close()
        self._connected = False
