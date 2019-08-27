# Based on the buildah connection plugin
# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Connection plugin to interact with existing podman containers.
#   https://github.com/containers/libpod
#
# Written by: Tomas Tomecek (https://github.com/TomasTomecek)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import shlex
import shutil
import subprocess

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_bytes, to_native
from ansible.plugins.connection import ConnectionBase, ensure_connect
from ansible.utils.display import Display

display = Display()


DOCUMENTATION = """
    author: Tomas Tomecek (ttomecek@redhat.com)
    connection: podman
    short_description: Interact with an existing podman container
    description:
        - Run commands or put/fetch files to an existing container using podman tool.
    version_added: 2.8
    options:
      remote_addr:
        description:
          - The ID of the container you want to access.
        default: inventory_hostname
        vars:
          - name: ansible_host
      remote_user:
        description:
            - User specified via name or UID which is used to execute commands inside the container. If you
              specify the user via UID, you must set C(ANSIBLE_REMOTE_TMP) to a path that exits
               inside the container and is writable by Ansible.
        ini:
          - section: defaults
            key: remote_user
        env:
          - name: ANSIBLE_REMOTE_USER
        vars:
          - name: ansible_user
"""


# this _has to be_ named Connection
class Connection(ConnectionBase):
    """
    This is a connection plugin for podman. It uses podman binary to interact with the containers
    """

    # String used to identify this Connection class from other classes
    transport = 'podman'
    has_pipelining = True

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        self._container_id = self._play_context.remote_addr
        self._connected = False
        # container filesystem will be mounted here on host
        self._mount_point = None
        self.user = self._play_context.remote_user

    def _podman(self, cmd, cmd_args=None, in_data=None, use_container_id=True):
        """
        run podman executable

        :param cmd: podman's command to execute (str)
        :param cmd_args: list of arguments to pass to the command (list of str/bytes)
        :param in_data: data passed to podman's stdin
        :return: return code, stdout, stderr
        """
        local_cmd = ['podman', cmd]
        if use_container_id:
            local_cmd.append(self._container_id)
        if cmd_args:
            local_cmd += cmd_args
        local_cmd = [to_bytes(i, errors='surrogate_or_strict') for i in local_cmd]

        display.vvv("RUN %s" % (local_cmd,), host=self._container_id)
        p = subprocess.Popen(local_cmd, shell=False, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = p.communicate(input=in_data)
        display.vvvvv("STDOUT %s" % stdout)
        display.vvvvv("STDERR %s" % stderr)
        display.vvvvv("RC CODE %s" % p.returncode)
        stdout = to_bytes(stdout, errors='surrogate_or_strict')
        stderr = to_bytes(stderr, errors='surrogate_or_strict')
        return p.returncode, stdout, stderr

    def _connect(self):
        """
        no persistent connection is being maintained, mount container's filesystem
        so we can easily access it
        """
        super(Connection, self)._connect()
        rc, self._mount_point, stderr = self._podman("mount")
        if rc != 0:
            display.v("Failed to mount container %s: %s" % (self._container_id, stderr.strip()))
        else:
            self._mount_point = self._mount_point.strip()
            display.vvvvv("MOUNTPOINT %s RC %s STDERR %r" % (self._mount_point, rc, stderr))
        self._connected = True

    @ensure_connect
    def exec_command(self, cmd, in_data=None, sudoable=False):
        """ run specified command in a running OCI container using podman """
        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        # shlex.split has a bug with text strings on Python-2.6 and can only handle text strings on Python-3
        cmd_args_list = shlex.split(to_native(cmd, errors='surrogate_or_strict'))
        if self.user:
            cmd_args_list += ["--user", self.user]

        rc, stdout, stderr = self._podman("exec", cmd_args_list, in_data)

        display.vvvvv("STDOUT %r STDERR %r" % (stderr, stderr))
        return rc, stdout, stderr

    def put_file(self, in_path, out_path):
        """ Place a local file located in 'in_path' inside container at 'out_path' """
        super(Connection, self).put_file(in_path, out_path)
        display.vvv("PUT %s TO %s" % (in_path, out_path), host=self._container_id)
        if not self._mount_point:
            rc, stdout, stderr = self._podman(
                "cp", [in_path, self._container_id + ":" + out_path], use_container_id=False)
            if rc != 0:
                raise AnsibleError("Failed to copy file from %s to %s in container %s\n%s" % (
                    in_path, out_path, self._container_id, stderr))
        else:
            real_out_path = self._mount_point + to_bytes(out_path, errors='surrogate_or_strict')
            shutil.copyfile(
                to_bytes(in_path, errors='surrogate_or_strict'),
                to_bytes(real_out_path, errors='surrogate_or_strict')
            )

    def fetch_file(self, in_path, out_path):
        """ obtain file specified via 'in_path' from the container and place it at 'out_path' """
        super(Connection, self).fetch_file(in_path, out_path)
        display.vvv("FETCH %s TO %s" % (in_path, out_path), host=self._container_id)
        if not self._mount_point:
            rc, stdout, stderr = self._podman(
                "cp", [self._container_id + ":" + in_path, out_path], use_container_id=False)
            if rc != 0:
                raise AnsibleError("Failed to fetch file from %s to %s from container %s\n%s" % (
                    in_path, out_path, self._container_id, stderr))
        else:
            real_in_path = self._mount_point + to_bytes(in_path, errors='surrogate_or_strict')
            shutil.copyfile(
                to_bytes(real_in_path, errors='surrogate_or_strict'),
                to_bytes(out_path, errors='surrogate_or_strict')
            )

    def close(self):
        """ unmount container's filesystem """
        super(Connection, self).close()
        # we actually don't need to unmount since the container is mounted anyway
        # rc, stdout, stderr = self._podman("umount")
        # display.vvvvv("RC %s STDOUT %r STDERR %r" % (rc, stdout, stderr))
        self._connected = False
