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
import json
from collections import namedtuple

linode_apiv4 = pytest.importorskip('linode_api4')
mandatory_py_version = pytest.mark.skipif(
    sys.version_info < (2, 7),
    reason='The linode_api4 dependency requires python2.7 or higher'
)


from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.inventory.linode import InventoryModule

instances_json = """
{
  "data": [
    {
      "group": "test",
      "hypervisor": "kvm",
      "id": 123,
      "status": "running",
      "type": "g5-standard-1",
      "alerts": {
        "network_in": 5,
        "network_out": 5,
        "cpu": 90,
        "transfer_quota": 80,
        "io": 5000
      },
      "label": "linode123",
      "backups": {
        "enabled": true,
        "schedule": {
          "window": "W02",
          "day": "Scheduling"
        }
      },
      "specs": {
        "memory": 2048,
        "disk": 30720,
        "vcpus": 1,
        "transfer": 2000
      },
      "ipv6": "1234:abcd::1234:abcd:89ef:67cd/64",
      "created": "2017-01-01T00:00:00",
      "region": "us-east-1a",
      "ipv4": [
        "123.45.67.89",
        "192.168.45.67"
      ],
      "updated": "2017-01-01T00:00:00",
      "image": "linode/ubuntu17.04",
      "tags": ["something"]
    },
    {
      "group": "test",
      "hypervisor": "kvm",
      "id": 456,
      "status": "running",
      "type": "g5-standard-1",
      "alerts": {
        "network_in": 5,
        "network_out": 5,
        "cpu": 90,
        "transfer_quota": 80,
        "io": 5000
      },
      "label": "linode456",
      "backups": {
        "enabled": false,
        "schedule": {
          "window": null,
          "day": null
        }
      },
      "specs": {
        "memory": 2048,
        "disk": 30720,
        "vcpus": 1,
        "transfer": 2000
      },
      "ipv6": "1234:abcd::1234:abcd:89ef:67cd/64",
      "created": "2017-01-01T00:00:00",
      "region": "us-east-1a",
      "ipv4": [
        "123.45.67.89",
        "192.168.45.68"
      ],
      "updated": "2017-01-01T00:00:00",
      "image": "linode/debian9",
      "tags": []
    }
  ]
}
"""

# converts instance_json dict into python objects
instances = json.loads(instances_json, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))


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
    regions, types, instance_access = inventory._get_user_options({})
    assert regions == types == []
    assert instance_access == 'hostname'


def test_config_user_options(inventory):
    regions, types, instance_access = inventory._get_user_options({
        'regions': ['eu-west', 'us-east'],
        'types': ['g5-standard-2', 'g6-standard-2'],
        'instance_access': 'public_ip',
    })

    assert regions == ['eu-west', 'us-east']
    assert types == ['g5-standard-2', 'g6-standard-2']
    assert instance_access == 'public_ip'


def test_verify_file_bad_config(inventory):
    assert inventory.verify_file('foobar.linde.yml') is False


def test_get_instance_ip_public(inventory):
    instance = instances.data[0]
    assert inventory._get_instance_ip(instance, private=False) == '123.45.67.89'


def test_get_instance_ip_private(inventory):
    instance = instances.data[0]
    assert inventory._get_instance_ip(instance, private=True) == '192.168.45.67'
