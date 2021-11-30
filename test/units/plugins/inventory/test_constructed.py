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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible.errors import AnsibleParserError
from ansible.plugins.inventory.constructed import InventoryModule
from ansible.inventory.data import InventoryData
from ansible.template import Templar


@pytest.fixture()
def inventory_module():
    r = InventoryModule()
    r.inventory = InventoryData()
    r.templar = Templar(None)
    r._options = {'leading_separator': True}
    return r


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
        keyed_groups, host.vars, host.name, strict=False
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
        keyed_groups, host.vars, host.name, strict=False
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
        keyed_groups, host.vars, host.name, strict=True
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
        keyed_groups, host.vars, host.name, strict=True
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
            keyed_groups, host.vars, host.name, strict=False
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
        }
    ]
    inventory_module._add_host_to_keyed_groups(
        keyed_groups, host.vars, host.name, strict=True
    )
    # first keyed group, "betsy" is a parent group name dynamically generated
    betsys_group = inventory_module.inventory.groups['betsy']
    assert [child.name for child in betsys_group.child_groups] == ['sound_mmmmmmmmmm']
    # second keyed group, "nickname" is a statically-named root group
    nicknames_group = inventory_module.inventory.groups['nickname']
    assert [child.name for child in nicknames_group.child_groups] == ['betsy']
    # second keyed group actually generated the parent group of the first keyed group
    # assert that these are, in fact, the same object
    assert nicknames_group.child_groups[0] == betsys_group
    # second keyed group has two parents
    locations_group = inventory_module.inventory.groups['field']
    assert [child.name for child in locations_group.child_groups] == ['betsy']


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
    with pytest.raises(AnsibleParserError) as err_message:
        inventory_module._add_host_to_keyed_groups(
            keyed_groups, host.vars, host.name, strict=True
        )
        assert 'Could not generate parent group' in err_message
    # invalid parent group did not raise an exception with strict=False
    inventory_module._add_host_to_keyed_groups(
        keyed_groups, host.vars, host.name, strict=False
    )
    # assert group was never added with invalid parent
    assert 'betsy' not in inventory_module.inventory.groups


def test_keyed_group_exclusive_argument(inventory_module):
    inventory_module.inventory.add_host('cow')
    inventory_module.inventory.set_variable('cow', 'nickname', 'betsy')
    host = inventory_module.inventory.get_host('cow')
    keyed_groups = [
        {
            'key': 'tag',
            'separator': '_',
            'default_value': 'default_value_name',
            'trailing_separator': True
        }
    ]
    with pytest.raises(AnsibleParserError) as err_message:
        inventory_module._add_host_to_keyed_groups(
            keyed_groups, host.vars, host.name, strict=True
        )
        assert 'parameters are mutually exclusive' in err_message


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
        keyed_groups, host.vars, host.name, strict=False
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
        keyed_groups, host.vars, host.name, strict=False
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
        keyed_groups, host.vars, host.name, strict=False
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
        keyed_groups, host.vars, host.name, strict=False
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
        keyed_groups, host.vars, host.name, strict=False
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
        keyed_groups, host.vars, host.name, strict=False
    )
    for group_name in ('tag_environment_prod', 'tag_status'):
        assert group_name in inventory_module.inventory.groups
