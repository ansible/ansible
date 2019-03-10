# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import json
import pytest

from .FakeAnsibleModule import FailJsonException
from .common import xenserver_guest_expand_params
from .testcases.xenserver_guest_common import (testcase_vm_not_found,
                                               testcase_vm_found)
from .testcases.xenserver_guest_powerstate_common import (testcase_powerstate_change,
                                                          testcase_powerstate_change_check_mode,
                                                          testcase_no_powerstate_change_wait_for_ip_address)
from .testcases.xenserver_guest.deploy import (testcase_deploy_failures,
                                               testcase_deploy)
from .testcases.xenserver_guest.destroy import (testcase_destroy_failures,
                                                testcase_destroy,
                                                testcase_destroy_check_mode)
from .testcases.xenserver_guest.get_changes import (testcase_get_changes_failures,
                                                    testcase_get_changes_device_limits,
                                                    testcase_get_changes_no_change,
                                                    testcase_get_changes_need_poweredoff,
                                                    testcase_get_changes)
from .testcases.xenserver_guest.reconfigure import (testcase_reconfigure_failures,
                                                    testcase_reconfigure,
                                                    testcase_reconfigure_elifs,
                                                    testcase_reconfigure_check_mode)
from .testcases.xenserver_guest.get_normalized_disk_size import (testcase_get_normalized_disk_size_failures,
                                                                 testcase_get_normalized_disk_size)
from .testcases.xenserver_guest.get_cdrom_type import testcase_get_cdrom_type
from .testcases.xenserver_guest.main import testcase_guest


pytestmark = pytest.mark.usefixtures("fake_xenapi_db_vm")


@pytest.mark.parametrize('fake_ansible_module',
                         testcase_vm_not_found['params'],
                         ids=testcase_vm_not_found['ids'],
                         indirect=True)
def test_xenserver_guest_xenservervm_misc_vm_not_found(fake_ansible_module, xenserver_guest):
    """
    Tests successful run of XenServerVM.__init__() and misc methods
    when VM is not found.
    """
    xenserver_guest_expand_params(fake_ansible_module.params)

    vm = xenserver_guest.XenServerVM(fake_ansible_module)

    assert vm.vm_ref is None
    assert not vm.vm_params


@pytest.mark.parametrize('fake_ansible_module,fake_vm_facts',
                         testcase_vm_found['params'],
                         ids=testcase_vm_found['ids'],
                         indirect=True)
def test_xenserver_guest_xenservervm_misc_vm_found(fake_ansible_module, fake_vm_facts, xenserver_guest):
    """
    Tests successful run of XenServerVM.__init__() and misc methods
    when VM is found.
    """
    xenserver_guest_expand_params(fake_ansible_module.params)

    vm = xenserver_guest.XenServerVM(fake_ansible_module)

    assert vm.gather_facts() == fake_vm_facts


@pytest.mark.parametrize('fake_ansible_module,fake_vm_facts,expect_powerstate_changed',
                         testcase_powerstate_change['params'],
                         ids=testcase_powerstate_change['ids'],
                         indirect=['fake_ansible_module', 'fake_vm_facts'])
def test_xenserver_guest_xenservervm_set_power_state(mocker,
                                                     fake_ansible_module,
                                                     fake_vm_facts,
                                                     expect_powerstate_changed,
                                                     xenserver_guest):
    """Tests XenServerVM.set_power_state()."""
    mocked_set_vm_power_state = mocker.patch('ansible.modules.cloud.xenserver.xenserver_guest.set_vm_power_state',
                                             wraps=xenserver_guest.set_vm_power_state)
    mocker.patch('ansible.module_utils.xenserver.time.sleep')

    xenserver_guest_expand_params(fake_ansible_module.params)

    state = fake_ansible_module.params['state']
    state_change_timeout = fake_ansible_module.params['state_change_timeout']

    vm = xenserver_guest.XenServerVM(fake_ansible_module)
    powerstate_changed = vm.set_power_state(state)

    mocked_set_vm_power_state.assert_called_once_with(fake_ansible_module, vm.vm_ref, state, state_change_timeout)
    assert powerstate_changed == expect_powerstate_changed
    assert vm.gather_facts() == fake_vm_facts


@pytest.mark.parametrize('fake_ansible_module,fake_vm_facts,expect_powerstate_changed',
                         testcase_powerstate_change_check_mode['params'],
                         ids=testcase_powerstate_change_check_mode['ids'],
                         indirect=['fake_ansible_module', 'fake_vm_facts'])
def test_xenserver_guest_xenservervm_set_power_state_check_mode(mocker,
                                                                fake_ansible_module,
                                                                fake_vm_facts,
                                                                expect_powerstate_changed,
                                                                xenserver_guest):
    """Tests XenServerVM.set_power_state() in check mode."""
    mocked_set_vm_power_state = mocker.patch('ansible.modules.cloud.xenserver.xenserver_guest.set_vm_power_state',
                                             wraps=xenserver_guest.set_vm_power_state)
    mocker.patch('ansible.module_utils.xenserver.time.sleep')

    xenserver_guest_expand_params(fake_ansible_module.params)
    fake_ansible_module.check_mode = True

    state = fake_ansible_module.params['state']
    state_change_timeout = fake_ansible_module.params['state_change_timeout']

    vm = xenserver_guest.XenServerVM(fake_ansible_module)
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
def test_xenserver_guest_xenservervm_wait_for_ip_address(mocker,
                                                         fake_ansible_module,
                                                         fake_vm_facts,
                                                         expect_powerstate_changed,
                                                         xenserver_guest):
    """Tests XenServerVM.wait_for_ip_address()."""
    mocked_wait_for_vm_ip_address = mocker.patch('ansible.modules.cloud.xenserver.xenserver_guest.wait_for_vm_ip_address',
                                                 wraps=xenserver_guest.wait_for_vm_ip_address)
    mocker.patch('ansible.module_utils.xenserver.time.sleep')

    xenserver_guest_expand_params(fake_ansible_module.params)

    state_change_timeout = fake_ansible_module.params['state_change_timeout']

    vm = xenserver_guest.XenServerVM(fake_ansible_module)
    vm.wait_for_ip_address()

    mocked_wait_for_vm_ip_address.assert_called_once_with(fake_ansible_module, vm.vm_ref, state_change_timeout)
    assert vm.gather_facts() == fake_vm_facts


@pytest.mark.parametrize('fake_ansible_module,fail_msg',
                         testcase_deploy_failures['params'],
                         ids=testcase_deploy_failures['ids'],
                         indirect=['fake_ansible_module'])
def test_xenserver_guest_xenservervm_deploy_failures(mocker, fake_ansible_module, fail_msg, xenserver_guest):
    """Tests XenServerVM.deploy() failures."""
    mocker.patch('ansible.module_utils.xenserver.time.sleep')

    xenserver_guest_expand_params(fake_ansible_module.params)

    vm = xenserver_guest.XenServerVM(fake_ansible_module)
    vm.default_sr_ref = "OpaqueRef:NULL"

    with pytest.raises(FailJsonException) as exc_info:
        vm.deploy()

    assert exc_info.value.kwargs['msg'] == fail_msg


@pytest.mark.parametrize('fake_ansible_module,fail_msg',
                         testcase_deploy_failures['params'],
                         ids=testcase_deploy_failures['ids'],
                         indirect=['fake_ansible_module'])
def test_xenserver_guest_xenservervm_deploy_failures_check_mode(mocker, fake_ansible_module, fail_msg, xenserver_guest):
    """Tests XenServerVM.deploy() failures in check mode."""
    mocker.patch('ansible.module_utils.xenserver.time.sleep')

    xenserver_guest_expand_params(fake_ansible_module.params)
    fake_ansible_module.check_mode = True

    vm = xenserver_guest.XenServerVM(fake_ansible_module)
    vm.default_sr_ref = "OpaqueRef:NULL"

    with pytest.raises(FailJsonException) as exc_info:
        vm.deploy()

    assert exc_info.value.kwargs['msg'] == fail_msg


@pytest.mark.parametrize('fake_ansible_module,fake_vm_facts',
                         testcase_deploy['params'],
                         ids=testcase_deploy['ids'],
                         indirect=True)
def test_xenserver_guest_xenservervm_deploy(mocker, fake_ansible_module, fake_vm_facts, xenserver_guest):
    """Tests XenServerVM.deploy() regular run."""
    mocked_reconfigure = mocker.patch.object(xenserver_guest.XenServerVM, 'reconfigure')
    mocked_set_vm_power_state = mocker.patch('ansible.modules.cloud.xenserver.xenserver_guest.set_vm_power_state',
                                             wraps=xenserver_guest.set_vm_power_state)
    mocker.patch('ansible.module_utils.xenserver.time.sleep')

    xenserver_guest_expand_params(fake_ansible_module.params)

    vm = xenserver_guest.XenServerVM(fake_ansible_module)

    vm.deploy()

    if fake_ansible_module.params['linked_clone']:
        vm.xapi_session.xenapi_request.assert_xenapi_method_called_once('VM.clone')
        vm.xapi_session.xenapi_request.assert_xenapi_method_not_called('VM.copy')
    else:
        vm.xapi_session.xenapi_request.assert_xenapi_method_not_called('VM.clone')
        vm.xapi_session.xenapi_request.assert_xenapi_method_called_once('VM.copy')

    assert vm.vm_params['name_description'] == ""
    assert "disks" not in vm.vm_params['other_config']
    vm.xapi_session.xenapi_request.assert_xenapi_method_called_once('VM.provision')
    mocked_reconfigure.assert_called_once_with()

    if fake_ansible_module.params['state'] == "poweredon":
        mocked_set_vm_power_state.assert_called_once_with(fake_ansible_module, vm.vm_ref, 'poweredon', 0)
    else:
        mocked_set_vm_power_state.assert_not_called()

    vm_facts = vm.gather_facts()

    # Fill in the unknown UUID.
    fake_vm_facts['uuid'] = vm_facts['uuid']

    assert vm_facts == fake_vm_facts


@pytest.mark.parametrize('fake_ansible_module,fake_vm_facts',
                         testcase_deploy['params'],
                         ids=testcase_deploy['ids'],
                         indirect=True)
def test_xenserver_guest_xenservervm_deploy_check_mode(mocker, fake_ansible_module, fake_vm_facts, xenserver_guest):
    """Tests XenServerVM.deploy() regular run in check mode."""
    mocked_reconfigure = mocker.patch.object(xenserver_guest.XenServerVM, 'reconfigure')
    mocked_set_vm_power_state = mocker.patch('ansible.modules.cloud.xenserver.xenserver_guest.set_vm_power_state',
                                             wraps=xenserver_guest.set_vm_power_state)
    mocker.patch('ansible.module_utils.xenserver.time.sleep')

    xenserver_guest_expand_params(fake_ansible_module.params)
    fake_ansible_module.check_mode = True

    vm = xenserver_guest.XenServerVM(fake_ansible_module)

    vm.deploy()

    assert vm.vm_ref is None
    vm.xapi_session.xenapi_request.assert_xenapi_method_not_called('VM.clone')
    vm.xapi_session.xenapi_request.assert_xenapi_method_not_called('VM.copy')
    vm.xapi_session.xenapi_request.assert_xenapi_method_not_called('VM.provision')
    mocked_reconfigure.assert_not_called()
    mocked_set_vm_power_state.assert_not_called()

    assert vm.gather_facts() == {}


@pytest.mark.parametrize('fake_ansible_module,fail_msg',
                         testcase_destroy_failures['params'],
                         ids=testcase_destroy_failures['ids'],
                         indirect=['fake_ansible_module'])
def test_xenserver_guest_xenservervm_destroy_failures(mocker, fake_ansible_module, fail_msg, xenserver_guest):
    """Tests XenServerVM.destroy() failures."""
    mocked_set_vm_power_state = mocker.patch('ansible.modules.cloud.xenserver.xenserver_guest.set_vm_power_state',
                                             wraps=xenserver_guest.set_vm_power_state)
    mocker.patch('ansible.module_utils.xenserver.time.sleep')

    xenserver_guest_expand_params(fake_ansible_module.params)

    vm = xenserver_guest.XenServerVM(fake_ansible_module)

    with pytest.raises(FailJsonException) as exc_info:
        vm.destroy()

    mocked_set_vm_power_state.assert_not_called()
    assert exc_info.value.kwargs['msg'] == fail_msg


@pytest.mark.parametrize('fake_ansible_module,fail_msg',
                         testcase_destroy_failures['params'],
                         ids=testcase_destroy_failures['ids'],
                         indirect=['fake_ansible_module'])
def test_xenserver_guest_xenservervm_destroy_failures_check_mode(mocker, fake_ansible_module, fail_msg, xenserver_guest):
    """Tests XenServerVM.destroy() failures in check mode."""
    mocked_set_vm_power_state = mocker.patch('ansible.modules.cloud.xenserver.xenserver_guest.set_vm_power_state',
                                             wraps=xenserver_guest.set_vm_power_state)
    mocker.patch('ansible.module_utils.xenserver.time.sleep')

    xenserver_guest_expand_params(fake_ansible_module.params)
    fake_ansible_module.check_mode = True

    vm = xenserver_guest.XenServerVM(fake_ansible_module)

    with pytest.raises(FailJsonException) as exc_info:
        vm.destroy()

    mocked_set_vm_power_state.assert_not_called()
    assert exc_info.value.kwargs['msg'] == fail_msg


@pytest.mark.parametrize('fake_ansible_module,fake_vm_facts',
                         testcase_destroy['params'],
                         ids=testcase_destroy['ids'],
                         indirect=True)
def test_xenserver_guest_xenservervm_destroy(mocker, fake_ansible_module, fake_vm_facts, xenserver_guest):
    """Tests XenServerVM.destroy() regular run."""
    mocked_set_vm_power_state = mocker.patch('ansible.modules.cloud.xenserver.xenserver_guest.set_vm_power_state',
                                             wraps=xenserver_guest.set_vm_power_state)
    mocker.patch('ansible.module_utils.xenserver.time.sleep')

    xenserver_guest_expand_params(fake_ansible_module.params)

    state_change_timeout = fake_ansible_module.params['state_change_timeout']

    vm = xenserver_guest.XenServerVM(fake_ansible_module)

    vm.destroy()

    mocked_set_vm_power_state.assert_called_once_with(fake_ansible_module, vm.vm_ref, "poweredoff", state_change_timeout)
    vm.xapi_session.xenapi_request.assert_xenapi_method_called_once('VM.destroy')
    vm.xapi_session.xenapi_request.assert_xenapi_method_called('VDI.destroy')
    assert vm.gather_facts() == fake_vm_facts


@pytest.mark.parametrize('fake_ansible_module,fake_vm_facts',
                         testcase_destroy_check_mode['params'],
                         ids=testcase_destroy_check_mode['ids'],
                         indirect=True)
def test_xenserver_guest_xenservervm_destroy_check_mode(mocker, fake_ansible_module, fake_vm_facts, xenserver_guest):
    """Tests XenServerVM.destroy() regular run in check mode."""
    mocked_set_vm_power_state = mocker.patch('ansible.modules.cloud.xenserver.xenserver_guest.set_vm_power_state',
                                             wraps=xenserver_guest.set_vm_power_state)
    mocker.patch('ansible.module_utils.xenserver.time.sleep')

    xenserver_guest_expand_params(fake_ansible_module.params)
    fake_ansible_module.check_mode = True

    vm = xenserver_guest.XenServerVM(fake_ansible_module)

    vm.destroy()

    mocked_set_vm_power_state.assert_not_called()
    vm.xapi_session.xenapi_request.assert_xenapi_method_not_called('VM.destroy')
    vm.xapi_session.xenapi_request.assert_xenapi_method_not_called('VDI.destroy')

    assert vm.gather_facts() == fake_vm_facts


@pytest.mark.parametrize('fake_ansible_module,fail_msg',
                         testcase_get_changes_failures['params'],
                         ids=testcase_get_changes_failures['ids'],
                         indirect=['fake_ansible_module'])
def test_xenserver_guest_xenservervm_get_changes_failures(fake_ansible_module, fail_msg, xenserver_guest):
    """Tests XenServerVM.get_changes() failures."""
    xenserver_guest_expand_params(fake_ansible_module.params)

    vm = xenserver_guest.XenServerVM(fake_ansible_module)
    vm.default_sr_ref = "OpaqueRef:NULL"

    with pytest.raises(FailJsonException) as exc_info:
        vm.get_changes()

    assert exc_info.value.kwargs['msg'] == fail_msg


@pytest.mark.parametrize('fake_ansible_module,max_vbd,max_vif,fail_msg',
                         testcase_get_changes_device_limits['params'],
                         ids=testcase_get_changes_device_limits['ids'],
                         indirect=['fake_ansible_module'])
def test_xenserver_guest_xenservervm_get_changes_device_limits(mocker, fake_ansible_module, max_vbd, max_vif, fail_msg, xenserver_guest):
    """Tests XenServerVM.get_changes() device limit failures."""
    mocker.patch('XenAPI._MAX_VBD_DEVICES', max_vbd)
    mocker.patch('XenAPI._MAX_VIF_DEVICES', max_vif)

    xenserver_guest_expand_params(fake_ansible_module.params)

    vm = xenserver_guest.XenServerVM(fake_ansible_module)

    with pytest.raises(FailJsonException) as exc_info:
        vm.get_changes()

    assert exc_info.value.kwargs['msg'] == fail_msg


@pytest.mark.parametrize('fake_ansible_module',
                         testcase_get_changes_no_change['params'],
                         ids=testcase_get_changes_no_change['ids'],
                         indirect=True)
def test_xenserver_guest_xenservervm_get_changes_no_changes(fake_ansible_module, xenserver_guest):
    """Tests XenServerVM.get_changes() regular run without changes."""
    xenserver_guest_expand_params(fake_ansible_module.params)

    vm = xenserver_guest.XenServerVM(fake_ansible_module)

    assert vm.get_changes() == []


@pytest.mark.parametrize('fake_ansible_module,need_poweredoff',
                         testcase_get_changes_need_poweredoff['params'],
                         ids=testcase_get_changes_need_poweredoff['ids'],
                         indirect=['fake_ansible_module'])
def test_xenserver_guest_xenservervm_get_changes_need_poweredoff(fake_ansible_module, need_poweredoff, xenserver_guest):
    """Tests if XenServerVM.get_changes() generates need_poweredoff flag when conditions are met."""
    xenserver_guest_expand_params(fake_ansible_module.params)

    vm = xenserver_guest.XenServerVM(fake_ansible_module)

    changes = vm.get_changes()

    if need_poweredoff:
        assert "need_poweredoff" in changes
    else:
        assert "need_poweredoff" not in changes


@pytest.mark.parametrize('fake_ansible_module,fake_vm_changes',
                         testcase_get_changes['params'],
                         ids=testcase_get_changes['ids'],
                         indirect=True)
def test_xenserver_guest_xenservervm_get_changes(fake_ansible_module, fake_vm_changes, xenserver_guest):
    """Tests XenServerVM.get_changes() regular run with changes."""
    xenserver_guest_expand_params(fake_ansible_module.params)

    vm = xenserver_guest.XenServerVM(fake_ansible_module)

    changes = vm.get_changes()

    # We have to convert tuples to lists because tuples can't be
    # expressed in json.
    for change in changes:
        if isinstance(change, dict):
            if "disks_new" in change:
                disks_new_list = []

                for disk_new in change['disks_new']:
                    disks_new_list.append(list(disk_new))

                change['disks_new'] = disks_new_list
            elif "networks_new" in change:
                networks_new_list = []

                for network_new in change['networks_new']:
                    networks_new_list.append(list(network_new))

                change['networks_new'] = networks_new_list

    assert changes == fake_vm_changes


@pytest.mark.parametrize('fake_ansible_module,fail_msg',
                         testcase_reconfigure_failures['params'],
                         ids=testcase_reconfigure_failures['ids'],
                         indirect=['fake_ansible_module'])
def test_xenserver_guest_xenservervm_reconfigure_failures(mocker, fake_ansible_module, fail_msg, xenserver_guest):
    """Tests XenServerVM.reconfigure() failures."""
    mocker.patch('ansible.module_utils.xenserver.time.sleep')

    xenserver_guest_expand_params(fake_ansible_module.params)

    vm = xenserver_guest.XenServerVM(fake_ansible_module)
    vm.default_sr_ref = "OpaqueRef:NULL"

    with pytest.raises(FailJsonException) as exc_info:
        vm.reconfigure()

    assert exc_info.value.kwargs['msg'] == fail_msg


@pytest.mark.parametrize('fake_ansible_module,fail_msg',
                         testcase_reconfigure_failures['params'],
                         ids=testcase_reconfigure_failures['ids'],
                         indirect=['fake_ansible_module'])
def test_xenserver_guest_xenservervm_reconfigure_failures_check_mode(mocker, fake_ansible_module, fail_msg, xenserver_guest):
    """Tests XenServerVM.reconfigure() failures in check mode."""
    mocker.patch('ansible.module_utils.xenserver.time.sleep')

    xenserver_guest_expand_params(fake_ansible_module.params)
    fake_ansible_module.check_mode = True

    vm = xenserver_guest.XenServerVM(fake_ansible_module)
    vm.default_sr_ref = "OpaqueRef:NULL"

    with pytest.raises(FailJsonException) as exc_info:
        vm.reconfigure()

    assert exc_info.value.kwargs['msg'] == fail_msg


@pytest.mark.parametrize('fake_ansible_module,fake_vm_facts',
                         testcase_reconfigure['params'],
                         ids=testcase_reconfigure['ids'],
                         indirect=True)
def test_xenserver_guest_xenservervm_reconfigure(mocker, fake_ansible_module, fake_vm_facts, xenserver_guest):
    """Tests XenServerVM.reconfigure() regular run with changes."""
    mocker.patch('ansible.module_utils.xenserver.time.sleep')

    xenserver_guest_expand_params(fake_ansible_module.params)

    vm = xenserver_guest.XenServerVM(fake_ansible_module)

    vm.reconfigure()

    assert vm.gather_facts() == fake_vm_facts


@pytest.mark.parametrize('fake_ansible_module,fake_vm_changes',
                         testcase_reconfigure_elifs['params'],
                         ids=testcase_reconfigure_elifs['ids'],
                         indirect=True)
def test_xenserver_guest_xenservervm_reconfigure_elifs(mocker, fake_ansible_module, fake_vm_changes, xenserver_guest):
    """Tests XenServerVM.reconfigure() extraneous elifs."""
    mocker.patch('ansible.module_utils.xenserver.time.sleep')
    mocker.patch.object(xenserver_guest.XenServerVM, 'get_changes', return_value=fake_vm_changes)

    xenserver_guest_expand_params(fake_ansible_module.params)

    vm = xenserver_guest.XenServerVM(fake_ansible_module)
    vm.vm_params['customization_agent'] = "impossible"

    vm.reconfigure()


@pytest.mark.parametrize('fake_ansible_module,fake_vm_facts',
                         testcase_reconfigure_check_mode['params'],
                         ids=testcase_reconfigure_check_mode['ids'],
                         indirect=True)
def test_xenserver_guest_xenservervm_reconfigure_check_mode(mocker, fake_ansible_module, fake_vm_facts, xenserver_guest):
    """Tests XenServerVM.reconfigure() regular run with changes in check mode."""
    mocker.patch('ansible.module_utils.xenserver.time.sleep')

    xenserver_guest_expand_params(fake_ansible_module.params)
    fake_ansible_module.check_mode = True

    vm = xenserver_guest.XenServerVM(fake_ansible_module)

    vm_changes = vm.reconfigure()

    assert vm.gather_facts() == fake_vm_facts


@pytest.mark.parametrize('disk_params,fail_msg',
                         testcase_get_normalized_disk_size_failures['params'],
                         ids=testcase_get_normalized_disk_size_failures['ids'])
def test_xenserver_guest_xenservervm_get_normalized_disk_size_failures(fake_ansible_module, disk_params, fail_msg, xenserver_guest):
    """Tests XenServerVM.get_normalized_disk_size() failures."""
    # This is required for XenServerVM to be instantiated which is on the other
    # hand needed to call get_normalized_disk_size() because it is not a static
    # method. get_normalized_disk_size() should be converted to static method
    # or moved to xenserver module util so that this piece of code can be
    # removed.
    fake_ansible_module.params.update({
        "uuid": "some-vm-uuid",
    })

    xenserver_guest_expand_params(fake_ansible_module.params)

    vm = xenserver_guest.XenServerVM(fake_ansible_module)

    with pytest.raises(FailJsonException) as exc_info:
        vm.get_normalized_disk_size(disk_params)

    assert exc_info.value.kwargs['msg'] == fail_msg


@pytest.mark.parametrize('disk_params,normalized_size',
                         testcase_get_normalized_disk_size['params'],
                         ids=testcase_get_normalized_disk_size['ids'])
def test_xenserver_guest_xenservervm_get_normalized_disk_size(fake_ansible_module, disk_params, normalized_size, xenserver_guest):
    """Tests XenServerVM.get_normalized_disk_size() regular run."""
    # This is required for XenServerVM to be instantiated which is on the other
    # hand needed to call get_normalized_disk_size() because it is not a static
    # method. get_normalized_disk_size() should be converted to static method
    # or moved to xenserver module util so that this piece of code can be
    # removed.
    fake_ansible_module.params.update({
        "uuid": "some-vm-uuid",
    })

    xenserver_guest_expand_params(fake_ansible_module.params)

    vm = xenserver_guest.XenServerVM(fake_ansible_module)

    assert vm.get_normalized_disk_size(disk_params) == normalized_size


@pytest.mark.parametrize('vm_cdrom_params,cdrom_type',
                         testcase_get_cdrom_type['params'],
                         ids=testcase_get_cdrom_type['ids'])
def test_xenserver_guest_xenservervm_get_cdrom_type(vm_cdrom_params, cdrom_type, xenserver_guest):
    """Tests XenServerVM.get_cdrom_type() regular run."""
    assert xenserver_guest.XenServerVM.get_cdrom_type(vm_cdrom_params) == cdrom_type


@pytest.mark.parametrize('patch_ansible_module,fake_vm_facts,expect_changed',
                         testcase_guest['params'],
                         ids=testcase_guest['ids'],
                         indirect=['patch_ansible_module', 'fake_vm_facts'])
def test_xenserver_guest_main(mocker, capfd, patch_ansible_module, fake_vm_facts, expect_changed, xenserver_guest):
    """
    Tests successful module invocation with parsing and propagation of
    module parameters and correctness of module output.
    """
    mocker.patch('ansible.module_utils.xenserver.time.sleep')

    with pytest.raises(SystemExit):
        xenserver_guest.main()

    out, err = capfd.readouterr()
    result = json.loads(out)

    # if result['failed']:
    #    print(result['msg'])

    assert result['failed'] is False
    assert result['changed'] is expect_changed

    # Fill in the unknown UUID.
    if fake_vm_facts['uuid'] == "unknown":
        fake_vm_facts['uuid'] = result['instance']['uuid']

    assert result['instance'] == fake_vm_facts
