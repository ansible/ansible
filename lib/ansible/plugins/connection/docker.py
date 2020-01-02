# Based on the chroot connection plugin by Maykel Moya
#
# (c) 2014, Lorin Hochstein
# (c) 2015, Leendert Brouwer (https://github.com/objectified)
# (c) 2015, Toshio Kuratomi <tkuratomi@ansible.com>
# (c) 2019, Felix Fontein <felix@fontein.de>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    author:
        - Lorin Hochestein
        - Leendert Brouwer
        - Felix Fontein (@felixfontein)
    connection: docker
    short_description: Run tasks in docker containers
    description:
        - Run commands or put/fetch files to an existing docker container.
    version_added: "2.0"
    options:
      remote_user:
        type: str
        description:
            - The user to execute as inside the container
        vars:
            - name: ansible_user
            - name: ansible_docker_user
      #docker_command:
      #  type: str
      #  description:
      #      - Docker CLI command to use instead of trying to find C(docker) in the path.
      #      - Note that this is ignored by the Docker SDK for Python driver.
      docker_extra_args:
        type: str
        description:
            - Extra arguments to pass to the docker command line
            - Note that this is ignored by the Docker SDK for Python driver.
        default: ''
      remote_addr:
        type: str
        description:
            - The name of the container you want to access.
        default: inventory_hostname
        vars:
            - name: ansible_host
            - name: ansible_docker_host
      docker_driver:
        type: str
        description:
            - Which internal driver to use to talk to the docker daemon.
            - Allowed values are C(auto) for autodetection, C(cli) for using the C(docker) CLI program,
              and C(docker-py) for using the Docker SDK for Python.
            - C(auto) tries to decide which driver to use. If I(docker_extra_args)
              is specified, the CLI driver will be used. Otherwise, it will check whether the Docker
              SDK for Python is installed; if a new enough version (1.7.0 or higher) is there, it will
              be used. Otherwise, it will check whether C(docker) can be found in the path. If it is
              found with a new enough version (1.3 or higher), it will be used.
        default: auto
        choices: [auto, cli, docker-py]
        vars:
            - name: docker_driver
        version_added: '2.10'
"""

import distutils.spawn
import fcntl
import io
import os
import os.path
import re
import socket as pysocket
import subprocess
import tarfile
import traceback

from distutils.version import LooseVersion

from ansible.compat import selectors
from ansible.errors import AnsibleError, AnsibleConnectionFailure, AnsibleFileNotFound
from ansible.module_utils.six import PY3
from ansible.module_utils.six.moves import shlex_quote
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.plugins.connection import ConnectionBase, BUFSIZE
from ansible.utils.display import Display

from ansible.module_utils.docker.common import (
    AnsibleDockerClientBase,
    RequestException,
)

try:
    from ansible.module_utils.docker.common import docker_version
    from docker.errors import DockerException, APIError, NotFound
    from docker.utils import socket as docker_socket
    import struct
except Exception:
    # missing Docker SDK for Python handled in ansible.module_utils.docker.common
    docker_version = None

display = Display()


MIN_DOCKER_PY = '1.7.0'
MIN_DOCKER_API = None


def _sanitize_version(version):
    return re.sub(u'[^0-9a-zA-Z.]', u'', version)


def _old_docker_cli_version(docker_cmd, play_context):
    cmd_args = []
    if play_context.docker_extra_args:
        cmd_args += play_context.docker_extra_args.split(' ')

    old_version_subcommand = ['version']

    old_docker_cmd = [docker_cmd] + cmd_args + old_version_subcommand
    p = subprocess.Popen(old_docker_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    cmd_output, err = p.communicate()

    return old_docker_cmd, to_native(cmd_output), err, p.returncode


def _new_docker_cli_version(docker_cmd, play_context):
    # no result yet, must be newer Docker version
    cmd_args = []
    if play_context.docker_extra_args:
        cmd_args += play_context.docker_extra_args.split(' ')

    new_version_subcommand = ['version', '--format', "'{{.Server.Version}}'"]

    new_docker_cmd = [docker_cmd] + cmd_args + new_version_subcommand
    p = subprocess.Popen(new_docker_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    cmd_output, err = p.communicate()
    return new_docker_cmd, to_native(cmd_output), err, p.returncode


def get_docker_cli_version(docker_cmd, play_context):

    cmd, cmd_output, err, returncode = _old_docker_cli_version(docker_cmd, play_context)
    if returncode == 0:
        for line in to_text(cmd_output, errors='surrogate_or_strict').split(u'\n'):
            if line.startswith(u'Server version:'):  # old docker versions
                return _sanitize_version(line.split()[2])

    cmd, cmd_output, err, returncode = _new_docker_cli_version(docker_cmd, play_context)
    if returncode:
        raise AnsibleError('Docker version check (%s) failed: %s' % (to_native(cmd), to_native(err)))

    return _sanitize_version(to_text(cmd_output, errors='surrogate_or_strict'))


class Connection(ConnectionBase):
    ''' Local docker based connections '''

    transport = 'docker'
    has_pipelining = True

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)
        self.kwargs = kwargs

        self.driver = None
        self.docker_cmd = None

    def _connect(self, port=None):
        """ Connect to the container. Nothing to do """
        super(Connection, self)._connect()
        if not self._connected:
            # Driver selection
            orig_driver = driver = self.get_option('docker_driver')
            if self.kwargs.get('docker_command') is not None or self._play_context.docker_extra_args:
                if driver == 'auto':
                    driver = 'cli'
                elif driver == 'docker-py':
                    raise AnsibleError('docker_extra_args must not be specified for docker-py driver')

            docker_cli_version = None
            if driver == 'auto':
                # If a new enough Docker SDK for Python is around, use it
                if docker_version is not None and LooseVersion(docker_version) >= LooseVersion(MIN_DOCKER_PY):
                    driver = 'docker-py'

                # If that wasn't the case, detect 'docker' CLI command
                if driver == 'auto':
                    docker_cmd = distutils.spawn.find_executable('docker')
                    if docker_cmd:
                        docker_cli_version = get_docker_cli_version(docker_cmd, self._play_context)
                        if docker_cli_version == u'dev' or LooseVersion(docker_cli_version) >= LooseVersion(u'1.3'):
                            driver = 'cli'
                            self.kwargs['docker_command'] = docker_cmd

                # If auto-detection failed, fail
                if driver == 'auto':
                    raise AnsibleError(
                        'Cannot find either Docker SDK for Python (>= {0}) or docker CLI command (>= 1.3)'.format(MIN_DOCKER_PY)
                    )

            display.vvv(
                'User asked for docker connection driver "{0}", and gets "{1}"'.format(orig_driver, driver),
                host=self._play_context.remote_addr
            )

            # Instantiate driver
            self.docker_cmd = None
            if driver == 'cli':
                self.driver = CLIDriver(self._display, self._play_context, docker_cli_version, self.kwargs)
                self.docker_cmd = self.driver.docker_cmd
            if driver == 'docker-py':
                self.driver = DockerPyDriver(self._display, self._play_context, self)

            # Log result
            display.vvv(u"ESTABLISH DOCKER CONNECTION FOR USER: {0}".format(
                self.driver.actual_user or u'?'), host=self._play_context.remote_addr
            )
            self._connected = True

    def exec_command(self, cmd, in_data=None, sudoable=False):
        """ Run a command on the docker host """
        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        return self.driver.exec_command(self._play_context, self.become, cmd, in_data, sudoable)

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
                "file or module does not exist: %s" % to_native(in_path))

        return self.driver.put_file(self._play_context, in_path, out_path)

    def fetch_file(self, in_path, out_path):
        """ Fetch a file from container to local. """
        super(Connection, self).fetch_file(in_path, out_path)
        display.vvv("FETCH %s TO %s" % (in_path, out_path), host=self._play_context.remote_addr)

        in_path = self._prefix_login_path(in_path)

        return self.driver.fetch_file(self._play_context, in_path, out_path)

    def close(self):
        """ Terminate the connection. Nothing to do for Docker"""
        super(Connection, self).close()
        self._connected = False


class CLIDriver:
    def __init__(self, connection_display, play_context, docker_cli_version, kwargs):
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

        if docker_cli_version is None:
            docker_cli_version = get_docker_cli_version(self.docker_cmd, play_context)
        if docker_cli_version == u'dev':
            display.warning(u'Docker version number is "dev". Will assume latest version.')
        if docker_cli_version != u'dev' and LooseVersion(docker_cli_version) < LooseVersion(u'1.3'):
            raise AnsibleError('docker connection type requires docker 1.3 or higher')

        # The remote user we will request from docker (if supported)
        self.remote_user = None
        # The actual user which will execute commands in docker (if known)
        self.actual_user = None

        if play_context.remote_user is not None:
            if docker_cli_version == u'dev' or LooseVersion(docker_cli_version) >= LooseVersion(u'1.7'):
                # Support for specifying the exec user was added in docker 1.7
                self.remote_user = play_context.remote_user
                self.actual_user = self.remote_user
            else:
                self.actual_user = self._get_docker_remote_user()

                if self.actual_user != play_context.remote_user:
                    display.warning(u'docker CLI {0} does not support remote_user, using container default: {1}'
                                    .format(docker_cli_version, self.actual_user or u'?'))
        elif connection_display.verbosity > 2:
            # Since we're not setting the actual_user, look it up so we have it for logging later
            # Only do this if display verbosity is high enough that we'll need the value
            # This saves overhead from calling into docker when we don't need to
            self.actual_user = self._get_docker_remote_user(play_context)

    def _get_docker_remote_user(self, play_context):
        """ Get the default user configured in the docker container """
        p = subprocess.Popen([self.docker_cmd, 'inspect', '--format', '{{.Config.User}}', play_context.remote_addr],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        out, err = p.communicate()
        out = to_text(out, errors='surrogate_or_strict')

        if p.returncode != 0:
            display.warning(u'unable to retrieve default user from docker container: %s %s' % (out, to_text(err)))
            return None

        # The default exec user is root, unless it was changed in the Dockerfile with USER
        return out.strip() or u'root'

    def _build_exec_cmd(self, play_context, cmd):
        """ Build the local docker exec command to run cmd on remote_host

            If remote_user is available and is supported by the docker
            version we are using, it will be provided to docker exec.
        """

        local_cmd = [self.docker_cmd]

        if play_context.docker_extra_args:
            local_cmd += play_context.docker_extra_args.split(' ')

        local_cmd += [b'exec']

        if self.remote_user is not None:
            local_cmd += [b'-u', self.remote_user]

        # -i is needed to keep stdin open which allows pipelining to work
        local_cmd += [b'-i', play_context.remote_addr] + cmd

        return local_cmd

    def exec_command(self, play_context, become, cmd, in_data=None, sudoable=False):
        """ Run a command on the docker host """
        local_cmd = self._build_exec_cmd(play_context, [play_context.executable, '-c', cmd])

        display.vvv(u"EXEC {0}".format(to_text(local_cmd)), host=play_context.remote_addr)
        display.debug("opening command with Popen()")

        local_cmd = [to_bytes(i, errors='surrogate_or_strict') for i in local_cmd]

        p = subprocess.Popen(
            local_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        display.debug("done running command with Popen()")

        if become and become.expect_prompt() and sudoable:
            fcntl.fcntl(p.stdout, fcntl.F_SETFL, fcntl.fcntl(p.stdout, fcntl.F_GETFL) | os.O_NONBLOCK)
            fcntl.fcntl(p.stderr, fcntl.F_SETFL, fcntl.fcntl(p.stderr, fcntl.F_GETFL) | os.O_NONBLOCK)
            selector = selectors.DefaultSelector()
            selector.register(p.stdout, selectors.EVENT_READ)
            selector.register(p.stderr, selectors.EVENT_READ)

            become_output = b''
            try:
                while not become.check_success(become_output) and not become.check_password_prompt(become_output):
                    events = selector.select(play_context.timeout)
                    if not events:
                        stdout, stderr = p.communicate()
                        raise AnsibleConnectionFailure('timeout waiting for privilege escalation password prompt:\n' + to_native(become_output))

                    for key, event in events:
                        if key.fileobj == p.stdout:
                            chunk = p.stdout.read()
                        elif key.fileobj == p.stderr:
                            chunk = p.stderr.read()

                    if not chunk:
                        stdout, stderr = p.communicate()
                        raise AnsibleConnectionFailure('privilege output closed while waiting for password prompt:\n' + to_native(become_output))
                    become_output += chunk
            finally:
                selector.close()

            if not become.check_success(become_output):
                become_pass = become.get_option('become_pass', playcontext=play_context)
                p.stdin.write(to_bytes(become_pass, errors='surrogate_or_strict') + b'\n')
            fcntl.fcntl(p.stdout, fcntl.F_SETFL, fcntl.fcntl(p.stdout, fcntl.F_GETFL) & ~os.O_NONBLOCK)
            fcntl.fcntl(p.stderr, fcntl.F_SETFL, fcntl.fcntl(p.stderr, fcntl.F_GETFL) & ~os.O_NONBLOCK)

        display.debug("getting output with communicate()")
        stdout, stderr = p.communicate(in_data)
        display.debug("done communicating")

        display.debug("done with docker.exec_command()")
        return (p.returncode, stdout, stderr)

    def put_file(self, play_context, in_path, out_path):
        """ Transfer a file from local to docker container """
        out_path = shlex_quote(out_path)
        # Older docker doesn't have native support for copying files into
        # running containers, so we use docker exec to implement this
        # Although docker version 1.8 and later provide support, the
        # owner and group of the files are always set to root
        with open(to_bytes(in_path, errors='surrogate_or_strict'), 'rb') as in_file:
            if not os.fstat(in_file.fileno()).st_size:
                count = ' count=0'
            else:
                count = ''
            args = self._build_exec_cmd(play_context, [play_context.executable, "-c", "dd of=%s bs=%s%s" % (out_path, BUFSIZE, count)])
            args = [to_bytes(i, errors='surrogate_or_strict') for i in args]
            try:
                p = subprocess.Popen(args, stdin=in_file,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except OSError:
                raise AnsibleConnectionFailure("docker connection requires dd command in the container to put files")
            stdout, stderr = p.communicate()

            if p.returncode != 0:
                raise AnsibleConnectionFailure("failed to transfer file %s to %s:\n%s\n%s" %
                                               (to_native(in_path), to_native(out_path), to_native(stdout), to_native(stderr)))

    def fetch_file(self, play_context, in_path, out_path):
        """ Fetch a file from container to local. """
        # out_path is the final file path, but docker takes a directory, not a
        # file path
        out_dir = os.path.dirname(out_path)

        args = [self.docker_cmd, "cp", "%s:%s" % (play_context.remote_addr, in_path), out_dir]
        args = [to_bytes(i, errors='surrogate_or_strict') for i in args]

        p = subprocess.Popen(args, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.communicate()

        actual_out_path = os.path.join(out_dir, os.path.basename(in_path))

        if p.returncode != 0:
            # Older docker doesn't have native support for fetching files command `cp`
            # If `cp` fails, try to use `dd` instead
            args = self._build_exec_cmd(play_context, [play_context.executable, "-c", "dd if=%s bs=%s" % (in_path, BUFSIZE)])
            args = [to_bytes(i, errors='surrogate_or_strict') for i in args]
            with open(to_bytes(actual_out_path, errors='surrogate_or_strict'), 'wb') as out_file:
                try:
                    p = subprocess.Popen(args, stdin=subprocess.PIPE,
                                         stdout=out_file, stderr=subprocess.PIPE)
                except OSError:
                    raise AnsibleConnectionFailure("docker connection requires dd command in the container to put files")
                stdout, stderr = p.communicate()

                if p.returncode != 0:
                    raise AnsibleConnectionFailure("failed to fetch file %s to %s:\n%s\n%s" % (in_path, out_path, stdout, stderr))

        # Rename if needed
        if actual_out_path != out_path:
            os.rename(to_bytes(actual_out_path, errors='strict'), to_bytes(out_path, errors='strict'))


class AnsibleDockerClient(AnsibleDockerClientBase):
    def __init__(self, connection_plugin):
        self.connection_plugin = connection_plugin
        super(AnsibleDockerClient, self).__init__(min_docker_version=MIN_DOCKER_PY, min_docker_api_version=MIN_DOCKER_API)

    def fail(self, msg, **kwargs):
        if kwargs:
            msg += '\nContext: ' + repr(kwargs)
        raise AnsibleConnectionFailure(msg)

    def _get_params(self):
        # TODO: use self.connection_plugin.get_option(...)
        return {}


class DockerSocketHandler:
    def __init__(self, sock, container=None):
        # Unfortunately necessary; see https://github.com/docker/docker-py/issues/983#issuecomment-492513718
        sock._writing = True
        sock._sock.setblocking(0)

        self._container = container

        self._sock = sock
        self._block_done_callback = None
        self._block_buffer = []
        self._eof = False
        self._read_buffer = b''
        self._write_buffer = b''

        self._current_stream = None
        self._current_missing = 0
        self._current_buffer = b''

        self._selector = selectors.DefaultSelector()
        self._selector.register(self._sock, selectors.EVENT_READ)

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        self._selector.close()

    def set_block_done_callback(self, block_done_callback):
        self._block_done_callback = block_done_callback
        if self._block_done_callback is not None:
            while self._block_buffer:
                elt = self._block_buffer.remove(0)
                self._block_done_callback(*elt)

    def _add_block(self, stream_id, data):
        if self._block_done_callback is not None:
            self._block_done_callback(stream_id, data)
        else:
            self._block_buffer.append((stream_id, data))

    def _read(self):
        if self._eof:
            return
        if hasattr(self._sock, 'recv'):
            data = self._sock.recv(4096)
        elif PY3 and isinstance(self._sock, getattr(pysocket, 'SocketIO')):
            data = self._sock.read()
        else:
            data = os.read(self._sock.fileno())
        if data is None:
            # no data available
            return
        display.vvv('read {0} bytes'.format(len(data)), host=self._container)
        if len(data) == 0:
            # Stream EOF
            self._eof = True
            return
        self._read_buffer += data
        while len(self._read_buffer) > 0:
            if self._current_missing > 0:
                n = min(len(self._read_buffer), self._current_missing)
                self._current_buffer += self._read_buffer[:n]
                self._read_buffer = self._read_buffer[n:]
                self._current_missing -= n
                if self._current_missing == 0:
                    self._add_block(self._current_stream, self._current_buffer)
                    self._current_buffer = b''
            if len(self._read_buffer) < 8:
                break
            self._current_stream, self._current_missing = struct.unpack('>BxxxL', self._read_buffer[:8])
            self._read_buffer = self._read_buffer[8:]
            if self._current_missing < 0:
                # Stream EOF (as reported by docker daemon)
                self._eof = True
                break

    def _write(self):
        if len(self._write_buffer) > 0:
            if hasattr(self._sock, 'send'):
                written = self._sock.send(self._write_buffer)
            else:
                written = os.write(self._sock.fileno(), self._write_buffer)
            self._write_buffer = self._write_buffer[written:]
            display.vvv('wrote {0} bytes, {1} are left'.format(written, len(self._write_buffer)), host=self._container)
            if len(self._write_buffer) > 0:
                self._selector.modify(self._sock, selectors.EVENT_READ | selectors.EVENT_WRITE)
            else:
                self._sock.flush()
                self._selector.modify(self._sock, selectors.EVENT_READ)

    def select(self, timeout=None):
        events = self._selector.select(timeout)
        for key, event in events:
            if key.fileobj == self._sock:
                display.vvvv(
                    '{0} read:{1} write:{2}'.format(event, event & selectors.EVENT_READ != 0, event & selectors.EVENT_WRITE != 0),
                    host=self._container)
                if event & selectors.EVENT_READ != 0:
                    self._read()
                if event & selectors.EVENT_WRITE != 0:
                    self._write()
        return len(events) > 0

    def is_eof(self):
        return self._eof

    def consume(self):
        stdout = []
        stderr = []

        def append_block(stream_id, data):
            if stream_id == docker_socket.STDOUT:
                stdout.append(data)
            elif stream_id == docker_socket.STDERR:
                stderr.append(data)
            else:
                raise ValueError('{0} is not a valid stream ID'.format(stream_id))

        self.set_block_done_callback(append_block)
        while not self._eof:
            self.select()
        return b''.join(stdout), b''.join(stderr)

    def write(self, str):
        self._write_buffer += str
        if len(self._write_buffer) == len(str):
            self._write()


class DockerPyDriver:
    def _call_client(self, play_context, callable, not_found_can_be_resource=False):
        try:
            return callable()
        except NotFound as e:
            if not_found_can_be_resource:
                raise AnsibleConnectionFailure('Could not find container "{1}" or resource in it ({0})'.format(e, play_context.remote_addr))
            else:
                raise AnsibleConnectionFailure('Could not find container "{1}" ({0})'.format(e, play_context.remote_addr))
        except APIError as e:
            if e.response and e.response.status_code == 409:
                raise AnsibleConnectionFailure('The container "{1}" has been paused ({0})'.format(e, play_context.remote_addr))
            self.client.fail(
                'An unexpected docker error occurred for container "{1}": {0}'.format(e, play_context.remote_addr),
                exception=traceback.format_exc()
            )
        except DockerException as e:
            self.client.fail(
                'An unexpected docker error occurred for container "{1}": {0}'.format(e, play_context.remote_addr),
                exception=traceback.format_exc()
            )
        except RequestException as e:
            self.client.fail(
                'An unexpected requests error occurred for container "{1}" when docker-py tried to talk to the docker daemon: {0}'
                .format(e, play_context.remote_addr),
                exception=traceback.format_exc()
            )

    def __init__(self, connection_display, play_context, connection_plugin):
        # Note: docker supports running as non-root in some configurations.
        # (For instance, setting the UNIX socket file to be readable and
        # writable by a specific UNIX group and then putting users into that
        # group).  Therefore we don't check that the user is root when using
        # this connection.  But if the user is getting a permission denied
        # error it probably means that docker on their system is only
        # configured to be connected to by root and they are not running as
        # root.

        self.client = AnsibleDockerClient(connection_plugin)

        self.actual_user = play_context.remote_user

        self.ids = dict()

        if self.actual_user is None and connection_display.verbosity > 2:
            # Since we're not setting the actual_user, look it up so we have it for logging later
            # Only do this if display verbosity is high enough that we'll need the value
            # This saves overhead from calling into docker when we don't need to
            result = self._call_client(play_context, lambda: self.client.inspect_container(play_context.remote_addr))
            if result.get('Config'):
                self.actual_user = result['Config'].get('User')

    def exec_command(self, play_context, become, cmd, in_data=None, sudoable=False):
        """ Run a command on the docker host """

        command = [play_context.executable, '-c', to_text(cmd)]

        do_become = become and become.expect_prompt() and sudoable

        display.vvv(
            u"EXEC {0}{1}{2}".format(
                to_text(command),
                ', with stdin ({0} bytes)'.format(len(in_data)) if in_data is not None else '',
                ', with become prompt' if do_become else '',
            ),
            host=play_context.remote_addr
        )

        need_stdin = True if (in_data is not None) or do_become else False

        exec_data = self._call_client(play_context, lambda: self.client.exec_create(
            play_context.remote_addr,
            command,
            stdout=True,
            stderr=True,
            stdin=need_stdin,
            user=play_context.remote_user or '',
            workdir=None,
        ))
        exec_id = exec_data['Id']

        if need_stdin:
            exec_socket = self._call_client(play_context, lambda: self.client.exec_start(
                exec_id,
                detach=False,
                socket=True,
            ))
            try:
                with DockerSocketHandler(exec_socket, container=play_context.remote_addr) as exec_socket_handler:
                    if do_become:
                        become_output = [b'']

                        def append_become_output(stream_id, data):
                            become_output[0] += data

                        exec_socket_handler.set_block_done_callback(append_become_output)

                        while not become.check_success(become_output[0]) and not become.check_password_prompt(become_output[0]):
                            if not exec_socket_handler.select(play_context.timeout):
                                stdout, stderr = exec_socket_handler.consume()
                                raise AnsibleConnectionFailure('timeout waiting for privilege escalation password prompt:\n' + to_native(become_output[0]))

                            if exec_socket_handler.is_eof():
                                raise AnsibleConnectionFailure('privilege output closed while waiting for password prompt:\n' + to_native(become_output[0]))

                        if not become.check_success(become_output[0]):
                            become_pass = become.get_option('become_pass', playcontext=play_context)
                            exec_socket_handler.write(to_bytes(become_pass, errors='surrogate_or_strict') + b'\n')

                    if in_data is not None:
                        exec_socket_handler.write(in_data)

                    stdout, stderr = exec_socket_handler.consume()
            finally:
                exec_socket.close()
        else:
            stdout, stderr = self._call_client(play_context, lambda: self.client.exec_start(
                exec_id,
                detach=False,
                stream=False,
                socket=False,
                demux=True,
            ))

        result = self._call_client(play_context, lambda: self.client.exec_inspect(exec_id))

        return result.get('ExitCode') or 0, stdout or b'', stderr or b''

    def put_file(self, play_context, in_path, out_path):
        """ Transfer a file from local to docker container """

        if self.actual_user not in self.ids:
            dummy, ids, dummy = self.exec_command(play_context, None, b'id -u && id -g')
            try:
                user_id, group_id = ids.splitlines()
                self.ids[self.actual_user] = int(user_id), int(group_id)
                display.vvvv(
                    'PUT: Determined uid={0} and gid={1} for user "{2}"'.format(user_id, group_id, self.actual_user),
                    host=play_context.remote_addr
                )
            except Exception as e:
                raise AnsibleConnectionFailure(
                    'Error while determining user and group ID of current user in container "{1}": {0}'
                    .format(e, play_context.remote_addr)
                )

        b_in_path = to_bytes(in_path, errors='surrogate_or_strict')

        out_dir, out_file = os.path.split(out_path)

        # TODO: stream tar file, instead of creating it in-memory into a BytesIO

        bio = io.BytesIO()
        with tarfile.open(fileobj=bio, mode='w|') as tar:
            tarinfo = tar.gettarinfo(in_path)
            tarinfo.name = out_file
            user_id, group_id = self.ids[self.actual_user]
            tarinfo.uid = user_id
            tarinfo.uname = ''
            if self.actual_user:
                tarinfo.uname = self.actual_user
            tarinfo.gid = group_id
            tarinfo.gname = ''
            tarinfo.mode &= 0o700
            with open(b_in_path, 'rb') as f:
                tar.addfile(tarinfo, fileobj=f)
        data = bio.getvalue()

        ok = self._call_client(play_context, lambda: self.client.put_archive(
            play_context.remote_addr,
            out_dir,
            data,  # can also be file object for streaming; this is only clear from the
                   # implementation of put_archive(), which uses requests's put().
                   # See https://2.python-requests.org/en/master/user/advanced/#streaming-uploads
        ), not_found_can_be_resource=True)
        if not ok:
            raise AnsibleConnectionFailure(
                'Unknown error while creating file "{0}" in container "{1}".'
                .format(out_path, play_context.remote_addr)
            )

    def fetch_file(self, play_context, in_path, out_path):
        """ Fetch a file from container to local. """

        considered_in_paths = set()

        while True:
            if in_path in considered_in_paths:
                raise AnsibleConnectionFailure('Found infinite symbolic link loop when trying to fetch "{0}"'.format(in_path))
            considered_in_paths.add(in_path)

            out_dir, out_file = os.path.split(out_path)

            display.vvvv('FETCH: Fetching "{0}"'.format(in_path), host=play_context.remote_addr)
            stream, stats = self._call_client(play_context, lambda: self.client.get_archive(
                play_context.remote_addr,
                in_path,
            ), not_found_can_be_resource=True)

            # TODO: stream tar file instead of downloading it into a BytesIO

            bio = io.BytesIO()
            for chunk in stream:
                bio.write(chunk)
            bio.seek(0)

            with tarfile.open(fileobj=bio, mode='r|') as tar:
                symlink_member = None
                first = True
                for member in tar:
                    if not first:
                        raise AnsibleConnectionFailure('Received tarfile contains more than one file!')
                    first = False
                    if member.issym():
                        symlink_member = member
                        continue
                    if not member.isfile():
                        raise AnsibleConnectionFailure('Remote file "{0}" is not a regular file or a symbolic link'.format(in_path))
                    member.name = out_file
                    tar.extract(member, path=out_dir, set_attrs=False)
                if first:
                    raise AnsibleConnectionFailure('Received tarfile is empty!')
                # If the only member was a file, it's already extracted. If it is a symlink, process it now.
                if symlink_member is not None:
                    in_path = os.path.join(os.path.split(in_path)[0], symlink_member.linkname)
                    display.vvvv('FETCH: Following symbolic link to "{0}"'.format(in_path), host=play_context.remote_addr)
                    continue
                return
