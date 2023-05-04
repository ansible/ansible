# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.errors import AnsibleError
from ansible.cli.galaxy import with_collection_artifacts_manager
from ansible.galaxy.collection import find_existing_collections
from ansible.module_utils.common.text.converters import to_bytes
from ansible.utils.collection_loader._collection_finder import _get_collection_name_from_path
from ansible.utils.display import Display

display = Display()


@with_collection_artifacts_manager
def list_collections(coll_filter=None, search_paths=None, dedupe=True, artifacts_manager=None):

    collections = {}
    for candidate in list_collection_dirs(search_paths=search_paths, coll_filter=coll_filter, artifacts_manager=artifacts_manager, dedupe=dedupe):
        collection = _get_collection_name_from_path(candidate)
        collections[collection] = candidate
    return collections


@with_collection_artifacts_manager
def list_collection_dirs(search_paths=None, coll_filter=None, artifacts_manager=None, dedupe=True):
    """
    Return paths for the specific collections found in passed or configured search paths
    :param search_paths: list of text-string paths, if none load default config
    :param coll_filter: limit collections to just the specific namespace or collection, if None all are returned
    :return: list of collection directory paths
    """

    namespace_filter = None
    collection_filter = None
    if coll_filter is not None:
        if '.' in coll_filter:
            try:
                namespace_filter, collection_filter = coll_filter.split('.')
            except ValueError:
                raise AnsibleError("Invalid collection pattern supplied: %s" % coll_filter)
        else:
            namespace_filter = coll_filter

    for req in find_existing_collections(search_paths, artifacts_manager, namespace_filter=namespace_filter,
                                         collection_filter=collection_filter, dedupe=dedupe):

        yield to_bytes(req.src)
