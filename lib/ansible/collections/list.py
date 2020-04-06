# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from collections import defaultdict

from ansible.collections import is_collection_path
from ansible.utils.collection_loader import AnsibleCollectionLoader, get_collection_name_from_path
from ansible.utils.display import Display

display = Display()


def list_valid_collection_paths(search_paths=None, warn=False):
    """
    Filter out non existing or invalid search_paths for collections
    :param search_paths: list of text-string paths, if none load default config
    :param warn: display warning if search_path does not exist
    :return: subset of original list
    """

    if search_paths is None:
        search_paths = AnsibleCollectionLoader().n_collection_paths

    for path in search_paths:

        if not os.path.exists(path):
            # warn for missing, but not if default
            if warn:
                display.warning("The configured collection path {0} does not exist.".format(path))
            continue

        if not os.path.isdir(path):
            if warn:
                display.warning("The configured collection path {0}, exists, but it is not a directory.".format(path))
            continue

        yield path


def list_collection_dirs(search_paths=None, coll_filter=None):
    """
    Return paths for the specific collections found in passed or configured search paths
    :param search_paths: list of text-string paths, if none load default config
    :param coll_filter: limit collections to just the specific namespace or collection, if None all are returned
    :return: list of collection directory paths
    """

    collections = defaultdict(dict)
    for path in list_valid_collection_paths(search_paths):

        if os.path.isdir(path):
            coll_root = os.path.join(path, 'ansible_collections')

            if os.path.exists(coll_root) and os.path.isdir(coll_root):

                coll = None
                if coll_filter is None:
                    namespaces = os.listdir(coll_root)
                else:
                    if '.' in coll_filter:
                        (nsp, coll) = coll_filter.split('.')
                    else:
                        nsp = coll_filter
                    namespaces = [nsp]

                for ns in namespaces:
                    namespace_dir = os.path.join(coll_root, ns)

                    if os.path.isdir(namespace_dir):

                        if coll is None:
                            colls = os.listdir(namespace_dir)
                        else:
                            colls = [coll]

                        for collection in colls:

                            # skip dupe collections as they will be masked in execution
                            if collection not in collections[ns]:
                                coll_dir = os.path.join(namespace_dir, collection)
                                if is_collection_path(coll_dir):
                                    cpath = os.path.join(namespace_dir, collection)
                                    collections[ns][collection] = cpath
                                    yield cpath
