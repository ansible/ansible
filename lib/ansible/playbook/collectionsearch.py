# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.module_utils.six import string_types
from ansible.playbook.attribute import FieldAttribute
from ansible.utils.collection_loader import AnsibleCollectionConfig
from ansible.template import is_template
from ansible.utils.display import Display

from jinja2.nativetypes import NativeEnvironment

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
    collections = FieldAttribute(isa='list', listof=string_types, priority=100, default=_ensure_default_collection,
                                 always_post_validate=True, static=True)

    def _load_collections(self, attr, ds):
        # We are always a mixin with Base, so we can validate this untemplated
        # field early on to guarantee we are dealing with a list.
        ds = self.get_validated_value('collections', self.fattributes.get('collections'), ds, None)

        # this will only be called if someone specified a value; call the shared value
        _ensure_default_collection(collection_list=ds)

        # ensure 'current's object collection is here', only playbooks, plays and roles should have this property
        if getattr(self, '_collection', False) and self._collection not in ds:
            ds.insert(0, self._collection)

        if not ds:  # don't return an empty collection list, just return None
            return None

        # This duplicates static attr checking logic from post_validate()
        # because if the user attempts to template a collection name, it may
        # error before it ever gets to the post_validate() warning (e.g. trying
        # to import a role from the collection).
        env = NativeEnvironment()
        for collection_name in ds:
            if is_template(collection_name, env):
                display.warning(f'"collections" is not templatable, but we found: {collection_name}, it will not be templated and will be used "as is".')

        return ds
