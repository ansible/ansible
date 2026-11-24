# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

from ansible.module_utils.common.text.converters import to_bytes
from ansible.utils.collection_loader import find_collection_paths
from ansible.module_utils._internal._collection_loader._collection_finder import _get_collection_name_from_path
from ansible.utils.display import Display

display = Display()


def list_collections(coll_filter=None, search_paths=None, dedupe=True):

    collections = {}
    for candidate in list_collection_dirs(search_paths=search_paths, coll_filter=coll_filter, dedupe=dedupe):
        if collection := _get_collection_name_from_path(candidate):
            collections[collection] = candidate
        else:
            display.debug(f'Skipping invalid collection in path: {candidate!r}')
    return collections


def list_collection_dirs(search_paths=None, coll_filter=None, dedupe=True):
    """
    Return paths for the specific collections found in passed or configured search paths
    :param search_paths: list of text-string paths, if none load default config
    :param coll_filter: limit collections to just the specific namespace or collection, if None all are returned
    :return: list of collection directory paths
    """
    for path in find_collection_paths(search_paths, coll_filter=coll_filter, dedupe=dedupe):
        yield to_bytes(path.as_posix())
