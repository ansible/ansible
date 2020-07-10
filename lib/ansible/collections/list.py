# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from collections import defaultdict

from ansible.collections import has_collection_flag
from ansible.module_utils._text import to_bytes, to_text
from ansible.module_utils.six import string_types
from ansible.module_utils.common._collections_compat import Iterable
from ansible.utils.collection_loader import AnsibleCollectionConfig
from ansible.utils.collection_loader._collection_finder import AnsibleCollectionRef, _get_collection_name_from_path, validated_collection_path
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
        search_paths = []
    elif isinstance(search_paths, string_types) or not isinstance(search_paths, Iterable):
        raise TypeError("'search_paths' is expected to be a list but got: %s" % type(search_paths))

    search_paths.extend(AnsibleCollectionConfig.collection_paths)

    for path in search_paths:

        b_path = to_bytes(path)
        if not os.path.exists(b_path):
            # warn for missing, but not if default
            if warn:
                display.warning("The configured collection path {0} does not exist.".format(path))
            continue

        if not os.path.isdir(b_path):
            if warn:
                display.warning("The configured collection path {0}, exists, but it is not a directory.".format(path))
            continue

        yield path


def list_collection_dirs(search_paths, coll_filter=None):
    """
    Return paths for the specific collections found in passed or configured search paths
    :param search_paths: list of text-string paths, if none load default config
    :param coll_filter: limit collections to just the specific namespace or collection, if None all are returned
    :return: list of collection directory paths
    """

    collections = defaultdict(dict)
    for path in list_valid_collection_paths(search_paths):

        b_path = to_bytes(path)
        if os.path.isdir(b_path):
            b_coll_root = to_bytes(validated_collection_path(path))

            if os.path.exists(b_coll_root) and os.path.isdir(b_coll_root):
                coll = None
                if coll_filter is None:
                    namespaces = os.listdir(b_coll_root)
                else:
                    if '.' in coll_filter:
                        (nsp, coll) = coll_filter.split('.')
                    else:
                        nsp = coll_filter
                    namespaces = [nsp]

                for ns in namespaces:
                    b_namespace_dir = os.path.join(b_coll_root, to_bytes(ns))

                    if os.path.isdir(b_namespace_dir):

                        if coll is None:
                            colls = os.listdir(b_namespace_dir)
                        else:
                            colls = [coll]

                        for collection in colls:

                            # skip dupe collections as they will be masked in execution
                            if collection not in collections[ns]:
                                b_coll = to_bytes(collection)
                                b_coll_dir = os.path.join(b_namespace_dir, b_coll)
                                is os.path.isdir(b_coll_dir):
                                    if not has_collection_flag(b_coll_dir):
                                        coll_dir = to_text(b_coll_dir, errors='surrogate_or_strict')
                                        display.warning('Found collection but missing MANIFEST.JSON or galaxy.yml: %s' % coll_dir)
                                    collections[ns][collection] = b_coll_dir
                                    yield b_coll_dir


def get_existing_collections(search_paths=None, warn=True):
    '''
    Return a list of collections for given a path

    :param path: OS path where collections should exist

    :return: a dict with collection name: path key pairs
    '''

    collections = {}

    for b_path in list_collection_dirs(search_paths):
        cname = _get_collection_name_from_path(b_path)

        # ensure we skip masked by precedence
        if cname not in collections:
            collections[cname] = b_path

    return collections
