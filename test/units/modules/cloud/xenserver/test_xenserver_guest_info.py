# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import json
import pytest

from .common import fake_xenapi_ref

pytestmark = pytest.mark.usefixtures('patch_ansible_module')


testcase_module_params = {
    "params": [
        {
            "hostname": "somehost",
            "username": "someuser",
            "password": "somepwd",
            "name": "somevmname",
        },
        {
            "hostname": "somehost",
            "username": "someuser",
            "password": "somepwd",
            "uuid": "somevmuuid",
        },
        {
            "hostname": "somehost",
            "username": "someuser",
            "password": "somepwd",
            "name": "somevmname",
            "uuid": "somevmuuid",
        },
    ],
    "ids": [
        "name",
        "uuid",
        "name+uuid",
    ],
}


@pytest.mark.parametrize('patch_ansible_module', testcase_module_params['params'], ids=testcase_module_params['ids'], indirect=True)
def test_xenserver_guest_info(mocker, capfd, XenAPI, xenserver_guest_info):
    """
    Tests regular module invocation including parsing and propagation of
    module params and module output.
    """
    fake_vm_facts = {"fake-vm-fact": True}

    mocker.patch('ansible.modules.cloud.xenserver.xenserver_guest_info.get_object_ref', return_value=None)
    mocker.patch('ansible.modules.cloud.xenserver.xenserver_guest_info.gather_vm_params', return_value=None)
    mocker.patch('ansible.modules.cloud.xenserver.xenserver_guest_info.gather_vm_facts', return_value=fake_vm_facts)

    mocked_xenapi = mocker.patch.object(XenAPI.Session, 'xenapi', create=True)

    mocked_returns = {
        "pool.get_all.return_value": [fake_xenapi_ref('pool')],
        "pool.get_default_SR.return_value": fake_xenapi_ref('SR'),
    }

    mocked_xenapi.configure_mock(**mocked_returns)

    mocker.patch('ansible.module_utils.xenserver.get_xenserver_version', return_value=[7, 2, 0])

    with pytest.raises(SystemExit):
        xenserver_guest_info.main()

    out, err = capfd.readouterr()
    result = json.loads(out)

    assert result['instance'] == fake_vm_facts
