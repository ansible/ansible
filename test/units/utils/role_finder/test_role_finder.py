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
from units.mock.loader import DictDataLoader


ROLEFINDER_PLAYBOOK_DIR = os.path.dirname(__file__)


class TestAnsibleRoleFinder:

    def test_result(self):
        role_name = "abc"
        role_path = "/path/to/foo/bar/roles/abc"
        collection_name = "foo.bar"

        finder = AnsibleRoleFinder(ROLEFINDER_PLAYBOOK_DIR)

        r = finder.Result(role_name, role_path)
        assert r.role_name == role_name
        assert r.role_path == role_path
        assert r.collection_name is None
        assert not r.masked

        r = finder.Result(role_name, role_path, collection_name, True)
        assert r.role_name == role_name
        assert r.role_path == role_path
        assert r.collection_name == collection_name
        assert r.masked

        with pytest.raises(Exception, match="Role name should not contain FQCN"):
            r = finder.Result("foo.bar.abc", role_path)

    def test_standard_role_search_paths(self):
        ''' Test that the path order is what we expect at initialization. '''
        relative_role_dir = os.path.join(ROLEFINDER_PLAYBOOK_DIR, 'roles', 'role1')
        finder = AnsibleRoleFinder(ROLEFINDER_PLAYBOOK_DIR, relative_role_dir)
        expected = []
        expected.append(os.path.join(ROLEFINDER_PLAYBOOK_DIR, 'roles'))
        expected.extend(config.get_config_value('DEFAULT_ROLES_PATH'))
        expected.append(relative_role_dir)
        expected.append(ROLEFINDER_PLAYBOOK_DIR)
        assert finder.standard_role_search_paths == expected

    def test_set_templar(self):
        ''' Test setting the templating object. '''

        finder = AnsibleRoleFinder(ROLEFINDER_PLAYBOOK_DIR)

        # Should allow None
        finder.templar = None

        # Test with correct type
        finder.templar = Templar(None)

        # Test with wrong type
        with pytest.raises(TypeError, match="templar must be of type Templar"):
            finder.templar = "invalid"

    def test_find_first(self):
        ''' Test find first role that matches a role name. '''

        # Set search path for collections
        collection_finder = get_default_finder()
        reset_collections_loader_state(collection_finder)

        finder = AnsibleRoleFinder(ROLEFINDER_PLAYBOOK_DIR)

        # No match should return None
        result = finder.find_first('does-not-exist')
        assert result is None

        # Match should return a result object (no collection context given)
        result = finder.find_first('role1')
        assert isinstance(result, finder.Result)
        assert result.role_name == 'role1'
        assert result.role_path == os.path.join(ROLEFINDER_PLAYBOOK_DIR, 'roles', 'role1')
        assert result.collection_name is None
        assert not result.masked

        expected_collection_path = os.path.join(
            default_test_collection_paths[0],
            'ansible_collections', 'namespace1', 'collection1', 'roles',
            'role1')

        # Test matching when a collection context is supplied.
        result = finder.find_first('role1', ['namespace1.collection1'])
        assert result.role_name == 'role1'
        assert result.role_path == expected_collection_path
        assert result.collection_name == 'namespace1.collection1'
        assert not result.masked

        # A FQCN role should return collection context and simple role name in result
        result = finder.find_first('namespace1.collection1.role1')
        assert result.role_name == 'role1'
        assert result.role_path == expected_collection_path
        assert result.collection_name == 'namespace1.collection1'
        assert not result.masked

        # Test a role name including path info
        role = os.path.join(ROLEFINDER_PLAYBOOK_DIR, 'roles', 'role1')
        result = finder.find_first(role)
        assert result.role_name == 'role1'
        assert result.role_path == role
        assert result.collection_name is None
        assert not result.masked

    def test_find_first_with_templar(self):
        ''' Test find_first() using templated values. '''

        test_vars = dict(
            rname="role1",
            pb_base=ROLEFINDER_PLAYBOOK_DIR,
        )

        templar = Templar(DictDataLoader({}), variables=test_vars)
        finder = AnsibleRoleFinder("{{ pb_base }}", templar=templar)

        result = finder.find_first("{{ rname }}")
        assert result is not None
        assert result.role_name == 'role1'
        assert result.role_path == os.path.join(ROLEFINDER_PLAYBOOK_DIR, 'roles', 'role1')
        assert result.collection_name is None
        assert not result.masked


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
