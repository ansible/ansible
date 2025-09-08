# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.playbook.attribute import FieldAttribute
from ansible.utils.collection_loader import AnsibleCollectionConfig
from ansible.utils.display import Display

display = Display()


def _ensure_default_collection(collection_list=None):
    default_collection = AnsibleCollectionConfig.default_collection

    # Will be None when used as the default
    if collection_list is None:
        collection_list = []

    # FIXME: exclude role tasks?
    if default_collection and default_collection not in collection_list:
        collection_list.insert(0, default_collection)

    # if there's something in the list, ensure that builtin or legacy is always there too
    if collection_list and 'ansible.builtin' not in collection_list and 'ansible.legacy' not in collection_list:
        collection_list.append('ansible.legacy')

    return collection_list


class CollectionSearch:

    # this needs to be populated before we can resolve tasks/roles/etc
    collections = FieldAttribute(isa='list', listof=(str,), priority=100, default=_ensure_default_collection, always_post_validate=True, static=True)

    def _load_collections(self, attr, ds):
        # We are always a mixin with Base, so we can validate this untemplated
        # field early on to guarantee we are dealing with a list.
        ds = self.get_validated_value('collections', self.fattributes.get('collections'), ds, None)

        # this will only be called if someone specified a value; call the shared value
        _ensure_default_collection(collection_list=ds)

        if not ds:  # don't return an empty collection list, just return None
            return None

        return ds
