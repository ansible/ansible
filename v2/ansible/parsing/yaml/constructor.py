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

from yaml.constructor import Constructor
from ansible.utils.unicode import to_unicode
from ansible.parsing.yaml.objects import AnsibleMapping, AnsibleUnicode

class AnsibleConstructor(Constructor):
    def __init__(self, file_name=None):
        self._ansible_file_name = file_name
        super(AnsibleConstructor, self).__init__()

    def construct_yaml_map(self, node):
        data = AnsibleMapping()
        yield data
        value = self.construct_mapping(node)
        data.update(value)
        data._line_number   = value._line_number
        data._column_number = value._column_number
        data._data_source   = value._data_source

    def construct_mapping(self, node, deep=False):
        ret = AnsibleMapping(super(Constructor, self).construct_mapping(node, deep))
        ret._line_number   = node.__line__
        ret._column_number = node.__column__

        # in some cases, we may have pre-read the data and then
        # passed it to the load() call for YAML, in which case we
        # want to override the default datasource (which would be
        # '<string>') to the actual filename we read in
        if self._ansible_file_name:
            ret._data_source = self._ansible_file_name
        else:
            ret._data_source = node.__datasource__

        return ret

    def construct_yaml_str(self, node):
        # Override the default string handling function
        # to always return unicode objects
        value = self.construct_scalar(node)
        value = to_unicode(value)
        data = AnsibleUnicode(self.construct_scalar(node))

        data._line_number = node.__line__
        data._column_number = node.__column__
        if self._ansible_file_name:
            data._data_source = self._ansible_file_name
        else:
            data._data_source = node.__datasource__

        return data

AnsibleConstructor.add_constructor(
    u'tag:yaml.org,2002:map',
    AnsibleConstructor.construct_yaml_map)

AnsibleConstructor.add_constructor(
    u'tag:yaml.org,2002:python/dict',
    AnsibleConstructor.construct_yaml_map)

AnsibleConstructor.add_constructor(
    u'tag:yaml.org,2002:str',
    AnsibleConstructor.construct_yaml_str)

AnsibleConstructor.add_constructor(
    u'tag:yaml.org,2002:python/unicode',
    AnsibleConstructor.construct_yaml_str)

