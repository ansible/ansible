# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import json
import pytest
import XenAPI

from ansible.modules.cloud.xenserver.xenserver_guest_facts import main

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
def test_xenserver_guest_facts(mocker, capfd):
    """
    Tests regular module invocation including parsing and propagation of
    module params and module output.
    """
    fake_vm_facts = {"fake-vm-fact": True}

    mocked_get_object_ref = mocker.patch('ansible.modules.cloud.xenserver.xenserver_guest_facts.get_object_ref', return_value=None)
    mocked_gather_vm_params = mocker.patch('ansible.modules.cloud.xenserver.xenserver_guest_facts.gather_vm_params', return_value=None)
    mocked_gather_vm_facts = mocker.patch('ansible.modules.cloud.xenserver.xenserver_guest_facts.gather_vm_facts', return_value=fake_vm_facts)

    mocked_xenapi = mocker.patch.object(XenAPI.Session, 'xenapi', create=True)

    mocked_returns = {
        "pool.get_all.return_value": ["OpaqueRef:fake-xenapi-pool-ref"],
        "pool.get_default_SR.return_value": "OpaqueRef:fake-xenapi-sr-ref",
        "session.get_this_host.return_value": "OpaqueRef:fake-xenapi-host-ref",
        "host.get_software_version.return_value": {"product_version_text_short": "7.2"},
    }

    mocked_xenapi.configure_mock(**mocked_returns)

    with pytest.raises(SystemExit):
        main()

    out, err = capfd.readouterr()
    result = json.loads(out)

    assert result['instance'] == fake_vm_facts
