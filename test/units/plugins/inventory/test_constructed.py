# -*- coding: utf-8 -*-

# Copyright 2019 Alan Rominger <arominge@redhat.net>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

import pytest

from ansible.errors import AnsibleParserError
from ansible._internal._datatag._tags import TrustedAsTemplate
from ansible.plugins.inventory.constructed import InventoryModule
from ansible.inventory.data import InventoryData
from ansible.template import Templar
from units.test_utils.controller.display import emits_warnings


@pytest.fixture()
def inventory_module():
    r = InventoryModule()
    r.inventory = InventoryData()
    r.templar = Templar()
    r._options = {'leading_separator': True}
    return r


def _trust(value):
    """Recursively apply TrustedAsTemplate to input (simulating what would come out of a trusted input source like the dataloader YAML/JSON/ini parser)"""
    if isinstance(value, dict):
        return {_trust(k): _trust(v) for k, v in value.items()}

    if isinstance(value, list):
        return [_trust(item) for item in value]

    if isinstance(value, str):
        return TrustedAsTemplate().tag(value)

    return value


def test_group_by_value_only(inventory_module):
    inventory_module.inventory.add_host('foohost')
    inventory_module.inventory.set_variable('foohost', 'bar', 'my_group_name')
    host = inventory_module.inventory.get_host('foohost')
    keyed_groups = [
        {
            'prefix': '',
            'separator': '',
            'key': 'bar'
        }
    ]
    inventory_module._add_host_to_keyed_groups(
        _trust(keyed_groups), host.vars, host.name, strict=False
    )
    assert 'my_group_name' in inventory_module.inventory.groups
    group = inventory_module.inventory.groups['my_group_name']
    assert group.hosts == [host]


def test_keyed_group_separator(inventory_module):
    inventory_module.inventory.add_host('farm')
    inventory_module.inventory.set_variable('farm', 'farmer', 'mcdonald')
    inventory_module.inventory.set_variable('farm', 'barn', {'cow': 'betsy'})
    host = inventory_module.inventory.get_host('farm')
    keyed_groups = [
        {
            'prefix': 'farmer',
            'separator': '_old_',
            'key': 'farmer'
        },
        {
            'separator': 'mmmmmmmmmm',
            'key': 'barn'
        }
    ]
    inventory_module._add_host_to_keyed_groups(
        _trust(keyed_groups), host.vars, host.name, strict=False
    )
    for group_name in ('farmer_old_mcdonald', 'mmmmmmmmmmcowmmmmmmmmmmbetsy'):
        assert group_name in inventory_module.inventory.groups
        group = inventory_module.inventory.groups[group_name]
        assert group.hosts == [host]


def test_keyed_group_empty_construction(inventory_module):
    inventory_module.inventory.add_host('farm')
    inventory_module.inventory.set_variable('farm', 'barn', {})
    host = inventory_module.inventory.get_host('farm')
    keyed_groups = [
        {
            'separator': 'mmmmmmmmmm',
            'key': 'barn'
        }
    ]
    inventory_module._add_host_to_keyed_groups(
        _trust(keyed_groups), host.vars, host.name, strict=True
    )
    assert host.groups == []


def test_keyed_group_host_confusion(inventory_module):
    inventory_module.inventory.add_host('cow')
    inventory_module.inventory.add_group('cow')
    host = inventory_module.inventory.get_host('cow')
    host.vars['species'] = 'cow'
    keyed_groups = [
        {
            'separator': '',
            'prefix': '',
            'key': 'species'
        }
    ]
    inventory_module._add_host_to_keyed_groups(
        _trust(keyed_groups), host.vars, host.name, strict=True
    )
    group = inventory_module.inventory.groups['cow']
    # group cow has host of cow
    assert group.hosts == [host]


def test_keyed_parent_groups(inventory_module):
    inventory_module.inventory.add_host('web1')
    inventory_module.inventory.add_host('web2')
    inventory_module.inventory.set_variable('web1', 'region', 'japan')
    inventory_module.inventory.set_variable('web2', 'region', 'japan')
    host1 = inventory_module.inventory.get_host('web1')
    host2 = inventory_module.inventory.get_host('web2')
    keyed_groups = [
        {
            'prefix': 'region',
            'key': 'region',
            'parent_group': 'region_list'
        }
    ]
    for host in [host1, host2]:
        inventory_module._add_host_to_keyed_groups(
            _trust(keyed_groups), host.vars, host.name, strict=False
        )
    assert 'region_japan' in inventory_module.inventory.groups
    assert 'region_list' in inventory_module.inventory.groups
    region_group = inventory_module.inventory.groups['region_japan']
    all_regions = inventory_module.inventory.groups['region_list']
    assert all_regions.child_groups == [region_group]
    assert region_group.hosts == [host1, host2]


def test_parent_group_templating(inventory_module):
    inventory_module.inventory.add_host('cow')
    inventory_module.inventory.set_variable('cow', 'sound', 'mmmmmmmmmm')
    inventory_module.inventory.set_variable('cow', 'nickname', 'betsy')
    host = inventory_module.inventory.get_host('cow')
    keyed_groups = [
        {
            'key': 'sound',
            'prefix': 'sound',
            'parent_group': '{{ nickname }}'
        },
        {
            'key': 'nickname',
            'prefix': '',
            'separator': '',
            'parent_group': 'nickname'  # statically-named parent group, conflicting with hostvar
        },
        {
            'key': 'nickname',
            'separator': '',
            'parent_group': '{{ location | default("field") }}'
        },
        {
            # duplicate this one to ensure it doesn't show up in parents more than once
            'key': 'nickname',
            'separator': '',
            'parent_group': '{{ location | default("field") }}'
        },
        {
            'key': 'nickname',
            'prefix': 'omitted_parent',
            'parent_group': '{{ omit }}'
        }

    ]
    inventory_module._add_host_to_keyed_groups(
        _trust(keyed_groups), host.vars, host.name, strict=True
    )
    # first keyed group, "betsy" is a parent group name dynamically generated
    betsys_group = inventory_module.inventory.groups['betsy']
    assert [child.name for child in betsys_group.child_groups] == ['sound_mmmmmmmmmm']
    # second keyed group, "nickname" is a statically-named root group
    nicknames_group = inventory_module.inventory.groups['nickname']
    assert [child.name for child in nicknames_group.child_groups] == ['betsy']
    # second keyed group actually generated the parent group of the first keyed group
    assert nicknames_group.child_groups == [betsys_group]
    # assert that these are, in fact, the same object
    assert nicknames_group.child_groups[0] is betsys_group
    # "betsy" has two parents
    locations_group = inventory_module.inventory.groups['field']
    assert [child.name for child in locations_group.child_groups] == ['betsy']
    assert len(inventory_module.inventory.groups['betsy'].parent_groups) == 2
    assert set(inventory_module.inventory.groups['betsy'].parent_groups) == {locations_group, nicknames_group}


def test_parent_group_templating_error(inventory_module):
    inventory_module.inventory.add_host('cow')
    inventory_module.inventory.set_variable('cow', 'nickname', 'betsy')
    host = inventory_module.inventory.get_host('cow')
    keyed_groups = [
        {
            'key': 'nickname',
            'separator': '',
            'parent_group': '{{ location.barn-yard }}'
        }
    ]
    with pytest.raises(AnsibleParserError) as ex:
        inventory_module._add_host_to_keyed_groups(
            _trust(keyed_groups), host.vars, host.name, strict=True
        )
    assert 'Could not generate parent group' in str(ex.value)
    # invalid parent group did not raise an exception with strict=False
    inventory_module._add_host_to_keyed_groups(
        _trust(keyed_groups), host.vars, host.name, strict=False
    )
    # assert group was never added with invalid parent
    assert 'betsy' not in inventory_module.inventory.groups


def test_keyed_group_exclusive_argument(inventory_module):
    inventory_module.inventory.add_host('cow')
    inventory_module.inventory.set_variable('cow', 'nickname', 'betsy')
    host = inventory_module.inventory.get_host('cow')
    keyed_groups = [
        {
            'key': 'nickname',
            'separator': '_',
            'default_value': 'default_value_name',
            'trailing_separator': True
        }
    ]
    with pytest.raises(AnsibleParserError) as ex:
        inventory_module._add_host_to_keyed_groups(
            _trust(keyed_groups), host.vars, host.name, strict=True
        )
    assert 'parameters are mutually exclusive' in str(ex.value)


def test_keyed_group_empty_value(inventory_module):
    inventory_module.inventory.add_host('server0')
    inventory_module.inventory.set_variable('server0', 'tags', {'environment': 'prod', 'status': ''})
    host = inventory_module.inventory.get_host('server0')
    keyed_groups = [
        {
            'prefix': 'tag',
            'separator': '_',
            'key': 'tags'
        }
    ]
    inventory_module._add_host_to_keyed_groups(
        _trust(keyed_groups), host.vars, host.name, strict=False
    )
    for group_name in ('tag_environment_prod', 'tag_status_'):
        assert group_name in inventory_module.inventory.groups


def test_keyed_group_dict_with_default_value(inventory_module):
    inventory_module.inventory.add_host('server0')
    inventory_module.inventory.set_variable('server0', 'tags', {'environment': 'prod', 'status': ''})
    host = inventory_module.inventory.get_host('server0')
    keyed_groups = [
        {
            'prefix': 'tag',
            'separator': '_',
            'key': 'tags',
            'default_value': 'running'
        }
    ]
    inventory_module._add_host_to_keyed_groups(
        _trust(keyed_groups), host.vars, host.name, strict=False
    )
    for group_name in ('tag_environment_prod', 'tag_status_running'):
        assert group_name in inventory_module.inventory.groups


def test_keyed_group_str_no_default_value(inventory_module):
    inventory_module.inventory.add_host('server0')
    inventory_module.inventory.set_variable('server0', 'tags', '')
    host = inventory_module.inventory.get_host('server0')
    keyed_groups = [
        {
            'prefix': 'tag',
            'separator': '_',
            'key': 'tags'
        }
    ]
    inventory_module._add_host_to_keyed_groups(
        _trust(keyed_groups), host.vars, host.name, strict=False
    )
    # when the value is an empty string. this group is not generated
    assert "tag_" not in inventory_module.inventory.groups


def test_keyed_group_str_with_default_value(inventory_module):
    inventory_module.inventory.add_host('server0')
    inventory_module.inventory.set_variable('server0', 'tags', '')
    host = inventory_module.inventory.get_host('server0')
    keyed_groups = [
        {
            'prefix': 'tag',
            'separator': '_',
            'key': 'tags',
            'default_value': 'running'
        }
    ]
    inventory_module._add_host_to_keyed_groups(
        _trust(keyed_groups), host.vars, host.name, strict=False
    )
    assert "tag_running" in inventory_module.inventory.groups


def test_keyed_group_list_with_default_value(inventory_module):
    inventory_module.inventory.add_host('server0')
    inventory_module.inventory.set_variable('server0', 'tags', ['test', ''])
    host = inventory_module.inventory.get_host('server0')
    keyed_groups = [
        {
            'prefix': 'tag',
            'separator': '_',
            'key': 'tags',
            'default_value': 'prod'
        }
    ]
    inventory_module._add_host_to_keyed_groups(
        _trust(keyed_groups), host.vars, host.name, strict=False
    )
    for group_name in ('tag_test', 'tag_prod'):
        assert group_name in inventory_module.inventory.groups


def test_keyed_group_with_trailing_separator(inventory_module):
    inventory_module.inventory.add_host('server0')
    inventory_module.inventory.set_variable('server0', 'tags', {'environment': 'prod', 'status': ''})
    host = inventory_module.inventory.get_host('server0')
    keyed_groups = [
        {
            'prefix': 'tag',
            'separator': '_',
            'key': 'tags',
            'trailing_separator': False
        }
    ]
    inventory_module._add_host_to_keyed_groups(
        _trust(keyed_groups), host.vars, host.name, strict=False
    )
    for group_name in ('tag_environment_prod', 'tag_status'):
        assert group_name in inventory_module.inventory.groups


def test_sanitize_group_name_valid_unchanged() -> None:
    """Verify that group names with only valid characters pass through unchanged and emit no warning."""
    with emits_warnings(warning_pattern=[], allow_unmatched_message=False):
        assert InventoryModule._sanitize_group_name('valid_group') == 'valid_group'
        assert InventoryModule._sanitize_group_name('group123') == 'group123'


def test_sanitize_group_name_hyphen_emits_warning() -> None:
    """Verify that a group name containing a hyphen is normalized and a warning is emitted."""
    # TODO: also assert the rename detail line is present at -vvvv verbosity once
    # emits_warnings (or a sibling utility) gains support for verbose-level output assertions.
    with emits_warnings(warning_pattern=r'Invalid characters were found in group names'):
        result = InventoryModule._sanitize_group_name('qa-windows')
    assert result == 'qa_windows'


def test_add_host_to_composed_groups_warns_on_invalid_group_name(inventory_module: InventoryModule) -> None:
    """Verify that composing groups with an invalid name normalizes it and emits a warning."""
    inventory_module.inventory.add_host('myhost')
    host = inventory_module.inventory.get_host('myhost')
    groups = _trust({'qa-windows': 'True'})
    with emits_warnings(warning_pattern=r'Invalid characters were found in group names'):
        inventory_module._add_host_to_composed_groups(groups, host.vars, host.name, strict=True)
    assert 'qa_windows' in inventory_module.inventory.groups
    assert host in inventory_module.inventory.groups['qa_windows'].hosts


def test_add_host_to_keyed_groups_warns_on_invalid_group_name(inventory_module: InventoryModule) -> None:
    """Verify that keyed groups with an invalid prefix are normalized and a warning is emitted."""
    inventory_module.inventory.add_host('myhost')
    inventory_module.inventory.set_variable('myhost', 'os', 'windows')
    host = inventory_module.inventory.get_host('myhost')
    keyed_groups = _trust([{'prefix': 'qa-env', 'separator': '_', 'key': 'os'}])
    with emits_warnings(warning_pattern=r'Invalid characters were found in group names'):
        inventory_module._add_host_to_keyed_groups(keyed_groups, host.vars, host.name, strict=True)
    assert 'qa_env_windows' in inventory_module.inventory.groups
