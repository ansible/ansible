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

from __future__ import annotations

from ansible.errors import AnsibleError
from ansible.module_utils.six import string_types
from ansible.module_utils.common.sentinel import Sentinel
from ansible.playbook.attribute import FieldAttribute
from ansible.template import Templar


def _flatten_tags(tags: list) -> list:
    rv = set()
    for tag in tags:
        if isinstance(tag, list):
            rv.update(tag)
        else:
            rv.add(tag)
    return list(rv)


class Taggable:

    untagged = frozenset(['untagged'])
    tags = FieldAttribute(isa='list', default=list, listof=(string_types, int), extend=True)

    def _load_tags(self, attr, ds):
        if isinstance(ds, list):
            return ds
        elif isinstance(ds, string_types):
            return [x.strip() for x in ds.split(',')]
        else:
            raise AnsibleError('tags must be specified as a list', obj=ds)

    def evaluate_tags(self, only_tags, skip_tags, all_vars):
        ''' this checks if the current item should be executed depending on tag options '''

        if self.tags:
            templar = Templar(loader=self._loader, variables=all_vars)
            obj = self
            while obj is not None:
                if (_tags := getattr(obj, "_tags", Sentinel)) is not Sentinel:
                    obj._tags = _flatten_tags(templar.template(_tags))
                obj = obj._parent
            tags = set(self.tags)
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
