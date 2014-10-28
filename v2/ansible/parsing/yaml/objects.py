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

class AnsibleBaseYAMLObject:
    '''
    the base class used to sub-class python built-in objects
    so that we can add attributes to them during yaml parsing

    '''
    _data_source   = None
    _line_number   = None
    _column_number = None

    def get_position_info(self):
        return (self._data_source, self._line_number, self._column_number)

    def set_position_info(self, src, line, col):
        self._data_source   = src
        self._line_number   = line
        self._column_number = col

    def copy_position_info(self, obj):
        ''' copies the position info from another object '''
        assert isinstance(obj, AnsibleBaseYAMLObject)

        (src, line, col) = obj.get_position_info()
        self._data_source   = src
        self._line_number   = line
        self._column_number = col

class AnsibleMapping(AnsibleBaseYAMLObject, dict):
    ''' sub class for dictionaries '''
    pass

