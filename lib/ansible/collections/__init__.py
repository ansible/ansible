# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible.module_utils._text import to_bytes

B_FLAG_FILES = frozenset([b'MANIFEST.json', b'galaxy.yml'])


def is_collection_path(path):
    """
    Verify that a path meets min requirements to be a collection
    :param path: byte-string path to evaluate for collection containment
    :return: boolean signifying 'collectionness'
    """

    is_coll = False
    b_path = to_bytes(path)
    if os.path.isdir(b_path):
        for b_flag in B_FLAG_FILES:
            if os.path.exists(os.path.join(b_path, b_flag)):
                is_coll = True
                break

    return is_coll
