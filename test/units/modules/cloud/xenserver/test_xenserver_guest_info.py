# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import json
import pytest

from .FakeAnsibleModule import FailJsonException
from .common import xenserver_guest_info_expand_params
from .testcases.xenserver_guest_common import (testcase_vm_not_found,
                                               testcase_vm_found)


pytestmark = pytest.mark.usefixtures("fake_xenapi_db_vm")


@pytest.mark.parametrize('fake_ansible_module',
                         testcase_vm_not_found['params'],
                         ids=testcase_vm_not_found['ids'],
                         indirect=True)
def test_xenserver_guest_info_xenservervm_misc_failures(fake_ansible_module, xenserver_guest_info):
    """Tests failures of XenServerVM.__init__()."""
    xenserver_guest_info_expand_params(fake_ansible_module.params)

    with pytest.raises(FailJsonException) as exc_info:
        xenserver_guest_info.XenServerVM(fake_ansible_module)

    assert "not found" in exc_info.value.kwargs['msg']


@pytest.mark.parametrize('fake_ansible_module,fake_vm_facts',
                         testcase_vm_found['params'],
                         ids=testcase_vm_found['ids'],
                         indirect=True)
def test_xenserver_guest_info_xenservervm_misc_success(fake_ansible_module, fake_vm_facts, xenserver_guest_info):
    """Tests successful run of XenServerVM.__init__() and misc methods."""
    xenserver_guest_info_expand_params(fake_ansible_module.params)

    vm = xenserver_guest_info.XenServerVM(fake_ansible_module)

    assert vm.gather_facts() == fake_vm_facts


@pytest.mark.parametrize('patch_ansible_module',
                         testcase_vm_not_found['params'],
                         ids=testcase_vm_not_found['ids'],
                         indirect=True)
def test_xenserver_guest_info_main_failures(capfd, patch_ansible_module, xenserver_guest_info):
    """
    Tests module failures with parsing and propagation of module parameters
    and correctness of module output.
    """
    with pytest.raises(SystemExit):
        xenserver_guest_info.main()

    out, err = capfd.readouterr()
    result = json.loads(out)

    assert result['failed'] is True
    assert "not found" in result['msg']
    assert "changed" not in result
    assert "instance" not in result


@pytest.mark.parametrize('patch_ansible_module,fake_vm_facts',
                         testcase_vm_found['params'],
                         ids=testcase_vm_found['ids'],
                         indirect=True)
def test_xenserver_guest_info_main_success(capfd, patch_ansible_module, fake_vm_facts, xenserver_guest_info):
    """
    Tests successful module invocation with parsing and propagation of
    module parameters and correctness of module output.
    """
    with pytest.raises(SystemExit):
        xenserver_guest_info.main()

    out, err = capfd.readouterr()
    result = json.loads(out)

    # if result['failed']:
    #     print(result['msg'])

    assert result['failed'] is False
    assert result['changed'] is False
    assert result['instance'] == fake_vm_facts
