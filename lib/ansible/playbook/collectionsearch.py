# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.six import string_types
from ansible.playbook.attribute import FieldAttribute


class CollectionSearch:
    # this needs to be populated before we can resolve tasks/roles/etc
    _collections = FieldAttribute(isa='list', listof=string_types, priority=100)

    def _load_collections(self, attr, ds):
        if not ds:
            # if empty/None, just return whatever was there; legacy behavior will do the right thing
            return ds

        if not isinstance(ds, list):
            ds = [ds]

        if 'ansible.builtin' not in ds and 'ansible.legacy' not in ds:
            ds.append('ansible.legacy')

        return ds
