# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.six import string_types
from ansible.playbook.attribute import FieldAttribute
from ansible.utils.collection_loader import AnsibleCollectionLoader


def _ensure_default_collection(collection_list=None):
    default_collection = AnsibleCollectionLoader().default_collection

    if collection_list is None:
        collection_list = []

    if default_collection:  # FIXME: exclude role tasks?
        if isinstance(collection_list, string_types):
            collection_list = [collection_list]

        if default_collection not in collection_list:
            collection_list.insert(0, default_collection)

    # if there's something in the list, ensure that builtin or legacy is always there too
    if collection_list and 'ansible.builtin' not in collection_list and 'ansible.legacy' not in collection_list:
        collection_list.append('ansible.legacy')

    return collection_list


class CollectionSearch:

    # this needs to be populated before we can resolve tasks/roles/etc
    _collections = FieldAttribute(isa='list', listof=string_types, priority=100, default=_ensure_default_collection)

    def _load_collections(self, attr, ds):
        # this will only be called if someone specified a value; call the shared value
        _ensure_default_collection(collection_list=ds)

        if not ds:  # don't return an empty collection list, just return None
            return None

        return ds
