# -*- coding: utf-8 -*-

# Copyright 2018 Lars Kellogg-Stedman <lars@redhat.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible.plugins.inventory.openstack import InventoryModule
from ansible.inventory.data import InventoryData
from ansible.template import Templar


config_data = {
    'plugin': 'openstack',
    'compose': {
        'composed_var': '"testvar-" + testvar',
    },
    'groups': {
        'testgroup': '"host" in inventory_hostname',
    },
    'keyed_groups':
    [{
        'prefix': 'keyed',
        'key': 'testvar',
    }]
}

hostvars = {
    'host0': {
        'inventory_hostname': 'host0',
        'testvar': '0',
    },
    'host1': {
        'inventory_hostname': 'host1',
        'testvar': '1',
    },
}


@pytest.fixture(scope="module")
def inventory():
    inventory = InventoryModule()
    inventory._config_data = config_data
    inventory.inventory = InventoryData()
    inventory.templar = Templar(loader=None)

    for host in hostvars:
        inventory.inventory.add_host(host)

    return inventory


def test_simple_groups(inventory):
    inventory._set_variables(hostvars, {})
    groups = inventory.inventory.get_groups_dict()
    assert 'testgroup' in groups
    assert len(groups['testgroup']) == len(hostvars)


def test_keyed_groups(inventory):
    inventory._set_variables(hostvars, {})
    assert 'keyed_0' in inventory.inventory.groups
    assert 'keyed_1' in inventory.inventory.groups


def test_composed_vars(inventory):
    inventory._set_variables(hostvars, {})

    for host in hostvars:
        assert host in inventory.inventory.hosts
        host = inventory.inventory.get_host(host)
        assert host.vars['composed_var'] == 'testvar-{testvar}'.format(**hostvars[host.name])
