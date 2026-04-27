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

import typing as t

from ansible._internal._templating._engine import TemplateEngine
from ansible.errors import AnsibleError
from ansible.module_utils.common.sentinel import Sentinel
from ansible.module_utils._internal._datatag import AnsibleTagHelper
from ansible.playbook.attribute import FieldAttribute
from ansible.utils.display import Display

_display = Display()


def _flatten_tags(tags: list[str | int]) -> list[str | int]:
    rv = set()
    for tag in tags:
        if isinstance(tag, list):
            rv.update(tag)
        else:
            rv.add(tag)
    return list(rv)


class Taggable:

    _RESERVED = frozenset(['tagged', 'all', 'untagged'])
    untagged = frozenset(['untagged'])
    tags = FieldAttribute(isa='list', default=list, listof=(str, int), extend=True)

    def _load_tags(self, attr, ds):

        tags = None
        if isinstance(ds, list):
            tags = ds
        elif isinstance(ds, str):
            tags = [AnsibleTagHelper.tag_copy(ds, item.strip()) for item in ds.split(',')]

        if tags is None:
            raise AnsibleError('tags must be specified as a list', obj=ds)

        if found := self._RESERVED.intersection(tags):
            _display.warning(f"Found reserved tagnames in tags: {list(found)!r}, we do not recommend doing this as it might give unexpected results", obj=ds)

        return tags

    def _get_all_taggable_objects(self) -> t.Iterable[Taggable]:
        obj = self
        while obj is not None:
            yield obj

            if (role := getattr(obj, "_role", Sentinel)) is not Sentinel:
                yield role  # type: ignore[misc]

            obj = obj._parent

        yield self.get_play()

    def evaluate_tags(self, only_tags, skip_tags, all_vars):
        """Check if the current item should be executed depending on the specified tags.

        NOTE this method is assumed to be called only on Task objects.
        """
        if self.tags:
            templar = TemplateEngine(loader=self._loader, variables=all_vars)
            for obj in self._get_all_taggable_objects():
                if (_tags := getattr(obj, "_tags", Sentinel)) is not Sentinel:
                    obj._tags = _flatten_tags(templar.template(_tags))
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
