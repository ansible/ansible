# Copyright (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright 2015 Abhijit Menon-Sen <ams@2ndQuadrant.com>
# Copyright 2017 Toshio Kuratomi <tkuratomi@ansible.com>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    connection: ssh
    short_description: connect via ssh client binary
    description:
        - This connection plugin allows ansible to communicate to the target machines via normal ssh command line.
    author: ansible (@core)
    version_added: historical
    options:
      host:
          description: Hostname/ip to connect to.
          default: inventory_hostname
          vars:
               - name: ansible_host
               - name: ansible_ssh_host
      host_key_checking:
          description: Determines if ssh should check host keys
          type: boolean
          ini:
              - section: defaults
                key: 'host_key_checking'
              - section: ssh_connection
                key: 'host_key_checking'
                version_added: '2.5'
          env:
              - name: ANSIBLE_HOST_KEY_CHECKING
              - name: ANSIBLE_SSH_HOST_KEY_CHECKING
                version_added: '2.5'
          vars:
              - name: ansible_host_key_checking
                version_added: '2.5'
              - name: ansible_ssh_host_key_checking
                version_added: '2.5'
      password:
          description: Authentication password for the C(remote_user). Can be supplied as CLI option.
          vars:
              - name: ansible_password
              - name: ansible_ssh_pass
      ssh_args:
          description: Arguments to pass to all ssh cli tools
          default: '-C -o ControlMaster=auto -o ControlPersist=60s'
          ini:
              - section: 'ssh_connection'
                key: 'ssh_args'
          env:
              - name: ANSIBLE_SSH_ARGS
      ssh_common_args:
          description: Common extra args for all ssh CLI tools
          vars:
              - name: ansible_ssh_common_args
      ssh_executable:
          default: ssh
          description:
            - This defines the location of the ssh binary. It defaults to `ssh` which will use the first ssh binary available in $PATH.
            - This option is usually not required, it might be useful when access to system ssh is restricted,
              or when using ssh wrappers to connect to remote hosts.
          env: [{name: ANSIBLE_SSH_EXECUTABLE}]
          ini:
          - {key: ssh_executable, section: ssh_connection}
          yaml: {key: ssh_connection.ssh_executable}
          #const: ANSIBLE_SSH_EXECUTABLE
          version_added: "2.2"
      scp_extra_args:
          description: Extra exclusive to the 'scp' CLI
          vars:
              - name: ansible_scp_extra_args
      sftp_extra_args:
          description: Extra exclusive to the 'sftp' CLI
          vars:
              - name: ansible_sftp_extra_args
      ssh_extra_args:
          description: Extra exclusive to the 'ssh' CLI
          vars:
              - name: ansible_ssh_extra_args
      retries:
          # constant: ANSIBLE_SSH_RETRIES
          description: Number of attempts to connect.
          default: 3
          type: integer
          env:
            - name: ANSIBLE_SSH_RETRIES
          ini:
            - section: connection
              key: retries
            - section: ssh_connection
              key: retries
      port:
          description: Remote port to connect to.
          type: int
          default: 22
          ini:
            - section: defaults
              key: remote_port
          env:
            - name: ANSIBLE_REMOTE_PORT
          vars:
            - name: ansible_port
            - name: ansible_ssh_port
      remote_user:
          description:
              - User name with which to login to the remote server, normally set by the remote_user keyword.
              - If no user is supplied, Ansible will let the ssh client binary choose the user as it normally
          ini:
            - section: defaults
              key: remote_user
          env:
            - name: ANSIBLE_REMOTE_USER
          vars:
            - name: ansible_user
            - name: ansible_ssh_user
      pipelining:
          default: ANSIBLE_PIPELINING
          description:
            - Pipelining reduces the number of SSH operations required to execute a module on the remote server,
              by executing many Ansible modules without actual file transfer.
            - This can result in a very significant performance improvement when enabled.
            - However this conflicts with privilege escalation (become).
              For example, when using sudo operations you must first disable 'requiretty' in the sudoers file for the target hosts,
              which is why this feature is disabled by default.
          env:
            - name: ANSIBLE_PIPELINING
            #- name: ANSIBLE_SSH_PIPELINING
          ini:
            - section: defaults
              key: pipelining
            #- section: ssh_connection
            #  key: pipelining
          type: boolean
          vars:
            - name: ansible_pipelining
            - name: ansible_ssh_pipelining
      private_key_file:
          description:
              - Path to private key file to use for authentication
          ini:
            - section: defaults
              key: private_key_file
          env:
            - name: ANSIBLE_PRIVATE_KEY_FILE
          vars:
            - name: ansible_private_key_file
            - name: ansible_ssh_private_key_file

      control_path:
        description:
          - This is the location to save ssh's ControlPath sockets, it uses ssh's variable substitution.
          - Since 2.3, if null, ansible will generate a unique hash. Use `%(directory)s` to indicate where to use the control dir path setting.
        env:
          - name: ANSIBLE_SSH_CONTROL_PATH
        ini:
          - key: control_path
            section: ssh_connection
      control_path_dir:
        default: ~/.ansible/cp
        description:
          - This sets the directory to use for ssh control path if the control path setting is null.
          - Also, provides the `%(directory)s` variable for the control path setting.
        env:
          - name: ANSIBLE_SSH_CONTROL_PATH_DIR
        ini:
          - section: ssh_connection
            key: control_path_dir
      sftp_batch_mode:
        default: 'yes'
        description: 'TODO: write it'
        env: [{name: ANSIBLE_SFTP_BATCH_MODE}]
        ini:
        - {key: sftp_batch_mode, section: ssh_connection}
        type: bool
      scp_if_ssh:
        default: smart
        description:
          - "Prefered method to use when transfering files over ssh"
          - When set to smart, Ansible will try them until one succeeds or they all fail
          - If set to True, it will force 'scp', if False it will use 'sftp'
        env: [{name: ANSIBLE_SCP_IF_SSH}]
        ini:
        - {key: scp_if_ssh, section: ssh_connection}
      use_tty:
        version_added: '2.5'
        default: 'yes'
        description: add -tt to ssh commands to force tty allocation
        env: [{name: ANSIBLE_SSH_USETTY}]
        ini:
        - {key: usetty, section: ssh_connection}
        type: bool
        yaml: {key: connection.usetty}
'''

import errno
import fcntl
import hashlib
import os
import pty
import subprocess
import time

from functools import wraps
from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleConnectionFailure, AnsibleFileNotFound
from ansible.errors import AnsibleOptionsError
from ansible.module_utils.six import PY3, text_type, binary_type
from ansible.module_utils.six.moves import shlex_quote
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.module_utils.parsing.convert_bool import BOOLEANS, boolean
from ansible.plugins.connection import ConnectionBase, BUFSIZE
from ansible.utils.path import unfrackpath, makedirs_safe

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


SSHPASS_AVAILABLE = None


class AnsibleControlPersistBrokenPipeError(AnsibleError):
    ''' ControlPersist broken pipe '''
    pass


def _ssh_retry(func):
    """
    Decorator to retry ssh/scp/sftp in the case of a connection failure

    Will retry if:
    * an exception is caught
    * ssh returns 255
    Will not retry if
    * remaining_tries is <2
    * retries limit reached
    """
    @wraps(func)
    def wrapped(self, *args, **kwargs):
        remaining_tries = int(C.ANSIBLE_SSH_RETRIES) + 1
        cmd_summary = "%s..." % args[0]
        for attempt in range(remaining_tries):
            cmd = args[0]
            if attempt != 0 and self._play_context.password and isinstance(cmd, list):
                # If this is a retry, the fd/pipe for sshpass is closed, and we need a new one
                self.sshpass_pipe = os.pipe()
                cmd[1] = b'-d' + to_bytes(self.sshpass_pipe[0], nonstring='simplerepr', errors='surrogate_or_strict')

            try:
                try:
                    return_tuple = func(self, *args, **kwargs)
                    display.vvv(return_tuple, host=self.host)
                    # 0 = success
                    # 1-254 = remote command return code
                    # 255 = failure from the ssh command itself
                except (AnsibleControlPersistBrokenPipeError) as e:
                    # Retry one more time because of the ControlPersist broken pipe (see #16731)
                    display.vvv(u"RETRYING BECAUSE OF CONTROLPERSIST BROKEN PIPE")
                    return_tuple = func(self, *args, **kwargs)

                if return_tuple[0] != 255:
                    break
                else:
                    raise AnsibleConnectionFailure("Failed to connect to the host via ssh: %s" % to_native(return_tuple[2]))
            except (AnsibleConnectionFailure, Exception) as e:
                if attempt == remaining_tries - 1:
                    raise
                else:
                    pause = 2 ** attempt - 1
                    if pause > 30:
                        pause = 30

                    if isinstance(e, AnsibleConnectionFailure):
                        msg = "ssh_retry: attempt: %d, ssh return code is 255. cmd (%s), pausing for %d seconds" % (attempt, cmd_summary, pause)
                    else:
                        msg = "ssh_retry: attempt: %d, caught exception(%s) from cmd (%s), pausing for %d seconds" % (attempt, e, cmd_summary, pause)

                    display.vv(msg, host=self.host)

                    time.sleep(pause)
                    continue

        return return_tuple
    return wrapped


class Connection(ConnectionBase):
    ''' ssh based connections '''

    transport = 'ssh'
    has_pipelining = True
    become_methods = frozenset(C.BECOME_METHODS).difference(['runas'])

    def __init__(self, *args, **kwargs):
        super(Connection, self).__init__(*args, **kwargs)

        self.host = self._play_context.remote_addr
        self.port = self._play_context.port
        self.user = self._play_context.remote_user
        self.control_path = C.ANSIBLE_SSH_CONTROL_PATH
        self.control_path_dir = C.ANSIBLE_SSH_CONTROL_PATH_DIR
        self.sshpass_pipe = None

    # The connection is created by running ssh/scp/sftp from the exec_command,
    # put_file, and fetch_file methods, so we don't need to do any connection
    # management here.

    def _connect(self):
        return self

    @staticmethod
    def _create_control_path(host, port, user, connection=None, pid=None):
        '''Make a hash for the controlpath based on con attributes'''
        pstring = '%s-%s-%s' % (host, port, user)
        if connection:
            pstring += '-%s' % connection
        if pid:
            pstring += '-%s' % to_text(pid)
        m = hashlib.sha1()
        m.update(to_bytes(pstring))
        digest = m.hexdigest()
        cpath = '%(directory)s/' + digest[:10]
        return cpath

    @staticmethod
    def _sshpass_available():
        global SSHPASS_AVAILABLE

        # We test once if sshpass is available, and remember the result. It
        # would be nice to use distutils.spawn.find_executable for this, but
        # distutils isn't always available; shutils.which() is Python3-only.

        if SSHPASS_AVAILABLE is None:
            try:
                p = subprocess.Popen(["sshpass"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                p.communicate()
                SSHPASS_AVAILABLE = True
            except OSError:
                SSHPASS_AVAILABLE = False

        return SSHPASS_AVAILABLE

    @staticmethod
    def _persistence_controls(b_command):
        '''
        Takes a command array and scans it for ControlPersist and ControlPath
        settings and returns two booleans indicating whether either was found.
        This could be smarter, e.g. returning false if ControlPersist is 'no',
        but for now we do it simple way.
        '''

        controlpersist = False
        controlpath = False

        for b_arg in (a.lower() for a in b_command):
            if b'controlpersist' in b_arg:
                controlpersist = True
            elif b'controlpath' in b_arg:
                controlpath = True

        return controlpersist, controlpath

    def _add_args(self, b_command, b_args, explanation):
        """
        Adds arguments to the ssh command and displays a caller-supplied explanation of why.

        :arg b_command: A list containing the command to add the new arguments to.
            This list will be modified by this method.
        :arg b_args: An iterable of new arguments to add.  This iterable is used
            more than once so it must be persistent (ie: a list is okay but a
            StringIO would not)
        :arg explanation: A text string containing explaining why the arguments
            were added.  It will be displayed with a high enough verbosity.
        .. note:: This function does its work via side-effect.  The b_command list has the new arguments appended.
        """
        display.vvvvv(u'SSH: %s: (%s)' % (explanation, ')('.join(to_text(a) for a in b_args)), host=self._play_context.remote_addr)
        b_command += b_args

    def _build_command(self, binary, *other_args):
        '''
        Takes a binary (ssh, scp, sftp) and optional extra arguments and returns
        a command line as an array that can be passed to subprocess.Popen.
        '''

        b_command = []

        #
        # First, the command to invoke
        #

        # If we want to use password authentication, we have to set up a pipe to
        # write the password to sshpass.

        if self._play_context.password:
            if not self._sshpass_available():
                raise AnsibleError("to use the 'ssh' connection type with passwords, you must install the sshpass program")

            self.sshpass_pipe = os.pipe()
            b_command += [b'sshpass', b'-d' + to_bytes(self.sshpass_pipe[0], nonstring='simplerepr', errors='surrogate_or_strict')]

        if binary == 'ssh':
            b_command += [to_bytes(self._play_context.ssh_executable, errors='surrogate_or_strict')]
        else:
            b_command += [to_bytes(binary, errors='surrogate_or_strict')]

        #
        # Next, additional arguments based on the configuration.
        #

        # sftp batch mode allows us to correctly catch failed transfers, but can
        # be disabled if the client side doesn't support the option. However,
        # sftp batch mode does not prompt for passwords so it must be disabled
        # if not using controlpersist and using sshpass
        if binary == 'sftp' and C.DEFAULT_SFTP_BATCH_MODE:
            if self._play_context.password:
                b_args = [b'-o', b'BatchMode=no']
                self._add_args(b_command, b_args, u'disable batch mode for sshpass')
            b_command += [b'-b', b'-']

        if self._play_context.verbosity > 3:
            b_command.append(b'-vvv')

        #
        # Next, we add [ssh_connection]ssh_args from ansible.cfg.
        #

        if self._play_context.ssh_args:
            b_args = [to_bytes(a, errors='surrogate_or_strict') for a in
                      self._split_ssh_args(self._play_context.ssh_args)]
            self._add_args(b_command, b_args, u"ansible.cfg set ssh_args")

        # Now we add various arguments controlled by configuration file settings
        # (e.g. host_key_checking) or inventory variables (ansible_ssh_port) or
        # a combination thereof.

        if not C.HOST_KEY_CHECKING:
            b_args = (b"-o", b"StrictHostKeyChecking=no")
            self._add_args(b_command, b_args, u"ANSIBLE_HOST_KEY_CHECKING/host_key_checking disabled")

        if self._play_context.port is not None:
            b_args = (b"-o", b"Port=" + to_bytes(self._play_context.port, nonstring='simplerepr', errors='surrogate_or_strict'))
            self._add_args(b_command, b_args, u"ANSIBLE_REMOTE_PORT/remote_port/ansible_port set")

        key = self._play_context.private_key_file
        if key:
            b_args = (b"-o", b'IdentityFile="' + to_bytes(os.path.expanduser(key), errors='surrogate_or_strict') + b'"')
            self._add_args(b_command, b_args, u"ANSIBLE_PRIVATE_KEY_FILE/private_key_file/ansible_ssh_private_key_file set")

        if not self._play_context.password:
            self._add_args(
                b_command, (
                    b"-o", b"KbdInteractiveAuthentication=no",
                    b"-o", b"PreferredAuthentications=gssapi-with-mic,gssapi-keyex,hostbased,publickey",
                    b"-o", b"PasswordAuthentication=no"
                ),
                u"ansible_password/ansible_ssh_pass not set"
            )

        user = self._play_context.remote_user
        if user:
            self._add_args(
                b_command,
                (b"-o", b"User=" + to_bytes(self._play_context.remote_user, errors='surrogate_or_strict')),
                u"ANSIBLE_REMOTE_USER/remote_user/ansible_user/user/-u set"
            )

        self._add_args(
            b_command,
            (b"-o", b"ConnectTimeout=" + to_bytes(self._play_context.timeout, errors='surrogate_or_strict', nonstring='simplerepr')),
            u"ANSIBLE_TIMEOUT/timeout set"
        )

        # Add in any common or binary-specific arguments from the PlayContext
        # (i.e. inventory or task settings or overrides on the command line).

        for opt in (u'ssh_common_args', u'{0}_extra_args'.format(binary)):
            attr = getattr(self._play_context, opt, None)
            if attr is not None:
                b_args = [to_bytes(a, errors='surrogate_or_strict') for a in self._split_ssh_args(attr)]
                self._add_args(b_command, b_args, u"PlayContext set %s" % opt)

        # Check if ControlPersist is enabled and add a ControlPath if one hasn't
        # already been set.

        controlpersist, controlpath = self._persistence_controls(b_command)

        if controlpersist:
            self._persistent = True

            if not controlpath:
                cpdir = unfrackpath(self.control_path_dir)
                b_cpdir = to_bytes(cpdir, errors='surrogate_or_strict')

                # The directory must exist and be writable.
                makedirs_safe(b_cpdir, 0o700)
                if not os.access(b_cpdir, os.W_OK):
                    raise AnsibleError("Cannot write to ControlPath %s" % to_native(cpdir))

                if not self.control_path:
                    self.control_path = self._create_control_path(
                        self.host,
                        self.port,
                        self.user
                    )
                b_args = (b"-o", b"ControlPath=" + to_bytes(self.control_path % dict(directory=cpdir), errors='surrogate_or_strict'))
                self._add_args(b_command, b_args, u"found only ControlPersist; added ControlPath")

        # Finally, we add any caller-supplied extras.
        if other_args:
            b_command += [to_bytes(a) for a in other_args]

        return b_command

    # Used by _run() to kill processes on failures
    @staticmethod
    def _terminate_process(p):
        """ Terminate a process, ignoring errors """
        try:
            p.terminate()
        except (OSError, IOError):
            pass

    @_ssh_retry
    def _run(self, cmd, in_data, sudoable=True, checkrc=True):
        """Wrapper around _bare_run that retries the connection
        """

        (returncode, b_stdout, b_stderr) = self._bare_run(cmd, in_data, sudoable=sudoable, external_fds=self.sshpass_pipe)

        if C.HOST_KEY_CHECKING:
            if cmd[0] == b"sshpass" and returncode == 6:
                raise AnsibleError('Using a SSH password instead of a key is not possible because Host Key checking is enabled and sshpass does not support '
                                   'this.  Please add this host\'s fingerprint to your known_hosts file to manage this host.')

        controlpersisterror = b'Bad configuration option: ControlPersist' in b_stderr or b'unknown configuration option: ControlPersist' in b_stderr
        if returncode != 0 and controlpersisterror:
            raise AnsibleError('using -c ssh on certain older ssh versions may not support ControlPersist, set ANSIBLE_SSH_ARGS="" '
                               '(or ssh_args in [ssh_connection] section of the config file) before running again')

        # If we find a broken pipe because of ControlPersist timeout expiring (see #16731),
        # we raise a special exception so that we can retry a connection.
        controlpersist_broken_pipe = b'mux_client_hello_exchange: write packet: Broken pipe' in b_stderr
        if returncode == 255 and controlpersist_broken_pipe:
            raise AnsibleControlPersistBrokenPipeError('SSH Error: data could not be sent because of ControlPersist broken pipe.')

        if returncode == 255 and in_data and checkrc:
            raise AnsibleConnectionFailure('SSH Error: data could not be sent to remote host "%s". Make sure this host can be reached over ssh' % self.host)

        return returncode, b_stdout, b_stderr

    @_ssh_retry
    def _file_transport_command(self, in_path, out_path, sftp_action):
        # scp and sftp require square brackets for IPv6 addresses, but
        # accept them for hostnames and IPv4 addresses too.
        host = '[%s]' % self.host

        # Transfer methods to try
        methods = []

        # Use the transfer_method option if set, otherwise use scp_if_ssh
        ssh_transfer_method = self._play_context.ssh_transfer_method
        if ssh_transfer_method is not None:
            if not (ssh_transfer_method in ('smart', 'sftp', 'scp', 'piped')):
                raise AnsibleOptionsError('transfer_method needs to be one of [smart|sftp|scp|piped]')
            if ssh_transfer_method == 'smart':
                methods = ['sftp', 'scp', 'piped']
            else:
                methods = [ssh_transfer_method]
        else:
            # since this can be a non-bool now, we need to handle it correctly
            scp_if_ssh = C.DEFAULT_SCP_IF_SSH
            if not isinstance(scp_if_ssh, bool):
                scp_if_ssh = scp_if_ssh.lower()
                if scp_if_ssh in BOOLEANS:
                    scp_if_ssh = boolean(scp_if_ssh, strict=False)
                elif scp_if_ssh != 'smart':
                    raise AnsibleOptionsError('scp_if_ssh needs to be one of [smart|True|False]')
            if scp_if_ssh == 'smart':
                methods = ['sftp', 'scp', 'piped']
            elif scp_if_ssh is True:
                methods = ['scp']
            else:
                methods = ['sftp']

        for method in methods:
            returncode = stdout = stderr = None
            if method == 'sftp':
                cmd = self._build_command('sftp', to_bytes(host))
                in_data = u"{0} {1} {2}\n".format(sftp_action, shlex_quote(in_path), shlex_quote(out_path))
                in_data = to_bytes(in_data, nonstring='passthru')
                (returncode, stdout, stderr) = self._bare_run(cmd, in_data, external_fds=self.sshpass_pipe)
            elif method == 'scp':
                if sftp_action == 'get':
                    cmd = self._build_command('scp', u'{0}:{1}'.format(host, shlex_quote(in_path)), out_path)
                else:
                    cmd = self._build_command('scp', in_path, u'{0}:{1}'.format(host, shlex_quote(out_path)))
                in_data = None
                (returncode, stdout, stderr) = self._bare_run(cmd, in_data, external_fds=self.sshpass_pipe)
            elif method == 'piped':
                if sftp_action == 'get':
                    # we pass sudoable=False to disable pty allocation, which
                    # would end up mixing stdout/stderr and screwing with newlines
                    (returncode, stdout, stderr) = self.exec_command('dd if=%s bs=%s' % (in_path, BUFSIZE), sudoable=False)
                    out_file = open(to_bytes(out_path, errors='surrogate_or_strict'), 'wb+')
                    out_file.write(stdout)
                    out_file.close()
                else:
                    in_data = open(to_bytes(in_path, errors='surrogate_or_strict'), 'rb').read()
                    in_data = to_bytes(in_data, nonstring='passthru')
                    (returncode, stdout, stderr) = self.exec_command('dd of=%s bs=%s' % (out_path, BUFSIZE), in_data=in_data, sudoable=False)

            # Check the return code and rollover to next method if failed
            if returncode == 0:
                return (returncode, stdout, stderr)
            else:
                # If not in smart mode, the data will be printed by the raise below
                if len(methods) > 1:
                    display.warning(msg='%s transfer mechanism failed on %s. Use ANSIBLE_DEBUG=1 to see detailed information' % (method, host))
                    display.debug(msg='%s' % to_native(stdout))
                    display.debug(msg='%s' % to_native(stderr))

        if returncode == 255:
            raise AnsibleConnectionFailure("Failed to connect to the host via %s: %s" % (method, to_native(stderr)))
        else:
            raise AnsibleError("failed to transfer file to %s %s:\n%s\n%s" %
                               (to_native(in_path), to_native(out_path), to_native(stdout), to_native(stderr)))

    #
    # Main public methods
    #
    def exec_command(self, cmd, in_data=None, sudoable=True):
        ''' run a command on the remote host '''

        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        display.vvv(u"ESTABLISH SSH CONNECTION FOR USER: {0}".format(self._play_context.remote_user), host=self._play_context.remote_addr)

        # we can only use tty when we are not pipelining the modules. piping
        # data into /usr/bin/python inside a tty automatically invokes the
        # python interactive-mode but the modules are not compatible with the
        # interactive-mode ("unexpected indent" mainly because of empty lines)

        ssh_executable = self._play_context.ssh_executable

        # -tt can cause various issues in some environments so allow the user
        # to disable it as a troubleshooting method.
        use_tty = self.get_option('use_tty')

        if not in_data and sudoable and use_tty:
            args = (ssh_executable, '-tt', self.host, cmd)
        else:
            args = (ssh_executable, self.host, cmd)

        cmd = self._build_command(*args)
        (returncode, stdout, stderr) = self._run(cmd, in_data, sudoable=sudoable)

        return (returncode, stdout, stderr)

    def put_file(self, in_path, out_path):
        ''' transfer a file from local to remote '''

        super(Connection, self).put_file(in_path, out_path)

        display.vvv(u"PUT {0} TO {1}".format(in_path, out_path), host=self.host)
        if not os.path.exists(to_bytes(in_path, errors='surrogate_or_strict')):
            raise AnsibleFileNotFound("file or module does not exist: {0}".format(to_native(in_path)))

        return self._file_transport_command(in_path, out_path, 'put')

    def fetch_file(self, in_path, out_path):
        ''' fetch a file from remote to local '''

        super(Connection, self).fetch_file(in_path, out_path)

        display.vvv(u"FETCH {0} TO {1}".format(in_path, out_path), host=self.host)
        return self._file_transport_command(in_path, out_path, 'get')

    def reset(self):
        # If we have a persistent ssh connection (ControlPersist), we can ask it to stop listening.
        cmd = self._build_command(self._play_context.ssh_executable, '-O', 'stop', self.host)
        controlpersist, controlpath = self._persistence_controls(cmd)
        if controlpersist:
            display.vvv(u'sending stop: %s' % cmd)
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = p.communicate()
            status_code = p.wait()
            if status_code != 0:
                raise AnsibleError("Cannot reset connection:\n%s" % stderr)

        self.close()

    def close(self):
        self._connected = False
