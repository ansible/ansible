# -*- coding: utf-8 -*-
# (c) 2019, Sandeep Bandi <sandeepb@avinetworks.com>
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

import os
import pytest
import json

from units.compat.mock import patch, MagicMock

from ansible.errors import AnsibleError
from ansible.plugins.loader import lookup_loader
from ansible.plugins.lookup import avi


try:
    import builtins as __builtin__
except ImportError:
    import __builtin__


fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')

with open(fixture_path + '/avi.json') as json_file:
    data = json.load(json_file)


@pytest.fixture
def dummy_credentials():
    dummy_credentials = {}
    dummy_credentials['controller'] = "192.0.2.13"
    dummy_credentials['username'] = "admin"
    dummy_credentials['password'] = "password"
    dummy_credentials['api_version'] = "17.2.14"
    dummy_credentials['tenant'] = 'admin'
    return dummy_credentials


@pytest.fixture
def super_switcher(scope="function", autouse=True):
    # Mocking the inbuilt super as it is used in ApiSession initialization
    original_super = __builtin__.super
    __builtin__.super = MagicMock()
    yield
    # Revert the super to default state
    __builtin__.super = original_super


def test_lookup_multiple_obj(dummy_credentials):
    avi_lookup = lookup_loader.get('avi')
    avi_mock = MagicMock()
    avi_mock.return_value.get.return_value.json.return_value = data["mock_multiple_obj"]
    with patch.object(avi, 'ApiSession', avi_mock):
        retval = avi_lookup.run([], {}, avi_credentials=dummy_credentials,
                                obj_type="network")
        assert retval == data["mock_multiple_obj"]["results"]


def test_lookup_single_obj(dummy_credentials):
    avi_lookup = lookup_loader.get('avi')
    avi_mock = MagicMock()
    avi_mock.return_value.get_object_by_name.return_value = data["mock_single_obj"]
    with patch.object(avi, 'ApiSession', avi_mock):
        retval = avi_lookup.run([], {}, avi_credentials=dummy_credentials,
                                obj_type="network", obj_name='PG-123')
        assert retval[0] == data["mock_single_obj"]


def test_invalid_lookup(dummy_credentials):
    avi_lookup = lookup_loader.get('avi')
    avi_mock = MagicMock()
    with pytest.raises(AnsibleError):
        with patch.object(avi, 'ApiSession', avi_mock):
            avi_lookup.run([], {}, avi_credentials=dummy_credentials)
