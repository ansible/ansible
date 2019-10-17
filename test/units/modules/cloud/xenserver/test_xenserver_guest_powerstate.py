# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import json
import pytest

from .common import fake_xenapi_ref


testcase_set_powerstate = {
    "params": [
        (False, "someoldstate"),
        (True, "somenewstate"),
    ],
    "ids": [
        "state-same",
        "state-changed",
    ],
}

testcase_module_params_state_present = {
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
            "name": "somevmname",
            "state": "present",
        },
    ],
    "ids": [
        "present-implicit",
        "present-explicit",
    ],
}

testcase_module_params_state_other = {
    "params": [
        {
            "hostname": "somehost",
            "username": "someuser",
            "password": "somepwd",
            "name": "somevmname",
            "state": "powered-on",
        },
        {
            "hostname": "somehost",
            "username": "someuser",
            "password": "somepwd",
            "name": "somevmname",
            "state": "powered-off",
        },
        {
            "hostname": "somehost",
            "username": "someuser",
            "password": "somepwd",
            "name": "somevmname",
            "state": "restarted",
        },
        {
            "hostname": "somehost",
            "username": "someuser",
            "password": "somepwd",
            "name": "somevmname",
            "state": "shutdown-guest",
        },
        {
            "hostname": "somehost",
            "username": "someuser",
            "password": "somepwd",
            "name": "somevmname",
            "state": "reboot-guest",
        },
        {
            "hostname": "somehost",
            "username": "someuser",
            "password": "somepwd",
            "name": "somevmname",
            "state": "suspended",
        },
    ],
    "ids": [
        "powered-on",
        "powered-off",
        "restarted",
        "shutdown-guest",
        "reboot-guest",
        "suspended",
    ],
}

testcase_module_params_wait = {
    "params": [
        {
            "hostname": "somehost",
            "username": "someuser",
            "password": "somepwd",
            "name": "somevmname",
            "state": "present",
            "wait_for_ip_address": "yes",
        },
        {
            "hostname": "somehost",
            "username": "someuser",
            "password": "somepwd",
            "name": "somevmname",
            "state": "powered-on",
            "wait_for_ip_address": "yes",
        },
    ],
    "ids": [
        "wait-present",
        "wait-other",
    ],
}


@pytest.mark.parametrize('power_state', testcase_set_powerstate['params'], ids=testcase_set_powerstate['ids'])
def test_xenserver_guest_powerstate_set_power_state(mocker, fake_ansible_module, XenAPI, xenserver_guest_powerstate, power_state):
    """Tests power state change handling."""
    mocker.patch('ansible.modules.cloud.xenserver.xenserver_guest_powerstate.get_object_ref', return_value=fake_xenapi_ref('VM'))
    mocker.patch('ansible.modules.cloud.xenserver.xenserver_guest_powerstate.gather_vm_params', return_value={"power_state": "Someoldstate"})
    mocked_set_vm_power_state = mocker.patch('ansible.modules.cloud.xenserver.xenserver_guest_powerstate.set_vm_power_state',
                                             return_value=power_state)

    mocked_xenapi = mocker.patch.object(XenAPI.Session, 'xenapi', create=True)

    mocked_returns = {
        "pool.get_all.return_value": [fake_xenapi_ref('pool')],
        "pool.get_default_SR.return_value": fake_xenapi_ref('SR'),
    }

    mocked_xenapi.configure_mock(**mocked_returns)

    mocker.patch('ansible.module_utils.xenserver.get_xenserver_version', return_value=[7, 2, 0])

    fake_ansible_module.params.update({
        "name": "somename",
        "uuid": "someuuid",
        "state_change_timeout": 1,
    })

    vm = xenserver_guest_powerstate.XenServerVM(fake_ansible_module)
    state_changed = vm.set_power_state(None)

    mocked_set_vm_power_state.assert_called_once_with(fake_ansible_module, fake_xenapi_ref('VM'), None, 1)
    assert state_changed == power_state[0]
    assert vm.vm_params['power_state'] == power_state[1].capitalize()


@pytest.mark.parametrize('patch_ansible_module',
                         testcase_module_params_state_present['params'],
                         ids=testcase_module_params_state_present['ids'],
                         indirect=True)
def test_xenserver_guest_powerstate_present(mocker, patch_ansible_module, capfd, XenAPI, xenserver_guest_powerstate):
    """
    Tests regular module invocation including parsing and propagation of
    module params and module output when state is set to present.
    """
    fake_vm_facts = {"fake-vm-fact": True}

    mocker.patch('ansible.modules.cloud.xenserver.xenserver_guest_powerstate.get_object_ref', return_value=fake_xenapi_ref('VM'))
    mocker.patch('ansible.modules.cloud.xenserver.xenserver_guest_powerstate.gather_vm_params', return_value={})
    mocker.patch('ansible.modules.cloud.xenserver.xenserver_guest_powerstate.gather_vm_facts', return_value=fake_vm_facts)
    mocked_set_vm_power_state = mocker.patch('ansible.modules.cloud.xenserver.xenserver_guest_powerstate.set_vm_power_state',
                                             return_value=(True, "somenewstate"))
    mocked_wait_for_vm_ip_address = mocker.patch('ansible.modules.cloud.xenserver.xenserver_guest_powerstate.wait_for_vm_ip_address',
                                                 return_value={})

    mocked_xenapi = mocker.patch.object(XenAPI.Session, 'xenapi', create=True)

    mocked_returns = {
        "pool.get_all.return_value": [fake_xenapi_ref('pool')],
        "pool.get_default_SR.return_value": fake_xenapi_ref('SR'),
    }

    mocked_xenapi.configure_mock(**mocked_returns)

    mocker.patch('ansible.module_utils.xenserver.get_xenserver_version', return_value=[7, 2, 0])

    with pytest.raises(SystemExit):
        xenserver_guest_powerstate.main()

    out, err = capfd.readouterr()
    result = json.loads(out)

    mocked_set_vm_power_state.assert_not_called()
    mocked_wait_for_vm_ip_address.assert_not_called()
    assert result['changed'] is False
    assert result['instance'] == fake_vm_facts


@pytest.mark.parametrize('patch_ansible_module',
                         testcase_module_params_state_other['params'],
                         ids=testcase_module_params_state_other['ids'],
                         indirect=True)
def test_xenserver_guest_powerstate_other(mocker, patch_ansible_module, capfd, XenAPI, xenserver_guest_powerstate):
    """
    Tests regular module invocation including parsing and propagation of
    module params and module output when state is set to other value than
    present.
    """
    fake_vm_facts = {"fake-vm-fact": True}

    mocker.patch('ansible.modules.cloud.xenserver.xenserver_guest_powerstate.get_object_ref', return_value=fake_xenapi_ref('VM'))
    mocker.patch('ansible.modules.cloud.xenserver.xenserver_guest_powerstate.gather_vm_params', return_value={})
    mocker.patch('ansible.modules.cloud.xenserver.xenserver_guest_powerstate.gather_vm_facts', return_value=fake_vm_facts)
    mocked_set_vm_power_state = mocker.patch(
        'ansible.modules.cloud.xenserver.xenserver_guest_powerstate.set_vm_power_state',
        return_value=(True, "somenewstate"))
    mocked_wait_for_vm_ip_address = mocker.patch(
        'ansible.modules.cloud.xenserver.xenserver_guest_powerstate.wait_for_vm_ip_address',
        return_value={})

    mocked_xenapi = mocker.patch.object(XenAPI.Session, 'xenapi', create=True)

    mocked_returns = {
        "pool.get_all.return_value": [fake_xenapi_ref('pool')],
        "pool.get_default_SR.return_value": fake_xenapi_ref('SR'),
    }

    mocked_xenapi.configure_mock(**mocked_returns)

    mocker.patch('ansible.module_utils.xenserver.get_xenserver_version', return_value=[7, 2, 0])

    with pytest.raises(SystemExit):
        xenserver_guest_powerstate.main()

    out, err = capfd.readouterr()
    result = json.loads(out)

    mocked_set_vm_power_state.assert_called_once()
    mocked_wait_for_vm_ip_address.assert_not_called()
    assert result['changed'] is True
    assert result['instance'] == fake_vm_facts


@pytest.mark.parametrize('patch_ansible_module',
                         testcase_module_params_wait['params'],
                         ids=testcase_module_params_wait['ids'],
                         indirect=True)
def test_xenserver_guest_powerstate_wait(mocker, patch_ansible_module, capfd, XenAPI, xenserver_guest_powerstate):
    """
    Tests regular module invocation including parsing and propagation of
    module params and module output when wait_for_ip_address option is used.
    """
    fake_vm_facts = {"fake-vm-fact": True}

    mocker.patch('ansible.modules.cloud.xenserver.xenserver_guest_powerstate.get_object_ref', return_value=fake_xenapi_ref('VM'))
    mocker.patch('ansible.modules.cloud.xenserver.xenserver_guest_powerstate.gather_vm_params', return_value={})
    mocker.patch('ansible.modules.cloud.xenserver.xenserver_guest_powerstate.gather_vm_facts', return_value=fake_vm_facts)
    mocked_set_vm_power_state = mocker.patch(
        'ansible.modules.cloud.xenserver.xenserver_guest_powerstate.set_vm_power_state',
        return_value=(True, "somenewstate"))
    mocked_wait_for_vm_ip_address = mocker.patch(
        'ansible.modules.cloud.xenserver.xenserver_guest_powerstate.wait_for_vm_ip_address',
        return_value={})

    mocked_xenapi = mocker.patch.object(XenAPI.Session, 'xenapi', create=True)

    mocked_returns = {
        "pool.get_all.return_value": [fake_xenapi_ref('pool')],
        "pool.get_default_SR.return_value": fake_xenapi_ref('SR'),
    }

    mocked_xenapi.configure_mock(**mocked_returns)

    mocker.patch('ansible.module_utils.xenserver.get_xenserver_version', return_value=[7, 2, 0])

    with pytest.raises(SystemExit):
        xenserver_guest_powerstate.main()

    out, err = capfd.readouterr()
    result = json.loads(out)

    mocked_wait_for_vm_ip_address.assert_called_once()
    assert result['instance'] == fake_vm_facts
