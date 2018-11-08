# -*- coding: utf-8 -*-

# Copyright 2018 Luke Murphy <lukewm@riseup.net>
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
import sys

linode_apiv4 = pytest.importorskip('linode_api4')
mandatory_py_version = pytest.mark.skipif(
    sys.version_info < (2, 7),
    reason='The linode_api4 dependency requires python2.7 or higher'
)


from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.inventory.linode import InventoryModule


@pytest.fixture(scope="module")
def inventory():
    return InventoryModule()


def test_access_token_lookup(inventory):
    inventory._options = {'access_token': None}
    with pytest.raises(AnsibleError) as error_message:
        inventory._build_client()
        assert 'Could not retrieve Linode access token' in error_message


def test_validate_option(inventory):
    assert ['eu-west'] == inventory._validate_option('regions', list, 'eu-west')
    assert ['eu-west'] == inventory._validate_option('regions', list, ['eu-west'])


def test_validation_option_bad_option(inventory):
    with pytest.raises(AnsibleParserError) as error_message:
        inventory._validate_option('regions', dict, [])
        assert "The option filters ([]) must be a <class 'dict'>" == error_message


def test_empty_config_query_options(inventory):
    regions, types = inventory._get_query_options({})
    assert regions == types == []


def test_conig_query_options(inventory):
    regions, types = inventory._get_query_options({
        'regions': ['eu-west', 'us-east'],
        'types': ['g5-standard-2', 'g6-standard-2'],
    })

    assert regions == ['eu-west', 'us-east']
    assert types == ['g5-standard-2', 'g6-standard-2']


def test_verify_file_bad_config(inventory):
    assert inventory.verify_file('foobar.linde.yml') is False
