# Copyright (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright 2015 Abhijit Menon-Sen <ams@2ndQuadrant.com>
# Copyright 2017 Toshio Kuratomi <tkuratomi@ansible.com>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: ssh
    short_description: connect via ssh client binary
    description:
        - This connection plugin allows ansible to communicate to the target machines via normal ssh command line.
        - Ansible does not expose a channel to allow communication between the user and the ssh process to accept
          a password manually to decrypt an ssh key when using this connection plugin (which is the default). The
          use of ``ssh-agent`` is highly recommended.
    author: ansible (@core)
    extends_documentation_fragment:
        - connection_pipelining
    version_added: historical
    notes:
        - Many options default to 'None' here but that only means we don't override the ssh tool's defaults and/or configuration.
          For example, if you specify the port in this plugin it will override any C(Port) entry in your C(.ssh/config).
    options:
      host:
          description: Hostname/ip to connect to.
          vars:
               - name: inventory_hostname
               - name: ansible_host
               - name: ansible_ssh_host
               - name: delegated_vars['ansible_host']
               - name: delegated_vars['ansible_ssh_host']
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
              - name: ansible_ssh_password
      sshpass_prompt:
          description: Password prompt that sshpass should search for. Supported by sshpass 1.06 and up.
          default: ''
          ini:
              - section: 'ssh_connection'
                key: 'sshpass_prompt'
          env:
              - name: ANSIBLE_SSHPASS_PROMPT
          vars:
              - name: ansible_sshpass_prompt
          version_added: '2.10'
      ssh_args:
          description: Arguments to pass to all ssh cli tools
          default: '-C -o ControlMaster=auto -o ControlPersist=60s'
          ini:
              - section: 'ssh_connection'
                key: 'ssh_args'
          env:
              - name: ANSIBLE_SSH_ARGS
          vars:
              - name: ansible_ssh_args
                version_added: '2.7'
          cli:
              - name: ssh_args
      ssh_common_args:
          description: Common extra args for all ssh CLI tools
          ini:
              - section: 'ssh_connection'
                key: 'ssh_common_args'
                version_added: '2.7'
          env:
              - name: ANSIBLE_SSH_COMMON_ARGS
                version_added: '2.7'
          vars:
              - name: ansible_ssh_common_args
          cli:
              - name: ssh_common_args
      ssh_executable:
          default: ssh
          description:
            - This defines the location of the ssh binary. It defaults to ``ssh`` which will use the first ssh binary available in $PATH.
            - This option is usually not required, it might be useful when access to system ssh is restricted,
              or when using ssh wrappers to connect to remote hosts.
          env: [{name: ANSIBLE_SSH_EXECUTABLE}]
          ini:
          - {key: ssh_executable, section: ssh_connection}
          #const: ANSIBLE_SSH_EXECUTABLE
          version_added: "2.2"
          vars:
              - name: ansible_ssh_executable
                version_added: '2.7'
      sftp_executable:
          default: sftp
          description:
            - This defines the location of the sftp binary. It defaults to ``sftp`` which will use the first binary available in $PATH.
          env: [{name: ANSIBLE_SFTP_EXECUTABLE}]
          ini:
          - {key: sftp_executable, section: ssh_connection}
          version_added: "2.6"
          vars:
              - name: ansible_sftp_executable
                version_added: '2.7'
      scp_executable:
          default: scp
          description:
            - This defines the location of the scp binary. It defaults to `scp` which will use the first binary available in $PATH.
          env: [{name: ANSIBLE_SCP_EXECUTABLE}]
          ini:
          - {key: scp_executable, section: ssh_connection}
          version_added: "2.6"
          vars:
              - name: ansible_scp_executable
                version_added: '2.7'
      scp_extra_args:
          description: Extra exclusive to the ``scp`` CLI
          vars:
              - name: ansible_scp_extra_args
          env:
            - name: ANSIBLE_SCP_EXTRA_ARGS
              version_added: '2.7'
          ini:
            - key: scp_extra_args
              section: ssh_connection
              version_added: '2.7'
          cli:
            - name: scp_extra_args
      sftp_extra_args:
          description: Extra exclusive to the ``sftp`` CLI
          vars:
              - name: ansible_sftp_extra_args
          env:
            - name: ANSIBLE_SFTP_EXTRA_ARGS
              version_added: '2.7'
          ini:
            - key: sftp_extra_args
              section: ssh_connection
              version_added: '2.7'
          cli:
            - name: sftp_extra_args
      ssh_extra_args:
          description: Extra exclusive to the 'ssh' CLI
          vars:
              - name: ansible_ssh_extra_args
          env:
            - name: ANSIBLE_SSH_EXTRA_ARGS
              version_added: '2.7'
          ini:
            - key: ssh_extra_args
              section: ssh_connection
              version_added: '2.7'
          cli:
            - name: ssh_extra_args
      retries:
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
          vars:
            - name: ansible_ssh_retries
              version_added: '2.7'
      port:
          description: Remote port to connect to.
          type: int
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
          cli:
            - name: user
      pipelining:
          env:
            - name: ANSIBLE_PIPELINING
            - name: ANSIBLE_SSH_PIPELINING
          ini:
            - section: connection
              key: pipelining
            - section: ssh_connection
              key: pipelining
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
          cli:
            - name: private_key_file

      control_path:
        description:
          - This is the location to save ssh's ControlPath sockets, it uses ssh's variable substitution.
          - Since 2.3, if null (default), ansible will generate a unique hash. Use `%(directory)s` to indicate where to use the control dir path setting.
          - Before 2.3 it defaulted to `control_path=%(directory)s/ansible-ssh-%%h-%%p-%%r`.
          - Be aware that this setting is ignored if `-o ControlPath` is set in ssh args.
        env:
          - name: ANSIBLE_SSH_CONTROL_PATH
        ini:
          - key: control_path
            section: ssh_connection
        vars:
          - name: ansible_control_path
            version_added: '2.7'
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
        vars:
          - name: ansible_control_path_dir
            version_added: '2.7'
      sftp_batch_mode:
        default: 'yes'
        description: 'TODO: write it'
        env: [{name: ANSIBLE_SFTP_BATCH_MODE}]
        ini:
        - {key: sftp_batch_mode, section: ssh_connection}
        type: bool
        vars:
          - name: ansible_sftp_batch_mode
            version_added: '2.7'
      ssh_transfer_method:
        default: smart
        description:
            - "Preferred method to use when transferring files over ssh"
            - Setting to 'smart' (default) will try them in order, until one succeeds or they all fail
            - Using 'piped' creates an ssh pipe with ``dd`` on either side to copy the data
        choices: ['sftp', 'scp', 'piped', 'smart']
        env: [{name: ANSIBLE_SSH_TRANSFER_METHOD}]
        ini:
            - {key: transfer_method, section: ssh_connection}
      scp_if_ssh:
        default: smart
        description:
          - "Preferred method to use when transfering files over ssh"
          - When set to smart, Ansible will try them until one succeeds or they all fail
          - If set to True, it will force 'scp', if False it will use 'sftp'
        env: [{name: ANSIBLE_SCP_IF_SSH}]
        ini:
        - {key: scp_if_ssh, section: ssh_connection}
        vars:
          - name: ansible_scp_if_ssh
            version_added: '2.7'
      use_tty:
        version_added: '2.5'
        default: 'yes'
        description: add -tt to ssh commands to force tty allocation
        env: [{name: ANSIBLE_SSH_USETTY}]
        ini:
        - {key: usetty, section: ssh_connection}
        type: bool
        vars:
          - name: ansible_ssh_use_tty
            version_added: '2.7'
      timeout:
        default: 10
        description:
            - This is the default ammount of time we will wait while establishing an ssh connection
            - It also controls how long we can wait to access reading the connection once established (select on the socket)
        env:
            - name: ANSIBLE_TIMEOUT
            - name: ANSIBLE_SSH_TIMEOUT
              version_added: '2.11'
        ini:
            - key: timeout
              section: defaults
            - key: timeout
              section: ssh_connection
              version_added: '2.11'
        vars:
          - name: ansible_ssh_timeout
            version_added: '2.11'
        cli:
          - name: timeout
        type: integer
'''

import errno
import fcntl
import hashlib
import os
import pty
import re
import subprocess
import time

from functools import wraps
from ansible import constants as C
from ansible.errors import (
    AnsibleAuthenticationFailure,
    AnsibleConnectionFailure,
    AnsibleError,
    AnsibleFileNotFound,
)
from ansible.errors import AnsibleOptionsError
from ansible.module_utils.compat import selectors
from ansible.module_utils.six import PY3, text_type, binary_type
from ansible.module_utils.six.moves import shlex_quote
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.module_utils.parsing.convert_bool import BOOLEANS, boolean
from ansible.plugins.connection import ConnectionBase, BUFSIZE
from ansible.plugins.shell.powershell import _parse_clixml
from ansible.utils.display import Display
from ansible.utils.path import unfrackpath, makedirs_safe

display = Display()


b_NOT_SSH_ERRORS = (b'Traceback (most recent call last):',  # Python-2.6 when there's an exception
                                                            # while invoking a script via -m
                    b'PHP Parse error:',  # Php always returns error 255
                    )

SSHPASS_AVAILABLE = None


class AnsibleControlPersistBrokenPipeError(AnsibleError):
    ''' ControlPersist broken pipe '''
    pass


def _handle_error(remaining_retries, command, return_tuple, no_log, host, display=display):

    # sshpass errors
    if command == b'sshpass':
        # Error 5 is invalid/incorrect password. Raise an exception to prevent retries from locking the account.
        if return_tuple[0] == 5:
            msg = 'Invalid/incorrect username/password. Skipping remaining {0} retries to prevent account lockout:'.format(remaining_retries)
            if remaining_retries <= 0:
                msg = 'Invalid/incorrect password:'
            if no_log:
                msg = '{0} <error censored due to no log>'.format(msg)
            else:
                msg = '{0} {1}'.format(msg, to_native(return_tuple[2]).rstrip())
            raise AnsibleAuthenticationFailure(msg)

        # sshpass returns codes are 1-6. We handle 5 previously, so this catches other scenarios.
        # No exception is raised, so the connection is retried - except when attempting to use
        # sshpass_prompt with an sshpass that won't let us pass -P, in which case we fail loudly.
        elif return_tuple[0] in [1, 2, 3, 4, 6]:
            msg = 'sshpass error:'
            if no_log:
                msg = '{0} <error censored due to no log>'.format(msg)
            else:
                details = to_native(return_tuple[2]).rstrip()
                if "sshpass: invalid option -- 'P'" in details:
                    details = 'Installed sshpass version does not support customized password prompts. ' \
                              'Upgrade sshpass to use sshpass_prompt, or otherwise switch to ssh keys.'
                    raise AnsibleError('{0} {1}'.format(msg, details))
                msg = '{0} {1}'.format(msg, details)

    if return_tuple[0] == 255:
        SSH_ERROR = True
        for signature in b_NOT_SSH_ERRORS:
            if signature in return_tuple[1]:
                SSH_ERROR = False
                break

        if SSH_ERROR:
            msg = "Failed to connect to the host via ssh:"
            if no_log:
                msg = '{0} <error censored due to no log>'.format(msg)
            else:
                msg = '{0} {1}'.format(msg, to_native(return_tuple[2]).rstrip())
            raise AnsibleConnectionFailure(msg)

    # For other errors, no exception is raised so the connection is retried and we only log the messages
    if 1 <= return_tuple[0] <= 254:
        msg = u"Failed to connect to the host via ssh:"
        if no_log:
            msg = u'{0} <error censored due to no log>'.format(msg)
        else:
            msg = u'{0} {1}'.format(msg, to_text(return_tuple[2]).rstrip())
        display.vvv(msg, host=host)


def _ssh_retry(func):
    """
    Decorator to retry ssh/scp/sftp in the case of a connection failure

    Will retry if:
    * an exception is caught
    * ssh returns 255
    Will not retry if
    * sshpass returns 5 (invalid password, to prevent account lockouts)
    * remaining_tries is < 2
    * retries limit reached
    """
    @wraps(func)
    def wrapped(self, *args, **kwargs):
        remaining_tries = int(self.get_option('retries')) + 1
        cmd_summary = u"%s..." % to_text(args[0])
        conn_password = self.get_option('password') or self._play_context.password
        for attempt in range(remaining_tries):
            cmd = args[0]
            if attempt != 0 and conn_password and isinstance(cmd, list):
                # If this is a retry, the fd/pipe for sshpass is closed, and we need a new one
                self.sshpass_pipe = os.pipe()
                cmd[1] = b'-d' + to_bytes(self.sshpass_pipe[0], nonstring='simplerepr', errors='surrogate_or_strict')

            try:
                try:
                    return_tuple = func(self, *args, **kwargs)
                    # TODO: this should come from task
                    if self._play_context.no_log:
                        display.vvv(u'rc=%s, stdout and stderr censored due to no log' % return_tuple[0], host=self.host)
                    else:
                        display.vvv(return_tuple, host=self.host)
                    # 0 = success
                    # 1-254 = remote command return code
                    # 255 could be a failure from the ssh command itself
                except (AnsibleControlPersistBrokenPipeError):
                    # Retry one more time because of the ControlPersist broken pipe (see #16731)
                    cmd = args[0]
                    if conn_password and isinstance(cmd, list):
                        # This is a retry, so the fd/pipe for sshpass is closed, and we need a new one
                        self.sshpass_pipe = os.pipe()
                        cmd[1] = b'-d' + to_bytes(self.sshpass_pipe[0], nonstring='simplerepr', errors='surrogate_or_strict')
                    display.vvv(u"RETRYING BECAUSE OF CONTROLPERSIST BROKEN PIPE")
                    return_tuple = func(self, *args, **kwargs)

                remaining_retries = remaining_tries - attempt - 1
                _handle_error(remaining_retries, cmd[0], return_tuple, self._play_context.no_log, self.host)

                break

            # 5 = Invalid/incorrect password from sshpass
            except AnsibleAuthenticationFailure:
                # Raising this exception, which is subclassed from AnsibleConnectionFailure, prevents further retries
                raise

            except (AnsibleConnectionFailure, Exception) as e:

                if attempt == remaining_tries - 1:
                    raise
                else:
                    pause = 2 ** attempt - 1
                    if pause > 30:
                        pause = 30

                    if isinstance(e, AnsibleConnectionFailure):
                        msg = u"ssh_retry: attempt: %d, ssh return code is 255. cmd (%s), pausing for %d seconds" % (attempt + 1, cmd_summary, pause)
                    else:
                        msg = (u"ssh_retry: attempt: %d, caught exception(%s) from cmd (%s), "
                               u"pausing for %d seconds" % (attempt + 1, to_text(e), cmd_summary, pause))

                    display.vv(msg, host=self.host)

                    time.sleep(pause)
                    continue

        return return_tuple
    return wrapped


class Connection(ConnectionBase):
    ''' ssh based connections '''

    transport = 'ssh'
    has_pipelining = True

    def __init__(self, *args, **kwargs):
        super(Connection, self).__init__(*args, **kwargs)

        # TODO: all should come from get_option(), but not might be set at this point yet
        self.host = self._play_context.remote_addr
        self.port = self._play_context.port
        self.user = self._play_context.remote_user
        self.control_path = None
        self.control_path_dir = None

        # Windows operates differently from a POSIX connection/shell plugin,
        # we need to set various properties to ensure SSH on Windows continues
        # to work
        if getattr(self._shell, "_IS_WINDOWS", False):
            self.has_native_async = True
            self.always_pipeline_modules = True
            self.module_implementation_preferences = ('.ps1', '.exe', '')
            self.allow_executable = False

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

    def _build_command(self, binary, subsystem, *other_args):
        '''
        Takes a executable (ssh, scp, sftp or wrapper) and optional extra arguments and returns the remote command
        wrapped in local ssh shell commands and ready for execution.

        :arg binary: actual executable to use to execute command.
        :arg subsystem: type of executable provided, ssh/sftp/scp, needed because wrappers for ssh might have diff names.
        :arg other_args: dict of, value pairs passed as arguments to the ssh binary

        '''

        b_command = []
        conn_password = self.get_option('password') or self._play_context.password

        #
        # First, the command to invoke
        #

        # If we want to use password authentication, we have to set up a pipe to
        # write the password to sshpass.

        if conn_password:
            if not self._sshpass_available():
                raise AnsibleError("to use the 'ssh' connection type with passwords, you must install the sshpass program")

            self.sshpass_pipe = os.pipe()
            b_command += [b'sshpass', b'-d' + to_bytes(self.sshpass_pipe[0], nonstring='simplerepr', errors='surrogate_or_strict')]

            password_prompt = self.get_option('sshpass_prompt')
            if password_prompt:
                b_command += [b'-P', to_bytes(password_prompt, errors='surrogate_or_strict')]

        b_command += [to_bytes(binary, errors='surrogate_or_strict')]

        #
        # Next, additional arguments based on the configuration.
        #

        # sftp batch mode allows us to correctly catch failed transfers, but can
        # be disabled if the client side doesn't support the option. However,
        # sftp batch mode does not prompt for passwords so it must be disabled
        # if not using controlpersist and using sshpass
        if subsystem == 'sftp' and self.get_option('sftp_batch_mode'):
            if conn_password:
                b_args = [b'-o', b'BatchMode=no']
                self._add_args(b_command, b_args, u'disable batch mode for sshpass')
            b_command += [b'-b', b'-']

        if self._play_context.verbosity > 3:
            b_command.append(b'-vvv')

        # Next, we add ssh_args
        ssh_args = self.get_option('ssh_args')
        if ssh_args:
            b_args = [to_bytes(a, errors='surrogate_or_strict') for a in
                      self._split_ssh_args(ssh_args)]
            self._add_args(b_command, b_args, u"ansible.cfg set ssh_args")

        # Now we add various arguments that have their own specific settings defined in docs above.
        if not self.get_option('host_key_checking'):
            b_args = (b"-o", b"StrictHostKeyChecking=no")
            self._add_args(b_command, b_args, u"ANSIBLE_HOST_KEY_CHECKING/host_key_checking disabled")

        self.port = self.get_option('port')
        if self.port is not None:
            b_args = (b"-o", b"Port=" + to_bytes(self.port, nonstring='simplerepr', errors='surrogate_or_strict'))
            self._add_args(b_command, b_args, u"ANSIBLE_REMOTE_PORT/remote_port/ansible_port set")

        key = self.get_option('private_key_file')
        if key:
            b_args = (b"-o", b'IdentityFile="' + to_bytes(os.path.expanduser(key), errors='surrogate_or_strict') + b'"')
            self._add_args(b_command, b_args, u"ANSIBLE_PRIVATE_KEY_FILE/private_key_file/ansible_ssh_private_key_file set")

        if not conn_password:
            self._add_args(
                b_command, (
                    b"-o", b"KbdInteractiveAuthentication=no",
                    b"-o", b"PreferredAuthentications=gssapi-with-mic,gssapi-keyex,hostbased,publickey",
                    b"-o", b"PasswordAuthentication=no"
                ),
                u"ansible_password/ansible_ssh_password not set"
            )

        self.user = self.get_option('remote_user')
        if self.user:
            self._add_args(
                b_command,
                (b"-o", b'User="%s"' % to_bytes(self.user, errors='surrogate_or_strict')),
                u"ANSIBLE_REMOTE_USER/remote_user/ansible_user/user/-u set"
            )

        timeout = self.get_option('timeout')
        self._add_args(
            b_command,
            (b"-o", b"ConnectTimeout=" + to_bytes(timeout, errors='surrogate_or_strict', nonstring='simplerepr')),
            u"ANSIBLE_TIMEOUT/timeout set"
        )

        # Add in any common or binary-specific arguments from the PlayContext
        # (i.e. inventory or task settings or overrides on the command line).

        for opt in (u'ssh_common_args', u'{0}_extra_args'.format(subsystem)):
            attr = self.get_option(opt)
            if attr is not None:
                b_args = [to_bytes(a, errors='surrogate_or_strict') for a in self._split_ssh_args(attr)]
                self._add_args(b_command, b_args, u"Set %s" % opt)

        # Check if ControlPersist is enabled and add a ControlPath if one hasn't
        # already been set.

        controlpersist, controlpath = self._persistence_controls(b_command)

        if controlpersist:
            self._persistent = True

            if not controlpath:
                self.control_path_dir = self.get_option('control_path_dir')
                cpdir = unfrackpath(self.control_path_dir)
                b_cpdir = to_bytes(cpdir, errors='surrogate_or_strict')

                # The directory must exist and be writable.
                makedirs_safe(b_cpdir, 0o700)
                if not os.access(b_cpdir, os.W_OK):
                    raise AnsibleError("Cannot write to ControlPath %s" % to_native(cpdir))

                self.control_path = self.get_option('control_path')
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

    def _send_initial_data(self, fh, in_data, ssh_process):
        '''
        Writes initial data to the stdin filehandle of the subprocess and closes
        it. (The handle must be closed; otherwise, for example, "sftp -b -" will
        just hang forever waiting for more commands.)
        '''

        display.debug(u'Sending initial data')

        try:
            fh.write(to_bytes(in_data))
            fh.close()
        except (OSError, IOError) as e:
            # The ssh connection may have already terminated at this point, with a more useful error
            # Only raise AnsibleConnectionFailure if the ssh process is still alive
            time.sleep(0.001)
            ssh_process.poll()
            if getattr(ssh_process, 'returncode', None) is None:
                raise AnsibleConnectionFailure(
                    'Data could not be sent to remote host "%s". Make sure this host can be reached '
                    'over ssh: %s' % (self.host, to_native(e)), orig_exc=e
                )

        display.debug(u'Sent initial data (%d bytes)' % len(in_data))

    # Used by _run() to kill processes on failures
    @staticmethod
    def _terminate_process(p):
        """ Terminate a process, ignoring errors """
        try:
            p.terminate()
        except (OSError, IOError):
            pass

    # This is separate from _run() because we need to do the same thing for stdout
    # and stderr.
    def _examine_output(self, source, state, b_chunk, sudoable):
        '''
        Takes a string, extracts complete lines from it, tests to see if they
        are a prompt, error message, etc., and sets appropriate flags in self.
        Prompt and success lines are removed.

        Returns the processed (i.e. possibly-edited) output and the unprocessed
        remainder (to be processed with the next chunk) as strings.
        '''

        output = []
        for b_line in b_chunk.splitlines(True):
            display_line = to_text(b_line).rstrip('\r\n')
            suppress_output = False

            # display.debug("Examining line (source=%s, state=%s): '%s'" % (source, state, display_line))
            if self.become.expect_prompt() and self.become.check_password_prompt(b_line):
                display.debug(u"become_prompt: (source=%s, state=%s): '%s'" % (source, state, display_line))
                self._flags['become_prompt'] = True
                suppress_output = True
            elif self.become.success and self.become.check_success(b_line):
                display.debug(u"become_success: (source=%s, state=%s): '%s'" % (source, state, display_line))
                self._flags['become_success'] = True
                suppress_output = True
            elif sudoable and self.become.check_incorrect_password(b_line):
                display.debug(u"become_error: (source=%s, state=%s): '%s'" % (source, state, display_line))
                self._flags['become_error'] = True
            elif sudoable and self.become.check_missing_password(b_line):
                display.debug(u"become_nopasswd_error: (source=%s, state=%s): '%s'" % (source, state, display_line))
                self._flags['become_nopasswd_error'] = True

            if not suppress_output:
                output.append(b_line)

        # The chunk we read was most likely a series of complete lines, but just
        # in case the last line was incomplete (and not a prompt, which we would
        # have removed from the output), we retain it to be processed with the
        # next chunk.

        remainder = b''
        if output and not output[-1].endswith(b'\n'):
            remainder = output[-1]
            output = output[:-1]

        return b''.join(output), remainder

    def _bare_run(self, cmd, in_data, sudoable=True, checkrc=True):
        '''
        Starts the command and communicates with it until it ends.
        '''

        # We don't use _shell.quote as this is run on the controller and independent from the shell plugin chosen
        display_cmd = u' '.join(shlex_quote(to_text(c)) for c in cmd)
        display.vvv(u'SSH: EXEC {0}'.format(display_cmd), host=self.host)

        # Start the given command. If we don't need to pipeline data, we can try
        # to use a pseudo-tty (ssh will have been invoked with -tt). If we are
        # pipelining data, or can't create a pty, we fall back to using plain
        # old pipes.

        p = None

        if isinstance(cmd, (text_type, binary_type)):
            cmd = to_bytes(cmd)
        else:
            cmd = list(map(to_bytes, cmd))

        conn_password = self.get_option('password') or self._play_context.password

        if not in_data:
            try:
                # Make sure stdin is a proper pty to avoid tcgetattr errors
                master, slave = pty.openpty()
                if PY3 and conn_password:
                    # pylint: disable=unexpected-keyword-arg
                    p = subprocess.Popen(cmd, stdin=slave, stdout=subprocess.PIPE, stderr=subprocess.PIPE, pass_fds=self.sshpass_pipe)
                else:
                    p = subprocess.Popen(cmd, stdin=slave, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdin = os.fdopen(master, 'wb', 0)
                os.close(slave)
            except (OSError, IOError):
                p = None

        if not p:
            try:
                if PY3 and conn_password:
                    # pylint: disable=unexpected-keyword-arg
                    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE, pass_fds=self.sshpass_pipe)
                else:
                    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
                stdin = p.stdin
            except (OSError, IOError) as e:
                raise AnsibleError('Unable to execute ssh command line on a controller due to: %s' % to_native(e))

        # If we are using SSH password authentication, write the password into
        # the pipe we opened in _build_command.

        if conn_password:
            os.close(self.sshpass_pipe[0])
            try:
                os.write(self.sshpass_pipe[1], to_bytes(conn_password) + b'\n')
            except OSError as e:
                # Ignore broken pipe errors if the sshpass process has exited.
                if e.errno != errno.EPIPE or p.poll() is None:
                    raise
            os.close(self.sshpass_pipe[1])

        #
        # SSH state machine
        #

        # Now we read and accumulate output from the running process until it
        # exits. Depending on the circumstances, we may also need to write an
        # escalation password and/or pipelined input to the process.

        states = [
            'awaiting_prompt', 'awaiting_escalation', 'ready_to_send', 'awaiting_exit'
        ]

        # Are we requesting privilege escalation? Right now, we may be invoked
        # to execute sftp/scp with sudoable=True, but we can request escalation
        # only when using ssh. Otherwise we can send initial data straightaway.

        state = states.index('ready_to_send')
        if to_bytes(self.get_option('ssh_executable')) in cmd and sudoable:
            prompt = getattr(self.become, 'prompt', None)
            if prompt:
                # We're requesting escalation with a password, so we have to
                # wait for a password prompt.
                state = states.index('awaiting_prompt')
                display.debug(u'Initial state: %s: %s' % (states[state], to_text(prompt)))
            elif self.become and self.become.success:
                # We're requesting escalation without a password, so we have to
                # detect success/failure before sending any initial data.
                state = states.index('awaiting_escalation')
                display.debug(u'Initial state: %s: %s' % (states[state], to_text(self.become.success)))

        # We store accumulated stdout and stderr output from the process here,
        # but strip any privilege escalation prompt/confirmation lines first.
        # Output is accumulated into tmp_*, complete lines are extracted into
        # an array, then checked and removed or copied to stdout or stderr. We
        # set any flags based on examining the output in self._flags.

        b_stdout = b_stderr = b''
        b_tmp_stdout = b_tmp_stderr = b''

        self._flags = dict(
            become_prompt=False, become_success=False,
            become_error=False, become_nopasswd_error=False
        )

        # select timeout should be longer than the connect timeout, otherwise
        # they will race each other when we can't connect, and the connect
        # timeout usually fails
        timeout = 2 + self.get_option('timeout')
        for fd in (p.stdout, p.stderr):
            fcntl.fcntl(fd, fcntl.F_SETFL, fcntl.fcntl(fd, fcntl.F_GETFL) | os.O_NONBLOCK)

        # TODO: bcoca would like to use SelectSelector() when open
        # select is faster when filehandles is low and we only ever handle 1.
        selector = selectors.DefaultSelector()
        selector.register(p.stdout, selectors.EVENT_READ)
        selector.register(p.stderr, selectors.EVENT_READ)

        # If we can send initial data without waiting for anything, we do so
        # before we start polling
        if states[state] == 'ready_to_send' and in_data:
            self._send_initial_data(stdin, in_data, p)
            state += 1

        try:
            while True:
                poll = p.poll()
                events = selector.select(timeout)

                # We pay attention to timeouts only while negotiating a prompt.

                if not events:
                    # We timed out
                    if state <= states.index('awaiting_escalation'):
                        # If the process has already exited, then it's not really a
                        # timeout; we'll let the normal error handling deal with it.
                        if poll is not None:
                            break
                        self._terminate_process(p)
                        raise AnsibleError('Timeout (%ds) waiting for privilege escalation prompt: %s' % (timeout, to_native(b_stdout)))

                # Read whatever output is available on stdout and stderr, and stop
                # listening to the pipe if it's been closed.

                for key, event in events:
                    if key.fileobj == p.stdout:
                        b_chunk = p.stdout.read()
                        if b_chunk == b'':
                            # stdout has been closed, stop watching it
                            selector.unregister(p.stdout)
                            # When ssh has ControlMaster (+ControlPath/Persist) enabled, the
                            # first connection goes into the background and we never see EOF
                            # on stderr. If we see EOF on stdout, lower the select timeout
                            # to reduce the time wasted selecting on stderr if we observe
                            # that the process has not yet existed after this EOF. Otherwise
                            # we may spend a long timeout period waiting for an EOF that is
                            # not going to arrive until the persisted connection closes.
                            timeout = 1
                        b_tmp_stdout += b_chunk
                        display.debug(u"stdout chunk (state=%s):\n>>>%s<<<\n" % (state, to_text(b_chunk)))
                    elif key.fileobj == p.stderr:
                        b_chunk = p.stderr.read()
                        if b_chunk == b'':
                            # stderr has been closed, stop watching it
                            selector.unregister(p.stderr)
                        b_tmp_stderr += b_chunk
                        display.debug("stderr chunk (state=%s):\n>>>%s<<<\n" % (state, to_text(b_chunk)))

                # We examine the output line-by-line until we have negotiated any
                # privilege escalation prompt and subsequent success/error message.
                # Afterwards, we can accumulate output without looking at it.

                if state < states.index('ready_to_send'):
                    if b_tmp_stdout:
                        b_output, b_unprocessed = self._examine_output('stdout', states[state], b_tmp_stdout, sudoable)
                        b_stdout += b_output
                        b_tmp_stdout = b_unprocessed

                    if b_tmp_stderr:
                        b_output, b_unprocessed = self._examine_output('stderr', states[state], b_tmp_stderr, sudoable)
                        b_stderr += b_output
                        b_tmp_stderr = b_unprocessed
                else:
                    b_stdout += b_tmp_stdout
                    b_stderr += b_tmp_stderr
                    b_tmp_stdout = b_tmp_stderr = b''

                # If we see a privilege escalation prompt, we send the password.
                # (If we're expecting a prompt but the escalation succeeds, we
                # didn't need the password and can carry on regardless.)

                if states[state] == 'awaiting_prompt':
                    if self._flags['become_prompt']:
                        display.debug(u'Sending become_password in response to prompt')
                        become_pass = self.become.get_option('become_pass', playcontext=self._play_context)
                        stdin.write(to_bytes(become_pass, errors='surrogate_or_strict') + b'\n')
                        # On python3 stdin is a BufferedWriter, and we don't have a guarantee
                        # that the write will happen without a flush
                        stdin.flush()
                        self._flags['become_prompt'] = False
                        state += 1
                    elif self._flags['become_success']:
                        state += 1

                # We've requested escalation (with or without a password), now we
                # wait for an error message or a successful escalation.

                if states[state] == 'awaiting_escalation':
                    if self._flags['become_success']:
                        display.vvv(u'Escalation succeeded')
                        self._flags['become_success'] = False
                        state += 1
                    elif self._flags['become_error']:
                        display.vvv(u'Escalation failed')
                        self._terminate_process(p)
                        self._flags['become_error'] = False
                        raise AnsibleError('Incorrect %s password' % self.become.name)
                    elif self._flags['become_nopasswd_error']:
                        display.vvv(u'Escalation requires password')
                        self._terminate_process(p)
                        self._flags['become_nopasswd_error'] = False
                        raise AnsibleError('Missing %s password' % self.become.name)
                    elif self._flags['become_prompt']:
                        # This shouldn't happen, because we should see the "Sorry,
                        # try again" message first.
                        display.vvv(u'Escalation prompt repeated')
                        self._terminate_process(p)
                        self._flags['become_prompt'] = False
                        raise AnsibleError('Incorrect %s password' % self.become.name)

                # Once we're sure that the privilege escalation prompt, if any, has
                # been dealt with, we can send any initial data and start waiting
                # for output.

                if states[state] == 'ready_to_send':
                    if in_data:
                        self._send_initial_data(stdin, in_data, p)
                    state += 1

                # Now we're awaiting_exit: has the child process exited? If it has,
                # and we've read all available output from it, we're done.

                if poll is not None:
                    if not selector.get_map() or not events:
                        break
                    # We should not see further writes to the stdout/stderr file
                    # descriptors after the process has closed, set the select
                    # timeout to gather any last writes we may have missed.
                    timeout = 0
                    continue

                # If the process has not yet exited, but we've already read EOF from
                # its stdout and stderr (and thus no longer watching any file
                # descriptors), we can just wait for it to exit.

                elif not selector.get_map():
                    p.wait()
                    break

                # Otherwise there may still be outstanding data to read.
        finally:
            selector.close()
            # close stdin, stdout, and stderr after process is terminated and
            # stdout/stderr are read completely (see also issues #848, #64768).
            stdin.close()
            p.stdout.close()
            p.stderr.close()

        if self.get_option('host_key_checking'):
            if cmd[0] == b"sshpass" and p.returncode == 6:
                raise AnsibleError('Using a SSH password instead of a key is not possible because Host Key checking is enabled and sshpass does not support '
                                   'this.  Please add this host\'s fingerprint to your known_hosts file to manage this host.')

        controlpersisterror = b'Bad configuration option: ControlPersist' in b_stderr or b'unknown configuration option: ControlPersist' in b_stderr
        if p.returncode != 0 and controlpersisterror:
            raise AnsibleError('using -c ssh on certain older ssh versions may not support ControlPersist, set ANSIBLE_SSH_ARGS="" '
                               '(or ssh_args in [ssh_connection] section of the config file) before running again')

        # If we find a broken pipe because of ControlPersist timeout expiring (see #16731),
        # we raise a special exception so that we can retry a connection.
        controlpersist_broken_pipe = b'mux_client_hello_exchange: write packet: Broken pipe' in b_stderr
        if p.returncode == 255:

            additional = to_native(b_stderr)
            if controlpersist_broken_pipe:
                raise AnsibleControlPersistBrokenPipeError('Data could not be sent because of ControlPersist broken pipe: %s' % additional)

            elif in_data and checkrc:
                raise AnsibleConnectionFailure('Data could not be sent to remote host "%s". Make sure this host can be reached over ssh: %s'
                                               % (self.host, additional))

        return (p.returncode, b_stdout, b_stderr)

    @_ssh_retry
    def _run(self, cmd, in_data, sudoable=True, checkrc=True):
        """Wrapper around _bare_run that retries the connection
        """
        return self._bare_run(cmd, in_data, sudoable=sudoable, checkrc=checkrc)

    @_ssh_retry
    def _file_transport_command(self, in_path, out_path, sftp_action):
        # scp and sftp require square brackets for IPv6 addresses, but
        # accept them for hostnames and IPv4 addresses too.
        host = '[%s]' % self.host

        smart_methods = ['sftp', 'scp', 'piped']

        # Windows does not support dd so we cannot use the piped method
        if getattr(self._shell, "_IS_WINDOWS", False):
            smart_methods.remove('piped')

        # Transfer methods to try
        methods = []

        # Use the transfer_method option if set, otherwise use scp_if_ssh
        ssh_transfer_method = self.get_option('ssh_transfer_method')
        if ssh_transfer_method is not None:
            if ssh_transfer_method == 'smart':
                methods = smart_methods
            else:
                methods = [ssh_transfer_method]
        else:
            # since this can be a non-bool now, we need to handle it correctly
            scp_if_ssh = self.get_option('scp_if_ssh')
            if not isinstance(scp_if_ssh, bool):
                scp_if_ssh = scp_if_ssh.lower()
                if scp_if_ssh in BOOLEANS:
                    scp_if_ssh = boolean(scp_if_ssh, strict=False)
                elif scp_if_ssh != 'smart':
                    raise AnsibleOptionsError('scp_if_ssh needs to be one of [smart|True|False]')
            if scp_if_ssh == 'smart':
                methods = smart_methods
            elif scp_if_ssh is True:
                methods = ['scp']
            else:
                methods = ['sftp']

        for method in methods:
            returncode = stdout = stderr = None
            if method == 'sftp':
                cmd = self._build_command(self.get_option('sftp_executable'), 'sftp', to_bytes(host))
                in_data = u"{0} {1} {2}\n".format(sftp_action, shlex_quote(in_path), shlex_quote(out_path))
                in_data = to_bytes(in_data, nonstring='passthru')
                (returncode, stdout, stderr) = self._bare_run(cmd, in_data, checkrc=False)
            elif method == 'scp':
                scp = self.get_option('scp_executable')

                if sftp_action == 'get':
                    cmd = self._build_command(scp, 'scp', u'{0}:{1}'.format(host, self._shell.quote(in_path)), out_path)
                else:
                    cmd = self._build_command(scp, 'scp', in_path, u'{0}:{1}'.format(host, self._shell.quote(out_path)))
                in_data = None
                (returncode, stdout, stderr) = self._bare_run(cmd, in_data, checkrc=False)
            elif method == 'piped':
                if sftp_action == 'get':
                    # we pass sudoable=False to disable pty allocation, which
                    # would end up mixing stdout/stderr and screwing with newlines
                    (returncode, stdout, stderr) = self.exec_command('dd if=%s bs=%s' % (in_path, BUFSIZE), sudoable=False)
                    with open(to_bytes(out_path, errors='surrogate_or_strict'), 'wb+') as out_file:
                        out_file.write(stdout)
                else:
                    with open(to_bytes(in_path, errors='surrogate_or_strict'), 'rb') as f:
                        in_data = to_bytes(f.read(), nonstring='passthru')
                    if not in_data:
                        count = ' count=0'
                    else:
                        count = ''
                    (returncode, stdout, stderr) = self.exec_command('dd of=%s bs=%s%s' % (out_path, BUFSIZE, count), in_data=in_data, sudoable=False)

            # Check the return code and rollover to next method if failed
            if returncode == 0:
                return (returncode, stdout, stderr)
            else:
                # If not in smart mode, the data will be printed by the raise below
                if len(methods) > 1:
                    display.warning(u'%s transfer mechanism failed on %s. Use ANSIBLE_DEBUG=1 to see detailed information' % (method, host))
                    display.debug(u'%s' % to_text(stdout))
                    display.debug(u'%s' % to_text(stderr))

        if returncode == 255:
            raise AnsibleConnectionFailure("Failed to connect to the host via %s: %s" % (method, to_native(stderr)))
        else:
            raise AnsibleError("failed to transfer file to %s %s:\n%s\n%s" %
                               (to_native(in_path), to_native(out_path), to_native(stdout), to_native(stderr)))

    def _escape_win_path(self, path):
        """ converts a Windows path to one that's supported by SFTP and SCP """
        # If using a root path then we need to start with /
        prefix = ""
        if re.match(r'^\w{1}:', path):
            prefix = "/"

        # Convert all '\' to '/'
        return "%s%s" % (prefix, path.replace("\\", "/"))

    #
    # Main public methods
    #
    def exec_command(self, cmd, in_data=None, sudoable=True):
        ''' run a command on the remote host '''

        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        display.vvv(u"ESTABLISH SSH CONNECTION FOR USER: {0}".format(self.user), host=self._play_context.remote_addr)

        if getattr(self._shell, "_IS_WINDOWS", False):
            # Become method 'runas' is done in the wrapper that is executed,
            # need to disable sudoable so the bare_run is not waiting for a
            # prompt that will not occur
            sudoable = False

            # Make sure our first command is to set the console encoding to
            # utf-8, this must be done via chcp to get utf-8 (65001)
            cmd_parts = ["chcp.com", "65001", self._shell._SHELL_REDIRECT_ALLNULL, self._shell._SHELL_AND]
            cmd_parts.extend(self._shell._encode_script(cmd, as_list=True, strict_mode=False, preserve_rc=False))
            cmd = ' '.join(cmd_parts)

        # we can only use tty when we are not pipelining the modules. piping
        # data into /usr/bin/python inside a tty automatically invokes the
        # python interactive-mode but the modules are not compatible with the
        # interactive-mode ("unexpected indent" mainly because of empty lines)

        ssh_executable = self.get_option('ssh_executable')

        # -tt can cause various issues in some environments so allow the user
        # to disable it as a troubleshooting method.
        use_tty = self.get_option('use_tty')

        if not in_data and sudoable and use_tty:
            args = ('-tt', self.host, cmd)
        else:
            args = (self.host, cmd)

        cmd = self._build_command(ssh_executable, 'ssh', *args)
        (returncode, stdout, stderr) = self._run(cmd, in_data, sudoable=sudoable)

        # When running on Windows, stderr may contain CLIXML encoded output
        if getattr(self._shell, "_IS_WINDOWS", False) and stderr.startswith(b"#< CLIXML"):
            stderr = _parse_clixml(stderr)

        return (returncode, stdout, stderr)

    def put_file(self, in_path, out_path):
        ''' transfer a file from local to remote '''

        super(Connection, self).put_file(in_path, out_path)

        display.vvv(u"PUT {0} TO {1}".format(in_path, out_path), host=self.host)
        if not os.path.exists(to_bytes(in_path, errors='surrogate_or_strict')):
            raise AnsibleFileNotFound("file or module does not exist: {0}".format(to_native(in_path)))

        if getattr(self._shell, "_IS_WINDOWS", False):
            out_path = self._escape_win_path(out_path)

        return self._file_transport_command(in_path, out_path, 'put')

    def fetch_file(self, in_path, out_path):
        ''' fetch a file from remote to local '''

        super(Connection, self).fetch_file(in_path, out_path)

        display.vvv(u"FETCH {0} TO {1}".format(in_path, out_path), host=self.host)

        # need to add / if path is rooted
        if getattr(self._shell, "_IS_WINDOWS", False):
            in_path = self._escape_win_path(in_path)

        return self._file_transport_command(in_path, out_path, 'get')

    def reset(self):

        run_reset = False

        # If we have a persistent ssh connection (ControlPersist), we can ask it to stop listening.
        # only run the reset if the ControlPath already exists or if it isn't configured and ControlPersist is set
        # 'check' will determine this.
        cmd = self._build_command(self.get_option('ssh_executable'), 'ssh', '-O', 'check', self.host)
        display.vvv(u'sending connection check: %s' % to_text(cmd))
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        status_code = p.wait()
        if status_code != 0:
            display.vvv(u"No connection to reset: %s" % to_text(stderr))
        else:
            run_reset = True

        if run_reset:
            cmd = self._build_command(self.get_option('ssh_executable'), 'ssh', '-O', 'stop', self.host)
            display.vvv(u'sending connection stop: %s' % to_text(cmd))
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = p.communicate()
            status_code = p.wait()
            if status_code != 0:
                display.warning(u"Failed to reset connection:%s" % to_text(stderr))

        self.close()

    def close(self):
        self._connected = False
