# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Bruno Inec (@sweenu) <bruno@inec.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
import pytest

from ansible.module_utils.net_tools.netbox.netbox_utils import (
    QUERY_TYPES,
    _build_diff,
    create_netbox_object,
    delete_netbox_object,
    update_netbox_object,
    normalize_data,
)


def test_normalize_data():
    assert "name" not in QUERY_TYPES
    assert QUERY_TYPES.get("rack") == "slug"
    assert QUERY_TYPES.get("primary_ip") != "slug"

    raw_data = {
        "name": "Some name",
        "primary_ip": "10.3.72.74/31",
        "rack": "Some rack",
    }
    normalized_data = raw_data.copy()
    normalized_data["rack"] = "some-rack"

    assert normalize_data(raw_data) == normalized_data


def test_build_diff():
    before = "The state before"
    after = {"A": "more", "complicated": "state"}
    diff = _build_diff(before=before, after=after)
    assert diff == {"before": before, "after": after}


@pytest.fixture
def nb_obj_mock(mocker):
    serialized_object = {"The serialized": "object"}
    nb_obj = mocker.Mock(name="nb_obj_mock")
    nb_obj.delete.return_value = True
    nb_obj.update.return_value = True
    nb_obj.update.side_effect = serialized_object.update
    nb_obj.serialize.return_value = serialized_object

    return nb_obj


@pytest.fixture
def endpoint_mock(mocker, nb_obj_mock):
    endpoint = mocker.Mock(name="endpoint_mock")
    endpoint.create.return_value = nb_obj_mock

    return endpoint


@pytest.fixture
def on_creation_diff():
    return _build_diff(before={"state": "absent"}, after={"state": "present"})


@pytest.fixture
def on_deletion_diff():
    return _build_diff(before={"state": "present"}, after={"state": "absent"})


@pytest.fixture
def data():
    return {"name": "Some Netbox object name"}


def test_create_netbox_object(endpoint_mock, data, on_creation_diff):
    return_value = endpoint_mock.create().serialize()

    serialized_obj, diff = create_netbox_object(
        endpoint_mock, data, check_mode=False
    )
    assert endpoint_mock.create.called_once_with(data)
    assert serialized_obj == return_value
    assert diff == on_creation_diff


def test_create_netbox_object_in_check_mode(endpoint_mock, data, on_creation_diff):
    serialized_obj, diff = create_netbox_object(
        endpoint_mock, data, check_mode=True
    )
    assert endpoint_mock.create.not_called()
    assert serialized_obj == data
    assert diff == on_creation_diff


def test_delete_netbox_object(nb_obj_mock, on_deletion_diff):
    serialized_obj, diff = delete_netbox_object(nb_obj_mock, check_mode=False)
    assert nb_obj_mock.delete.called_once()
    assert serialized_obj == nb_obj_mock.serialize()
    assert diff == on_deletion_diff


def test_delete_netbox_object_in_check_mode(nb_obj_mock, on_deletion_diff):
    serialized_obj, diff = delete_netbox_object(nb_obj_mock, check_mode=True)
    assert nb_obj_mock.delete.not_called()
    assert serialized_obj == nb_obj_mock.serialize()
    assert diff == on_deletion_diff


def test_update_netbox_object_no_changes(nb_obj_mock):
    unchanged_data = nb_obj_mock.serialize()
    serialized_obj, diff = update_netbox_object(nb_obj_mock, unchanged_data, check_mode=True)
    assert nb_obj_mock.update.not_called()
    assert serialized_obj == unchanged_data
    assert diff is None


@pytest.fixture
def changed_serialized_obj(nb_obj_mock):
    changed_serialized_obj = nb_obj_mock.serialize().copy()
    changed_serialized_obj[list(changed_serialized_obj.keys())[0]] += " (modified)"

    return changed_serialized_obj


@pytest.fixture
def on_update_diff(nb_obj_mock, changed_serialized_obj):
    return _build_diff(before=nb_obj_mock.serialize().copy(), after=changed_serialized_obj)


def test_update_netbox_object_with_changes(
    nb_obj_mock, changed_serialized_obj, on_update_diff
):
    serialized_obj, diff = update_netbox_object(
        nb_obj_mock, changed_serialized_obj, check_mode=False
    )
    assert nb_obj_mock.update.called_once_with(changed_serialized_obj)
    assert serialized_obj == nb_obj_mock.serialize()
    assert diff == on_update_diff


def test_update_netbox_object_with_changes_in_check_mode(
    nb_obj_mock, changed_serialized_obj, on_update_diff
):
    updated_serialized_obj = nb_obj_mock.serialize().copy()
    updated_serialized_obj.update(changed_serialized_obj)

    serialized_obj, diff = update_netbox_object(
        nb_obj_mock, changed_serialized_obj, check_mode=True
    )
    assert nb_obj_mock.update.not_called()

    assert serialized_obj == updated_serialized_obj
    assert diff == on_update_diff
