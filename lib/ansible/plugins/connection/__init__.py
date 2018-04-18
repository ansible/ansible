# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2015 Toshio Kuratomi <tkuratomi@ansible.com>
# (c) 2017, Peter Sprygada <psprygad@redhat.com>
# (c) 2017 Ansible Project
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import fcntl
import gettext
import os
import pty
import shlex
import subprocess
from abc import abstractmethod, abstractproperty
from functools import wraps

from ansible import constants as C
from ansible.compat import selectors
from ansible.errors import AnsibleError
from ansible.module_utils.six import PY3, string_types, text_type, binary_type
from ansible.module_utils.six.moves import shlex_quote
from ansible.module_utils._text import to_bytes, to_text
from ansible.plugins import AnsiblePlugin
from ansible.plugins.loader import shell_loader

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

    def _send_initial_data(self, fh, in_data):
        '''
        Writes initial data to the stdin filehandle of the subprocess and closes
        it. (The handle must be closed; otherwise, for example, "sftp -b -" will
        just hang forever waiting for more commands.)
        '''

        display.debug('Sending initial data')

        try:
            fh.write(to_bytes(in_data))
            fh.close()
        except (OSError, IOError):
            raise AnsibleConnectionFailure('Data could not be sent to remote host. Make sure this host is reachable using the configured connection method.')

        display.debug('Sent initial data (%d bytes)' % len(in_data))

    def _bare_run(self, cmd, in_data, executable=None, sudoable=True, external_fds=None):
        '''
        Starts the command and communicates with it until it ends.
        '''

        # Start the given command. If we don't need to pipeline data, we can try
        # to use a pseudo-tty. If we are pipelining data, or can't create a pty,
        # we fall back to using plain old pipes.

        p = None

        use_shell = False
        if isinstance(cmd, (text_type, binary_type)):
            cmd = to_bytes(cmd)
            display_cmd = shlex_quote(to_text(cmd))
            use_shell = True
        else:
            cmd = list(map(to_bytes, cmd))
            display_cmd = list(map(shlex_quote, map(to_text, cmd)))

        display.vvv(u'EXEC {0}'.format(display_cmd), host=getattr(self, 'host', None))

        if not in_data:
            try:
                # Make sure stdin is a proper pty to avoid tcgetattr errors
                master, slave = pty.openpty()
                if PY3 and self._play_context.password and external_fds is not None:
                    p = subprocess.Popen(cmd, shell=use_shell, executable=executable, stdin=slave, stdout=subprocess.PIPE, stderr=subprocess.PIPE, pass_fds=external_fds)
                else:
                    p = subprocess.Popen(cmd, shell=use_shell, executable=executable, stdin=slave, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdin = os.fdopen(master, 'wb', 0)
                os.close(slave)
            except (OSError, IOError):
                p = None

        if not p:
            if PY3 and self._play_context.password:
                p = subprocess.Popen(cmd, shell=use_shell, executable=executable, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, pass_fds=external_fds)
            else:
                p = subprocess.Popen(cmd, shell=use_shell, executable=executable, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdin = p.stdin

        # If we are using external password authentication (ie. sshpass),
        # write the password into the external pipe provided.

        if self._play_context.password and external_fds is not None:
            os.close(external_fds[0])
            try:
                os.write(external_fds[1], to_bytes(self._play_context.password) + b'\n')
            except OSError as e:
                # Ignore broken pipe errors if the external process has exited.
                if e.errno != errno.EPIPE or p.poll() is None:
                    raise
            os.close(external_fds[1])

        #
        # I/O state machine
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
        if self._play_context.become and sudoable:
            if self._play_context.prompt:
                # We're requesting escalation with a password, so we have to
                # wait for a password prompt.
                state = states.index('awaiting_prompt')
                display.debug(u'Initial state: %s: %s' % (states[state], self._play_context.prompt))
            elif self._play_context.success_key:
                # We're requesting escalation without a password, so we have to
                # detect success/failure before sending any initial data.
                state = states.index('awaiting_escalation')
                display.debug(u'Initial state: %s: %s' % (states[state], self._play_context.success_key))

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
        timeout = 2 + self._play_context.timeout
        for fd in (p.stdout, p.stderr):
            fcntl.fcntl(fd, fcntl.F_SETFL, fcntl.fcntl(fd, fcntl.F_GETFL) | os.O_NONBLOCK)

        # TODO: bcoca would like to use SelectSelector() when open
        # filehandles is low, then switch to more efficient ones when higher.
        # select is faster when filehandles is low.
        selector = selectors.DefaultSelector()
        selector.register(p.stdout, selectors.EVENT_READ)
        selector.register(p.stderr, selectors.EVENT_READ)

        # If we can send initial data without waiting for anything, we do so
        # before we start polling
        if states[state] == 'ready_to_send' and in_data:
            self._send_initial_data(stdin, in_data)
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
                        display.debug("stdout chunk (state=%s):\n>>>%s<<<\n" % (state, to_text(b_chunk)))
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
                        display.debug('Sending become_pass in response to prompt')
                        stdin.write(to_bytes(self._play_context.become_pass) + b'\n')
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
                        display.debug('Escalation succeeded')
                        self._flags['become_success'] = False
                        state += 1
                    elif self._flags['become_error']:
                        display.debug('Escalation failed')
                        self._terminate_process(p)
                        self._flags['become_error'] = False
                        raise AnsibleError('Incorrect %s password' % self._play_context.become_method)
                    elif self._flags['become_nopasswd_error']:
                        display.debug('Escalation requires password')
                        self._terminate_process(p)
                        self._flags['become_nopasswd_error'] = False
                        raise AnsibleError('Missing %s password' % self._play_context.become_method)
                    elif self._flags['become_prompt']:
                        # This shouldn't happen, because we should see the "Sorry,
                        # try again" message first.
                        display.debug('Escalation prompt repeated')
                        self._terminate_process(p)
                        self._flags['become_prompt'] = False
                        raise AnsibleError('Incorrect %s password' % self._play_context.become_method)

                # Once we're sure that the privilege escalation prompt, if any, has
                # been dealt with, we can send any initial data and start waiting
                # for output.

                if states[state] == 'ready_to_send':
                    if in_data:
                        self._send_initial_data(stdin, in_data)
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
            # close stdin after process is terminated and stdout/stderr are read
            # completely (see also issue #848)
            stdin.close()

        return (p.returncode, b_stdout, b_stderr)

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
            if self._play_context.prompt and self.check_password_prompt(b_line):
                display.debug("become_prompt: (source=%s, state=%s): '%s'" % (source, state, display_line))
                self._flags['become_prompt'] = True
                suppress_output = True
            elif self._play_context.success_key and self.check_become_success(b_line):
                display.debug("become_success: (source=%s, state=%s): '%s'" % (source, state, display_line))
                self._flags['become_success'] = True
                suppress_output = True
            elif sudoable and self.check_incorrect_password(b_line):
                display.debug("become_error: (source=%s, state=%s): '%s'" % (source, state, display_line))
                self._flags['become_error'] = True
            elif sudoable and self.check_missing_password(b_line):
                display.debug("become_nopasswd_error: (source=%s, state=%s): '%s'" % (source, state, display_line))
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
