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

from ansible.errors import AnsibleError
from ansible.playbook.attribute import FieldAttribute
from ansible.template import Templar

class Taggable:
    _tags = FieldAttribute(isa='list', default=[])

    def __init__(self):
        super(Taggable, self).__init__()

    def _load_tags(self, attr, ds):
        if isinstance(ds, list):
            return ds
        elif isinstance(ds, basestring):
            return [ ds ]
        else:
            raise AnsibleError('tags must be specified as a list', obj=ds)

    def evaluate_tags(self, only_tags, skip_tags, all_vars):
        templar = Templar(loader=self._loader, variables=all_vars)
        tags = templar.template(self.tags)
        if not isinstance(tags, list):
            tags = set([tags])
        else:
            tags = set(tags)

        #print("%s tags are: %s, only_tags=%s, skip_tags=%s" % (self, my_tags, only_tags, skip_tags))
        if skip_tags:
            skipped_tags = tags.intersection(skip_tags)
            if len(skipped_tags) > 0:
                return False
        matched_tags = tags.intersection(only_tags)
        #print("matched tags are: %s" % matched_tags)
        if len(matched_tags) > 0 or 'all' in only_tags:
            return True
        else:
            return False

