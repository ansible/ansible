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

import shlex
import shutil

import subprocess

import ansible.constants as C
from ansible.module_utils._text import to_bytes, to_native
from ansible.plugins.connection import ConnectionBase, ensure_connect


try:
    from __main__ import display
except ImportError:
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
    become_methods = frozenset(C.BECOME_METHODS)

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

    def _buildah(self, cmd, cmd_args=None, in_data=None):
        """
        run buildah executable

        :param cmd: buildah's command to execute (str)
        :param cmd_args: list of arguments to pass to the command (list of str/bytes)
        :param in_data: data passed to buildah's stdin
        :return: return code, stdout, stderr
        """
        local_cmd = ['buildah', cmd, '--', self._container_id]
        if cmd_args:
            local_cmd += cmd_args
        local_cmd = [to_bytes(i, errors='surrogate_or_strict') for i in local_cmd]

        display.vvv("RUN %s" % (local_cmd,), host=self._container_id)
        p = subprocess.Popen(local_cmd, shell=False, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = p.communicate(input=in_data)
        stdout = to_bytes(stdout, errors='surrogate_or_strict')
        stderr = to_bytes(stderr, errors='surrogate_or_strict')
        return p.returncode, stdout, stderr

    def _connect(self):
        """
        no persistent connection is being maintained, mount container's filesystem
        so we can easily access it
        """
        super(Connection, self)._connect()
        rc, self._mount_point, stderr = self._buildah("mount")
        self._mount_point = self._mount_point.strip()
        display.vvvvv("MOUNTPOINT %s RC %s STDERR %r" % (self._mount_point, rc, stderr))
        self._connected = True

    @ensure_connect
    def exec_command(self, cmd, in_data=None, sudoable=False):
        """ run specified command in a running OCI container using buildah """
        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        # shlex.split has a bug with text strings on Python-2.6 and can only handle text strings on Python-3
        cmd_args_list = shlex.split(to_native(cmd, errors='surrogate_or_strict'))

        rc, stdout, stderr = self._buildah("run", cmd_args_list)

        display.vvvvv("STDOUT %r STDERR %r" % (stderr, stderr))
        return rc, stdout, stderr

    def put_file(self, in_path, out_path):
        """ Place a local file located in 'in_path' inside container at 'out_path' """
        super(Connection, self).put_file(in_path, out_path)
        display.vvv("PUT %s TO %s" % (in_path, out_path), host=self._container_id)

        real_out_path = self._mount_point + to_bytes(out_path, errors='surrogate_or_strict')
        shutil.copyfile(
            to_bytes(in_path, errors='surrogate_or_strict'),
            to_bytes(real_out_path, errors='surrogate_or_strict')
        )
        # alternatively, this can be implemented using `buildah copy`:
        # rc, stdout, stderr = self._buildah(
        #     "copy",
        #     [to_bytes(in_path, errors='surrogate_or_strict'),
        #      to_bytes(out_path, errors='surrogate_or_strict')]
        # )

    def fetch_file(self, in_path, out_path):
        """ obtain file specified via 'in_path' from the container and place it at 'out_path' """
        super(Connection, self).fetch_file(in_path, out_path)
        display.vvv("FETCH %s TO %s" % (in_path, out_path), host=self._container_id)

        real_in_path = self._mount_point + to_bytes(in_path, errors='surrogate_or_strict')
        shutil.copyfile(
            to_bytes(real_in_path, errors='surrogate_or_strict'),
            to_bytes(out_path, errors='surrogate_or_strict')
        )

    def close(self):
        """ unmount container's filesystem """
        super(Connection, self).close()
        rc, stdout, stderr = self._buildah("umount")
        display.vvvvv("RC %s STDOUT %r STDERR %r" % (rc, stdout, stderr))
        self._connected = False
