# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import json
import pytest

from .FakeAnsibleModule import FailJsonException
from .common import xenserver_guest_powerstate_expand_params
from .testcases.xenserver_guest_common import (testcase_vm_not_found,
                                               testcase_vm_found)
from .testcases.xenserver_guest_powerstate_common import (testcase_powerstate_change,
                                                          testcase_powerstate_change_check_mode,
                                                          testcase_powerstate_change_wait_for_ip_address,
                                                          testcase_no_powerstate_change_wait_for_ip_address)
from .testcases.xenserver_guest_powerstate.main import testcase_powerstate


pytestmark = pytest.mark.usefixtures("fake_xenapi_db_vm")


@pytest.mark.parametrize('fake_ansible_module',
                         testcase_vm_not_found['params'],
                         ids=testcase_vm_not_found['ids'],
                         indirect=True)
def test_xenserver_guest_powerstate_xenservervm_misc_failures(fake_ansible_module, xenserver_guest_powerstate):
    """Tests failures of XenServerVM.__init__()."""
    xenserver_guest_powerstate_expand_params(fake_ansible_module.params)

    with pytest.raises(FailJsonException) as exc_info:
        xenserver_guest_powerstate.XenServerVM(fake_ansible_module)

    assert "not found" in exc_info.value.kwargs['msg']


@pytest.mark.parametrize('fake_ansible_module,fake_vm_facts',
                         testcase_vm_found['params'],
                         ids=testcase_vm_found['ids'],
                         indirect=True)
def test_xenserver_guest_powerstate_xenservervm_misc_success(fake_ansible_module, fake_vm_facts, xenserver_guest_powerstate):
    """Tests successful run of XenServerVM.__init__() and misc methods."""
    xenserver_guest_powerstate_expand_params(fake_ansible_module.params)

    vm = xenserver_guest_powerstate.XenServerVM(fake_ansible_module)

    assert vm.gather_facts() == fake_vm_facts


@pytest.mark.parametrize('fake_ansible_module,fake_vm_facts,expect_powerstate_changed',
                         testcase_powerstate_change['params'],
                         ids=testcase_powerstate_change['ids'],
                         indirect=['fake_ansible_module', 'fake_vm_facts'])
def test_xenserver_guest_powerstate_xenservervm_set_power_state(mocker,
                                                                fake_ansible_module,
                                                                fake_vm_facts,
                                                                expect_powerstate_changed,
                                                                xenserver_guest_powerstate):
    """Tests XenServerVM.set_power_state()."""
    mocked_set_vm_power_state = mocker.patch('ansible.modules.cloud.xenserver.xenserver_guest_powerstate.set_vm_power_state',
                                             wraps=xenserver_guest_powerstate.set_vm_power_state)
    mocker.patch('ansible.module_utils.xenserver.time.sleep')

    xenserver_guest_powerstate_expand_params(fake_ansible_module.params)

    state = fake_ansible_module.params['state']
    state_change_timeout = fake_ansible_module.params['state_change_timeout']

    vm = xenserver_guest_powerstate.XenServerVM(fake_ansible_module)
    powerstate_changed = vm.set_power_state(state)

    mocked_set_vm_power_state.assert_called_once_with(fake_ansible_module, vm.vm_ref, state, state_change_timeout)
    assert powerstate_changed == expect_powerstate_changed
    assert vm.gather_facts() == fake_vm_facts


@pytest.mark.parametrize('fake_ansible_module,fake_vm_facts,expect_powerstate_changed',
                         testcase_powerstate_change_check_mode['params'],
                         ids=testcase_powerstate_change_check_mode['ids'],
                         indirect=['fake_ansible_module', 'fake_vm_facts'])
def test_xenserver_guest_powerstate_xenservervm_set_power_state_check_mode(mocker,
                                                                           fake_ansible_module,
                                                                           fake_vm_facts,
                                                                           expect_powerstate_changed,
                                                                           xenserver_guest_powerstate):
    """Tests XenServerVM.set_power_state() in check mode."""
    mocked_set_vm_power_state = mocker.patch('ansible.modules.cloud.xenserver.xenserver_guest_powerstate.set_vm_power_state',
                                             wraps=xenserver_guest_powerstate.set_vm_power_state)
    mocker.patch('ansible.module_utils.xenserver.time.sleep')

    xenserver_guest_powerstate_expand_params(fake_ansible_module.params)
    fake_ansible_module.check_mode = True

    state = fake_ansible_module.params['state']
    state_change_timeout = fake_ansible_module.params['state_change_timeout']

    vm = xenserver_guest_powerstate.XenServerVM(fake_ansible_module)
    powerstate_changed = vm.set_power_state(state)

    mocked_set_vm_power_state.assert_called_once_with(fake_ansible_module, vm.vm_ref, state, state_change_timeout)
    assert powerstate_changed == expect_powerstate_changed

    # Workaround for set_power_state() side effect.
    vm_facts = vm.gather_facts()
    fake_vm_facts['state'] = vm_facts['state']

    assert vm_facts == fake_vm_facts


@pytest.mark.parametrize('fake_ansible_module,fake_vm_facts,expect_powerstate_changed',
                         testcase_no_powerstate_change_wait_for_ip_address['params'],
                         ids=testcase_no_powerstate_change_wait_for_ip_address['ids'],
                         indirect=['fake_ansible_module', 'fake_vm_facts'])
def test_xenserver_guest_powerstate_xenservervm_wait_for_ip_address(mocker,
                                                                    fake_ansible_module,
                                                                    fake_vm_facts,
                                                                    expect_powerstate_changed,
                                                                    xenserver_guest_powerstate):
    """Tests XenServerVM.wait_for_ip_address()."""
    mocked_wait_for_vm_ip_address = mocker.patch('ansible.modules.cloud.xenserver.xenserver_guest_powerstate.wait_for_vm_ip_address',
                                                 wraps=xenserver_guest_powerstate.wait_for_vm_ip_address)
    mocker.patch('ansible.module_utils.xenserver.time.sleep')

    xenserver_guest_powerstate_expand_params(fake_ansible_module.params)

    state_change_timeout = fake_ansible_module.params['state_change_timeout']

    vm = xenserver_guest_powerstate.XenServerVM(fake_ansible_module)
    vm.wait_for_ip_address()

    mocked_wait_for_vm_ip_address.assert_called_once_with(fake_ansible_module, vm.vm_ref, state_change_timeout)
    assert vm.gather_facts() == fake_vm_facts


@pytest.mark.parametrize('patch_ansible_module',
                         testcase_vm_not_found['params'],
                         ids=testcase_vm_not_found['ids'],
                         indirect=True)
def test_xenserver_guest_powerstate_main_failures(capfd, patch_ansible_module, xenserver_guest_powerstate):
    """
    Tests module failures with parsing and propagation of module parameters
    and correctness of module output.
    """
    with pytest.raises(SystemExit):
        xenserver_guest_powerstate.main()

    out, err = capfd.readouterr()
    result = json.loads(out)

    assert result['failed'] is True
    assert "not found" in result['msg']
    assert "changed" not in result
    assert "instance" not in result


@pytest.mark.parametrize('patch_ansible_module,fake_vm_facts,expect_powerstate_changed',
                         testcase_powerstate['params'],
                         ids=testcase_powerstate['ids'],
                         indirect=['patch_ansible_module', 'fake_vm_facts'])
def test_xenserver_guest_powerstate_main_success(mocker,
                                                 capfd,
                                                 patch_ansible_module,
                                                 fake_vm_facts,
                                                 expect_powerstate_changed,
                                                 xenserver_guest_powerstate):
    """
    Tests successful module invocation with parsing and propagation of
    module parameters and correctness of module output when no change is made.
    """
    mocker.patch('ansible.module_utils.xenserver.time.sleep')

    with pytest.raises(SystemExit):
        xenserver_guest_powerstate.main()

    out, err = capfd.readouterr()
    result = json.loads(out)

    # if result['failed']:
    #     print(result['msg'])

    assert result['failed'] is False
    assert result['changed'] is expect_powerstate_changed
    assert result['instance'] == fake_vm_facts
