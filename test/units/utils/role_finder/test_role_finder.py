from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import pytest
import sys

from ansible.constants import config
from ansible.template import Templar
from ansible.utils.role_finder import AnsibleRoleFinder
from ansible.utils.collection_loader import AnsibleCollectionConfig
from ansible.utils.collection_loader._collection_finder import _AnsibleCollectionFinder, _AnsibleCollectionLoader
from ansible.utils.collection_loader._collection_config import _EventSource


ROLEFINDER_PLAYBOOK_DIR = os.path.dirname(__file__)


def test_standard_role_search_paths():
    ''' Test that the path order is what we expect at initialization. '''
    relative_role_dir = os.path.join(ROLEFINDER_PLAYBOOK_DIR, 'roles', 'role1')
    iterator = AnsibleRoleFinder(ROLEFINDER_PLAYBOOK_DIR, relative_role_dir)
    expected = []
    expected.append(os.path.join(ROLEFINDER_PLAYBOOK_DIR, 'roles'))
    expected.extend(config.get_config_value('DEFAULT_ROLES_PATH'))
    expected.append(relative_role_dir)
    expected.append(ROLEFINDER_PLAYBOOK_DIR)
    assert iterator.standard_role_search_paths == expected


def test_set_templar():
    ''' Test setting the templating object. '''
    iterator = AnsibleRoleFinder(ROLEFINDER_PLAYBOOK_DIR)

    # Should allow None
    iterator.set_templar(None)

    # Test with correct type
    iterator.set_templar(Templar(None))

    # Test with wrong type
    with pytest.raises(TypeError, match="templar must be of type Templar"):
        iterator.set_templar("invalid")


def test_find_first():
    ''' Test find first role that matches a role name. '''

    # Set search path for collections
    finder = get_default_finder()
    reset_collections_loader_state(finder)

    iterator = AnsibleRoleFinder(ROLEFINDER_PLAYBOOK_DIR)

    # No match should return None
    result = iterator.find_first('does-not-exist')
    assert result is None

    # Match should return a single full path (no collection context given)
    result = iterator.find_first('role1')
    assert result == os.path.join(ROLEFINDER_PLAYBOOK_DIR, 'roles', 'role1')

    expected_collection_path = os.path.join(
        default_test_collection_paths[0],
        'ansible_collections', 'namespace1', 'collection1', 'roles',
        'role1')

    # Test matching when a collection context is supplied.
    result = iterator.find_first('role1', ['namespace1.collection1'])
    assert result == expected_collection_path

    result = iterator.find_first('namespace1.collection1.role1')
    assert result == expected_collection_path


############################################################
# BEGIN TEST SUPPORT
############################################################


default_test_collection_paths = [
    os.path.join(ROLEFINDER_PLAYBOOK_DIR, 'collections'),
]


def get_default_finder():
    return _AnsibleCollectionFinder(paths=default_test_collection_paths)


def nuke_module_prefix(prefix):
    for module_to_nuke in [m for m in sys.modules if m.startswith(prefix)]:
        sys.modules.pop(module_to_nuke)


def reset_collections_loader_state(metapath_finder=None):
    _AnsibleCollectionFinder._remove()

    nuke_module_prefix('ansible_collections')
    nuke_module_prefix('ansible.modules')
    nuke_module_prefix('ansible.plugins')

    # FIXME: better to move this someplace else that gets cleaned up automatically?
    _AnsibleCollectionLoader._redirected_package_map = {}

    AnsibleCollectionConfig._default_collection = None
    AnsibleCollectionConfig._on_collection_load = _EventSource()

    if metapath_finder:
        metapath_finder._install()
