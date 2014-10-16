# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

import os
from ansible.parsing.yaml.objects import AnsibleBaseYAMLObject

class AnsibleError(Exception):
    def __init__(self, message, obj=None):
        self._obj     = obj
        if isinstance(self._obj, AnsibleBaseYAMLObject):
            extended_error = self._get_extended_error()
            if extended_error:
                self.message = '%s\n%s' % (message, extended_error)
        else:
            self.message = message

    def __repr__(self):
        return self.message

    def _get_line_from_file(self, filename, line_number):
        with open(filename, 'r') as f:
            lines = f.readlines()
            return lines[line_number]

    def _get_extended_error(self):
        error_message = ''

        try:
            (src_file, line_number, col_number) = self._obj.get_position_info()
            error_message += 'The error occurred on line %d of the file %s:\n' % (line_number, src_file)
            if src_file not in ('<string>', '<unicode>'):
                responsible_line = self._get_line_from_file(src_file, line_number - 1)
                if responsible_line:
                    error_message += responsible_line
                    error_message += (' ' * (col_number-1)) + '^'
        except IOError:
            error_message += '\n(could not open file to display line)'
        except IndexError:
            error_message += '\n(specified line no longer in file, maybe it changed?)'

        return error_message

class AnsibleParserError(AnsibleError):
    ''' something was detected early that is wrong about a playbook or data file '''
    pass

class AnsibleInternalError(AnsibleError):
    ''' internal safeguards tripped, something happened in the code that should never happen '''
    pass

class AnsibleRuntimeError(AnsibleError):
    ''' ansible had a problem while running a playbook '''
    pass

class AnsibleModuleError(AnsibleRuntimeError):
    ''' a module failed somehow '''
    pass

class AnsibleConnectionFailure(AnsibleRuntimeError):
    ''' the transport / connection_plugin had a fatal error '''
    pass
