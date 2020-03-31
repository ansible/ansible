# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os


FLAG_FILES = frozenset(['MANIFEST.json', 'galaxy.yml'])


def is_collection_path(path):
    """
    Verify that a path meets min requirements to be a collection
    :param path: byte-string path to evaluate for collection containment
    :return: boolean signifying 'collectionness'
    """

    is_coll = False
    if os.path.isdir(path):
        for flag in FLAG_FILES:
            if os.path.exists(os.path.join(path, flag)):
                is_coll = True
                break

    return is_coll
