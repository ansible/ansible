# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2015 Toshio Kuratomi <tkuratomi@ansible.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import fcntl
import gettext
import os
import shlex
from abc import ABCMeta, abstractmethod, abstractproperty

from functools import wraps
from ansible.compat.six import with_metaclass

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.plugins import shell_loader
from ansible.utils.unicode import to_bytes, to_unicode

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

__all__ = ['ConnectionBase', 'ensure_connect']


def ensure_connect(func):
    @wraps(func)
    def wrapped(self, *args, **kwargs):
        self._connect()
        return func(self, *args, **kwargs)
    return wrapped


class ConnectionBase(with_metaclass(ABCMeta, object)):
    '''
    A base class for connections to contain common code.
    '''

    has_pipelining = False
    become_methods = C.BECOME_METHODS
    # When running over this connection type, prefer modules written in a certain language
    # as discovered by the specified file extension.  An empty string as the
    # language means any language.
    module_implementation_preferences = ('',)
    allow_executable = True

    def __init__(self, play_context, new_stdin, *args, **kwargs):
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

        # load the shell plugin for this action/connection
        if play_context.shell:
            shell_type = play_context.shell
        elif hasattr(self, '_shell_type'):
            shell_type = getattr(self, '_shell_type')
        else:
            shell_type = 'sh'
            shell_filename = os.path.basename(C.DEFAULT_EXECUTABLE)
            for shell in shell_loader.all():
                if shell_filename in shell.COMPATIBLE_SHELLS:
                    shell_type = shell.SHELL_FAMILY
                    break

        self._shell = shell_loader.get(shell_type)
        if not self._shell:
            raise AnsibleError("Invalid shell type specified (%s), or the plugin for that shell type is missing." % shell_type)

    @property
    def connected(self):
        '''Read-only property holding whether the connection to the remote host is active or closed.'''
        return self._connected

    def _become_method_supported(self):
        ''' Checks if the current class supports this privilege escalation method '''

        if self._play_context.become_method in self.become_methods:
            return True

        raise AnsibleError("Internal Error: this connection module does not support running commands via %s" % self._play_context.become_method)

    def set_host_overrides(self, host):
        '''
        An optional method, which can be used to set connection plugin parameters
        from variables set on the host (or groups to which the host belongs)

        Any connection plugin using this should first initialize its attributes in
        an overridden `def __init__(self):`, and then use `host.get_vars()` to find
        variables which may be used to set those attributes in this method.
        '''
        pass

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
            return [to_unicode(x.strip()) for x in shlex.split(to_bytes(argstring)) if x.strip()]
        except AttributeError:
            return [to_unicode(x.strip()) for x in shlex.split(argstring) if x.strip()]

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

            HardCodedShell ConnectionCommand UsersLoginShell DEFAULT_EXECUTABLE BecomeCommand DEFAULT_EXECUTABLE Command
        :HardCodedShell: Is optional.  It is run locally to invoke the
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
        :UsersLoginShell: This is the shell that the ``ansible_ssh_user`` has
            configured as their login shell.  In traditional UNIX parlance,
            this is the last field of a user's ``/etc/passwd`` entry   We do not
            specifically try to run the ``UsersLoginShell`` when we connect.
            Instead it is implicit in the actions that the
            ``ConnectionCommand`` takes when it connects to a remote machine.
            ``ansible_shell_type`` may be set to inform ansible of differences
            in how the ``UsersLoginShell`` handles things like quoting if a
            shell has different semantics than the Bourne shell.
        :DEFAULT_EXECUTABLE: This is the shell accessible via
            ``ansible.constants.DEFAULT_EXECUTABLE``.  We explicitly invoke
            this shell so that we have predictable quoting rules at this
            point.  The ``DEFAULT_EXECUTABLE`` is only settable by the user
            because some sudo setups may only allow invoking a specific Bourne
            shell.  (For instance, ``/bin/bash`` may be allowed but
            ``/bin/sh``, our default, may not).  We invoke this twice, once
            after the ``ConnectionCommand`` and once after the
            ``BecomeCommand``.  After the ConnectionCommand, this is run by
            the ``UsersLoginShell``.  After the ``BecomeCommand`` we specify
            that the ``DEFAULT_EXECUTABLE`` is being invoked directly.
        :BecomeComand: Is the command that performs privilege escalation.
            Setting this up is performed by the action plugin prior to running
            ``exec_command``. So we just get passed :param:`cmd` which has the
            BecomeCommand already added.  (Examples: sudo, su)
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

    def check_become_success(self, output):
        for line in output.splitlines(True):
            if self._play_context.success_key == line.rstrip():
                return True
        return False

    def check_password_prompt(self, output):
        if self._play_context.prompt is None:
            return False
        elif isinstance(self._play_context.prompt, basestring):
            return output.startswith(self._play_context.prompt)
        else:
            return self._play_context.prompt(output)

    def check_incorrect_password(self, output):
        incorrect_password = gettext.dgettext(self._play_context.become_method, C.BECOME_ERROR_STRINGS[self._play_context.become_method])
        return incorrect_password and incorrect_password in output

    def check_missing_password(self, output):
        missing_password = gettext.dgettext(self._play_context.become_method, C.BECOME_MISSING_STRINGS[self._play_context.become_method])
        return missing_password and missing_password in output

    def connection_lock(self):
        f = self._play_context.connection_lockfd
        display.vvvv('CONNECTION: pid %d waiting for lock on %d' % (os.getpid(), f))
        fcntl.lockf(f, fcntl.LOCK_EX)
        display.vvvv('CONNECTION: pid %d acquired lock on %d' % (os.getpid(), f))

    def connection_unlock(self):
        f = self._play_context.connection_lockfd
        fcntl.lockf(f, fcntl.LOCK_UN)
        display.vvvv('CONNECTION: pid %d released lock on %d' % (os.getpid(), f))
