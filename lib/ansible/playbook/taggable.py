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
from ansible.module_utils.six import string_types
from ansible.playbook.attribute import FieldAttribute
from ansible.template import Templar
from ansible.utils.sentinel import Sentinel


class Taggable:

    untagged = frozenset(['untagged'])
    _tags = FieldAttribute(isa='list', default=list, listof=(string_types, int), extend=True)

    def _load_tags(self, attr, ds):
        if isinstance(ds, list):
            return ds
        elif isinstance(ds, string_types):
            if ',' in ds:
                value = ds.split(',')
                return [x.strip() for x in value]
            else:
                return ds
        else:
            raise AnsibleError('tags must be specified as a list', obj=ds)

    def _post_validate_tags(self, attr, value, templar):
        # This is here to keep evaluate_tags() in sync with general post validation
        parent_value = Sentinel
        if hasattr(self, '_parent') and hasattr(self._parent, '_post_validate_tags'):
            parent_value = self._parent._post_validate_tags(self._parent._tags, getattr(self._parent, 'tags'), templar)
        value = templar.template(value)
        if hasattr(self, '_extend_post_validated_value'):
            return self._extend_post_validated_value(value, parent_value)
        else:
            return value

    def evaluate_tags(self, only_tags, skip_tags, all_vars):
        ''' this checks if the current item should be executed depending on tag options '''

        if self.tags:
            templar = Templar(loader=self._loader, variables=all_vars)
            tags = set(self._post_validate_tags(self._tags, self.tags, templar))
            self.tags = list(tags)
        else:
            # this makes isdisjoint work for untagged
            tags = self.untagged

        should_run = True  # default, tasks to run

        if only_tags:
            if 'always' in tags:
                should_run = True
            elif ('all' in only_tags and 'never' not in tags):
                should_run = True
            elif not tags.isdisjoint(only_tags):
                should_run = True
            elif 'tagged' in only_tags and tags != self.untagged and 'never' not in tags:
                should_run = True
            else:
                should_run = False

        if should_run and skip_tags:

            # Check for tags that we need to skip
            if 'all' in skip_tags:
                if 'always' not in tags or 'always' in skip_tags:
                    should_run = False
            elif not tags.isdisjoint(skip_tags):
                should_run = False
            elif 'tagged' in skip_tags and tags != self.untagged:
                should_run = False

        return should_run
