# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Bruno Inec (@sweenu) <bruno@inec.fr>
# Copyright: (c) 2019, Alexander Stauch (@BlackestDawn) <blacke4dawn@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

pynbox = pytest.importorskip('pynetbox')

from units.compat import mock

import ansible.module_utils.net_tools.netbox.netbox_utils as netbox_module_utils


class AnsibleExitJson(BaseException):
    """Exception class to be raised by module.exit_json and caught by the test case"""
    pass


class AnsibleFailJson(BaseException):
    """Exception class to be raised by module.fail_json and caught by the test case"""
    pass


def exit_json(*args, **kwargs):
    """function to patch over exit_json; package return data into an exception"""
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):
    """function to patch over fail_json; package return data into an exception"""
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)


@pytest.fixture
def fake_ansible_module():
    ret = mock.Mock()
    ret.params = {
        'netbox_url': "http://some.url/",
        'netbox_token': "0123456789",
        'validate_certs': False,
        'check_mode': False,
        'data': {
            'testname': "Some mocked module",
            "name": "Some name",
            "primary_ip": "10.3.72.74/31",
            "rack": "Some rack"
        }
    }
    ret.tmpdir = None
    # ret.fail_json.side_effect = AnsibleFailJson()
    # ret.exit_json.side_effect = AnsibleExitJson()
    return ret


def fake_connect_to_api(module):
    return mock.Mock()


def fake_get_endpoint(self, endpoint):
    return endpoint


@pytest.fixture
def nb_obj_mock(mocker):
    serialized_object = {'testname': "Some mock object"}
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
    return netbox_module_utils.build_diff(before={"state": "absent"}, after={"state": "present"})


@pytest.fixture
def on_deletion_diff():
    return netbox_module_utils.build_diff(before={"state": "present"}, after={"state": "absent"})


@pytest.fixture
def data():
    return {"name": "Some Netbox object name"}


@pytest.fixture
def nb_class_mock(monkeypatch, fake_ansible_module):
    monkeypatch.setattr(netbox_module_utils, 'connect_to_api', fake_connect_to_api)
    monkeypatch.setattr(netbox_module_utils.PyNetboxBase, '_get_endpoint', fake_get_endpoint)
    pynb = netbox_module_utils.PyNetboxBase(fake_ansible_module)
    pynb.param_usage.update({
        'search': "testname",
        'success': "testname",
        'fail': "testname"
    })
    return pynb


def test_build_diff():
    before = {"The state before": 1}
    after = {"A": "more", "complicated": "state"}
    diff = netbox_module_utils.build_diff(before=before, after=after)
    assert diff == {"before": before, "after": after}


def test_normalize_data(nb_class_mock):
    normalized_data = nb_class_mock.params['data'].copy()
    normalized_data["rack"] = "some-rack"
    assert "name" not in netbox_module_utils.QUERY_TYPES
    assert netbox_module_utils.QUERY_TYPES.get("rack") == "slug"
    assert netbox_module_utils.QUERY_TYPES.get("primary_ip") != "slug"
    assert nb_class_mock.normalized_data == normalized_data


def test_create_netbox_object(endpoint_mock, data, on_creation_diff, nb_class_mock):
    return_value = endpoint_mock.create().serialize()
    nb_class_mock.check_mode = False
    nb_class_mock._create_object(data, endpoint_mock)
    serialized_obj = nb_class_mock.result['object']
    diff = nb_class_mock.result['diff']
    assert endpoint_mock.create.called_once_with(data)
    assert serialized_obj == return_value
    assert diff == on_creation_diff


def test_create_netbox_object_in_check_mode(
    endpoint_mock, data, on_creation_diff, nb_class_mock
):
    nb_class_mock.check_mode = True
    nb_class_mock._create_object(data, endpoint_mock)
    serialized_obj = nb_class_mock.result['object']
    diff = nb_class_mock.result['diff']
    assert endpoint_mock.create.not_called()
    assert serialized_obj == data
    assert diff == on_creation_diff


def test_delete_netbox_object(nb_obj_mock, on_deletion_diff, nb_class_mock):
    nb_class_mock.check_mode = False
    nb_class_mock._delete_object(nb_obj_mock)
    serialized_obj = nb_class_mock.result['object']
    diff = nb_class_mock.result['diff']
    assert nb_obj_mock.delete.called_once()
    assert serialized_obj == nb_obj_mock.serialize()
    assert diff == on_deletion_diff


def test_delete_netbox_object_in_check_mode(
    nb_obj_mock, on_deletion_diff, nb_class_mock
):
    nb_class_mock.check_mode = True
    nb_class_mock._delete_object(nb_obj_mock)
    serialized_obj = nb_class_mock.result['object']
    diff = nb_class_mock.result['diff']
    assert nb_obj_mock.delete.not_called()
    assert serialized_obj == nb_obj_mock.serialize()
    assert diff == on_deletion_diff


def test_update_netbox_object_no_changes(nb_obj_mock, nb_class_mock):
    unchanged_data = nb_obj_mock.serialize()
    nb_class_mock.check_mode = True
    nb_class_mock._update_object(nb_obj_mock, data=unchanged_data)
    serialized_obj = nb_class_mock.result['object']
    diff = nb_class_mock.result['diff']
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
    return netbox_module_utils.build_diff(before=nb_obj_mock.serialize().copy(), after=changed_serialized_obj)


def test_update_netbox_object_with_changes(
    nb_obj_mock, changed_serialized_obj, on_update_diff, nb_class_mock
):
    nb_class_mock.check_mode = False
    nb_class_mock._update_object(nb_obj_mock, data=changed_serialized_obj)
    serialized_obj = nb_class_mock.result['object']
    diff = nb_class_mock.result['diff']
    assert nb_obj_mock.update.called_once_with(changed_serialized_obj)
    assert serialized_obj == nb_obj_mock.serialize()
    assert diff == on_update_diff


def test_update_netbox_object_with_changes_in_check_mode(
    nb_obj_mock, changed_serialized_obj, on_update_diff, nb_class_mock
):
    updated_serialized_obj = nb_obj_mock.serialize().copy()
    updated_serialized_obj.update(changed_serialized_obj)
    nb_class_mock.check_mode = True
    nb_class_mock._update_object(nb_obj_mock, data=changed_serialized_obj)
    serialized_obj = nb_class_mock.result['object']
    diff = nb_class_mock.result['diff']
    assert nb_obj_mock.update.not_called()
    assert serialized_obj == updated_serialized_obj
    assert diff == on_update_diff
