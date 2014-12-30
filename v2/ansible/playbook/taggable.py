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

from ansible.playbook.attribute import FieldAttribute

class Taggable:
    _tags = FieldAttribute(isa='list', default=[])

    def __init__(self):
        super(Taggable, self).__init__()

    def get_tags(self):
        return self._tags[:]

    def evaluate_tags(self, only_tags, skip_tags):
        my_tags = set(self.tags)
        if skip_tags:
            skipped_tags = my_tags.intersection(skip_tags)
            if len(skipped_tags) > 0:
                return False
        matched_tags = my_tags.intersection(only_tags)
        if len(matched_tags) > 0 or 'all' in only_tags:
            return True
        else:
            return False

