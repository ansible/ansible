# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from collections import defaultdict

from ansible.errors import AnsibleError
from ansible.collections import is_collection_path
from ansible.module_utils._text import to_bytes
from ansible.utils.collection_loader import AnsibleCollectionConfig
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


def list_collection_dirs(search_paths=None, coll_filter=None):
    """
    Return paths for the specific collections found in passed or configured search paths
    :param search_paths: list of text-string paths, if none load default config
    :param coll_filter: limit collections to just the specific namespace or collection, if None all are returned
    :return: list of collection directory paths
    """

    collection = None
    namespace = None
    if coll_filter is not None:
        if '.' in coll_filter:
            try:
                (namespace, collection) = coll_filter.split('.')
            except ValueError:
                raise AnsibleError("Invalid collection pattern supplied: %s" % coll_filter)
        else:
            namespace = coll_filter

    collections = defaultdict(dict)
    for path in list_valid_collection_paths(search_paths):

        if os.path.basename(path) != 'ansible_collections':
            path = os.path.join(path, 'ansible_collections')

        b_coll_root = to_bytes(path, errors='surrogate_or_strict')

        if os.path.exists(b_coll_root) and os.path.isdir(b_coll_root):

            if namespace is None:
                namespaces = os.listdir(b_coll_root)
            else:
                namespaces = [namespace]

            for ns in namespaces:
                b_namespace_dir = os.path.join(b_coll_root, to_bytes(ns))

                if os.path.isdir(b_namespace_dir):

                    if collection is None:
                        colls = os.listdir(b_namespace_dir)
                    else:
                        colls = [collection]

                    for mycoll in colls:

                        # skip dupe collections as they will be masked in execution
                        if mycoll not in collections[ns]:
                            b_coll = to_bytes(mycoll)
                            b_coll_dir = os.path.join(b_namespace_dir, b_coll)
                            if is_collection_path(b_coll_dir):
                                collections[ns][mycoll] = b_coll_dir
                                yield b_coll_dir
