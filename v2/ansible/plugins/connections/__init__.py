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

from abc import ABCMeta, abstractmethod, abstractproperty

from six import add_metaclass

from ansible import constants as C
from ansible.errors import AnsibleError

# FIXME: this object should be created upfront and passed through
#        the entire chain of calls to here, as there are other things
#        which may want to output display/logs too
from ansible.utils.display import Display

__all__ = ['ConnectionBase']

@add_metaclass(ABCMeta)
class ConnectionBase:
    '''
    A base class for connections to contain common code.
    '''

    has_pipelining = False
    become_methods = C.BECOME_METHODS

    def __init__(self, connection_info, new_stdin, *args, **kwargs):
        # All these hasattrs allow subclasses to override these parameters
        if not hasattr(self, '_connection_info'):
            self._connection_info = connection_info
        if not hasattr(self, '_new_stdin'):
            self._new_stdin = new_stdin
        if not hasattr(self, '_display'):
            self._display = Display(verbosity=connection_info.verbosity)
        if not hasattr(self, '_connected'):
            self._connected = False

        self._connect()

    def _become_method_supported(self, become_method):
        ''' Checks if the current class supports this privilege escalation method '''

        if become_method in self.__class__.become_methods:
            return True

        raise AnsibleError("Internal Error: this connection module does not support running commands via %s" % become_method)

    @abstractproperty
    def transport(self):
        """String used to identify this Connection class from other classes"""
        pass

    @abstractmethod
    def _connect(self):
        """Connect to the host we've been initialized with"""
        pass

    @abstractmethod
    def exec_command(self, cmd, tmp_path, executable=None, in_data=None):
        """Run a command on the remote host"""
        pass

    @abstractmethod
    def put_file(self, in_path, out_path):
        """Transfer a file from local to remote"""
        pass

    @abstractmethod
    def fetch_file(self, in_path, out_path):
        """Fetch a file from remote to local"""
        pass

    @abstractmethod
    def close(self):
        """Terminate the connection"""
        pass
