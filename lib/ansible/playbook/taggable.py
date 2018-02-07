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

import itertools

from ansible.errors import AnsibleError
from ansible.module_utils.six import string_types
from ansible.playbook.attribute import FieldAttribute
from ansible.template import Templar


class Taggable:

    untagged = frozenset(['untagged'])
    _tags = FieldAttribute(isa='list', default=[], listof=(string_types, int), extend=True)

    def __init__(self):
        super(Taggable, self).__init__()

    def _load_tags(self, attr, ds):
        if isinstance(ds, list):
            return ds
        elif isinstance(ds, string_types):
            value = ds.split(',')
            if isinstance(value, list):
                return [x.strip() for x in value]
            else:
                return [ds]
        else:
            raise AnsibleError('tags must be specified as a list', obj=ds)

    def evaluate_tags(self, only_tags, skip_tags, all_vars):
        ''' this checks if the current item should be executed depending on tag options '''

        if self.tags:
            templar = Templar(loader=self._loader, variables=all_vars)
            tags = templar.template(self.tags)

            if not isinstance(tags, list):
                if tags.find(',') != -1:
                    tags = set(tags.split(','))
                else:
                    tags = set([tags])
            else:
                tags = set([i for i, _ in itertools.groupby(tags)])
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
