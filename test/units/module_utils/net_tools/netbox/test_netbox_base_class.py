# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Bruno Inec (@sweenu) <bruno@inec.fr>
# Copyright: (c) 2019, Mikhail Yohman (@FragmentedPacket) <mikhail.yohman@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
import pytest

from units.compat import unittest
from ansible.module_utils.basic import AnsibleModule
from units.compat.mock import patch, MagicMock, Mock
from ansible.module_utils.net_tools.netbox.netbox_utils import NetboxModule
from ansible.module_utils.net_tools.netbox.netbox_dcim import NB_DEVICES


@pytest.fixture
def fixture_arg_spec():
    return {
        "netbox_url": "http://netbox.local/",
        "netbox_token": "0123456789",
        "data": {
            "name": "Test Device1",
            "device_role": "Core Switch",
            "device_type": "Cisco Switch",
            "manufacturer": "Cisco",
            "site": "Test Site",
            "asset_tag": "1001",
        },
        "state": "present",
        "validate_certs": False,
    }


@pytest.fixture
def normalized_data():
    return {
        "name": "Test Device1",
        "device_role": "core-switch",
        "device_type": "cisco-switch",
        "manufacturer": "cisco",
        "site": "test-site",
        "asset_tag": "1001",
    }


@pytest.fixture
def mock_ansible_module(fixture_arg_spec):
    module = MagicMock(name="AnsibleModule")
    module.check_mode = False
    module.params = fixture_arg_spec

    return module


@pytest.fixture
def find_ids_return():
    return {
        "name": "Test Device1",
        "device_role": 1,
        "device_type": 1,
        "manufacturer": 1,
        "site": 1,
        "asset_tag": "1001",
    }


@pytest.fixture
def nb_obj_mock(mocker, normalized_data):
    nb_obj = mocker.Mock(name="nb_obj_mock")
    nb_obj.delete.return_value = True
    nb_obj.update.return_value = True
    nb_obj.update.side_effect = normalized_data.update
    nb_obj.serialize.return_value = normalized_data

    return nb_obj


@pytest.fixture
def endpoint_mock(mocker, nb_obj_mock):
    endpoint = mocker.Mock(name="endpoint_mock")
    endpoint.create.return_value = nb_obj_mock

    return endpoint


@pytest.fixture
def on_creation_diff(mock_netbox_module):
    return mock_netbox_module._build_diff(
        before={"state": "absent"}, after={"state": "present"}
    )


@pytest.fixture
def on_deletion_diff(mock_netbox_module):
    return mock_netbox_module._build_diff(
        before={"state": "present"}, after={"state": "absent"}
    )


@pytest.fixture
def mock_netbox_module(mocker, mock_ansible_module, find_ids_return):
    find_ids = mocker.patch(
        "ansible.module_utils.net_tools.netbox.netbox_utils.NetboxModule._find_ids"
    )
    find_ids.return_value = find_ids_return
    netbox = NetboxModule(mock_ansible_module, NB_DEVICES, nb_client=True)

    return netbox


@pytest.fixture
def changed_serialized_obj(nb_obj_mock):
    changed_serialized_obj = nb_obj_mock.serialize().copy()
    changed_serialized_obj["name"] += " (modified)"

    return changed_serialized_obj


@pytest.fixture
def on_update_diff(mock_netbox_module, nb_obj_mock, changed_serialized_obj):
    return mock_netbox_module._build_diff(
        before={"name": "Test Device1"}, after={"name": "Test Device1 (modified)"}
    )


def test_init(mock_netbox_module, find_ids_return):
    """Test that we can get a real mock NetboxModule."""
    assert mock_netbox_module.data == find_ids_return


def test_normalize_data_returns_correct_data(mock_netbox_module):
    data = {
        "cluster": "Test Cluster",
        "device": "Test Device",
        "device_role": "Core Switch",
        "device_type": "Cisco Switch",
        "manufacturer": "Cisco",
        "nat_inside": "192.168.1.1/24",
        "nat_outside": "192.168.10.1/24",
        "platform": "Cisco IOS",
        "primary_ip": "192.168.1.1/24",
        "primary_ip4": "192.168.1.1/24",
        "primary_ip6": "2001::1/128",
        "rack": "Test Rack",
        "region": "Test Region_1",
        "role": "TEst Role-1",
        "site": "Test Site",
        "tenant": "Test Tenant",
        "tenant_group": "Test Tenant Group",
        "time_zone": "America/Los Angeles",
        "vlan": "Test VLAN",
        "vlan_group": "Test VLAN Group",
        "vrf": "Test VRF",
    }
    norm_data_expected = {
        "cluster": "Test Cluster",
        "device": "Test Device",
        "device_role": "core-switch",
        "device_type": "cisco-switch",
        "manufacturer": "cisco",
        "nat_inside": "192.168.1.1/24",
        "nat_outside": "192.168.10.1/24",
        "platform": "cisco-ios",
        "primary_ip": "192.168.1.1/24",
        "primary_ip4": "192.168.1.1/24",
        "primary_ip6": "2001::1/128",
        "rack": "Test Rack",
        "region": "test-region_1",
        "role": "test-role-1",
        "site": "test-site",
        "tenant": "Test Tenant",
        "tenant_group": "test-tenant-group",
        "time_zone": "America/Los_Angeles",
        "vlan": "Test VLAN",
        "vlan_group": "test-vlan-group",
        "vrf": "Test VRF",
    }
    norm_data = mock_netbox_module._normalize_data(data)

    assert norm_data == norm_data_expected


def test_to_slug_returns_valid_slug(mock_netbox_module):
    not_slug = "Test device-1_2"
    expected_slug = "test-device-1_2"
    convert_to_slug = mock_netbox_module._to_slug(not_slug)

    assert expected_slug == convert_to_slug


@pytest.mark.parametrize(
    "endpoint, app",
    [
        ("devices", "dcim"),
        ("device_roles", "dcim"),
        ("device_types", "dcim"),
        ("interfaces", "dcim"),
        ("platforms", "dcim"),
        ("racks", "dcim"),
        ("regions", "dcim"),
        ("sites", "dcim"),
        ("ip_addresses", "ipam"),
        ("prefixes", "ipam"),
        ("roles", "ipam"),
        ("vlans", "ipam"),
        ("vlan_groups", "ipam"),
        ("vrfs", "ipam"),
        ("tenants", "tenancy"),
        ("tenant_groups", "tenancy"),
        ("clusters", "virtualization"),
    ],
)
def test_find_app_returns_valid_app(mock_netbox_module, endpoint, app):
    assert app == mock_netbox_module._find_app(endpoint), "app: %s, endpoint: %s" % (
        app,
        endpoint,
    )


def test_build_diff_returns_valid_diff(mock_netbox_module):
    before = "The state before"
    after = {"A": "more", "complicated": "state"}
    diff = mock_netbox_module._build_diff(before=before, after=after)

    assert diff == {"before": before, "after": after}


def test_create_netbox_object_check_mode_false(
    mock_netbox_module, endpoint_mock, normalized_data, on_creation_diff
):
    return_value = endpoint_mock.create().serialize()
    serialized_obj, diff = mock_netbox_module._create_netbox_object(
        endpoint_mock, normalized_data
    )
    assert endpoint_mock.create.called_once_with(normalized_data)
    assert serialized_obj.serialize() == return_value
    assert diff == on_creation_diff


def test_create_netbox_object_check_mode_true(
    mock_netbox_module, endpoint_mock, normalized_data, on_creation_diff
):
    mock_netbox_module.check_mode = True
    serialized_obj, diff = mock_netbox_module._create_netbox_object(
        endpoint_mock, normalized_data
    )
    assert endpoint_mock.create.not_called()
    assert serialized_obj == normalized_data
    assert diff == on_creation_diff


def test_delete_netbox_object_check_mode_false(
    mock_netbox_module, nb_obj_mock, on_deletion_diff
):
    mock_netbox_module.nb_object = nb_obj_mock
    diff = mock_netbox_module._delete_netbox_object()
    assert nb_obj_mock.delete.called_once()
    assert diff == on_deletion_diff


def test_delete_netbox_object_check_mode_true(
    mock_netbox_module, nb_obj_mock, on_deletion_diff
):
    mock_netbox_module.check_mode = True
    mock_netbox_module.nb_object = nb_obj_mock
    diff = mock_netbox_module._delete_netbox_object()
    assert nb_obj_mock.delete.not_called()
    assert diff == on_deletion_diff


def test_update_netbox_object_no_changes(mock_netbox_module, nb_obj_mock):
    mock_netbox_module.nb_object = nb_obj_mock
    unchanged_data = nb_obj_mock.serialize()
    serialized_object, diff = mock_netbox_module._update_netbox_object(unchanged_data)
    assert nb_obj_mock.update.not_called()
    assert serialized_object == unchanged_data
    assert diff is None


def test_update_netbox_object_with_changes_check_mode_false(
    mock_netbox_module, nb_obj_mock, changed_serialized_obj, on_update_diff
):
    mock_netbox_module.nb_object = nb_obj_mock
    serialized_obj, diff = mock_netbox_module._update_netbox_object(
        changed_serialized_obj
    )
    assert nb_obj_mock.update.called_once_with(changed_serialized_obj)
    assert serialized_obj == nb_obj_mock.serialize()
    assert diff == on_update_diff


def test_update_netbox_object_with_changes_check_mode_true(
    mock_netbox_module, nb_obj_mock, changed_serialized_obj, on_update_diff
):
    mock_netbox_module.nb_object = nb_obj_mock
    mock_netbox_module.check_mode = True
    updated_serialized_obj = nb_obj_mock.serialize().copy()
    updated_serialized_obj.update(changed_serialized_obj)

    serialized_obj, diff = mock_netbox_module._update_netbox_object(
        changed_serialized_obj
    )
    assert nb_obj_mock.update.not_called()
    assert serialized_obj == updated_serialized_obj
    assert diff == on_update_diff


@pytest.mark.parametrize(
    "endpoint, data, expected",
    [
        ("devices", {"status": "Active", "face": "Front"}, {"status": 1, "face": 0}),
        (
            "interfaces",
            {"form_factor": "1000base-t (1ge)", "mode": "access"},
            {"form_factor": 1000, "mode": 100},
        ),
        (
            "ip_addresses",
            {"status": "Deprecated", "role": "loopback"},
            {"status": 3, "role": 10},
        ),
        ("prefixes", {"status": "Active"}, {"status": 1}),
        ("sites", {"status": "Retired"}, {"status": 4}),
    ],
)
def test_change_choices_id(mock_netbox_module, endpoint, data, expected):
    new_data = mock_netbox_module._change_choices_id(endpoint, data)
    assert new_data == expected


@pytest.mark.parametrize(
    "parent, module_data, expected",
    [
        (
            "device",
            {"name": "Test Device", "status": "Active"},
            {"name": "Test Device"},
        ),
        (
            "interface",
            {"name": "GigabitEthernet1", "device": "Test Device", "form_factor": 1000},
            {"name": "GigabitEthernet1", "device_id": 1},
        ),
        (
            "ip_address",
            {
                "address": "192.168.1.1/24",
                "vrf": "Test VRF",
                "description": "Test description",
            },
            {"address": "192.168.1.1/24", "vrf_id": 1},
        ),
        (
            "prefix",
            {"prefix": "10.10.10.0/24", "vrf": "Test VRF", "status": "Reserved"},
            {"prefix": "10.10.10.0/24", "vrf_id": 1},
        ),
        ("prefix", {"parent": "10.10.0.0/16"}, {"prefix": "10.10.0.0/16"}),
        (
            "site",
            {"name": "Test Site", "asn": 65000, "contact_name": "John Smith"},
            {"name": "Test Site"},
        ),
    ],
)
def test_build_query_params_no_child(
    mock_netbox_module, mocker, parent, module_data, expected
):
    get_query_param_id = mocker.patch(
        "ansible.module_utils.net_tools.netbox.netbox_utils.NetboxModule._get_query_param_id"
    )
    get_query_param_id.return_value = 1
    query_params = mock_netbox_module._build_query_params(parent, module_data)
    assert query_params == expected


@pytest.mark.parametrize(
    "parent, module_data, child, expected",
    [
        (
            "lag",
            {"name": "GigabitEthernet1", "device": 1, "lag": {"name": "port-channel1"}},
            {"name": "port-channel1"},
            {"device_id": 1, "form_factor": 200, "name": "port-channel1"},
        ),
        (
            "lag",
            {
                "name": "GigabitEthernet1",
                "device": "Test Device",
                "lag": {"name": "port-channel1"},
            },
            {"name": "port-channel1"},
            {"device": "Test Device", "form_factor": 200, "name": "port-channel1"},
        ),
        (
            "nat_inside",
            {
                "address": "10.10.10.1/24",
                "nat_inside": {"address": "192.168.1.1/24", "vrf": "Test VRF"},
            },
            {"address": "192.168.1.1/24", "vrf": "Test VRF"},
            {"address": "192.168.1.1/24", "vrf_id": 1},
        ),
        (
            "vlan",
            {
                "prefix": "10.10.10.0/24",
                "description": "Test Prefix",
                "vlan": {
                    "name": "Test VLAN",
                    "site": "Test Site",
                    "tenant": "Test Tenant",
                    "vlan_group": "Test VLAN group",
                },
            },
            {
                "name": "Test VLAN",
                "site": "Test Site",
                "tenant": "Test Tenant",
                "vlan_group": "Test VLAN group",
            },
            {"name": "Test VLAN", "site_id": 1, "tenant_id": 1, "vlan_group_id": 1},
        ),
        (
            "untagged_vlan",
            {
                "prefix": "10.10.10.0/24",
                "description": "Test Prefix",
                "untagged_vlan": {"name": "Test VLAN", "site": "Test Site"},
            },
            {"name": "Test VLAN", "site": "Test Site"},
            {"name": "Test VLAN", "site_id": 1},
        ),
    ],
)
def test_build_query_params_child(
    mock_netbox_module, mocker, parent, module_data, child, expected
):
    get_query_param_id = mocker.patch(
        "ansible.module_utils.net_tools.netbox.netbox_utils.NetboxModule._get_query_param_id"
    )
    get_query_param_id.return_value = 1
    query_params = mock_netbox_module._build_query_params(parent, module_data, child)
    assert query_params == expected
