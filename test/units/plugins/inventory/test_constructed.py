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

import pytest

from ansible.plugins.inventory.constructed import InventoryModule
from ansible.inventory.data import InventoryData
from ansible.template import Templar


@pytest.fixture(scope="module")
def inventory_module():
    r = InventoryModule()
    r.inventory = InventoryData()
    r.templar = Templar(None)
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
            'key': 'farmer',
            'unsafe': True
        },
        {
            'separator': 'mmmmmmmmmm',
            'key': 'barn',
            'unsafe': True
        }
    ]
    inventory_module._add_host_to_keyed_groups(
        keyed_groups, host.vars, host.name, strict=False
    )
    for group_name in ('farmer_old_mcdonald', 'mmmmmmmmmmcowmmmmmmmmmmbetsy'):
        assert group_name in inventory_module.inventory.groups
        group = inventory_module.inventory.groups[group_name]
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
