# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2015 Toshio Kuratomi <tkuratomi@ansible.com>
# (c) 2017, Peter Sprygada <psprygad@redhat.com>
# (c) 2017 Ansible Project
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import fcntl
import gettext
import os
import shlex
from abc import abstractmethod, abstractproperty
from functools import wraps

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_bytes, to_text
from ansible.plugins import AnsiblePlugin
from ansible.plugins.loader import shell_loader, connection_loader
from ansible.utils.path import unfrackpath

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


__all__ = ['ConnectionBase', 'ensure_connect']

BUFSIZE = 65536


def ensure_connect(func):
    @wraps(func)
    def wrapped(self, *args, **kwargs):
        if not self._connected:
            self._connect()
        return func(self, *args, **kwargs)
    return wrapped


class ConnectionBase(AnsiblePlugin):
    '''
    A base class for connections to contain common code.
    '''

    has_pipelining = False
    has_native_async = False  # eg, winrm
    always_pipeline_modules = False  # eg, winrm
    become_methods = C.BECOME_METHODS
    # When running over this connection type, prefer modules written in a certain language
    # as discovered by the specified file extension.  An empty string as the
    # language means any language.
    module_implementation_preferences = ('',)
    allow_executable = True

    # the following control whether or not the connection supports the
    # persistent connection framework or not
    supports_persistence = False
    force_persistence = False

    default_user = None

    def __init__(self, play_context, new_stdin, shell=None, *args, **kwargs):

        super(ConnectionBase, self).__init__()

        # All these hasattrs allow subclasses to override these parameters
        if not hasattr(self, '_play_context'):
            self._play_context = play_context
        if not hasattr(self, '_new_stdin'):
            self._new_stdin = new_stdin
        # Backwards compat: self._display isn't really needed, just import the global display and use that.
        if not hasattr(self, '_display'):
            self._display = display
        if not hasattr(self, '_connected'):
            self._connected = False

        self.success_key = None
        self.prompt = None
        self._connected = False
        self._socket_path = None

        if shell is not None:
            self._shell = shell

        # load the shell plugin for this action/connection
        if play_context.shell:
            shell_type = play_context.shell
        elif hasattr(self, '_shell_type'):
            shell_type = getattr(self, '_shell_type')
        else:
            shell_type = 'sh'
            shell_filename = os.path.basename(self._play_context.executable)
            try:
                shell = shell_loader.get(shell_filename)
            except Exception:
                shell = None
            if shell is None:
                for shell in shell_loader.all():
                    if shell_filename in shell.COMPATIBLE_SHELLS:
                        break
            shell_type = shell.SHELL_FAMILY

        self._shell = shell_loader.get(shell_type)
        if not self._shell:
            raise AnsibleError("Invalid shell type specified (%s), or the plugin for that shell type is missing." % shell_type)

    @property
    def connected(self):
        '''Read-only property holding whether the connection to the remote host is active or closed.'''
        return self._connected

    @property
    def socket_path(self):
        '''Read-only property holding the connection socket path for this remote host'''
        return self._socket_path

    def _become_method_supported(self):
        ''' Checks if the current class supports this privilege escalation method '''

        if self._play_context.become_method in self.become_methods:
            return True

        raise AnsibleError("Internal Error: this connection module does not support running commands via %s" % self._play_context.become_method)

    @staticmethod
    def _split_ssh_args(argstring):
        """
        Takes a string like '-o Foo=1 -o Bar="foo bar"' and returns a
        list ['-o', 'Foo=1', '-o', 'Bar=foo bar'] that can be added to
        the argument list. The list will not contain any empty elements.
        """
        try:
            # Python 2.6.x shlex doesn't handle unicode type so we have to
            # convert args to byte string for that case.  More efficient to
            # try without conversion first but python2.6 doesn't throw an
            # exception, it merely mangles the output:
            # >>> shlex.split(u't e')
            # ['t\x00\x00\x00', '\x00\x00\x00e\x00\x00\x00']
            return [to_text(x.strip()) for x in shlex.split(to_bytes(argstring)) if x.strip()]
        except AttributeError:
            # In Python3, shlex.split doesn't work on a byte string.
            return [to_text(x.strip()) for x in shlex.split(argstring) if x.strip()]

    @abstractproperty
    def transport(self):
        """String used to identify this Connection class from other classes"""
        pass

    @abstractmethod
    def _connect(self):
        """Connect to the host we've been initialized with"""

        # Check if PE is supported
        if self._play_context.become:
            self._become_method_supported()

    @ensure_connect
    @abstractmethod
    def exec_command(self, cmd, in_data=None, sudoable=True):
        """Run a command on the remote host.

        :arg cmd: byte string containing the command
        :kwarg in_data: If set, this data is passed to the command's stdin.
            This is used to implement pipelining.  Currently not all
            connection plugins implement pipelining.
        :kwarg sudoable: Tell the connection plugin if we're executing
            a command via a privilege escalation mechanism.  This may affect
            how the connection plugin returns data.  Note that not all
            connections can handle privilege escalation.
        :returns: a tuple of (return code, stdout, stderr)  The return code is
            an int while stdout and stderr are both byte strings.

        When a command is executed, it goes through multiple commands to get
        there.  It looks approximately like this::

            [LocalShell] ConnectionCommand [UsersLoginShell (*)] ANSIBLE_SHELL_EXECUTABLE [(BecomeCommand ANSIBLE_SHELL_EXECUTABLE)] Command
        :LocalShell: Is optional.  It is run locally to invoke the
            ``Connection Command``.  In most instances, the
            ``ConnectionCommand`` can be invoked directly instead.  The ssh
            connection plugin which can have values that need expanding
            locally specified via ssh_args is the sole known exception to
            this.  Shell metacharacters in the command itself should be
            processed on the remote machine, not on the local machine so no
            shell is needed on the local machine.  (Example, ``/bin/sh``)
        :ConnectionCommand: This is the command that connects us to the remote
            machine to run the rest of the command.  ``ansible_ssh_user``,
            ``ansible_ssh_host`` and so forth are fed to this piece of the
            command to connect to the correct host (Examples ``ssh``,
            ``chroot``)
        :UsersLoginShell: This shell may or may not be created depending on
            the ConnectionCommand used by the connection plugin.  This is the
            shell that the ``ansible_ssh_user`` has configured as their login
            shell.  In traditional UNIX parlance, this is the last field of
            a user's ``/etc/passwd`` entry   We do not specifically try to run
            the ``UsersLoginShell`` when we connect.  Instead it is implicit
            in the actions that the ``ConnectionCommand`` takes when it
            connects to a remote machine.  ``ansible_shell_type`` may be set
            to inform ansible of differences in how the ``UsersLoginShell``
            handles things like quoting if a shell has different semantics
            than the Bourne shell.
        :ANSIBLE_SHELL_EXECUTABLE: This is the shell set via the inventory var
            ``ansible_shell_executable`` or via
            ``constants.DEFAULT_EXECUTABLE`` if the inventory var is not set.
            We explicitly invoke this shell so that we have predictable
            quoting rules at this point.  ``ANSIBLE_SHELL_EXECUTABLE`` is only
            settable by the user because some sudo setups may only allow
            invoking a specific shell.  (For instance, ``/bin/bash`` may be
            allowed but ``/bin/sh``, our default, may not).  We invoke this
            twice, once after the ``ConnectionCommand`` and once after the
            ``BecomeCommand``.  After the ConnectionCommand, this is run by
            the ``UsersLoginShell``.  After the ``BecomeCommand`` we specify
            that the ``ANSIBLE_SHELL_EXECUTABLE`` is being invoked directly.
        :BecomeComand ANSIBLE_SHELL_EXECUTABLE: Is the command that performs
            privilege escalation.  Setting this up is performed by the action
            plugin prior to running ``exec_command``. So we just get passed
            :param:`cmd` which has the BecomeCommand already added.
            (Examples: sudo, su)  If we have a BecomeCommand then we will
            invoke a ANSIBLE_SHELL_EXECUTABLE shell inside of it so that we
            have a consistent view of quoting.
        :Command: Is the command we're actually trying to run remotely.
            (Examples: mkdir -p $HOME/.ansible, python $HOME/.ansible/tmp-script-file)
        """
        pass

    @ensure_connect
    @abstractmethod
    def put_file(self, in_path, out_path):
        """Transfer a file from local to remote"""
        pass

    @ensure_connect
    @abstractmethod
    def fetch_file(self, in_path, out_path):
        """Fetch a file from remote to local"""
        pass

    @abstractmethod
    def close(self):
        """Terminate the connection"""
        pass

    def check_become_success(self, b_output):
        b_success_key = to_bytes(self._play_context.success_key)
        for b_line in b_output.splitlines(True):
            if b_success_key == b_line.rstrip():
                return True
        return False

    def check_password_prompt(self, b_output):
        if self._play_context.prompt is None:
            return False
        elif isinstance(self._play_context.prompt, string_types):
            b_prompt = to_bytes(self._play_context.prompt).strip()
            b_lines = b_output.splitlines()
            return any(l.strip().startswith(b_prompt) for l in b_lines)
        else:
            return self._play_context.prompt(b_output)

    def check_incorrect_password(self, b_output):
        b_incorrect_password = to_bytes(gettext.dgettext(self._play_context.become_method, C.BECOME_ERROR_STRINGS[self._play_context.become_method]))
        return b_incorrect_password and b_incorrect_password in b_output

    def check_missing_password(self, b_output):
        b_missing_password = to_bytes(gettext.dgettext(self._play_context.become_method, C.BECOME_MISSING_STRINGS[self._play_context.become_method]))
        return b_missing_password and b_missing_password in b_output

    def connection_lock(self):
        f = self._play_context.connection_lockfd
        display.vvvv('CONNECTION: pid %d waiting for lock on %d' % (os.getpid(), f), host=self._play_context.remote_addr)
        fcntl.lockf(f, fcntl.LOCK_EX)
        display.vvvv('CONNECTION: pid %d acquired lock on %d' % (os.getpid(), f), host=self._play_context.remote_addr)

    def connection_unlock(self):
        f = self._play_context.connection_lockfd
        fcntl.lockf(f, fcntl.LOCK_UN)
        display.vvvv('CONNECTION: pid %d released lock on %d' % (os.getpid(), f), host=self._play_context.remote_addr)

    def reset(self):
        display.warning("Reset is not implemented for this connection")


class NetworkConnectionBase(ConnectionBase):
    """
    A base class for network-style connections.
    """

    force_persistence = True
    # Do not use _remote_is_local in other connections
    _remote_is_local = True

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(NetworkConnectionBase, self).__init__(play_context, new_stdin, *args, **kwargs)

        self._network_os = self._play_context.network_os

        self._local = connection_loader.get('local', play_context, '/dev/null')
        self._local.set_options()

        self._implementation_plugins = []

        # reconstruct the socket_path and set instance values accordingly
        self._ansible_playbook_pid = kwargs.get('ansible_playbook_pid')
        self._update_connection_state()

    def __getattr__(self, name):
        try:
            return self.__dict__[name]
        except KeyError:
            if not name.startswith('_'):
                for plugin in self._implementation_plugins:
                    method = getattr(plugin, name, None)
                    if method is not None:
                        return method
            raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, name))

    def exec_command(self, cmd, in_data=None, sudoable=True):
        return self._local.exec_command(cmd, in_data, sudoable)

    def put_file(self, in_path, out_path):
        """Transfer a file from local to remote"""
        return self._local.put_file(in_path, out_path)

    def fetch_file(self, in_path, out_path):
        """Fetch a file from remote to local"""
        return self._local.fetch_file(in_path, out_path)

    def reset(self):
        '''
        Reset the connection
        '''
        if self._socket_path:
            display.vvvv('resetting persistent connection for socket_path %s' % self._socket_path, host=self._play_context.remote_addr)
            self.close()
        display.vvvv('reset call on connection instance', host=self._play_context.remote_addr)

    def close(self):
        if self._connected:
            self._connected = False
        self._implementation_plugins = []

    def _update_connection_state(self):
        '''
        Reconstruct the connection socket_path and check if it exists

        If the socket path exists then the connection is active and set
        both the _socket_path value to the path and the _connected value
        to True.  If the socket path doesn't exist, leave the socket path
        value to None and the _connected value to False
        '''
        ssh = connection_loader.get('ssh', class_only=True)
        control_path = ssh._create_control_path(
            self._play_context.remote_addr, self._play_context.port,
            self._play_context.remote_user, self._play_context.connection,
            self._ansible_playbook_pid
        )

        tmp_path = unfrackpath(C.PERSISTENT_CONTROL_PATH_DIR)
        socket_path = unfrackpath(control_path % dict(directory=tmp_path))

        if os.path.exists(socket_path):
            self._connected = True
            self._socket_path = socket_path
