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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.module_utils._text import to_text

from ansible.utils.display import Display

display = Display()


def to_safe_group_name(name, replacer="_", force=False, silent=False):
    # Converts 'bad' characters in a string to underscores (or provided replacer) so they can be used as Ansible hosts or groups

    warn = ''
    if name:  # when deserializing we might not have name yet
        invalid_chars = C.INVALID_VARIABLE_NAMES.findall(name)
        if invalid_chars:
            msg = 'invalid character(s) "%s" in group name (%s)' % (to_text(set(invalid_chars)), to_text(name))
            if C.TRANSFORM_INVALID_GROUP_CHARS not in ('never', 'ignore') or force:
                name = C.INVALID_VARIABLE_NAMES.sub(replacer, name)
                if not (silent or C.TRANSFORM_INVALID_GROUP_CHARS == 'silently'):
                    display.vvvv('Replacing ' + msg)
                    warn = 'Invalid characters were found in group names and automatically replaced, use -vvvv to see details'
            else:
                if C.TRANSFORM_INVALID_GROUP_CHARS == 'never':
                    display.vvvv('Not replacing %s' % msg)
                    warn = True
                    warn = 'Invalid characters were found in group names but not replaced, use -vvvv to see details'

                # remove this message after 2.10 AND changing the default to 'always'
                group_chars_setting, group_chars_origin = C.config.get_config_value_and_origin('TRANSFORM_INVALID_GROUP_CHARS')
                if group_chars_origin == 'default':
                    display.deprecated('The TRANSFORM_INVALID_GROUP_CHARS settings is set to allow bad characters in group names by default,'
                                       ' this will change, but still be user configurable on deprecation', version='2.10')

    if warn:
        display.warning(warn)

    return name


class Group:
    ''' a group of ansible hosts '''

    # __slots__ = [ 'name', 'hosts', 'vars', 'child_groups', 'parent_groups', 'depth', '_hosts_cache' ]

    def __init__(self, name=None):

        self.depth = 0
        self.name = to_safe_group_name(name)
        self.hosts = []
        self._hosts = None
        self.vars = {}
        self.child_groups = []
        self.parent_groups = []
        self._hosts_cache = None
        self.priority = 1

    def __repr__(self):
        return self.get_name()

    def __str__(self):
        return self.get_name()

    def __getstate__(self):
        return self.serialize()

    def __setstate__(self, data):
        return self.deserialize(data)

    def serialize(self):
        self._hosts = None

        result = dict(
            name=self.name,
            vars=self.vars.copy(),
            parent_groups=self.parent_groups,
            depth=self.depth,
            hosts=self.hosts,
            child_groups=self.child_groups,
        )

        return result

    def deserialize(self, data):
        self.__init__()
        self.name = data.get('name')
        self.vars = data.get('vars', dict())
        self.depth = data.get('depth', 0)
        self.hosts = data.get('hosts', [])
        self._hosts = None
        self.child_groups = data.get('child_groups', [])
        self.parent_groups = data.get('parent_groups', [])

    @property
    def host_names(self):
        if self._hosts is None:
            self._hosts = set(self.hosts)
        return self._hosts

    def get_name(self):
        return self.name

    def set_variable(self, key, value):

        if key == 'ansible_group_priority':
            self.set_priority(int(value))
        else:
            self.vars[key] = value

    def get_vars(self):
        return self.vars.copy()

    def set_priority(self, priority):
        try:
            self.priority = int(priority)
        except TypeError:
            # FIXME: warn about invalid priority
            pass
