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

from errors import AnsibleError
from ansible.utils import list_union

class Tag:
    def __init__(self, tags=[]):
        assert isinstance(tags, list)
        self._tags = tags

    def push(self, tags):
        if not isinstance(tags, list):
            tags = [ tags ]
        for tag in tags:
            if not isinstance(tag, basestring):
                tag = str(tag)
            if tag not in self._tags:
                self._tags.append(tag)

    def get_tags(self):
        return self._tags

    def merge(self, tags):
        # returns a union of the tags, which can be a string,
        # a list of strings, or another Tag() class
        if isinstance(tags, basestring):
            tags = Tag([tags])
        elif isinstance(tags, list):
            tags = Tag(tags)
        elif not isinstance(tags, Tag):
            raise AnsibleError('expected a Tag() instance, instead got %s' % type(tags))
        return utils.list_union(self._tags, tags.get_tags())

    def matches(self, tag):
        return tag in self._tags
        
