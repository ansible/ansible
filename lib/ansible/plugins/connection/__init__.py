# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2015 Toshio Kuratomi <tkuratomi@ansible.com>
# (c) 2017, Peter Sprygada <psprygad@redhat.com>
# (c) 2017 Ansible Project
from __future__ import annotations

import collections.abc as c
import fcntl
import os
import shlex
import typing as t

from abc import abstractmethod
from functools import wraps

from ansible import constants as C
from ansible.errors import AnsibleValueOmittedError
from ansible.module_utils.common.text.converters import to_text
from ansible.playbook.play_context import PlayContext
from ansible.plugins import AnsiblePlugin
from ansible.plugins.become import BecomeBase
from ansible.plugins.shell import ShellBase
from ansible.utils.display import Display
from ansible.plugins.loader import connection_loader, get_shell_plugin
from ansible.utils.path import unfrackpath

display = Display()


__all__ = ['ConnectionBase', 'ensure_connect']

BUFSIZE = 65536


class ConnectionKwargs(t.TypedDict):
    task_uuid: str
    ansible_playbook_pid: str
    shell: t.NotRequired[ShellBase]


def ensure_connect[T, **P](
    func: c.Callable[t.Concatenate[ConnectionBase, P], T],
) -> c.Callable[t.Concatenate[ConnectionBase, P], T]:
    @wraps(func)
    def wrapped(self: ConnectionBase, *args: P.args, **kwargs: P.kwargs) -> T:
        if not self._connected:
            self._connect()
        return func(self, *args, **kwargs)
    return wrapped


class ConnectionBase(AnsiblePlugin):
    """
    A base class for connections to contain common code.
    """

    has_pipelining = False
    has_native_async = False  # eg, winrm
    always_pipeline_modules = False  # eg, winrm
    has_tty = True  # for interacting with become plugins
    # When running over this connection type, prefer modules written in a certain language
    # as discovered by the specified file extension.  An empty string as the
    # language means any language.
    module_implementation_preferences = ('',)  # type: t.Iterable[str]
    allow_executable = True

    # the following control whether or not the connection supports the
    # persistent connection framework or not
    supports_persistence = False
    force_persistence = False

    default_user: str | None = None

    def __init__(
        self,
        play_context: PlayContext,
        *args: t.Any,
        **kwargs: t.Unpack[ConnectionKwargs],
    ) -> None:

        super(ConnectionBase, self).__init__()

        # All these hasattrs allow subclasses to override these parameters
        if not hasattr(self, '_play_context'):
            # Backwards compat: self._play_context isn't really needed, using set_options/get_option
            self._play_context = play_context
        if not hasattr(self, '_display'):
            # Backwards compat: self._display isn't really needed, just import the global display and use that.
            self._display = display

        self.success_key = None
        self.prompt = None
        self._connected = False
        self._socket_path: str | None = None

        # we always must have shell
        if not (shell := kwargs.get('shell')):
            shell_type = play_context.shell if play_context.shell else getattr(self, '_shell_type', None)
            shell = get_shell_plugin(shell_type=shell_type, executable=self._play_context.executable)
        self._shell = shell

        self.become: BecomeBase | None = None

    def set_become_plugin(self, plugin: BecomeBase) -> None:
        self.become = plugin

    @property
    def connected(self) -> bool:
        """Read-only property holding whether the connection to the remote host is active or closed."""
        return self._connected

    @property
    def socket_path(self) -> str | None:
        """Read-only property holding the connection socket path for this remote host"""
        return self._socket_path

    @staticmethod
    def _split_ssh_args(argstring: str) -> list[str]:
        """
        Takes a string like '-o Foo=1 -o Bar="foo bar"' and returns a
        list ['-o', 'Foo=1', '-o', 'Bar=foo bar'] that can be added to
        the argument list. The list will not contain any empty elements.
        """
        # In Python3, shlex.split doesn't work on a byte string.
        return [to_text(x.strip()) for x in shlex.split(argstring) if x.strip()]

    @property
    @abstractmethod
    def transport(self) -> str:
        """String used to identify this Connection class from other classes"""
        pass

    @abstractmethod
    def _connect[T](self: T) -> T:
        """Connect to the host we've been initialized with"""

    @ensure_connect
    @abstractmethod
    def exec_command(self, cmd: str, in_data: bytes | None = None, sudoable: bool = True) -> tuple[int, bytes, bytes]:
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
            machine to run the rest of the command.  ``ansible_user``,
            ``ansible_ssh_host`` and so forth are fed to this piece of the
            command to connect to the correct host (Examples ``ssh``,
            ``chroot``)
        :UsersLoginShell: This shell may or may not be created depending on
            the ConnectionCommand used by the connection plugin.  This is the
            shell that the ``ansible_user`` has configured as their login
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
    def put_file(self, in_path: str, out_path: str) -> None:
        """Transfer a file from local to remote"""
        pass

    @ensure_connect
    @abstractmethod
    def fetch_file(self, in_path: str, out_path: str) -> None:
        """Fetch a file from remote to local; callers are expected to have pre-created the directory chain for out_path"""
        pass

    @abstractmethod
    def close(self) -> None:
        """Terminate the connection"""
        pass

    def connection_lock(self) -> None:
        f = self._play_context.connection_lockfd
        display.vvvv('CONNECTION: pid %d waiting for lock on %d' % (os.getpid(), f), host=self._play_context.remote_addr)
        fcntl.lockf(f, fcntl.LOCK_EX)
        display.vvvv('CONNECTION: pid %d acquired lock on %d' % (os.getpid(), f), host=self._play_context.remote_addr)

    def connection_unlock(self) -> None:
        f = self._play_context.connection_lockfd
        fcntl.lockf(f, fcntl.LOCK_UN)
        display.vvvv('CONNECTION: pid %d released lock on %d' % (os.getpid(), f), host=self._play_context.remote_addr)

    def reset(self) -> None:
        display.warning("Reset is not implemented for this connection")

    def update_vars(self, variables: dict[str, t.Any]) -> None:
        """
        Adds 'magic' variables relating to connections to the variable dictionary provided.
        In case users need to access from the play, this is a legacy from runner.
        """
        for varname in C.COMMON_CONNECTION_VARS:
            value = None
            if varname in variables:
                # dont update existing
                continue
            elif 'password' in varname or 'passwd' in varname:
                # no secrets!
                continue
            elif varname == 'ansible_connection':
                # its me mom!
                value = self._load_name
            elif varname == 'ansible_shell_type' and self._shell:
                # its my cousin ...
                value = self._shell._load_name
            else:
                # deal with generic options if the plugin supports em (for example not all connections have a remote user)
                options = C.config.get_plugin_options_from_var('connection', self._load_name, varname)
                if options:
                    value = self.get_option(options[0])  # for these variables there should be only one option
                elif 'become' not in varname:
                    # fallback to play_context, unless become related  TODO: in the end, should come from task/play and not pc
                    for prop, var_list in C.MAGIC_VARIABLE_MAPPING.items():
                        if varname in var_list:
                            try:
                                value = getattr(self._play_context, prop)
                                break
                            except AttributeError:
                                # It was not defined; fine to ignore
                                continue

            if value is not None:
                display.debug('Set connection var {0} to {1}'.format(varname, value))
                variables[varname] = value

    def _resolve_option_variables(self, variables, templar):
        """
        Return a dict of variable -> templated value, for any variables that
        that match options registered by this plugin.
        """
        # create dict of 'templated vars'
        var_options = {
            '_extras': {},
        }
        for var_name in C.config.get_plugin_vars('connection', self._load_name):
            if var_name in variables:
                try:
                    var_options[var_name] = templar.template(variables[var_name])
                except AnsibleValueOmittedError:
                    pass

        # add extras if plugin supports them
        if getattr(self, 'allow_extras', False):
            for var_name in variables:
                if var_name.startswith(f'ansible_{self.extras_prefix}_') and var_name not in var_options:
                    try:
                        var_options['_extras'][var_name] = templar.template(variables[var_name])
                    except AnsibleValueOmittedError:
                        pass

        return var_options

    def is_pipelining_enabled(self, wrap_async: bool = False) -> bool:

        is_enabled = False
        if self.has_pipelining and (not self.become or self.become.pipelining):
            try:
                is_enabled = self.get_option('pipelining')
            except KeyError:
                is_enabled = getattr(self._play_context, 'pipelining', False)

        # TODO: deprecate always_pipeline_modules and has_native_async in favor for each plugin overriding this function
        conditions = [
            is_enabled or self.always_pipeline_modules,       # enabled via config or forced via connection (eg winrm)
            not C.DEFAULT_KEEP_REMOTE_FILES,                  # user wants remote files
            not wrap_async or self.has_native_async,          # async does not normally support pipelining unless it does (eg winrm)
        ]
        return all(conditions)


class NetworkConnectionBase(ConnectionBase):
    """
    A base class for network-style connections.
    """

    force_persistence = True
    # Do not use _remote_is_local in other connections
    _remote_is_local = True

    def __init__(
        self,
        play_context: PlayContext,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> None:
        super(NetworkConnectionBase, self).__init__(play_context, *args, **kwargs)
        self._messages: list[tuple[str, str]] = []
        self._conn_closed = False

        self._network_os = self._play_context.network_os

        self._local = connection_loader.get('local', play_context, '/dev/null')
        self._local.set_options()

        self._sub_plugin: dict[str, t.Any] = {}
        self._cached_variables = (None, None, None)

        # reconstruct the socket_path and set instance values accordingly
        self._ansible_playbook_pid = kwargs.get('ansible_playbook_pid')
        self._update_connection_state()

    def __getattr__(self, name):
        try:
            return self.__dict__[name]
        except KeyError:
            if not name.startswith('_'):
                plugin = self._sub_plugin.get('obj')
                if plugin:
                    method = getattr(plugin, name, None)
                    if method is not None:
                        return method
            raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, name))

    def exec_command(self, cmd: str, in_data: bytes | None = None, sudoable: bool = True) -> tuple[int, bytes, bytes]:
        return self._local.exec_command(cmd, in_data, sudoable)

    def queue_message(self, level: str, message: str) -> None:
        """
        Adds a message to the queue of messages waiting to be pushed back to the controller process.

        :arg level: A string which can either be the name of a method in display, or 'log'. When
            the messages are returned to task_executor, a value of log will correspond to
            ``display.display(message, log_only=True)``, while another value will call ``display.[level](message)``
        """
        self._messages.append((level, message))

    def pop_messages(self) -> list[tuple[str, str]]:
        messages, self._messages = self._messages, []
        return messages

    def put_file(self, in_path: str, out_path: str) -> None:
        """Transfer a file from local to remote"""
        return self._local.put_file(in_path, out_path)

    def fetch_file(self, in_path: str, out_path: str) -> None:
        """Fetch a file from remote to local"""
        return self._local.fetch_file(in_path, out_path)

    def reset(self) -> None:
        """
        Reset the connection
        """
        if self._socket_path:
            self.queue_message('vvvv', 'resetting persistent connection for socket_path %s' % self._socket_path)
            self.close()
        self.queue_message('vvvv', 'reset call on connection instance')

    def close(self) -> None:
        self._conn_closed = True
        if self._connected:
            self._connected = False

    def set_options(
        self,
        task_keys: dict[str, t.Any] | None = None,
        var_options: dict[str, t.Any] | None = None,
        direct: dict[str, t.Any] | None = None,
    ) -> None:
        super(NetworkConnectionBase, self).set_options(task_keys=task_keys, var_options=var_options, direct=direct)
        if self.get_option('persistent_log_messages'):
            warning = "Persistent connection logging is enabled for %s. This will log ALL interactions" % self._play_context.remote_addr
            logpath = getattr(C, 'DEFAULT_LOG_PATH')
            if logpath is not None:
                warning += " to %s" % logpath
            self.queue_message('warning', "%s and WILL NOT redact sensitive configuration like passwords. USE WITH CAUTION!" % warning)

        if self._sub_plugin.get('obj') and self._sub_plugin.get('type') != 'external':
            try:
                self._sub_plugin['obj'].set_options(task_keys=task_keys, var_options=var_options, direct=direct)
            except AttributeError:
                pass

    def _update_connection_state(self) -> None:
        """
        Reconstruct the connection socket_path and check if it exists

        If the socket path exists then the connection is active and set
        both the _socket_path value to the path and the _connected value
        to True.  If the socket path doesn't exist, leave the socket path
        value to None and the _connected value to False
        """
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

    def _log_messages(self, message: str) -> None:
        if self.get_option('persistent_log_messages'):
            self.queue_message('log', message)
