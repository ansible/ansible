# Copyright: (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from abc import ABCMeta, abstractmethod

from ansible.module_utils.six import with_metaclass


class TargetBase(with_metaclass(ABCMeta, object)):
    '''
    Base class for target plugins.

    Similar to how a connection has an associated shell plugin to abstract
    details of its OS shell, a target plugin abstracts higher level interaction
    between action plugins and the remote machine, such as how modules execute,
    and how file operations are implemented.

    Target plugins could be implemented by:

    * building equivalent shell commands using the shell plugin and forwarding
      them to :meth:`Connection.exec_command`.
    * forwarding operations to a persistent external process to execute on its
      behalf, such as `ansible-connection`,
    * forwarding them to a persistent agent running on the target, using some
      custom network protocol tailored to Ansible's needs, or
    * forwarding them to an ephemeral agent managed by the connection plugin.
    '''
    def __init__(self, connection, play_context):
        '''
        :param Connection connection:
            Associated connection.
        :param PlayContext play_context:
            PlayContext describing the action's execution environment.
        '''
        self._connection = connection
        self._play_context = play_context

    @abstractmethod
    def exists(self, path):
        '''
        Return :data:`True` if a path exists on the remote system.

        :param str path:
        '''

    @abstractmethod
    def expand_user(self, path, sudoable=True):
        '''
        Tilde-expand and $variable-expand a path in the context of the login
        user account or a become user account.

        :param str path:
            Path to expand.
        :param bool sudoable:
            If :data:`True`, expand in the context of any become_user specified
            by the play context, if become is active, otherwise use the login
            account.
        '''

    @abstractmethod
    def make_tmp_path(self):
        '''
        Create and return a private temporary directory on the target. The
        directory is always owned by the login user account.

        :raises AnsibleError:
            Connection attempt failed, or directory could not be created.
        :returns:
            Absolute directory path.
        '''

    @abstractmethod
    def ensure_readable(self, paths, remote_user, execute):
        '''
        Ensure a list of paths created on the target as the login user are
        readable by `remote_user`.

        :param list paths:
            Absolute paths to make readable.
        :param str remote_user:
            Name of remote user to make paths accessible from.
        :param bool execute:
            If :data:`True`, additionally set the execute bit.
        '''

    @abstractmethod
    def remove(self, path):
        '''
        Recursively delete a file or directory on the target.

        :returns:
            :data:`True` on success.
        '''

    @abstractmethod
    def execute_command(self, cmd, sudoable=True, in_data=None, executable=None, chdir=None):
        '''
        Execute a command on the target. Unlike
        :meth:`Connection.exec_command`, this method knows how to.

        :param bool sudoable:
            If :data:`True`, execute the command in the context of any become
            user specified by the play context.
        :param bytes in_data:
            Standard input to supply to command.

        :returns:
            Dict with keys:

            * `rc`: exit status
            * `stdout`: string or bytes standard output
            * `stderr`: string or bytes standard error
        '''

    @abstractmethod
    def execute_module(self, name, args, env, task_vars, wrap_async, async_timeout):
        '''
        :param str name:
            Name of module to execute.
        :param dict args:
        :param dict env:
        :param dict task_vars:
        :param bool wrap_async:
            If :data:`True`, arrange for the module to execute with a lifetime
            independent of the Ansible run, and for its status and eventual
            result to be written to a job file on the remote disk.
        :param int async_timeout:
            When `wrap_async` is :data:`True`, specifies the maximum duration of
            the asynchronous task in seconds, or :data:`None` to indicate no
            job time limit.

        :returns:
            Dictionary with keys:
        '''
