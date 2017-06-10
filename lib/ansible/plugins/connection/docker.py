# Based on the chroot connection plugin by Maykel Moya
#
# Connection plugin for configuring docker containers
# (c) 2014, Lorin Hochstein
# (c) 2015, Leendert Brouwer
# (c) 2015, Toshio Kuratomi <tkuratomi@ansible.com>
#
# Maintainer: Leendert Brouwer (https://github.com/objectified)
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

import distutils.spawn
import os
import os.path
import subprocess
import re

from distutils.version import LooseVersion

import ansible.constants as C
from ansible.errors import AnsibleError, AnsibleFileNotFound
from ansible.module_utils.six.moves import shlex_quote
from ansible.module_utils._text import to_bytes, to_native
from ansible.plugins.connection import ConnectionBase, BUFSIZE


try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class Connection(ConnectionBase):
    ''' Local docker based connections '''

    transport = 'docker'
    has_pipelining = True
    become_methods = frozenset(C.BECOME_METHODS)

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        # Note: docker supports running as non-root in some configurations.
        # (For instance, setting the UNIX socket file to be readable and
        # writable by a specific UNIX group and then putting users into that
        # group).  Therefore we don't check that the user is root when using
        # this connection.  But if the user is getting a permission denied
        # error it probably means that docker on their system is only
        # configured to be connected to by root and they are not running as
        # root.

        if 'docker_command' in kwargs:
            self.docker_cmd = kwargs['docker_command']
        else:
            self.docker_cmd = distutils.spawn.find_executable('docker')
            if not self.docker_cmd:
                raise AnsibleError("docker command not found in PATH")

        docker_version = self._get_docker_version()
        if LooseVersion(docker_version) < LooseVersion('1.3'):
            raise AnsibleError('docker connection type requires docker 1.3 or higher')

        # The remote user we will request from docker (if supported)
        self.remote_user = None
        # The actual user which will execute commands in docker (if known)
        self.actual_user = None

        if self._play_context.remote_user is not None:
            if LooseVersion(docker_version) >= LooseVersion('1.7'):
                # Support for specifying the exec user was added in docker 1.7
                self.remote_user = self._play_context.remote_user
                self.actual_user = self.remote_user
            else:
                self.actual_user = self._get_docker_remote_user()

                if self.actual_user != self._play_context.remote_user:
                    display.warning('docker {0} does not support remote_user, using container default: {1}'
                                    .format(docker_version, self.actual_user or '?'))
        elif self._display.verbosity > 2:
            # Since we're not setting the actual_user, look it up so we have it for logging later
            # Only do this if display verbosity is high enough that we'll need the value
            # This saves overhead from calling into docker when we don't need to
            self.actual_user = self._get_docker_remote_user()

    @staticmethod
    def _sanitize_version(version):
        return re.sub('[^0-9a-zA-Z\.]', '', version)

    def _old_docker_version(self):
        cmd_args = []
        if self._play_context.docker_extra_args:
            cmd_args += self._play_context.docker_extra_args.split(' ')

        old_version_subcommand = ['version']

        old_docker_cmd = [self.docker_cmd] + cmd_args + old_version_subcommand
        p = subprocess.Popen(old_docker_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        cmd_output, err = p.communicate()

        return old_docker_cmd, to_native(cmd_output), err, p.returncode

    def _new_docker_version(self):
        # no result yet, must be newer Docker version
        cmd_args = []
        if self._play_context.docker_extra_args:
            cmd_args += self._play_context.docker_extra_args.split(' ')

        new_version_subcommand = ['version', '--format', "'{{.Server.Version}}'"]

        new_docker_cmd = [self.docker_cmd] + cmd_args + new_version_subcommand
        p = subprocess.Popen(new_docker_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        cmd_output, err = p.communicate()
        return new_docker_cmd, to_native(cmd_output), err, p.returncode

    def _get_docker_version(self):

        cmd, cmd_output, err, returncode = self._old_docker_version()
        if returncode == 0:
            for line in cmd_output.split('\n'):
                if line.startswith('Server version:'):  # old docker versions
                    return self._sanitize_version(line.split()[2])

        cmd, cmd_output, err, returncode = self._new_docker_version()
        if returncode:
            raise AnsibleError('Docker version check (%s) failed: %s' % (cmd, err))

        return self._sanitize_version(cmd_output)

    def _get_docker_remote_user(self):
        """ Get the default user configured in the docker container """
        p = subprocess.Popen([self.docker_cmd, 'inspect', '--format', '{{.Config.User}}', self._play_context.remote_addr],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        out, err = p.communicate()

        if p.returncode != 0:
            display.warning('unable to retrieve default user from docker container: %s' % out + err)
            return None

        # The default exec user is root, unless it was changed in the Dockerfile with USER
        return out.strip() or 'root'

    def _build_exec_cmd(self, cmd):
        """ Build the local docker exec command to run cmd on remote_host

            If remote_user is available and is supported by the docker
            version we are using, it will be provided to docker exec.
        """

        local_cmd = [self.docker_cmd]

        if self._play_context.docker_extra_args:
            local_cmd += self._play_context.docker_extra_args.split(' ')

        local_cmd += ['exec']

        if self.remote_user is not None:
            local_cmd += ['-u', self.remote_user]

        # -i is needed to keep stdin open which allows pipelining to work
        local_cmd += ['-i', self._play_context.remote_addr] + cmd

        return local_cmd

    def _connect(self, port=None):
        """ Connect to the container. Nothing to do """
        super(Connection, self)._connect()
        if not self._connected:
            display.vvv(u"ESTABLISH DOCKER CONNECTION FOR USER: {0}".format(
                self.actual_user or '?'), host=self._play_context.remote_addr
            )
            self._connected = True

    def exec_command(self, cmd, in_data=None, sudoable=False):
        """ Run a command on the docker host """
        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        local_cmd = self._build_exec_cmd([self._play_context.executable, '-c', cmd])

        display.vvv("EXEC %s" % (local_cmd,), host=self._play_context.remote_addr)
        local_cmd = [to_bytes(i, errors='surrogate_or_strict') for i in local_cmd]
        p = subprocess.Popen(local_cmd, shell=False, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)

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
        """ Transfer a file from local to docker container """
        super(Connection, self).put_file(in_path, out_path)
        display.vvv("PUT %s TO %s" % (in_path, out_path), host=self._play_context.remote_addr)

        out_path = self._prefix_login_path(out_path)
        if not os.path.exists(to_bytes(in_path, errors='surrogate_or_strict')):
            raise AnsibleFileNotFound(
                "file or module does not exist: %s" % in_path)

        out_path = shlex_quote(out_path)
        # Older docker doesn't have native support for copying files into
        # running containers, so we use docker exec to implement this
        # Although docker version 1.8 and later provide support, the
        # owner and group of the files are always set to root
        args = self._build_exec_cmd([self._play_context.executable, "-c", "dd of=%s bs=%s" % (out_path, BUFSIZE)])
        args = [to_bytes(i, errors='surrogate_or_strict') for i in args]
        with open(to_bytes(in_path, errors='surrogate_or_strict'), 'rb') as in_file:
            try:
                p = subprocess.Popen(args, stdin=in_file,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except OSError:
                raise AnsibleError("docker connection requires dd command in the container to put files")
            stdout, stderr = p.communicate()

            if p.returncode != 0:
                raise AnsibleError("failed to transfer file %s to %s:\n%s\n%s" % (in_path, out_path, stdout, stderr))

    def fetch_file(self, in_path, out_path):
        """ Fetch a file from container to local. """
        super(Connection, self).fetch_file(in_path, out_path)
        display.vvv("FETCH %s TO %s" % (in_path, out_path), host=self._play_context.remote_addr)

        in_path = self._prefix_login_path(in_path)
        # out_path is the final file path, but docker takes a directory, not a
        # file path
        out_dir = os.path.dirname(out_path)

        args = [self.docker_cmd, "cp", "%s:%s" % (self._play_context.remote_addr, in_path), out_dir]
        args = [to_bytes(i, errors='surrogate_or_strict') for i in args]

        p = subprocess.Popen(args, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.communicate()

        # Rename if needed
        actual_out_path = os.path.join(out_dir, os.path.basename(in_path))
        if actual_out_path != out_path:
            os.rename(to_bytes(actual_out_path, errors='strict'), to_bytes(out_path, errors='strict'))

    def close(self):
        """ Terminate the connection. Nothing to do for Docker"""
        super(Connection, self).close()
        self._connected = False
