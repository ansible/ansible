# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import pytest

from .FakeAnsibleModule import FakeAnsibleModule, ExitJsonException, FailJsonException
from .common import fake_xenapi_ref


def test_get_object_ref_xenapi_failure(mocker, fake_ansible_module, XenAPI, xenserver):
    """Tests catching of XenAPI failures."""
    mocked_xenapi = mocker.patch.object(XenAPI.Session, 'xenapi_request', side_effect=XenAPI.Failure('Fake XAPI method call error!'))

    with pytest.raises(FailJsonException) as exc_info:
        xenserver.get_object_ref(fake_ansible_module, "name")

    assert exc_info.value.kwargs['msg'] == "XAPI ERROR: Fake XAPI method call error!"


def test_get_object_ref_bad_uuid_and_name(mocker, fake_ansible_module, XenAPI, xenserver):
    """Tests failure on bad object uuid and/or name."""
    mocked_xenapi = mocker.patch.object(XenAPI.Session, 'xenapi_request')

    with pytest.raises(FailJsonException) as exc_info:
        xenserver.get_object_ref(fake_ansible_module, None, msg_prefix="Test: ")

    mocked_xenapi.xenapi_request.assert_not_called()
    assert exc_info.value.kwargs['msg'] == "Test: no valid name or UUID supplied for VM!"


def test_get_object_ref_uuid_not_found(mocker, fake_ansible_module, XenAPI, xenserver):
    """Tests when object is not found by uuid."""
    mocked_xenapi = mocker.patch.object(XenAPI.Session, 'xenapi_request', side_effect=XenAPI.Failure('Fake XAPI not found error!'))

    with pytest.raises(FailJsonException) as exc_info:
        xenserver.get_object_ref(fake_ansible_module, "name", uuid="fake-uuid", msg_prefix="Test: ")

    assert exc_info.value.kwargs['msg'] == "Test: VM with UUID 'fake-uuid' not found!"
    assert xenserver.get_object_ref(fake_ansible_module, "name", uuid="fake-uuid", fail=False, msg_prefix="Test: ") is None


def test_get_object_ref_name_not_found(mocker, fake_ansible_module, XenAPI, xenserver):
    """Tests when object is not found by name."""
    mocked_xenapi = mocker.patch.object(XenAPI.Session, 'xenapi_request', return_value=[])

    with pytest.raises(FailJsonException) as exc_info:
        xenserver.get_object_ref(fake_ansible_module, "name", msg_prefix="Test: ")

    assert exc_info.value.kwargs['msg'] == "Test: VM with name 'name' not found!"
    assert xenserver.get_object_ref(fake_ansible_module, "name", fail=False, msg_prefix="Test: ") is None


def test_get_object_ref_name_multiple_found(mocker, fake_ansible_module, XenAPI, xenserver):
    """Tests when multiple objects are found by name."""
    mocked_xenapi = mocker.patch.object(XenAPI.Session, 'xenapi_request', return_value=[fake_xenapi_ref('VM'), fake_xenapi_ref('VM')])

    error_msg = "Test: multiple VMs with name 'name' found! Please use UUID."

    with pytest.raises(FailJsonException) as exc_info:
        xenserver.get_object_ref(fake_ansible_module, "name", msg_prefix="Test: ")

    assert exc_info.value.kwargs['msg'] == error_msg

    with pytest.raises(FailJsonException) as exc_info:
        xenserver.get_object_ref(fake_ansible_module, "name", fail=False, msg_prefix="Test: ")

    assert exc_info.value.kwargs['msg'] == error_msg
