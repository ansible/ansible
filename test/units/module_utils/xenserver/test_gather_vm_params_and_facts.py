# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import pytest

from .common import testcase_bad_xenapi_refs


testcase_gather_vm_params_and_facts = {
    "params": [
        ["ansible-test-vm-1-params.json", "ansible-test-vm-1-facts.json"],
        ["ansible-test-vm-2-params.json", "ansible-test-vm-2-facts.json"],
        ["ansible-test-vm-3-params.json", "ansible-test-vm-3-facts.json"],
    ],
    "ids": [
        "ansible-test-vm-1",
        "ansible-test-vm-2",
        "ansible-test-vm-3",
    ],
}


@pytest.mark.parametrize('vm_ref', testcase_bad_xenapi_refs['params'], ids=testcase_bad_xenapi_refs['ids'])
def test_gather_vm_params_bad_vm_ref(fake_ansible_module, xenserver, vm_ref):
    """Tests return of empty dict on bad vm_ref."""
    assert xenserver.gather_vm_params(fake_ansible_module, vm_ref) == {}


def test_gather_vm_facts_no_vm_params(fake_ansible_module, xenserver):
    """Tests return of empty facts dict when vm_params is not available"""
    assert xenserver.gather_vm_facts(fake_ansible_module, None) == {}
    assert xenserver.gather_vm_facts(fake_ansible_module, {}) == {}


@pytest.mark.parametrize('fixture_data_from_file',
                         testcase_gather_vm_params_and_facts['params'],
                         ids=testcase_gather_vm_params_and_facts['ids'],
                         indirect=True)
def test_gather_vm_params_and_facts(mocker, fake_ansible_module, XenAPI, xenserver, fixture_data_from_file):
    """Tests proper parsing of VM parameters and facts."""
    mocked_xenapi = mocker.patch.object(XenAPI.Session, 'xenapi', create=True)

    if "params" in list(fixture_data_from_file.keys())[0]:
        params_file = list(fixture_data_from_file.keys())[0]
        facts_file = list(fixture_data_from_file.keys())[1]
    else:
        params_file = list(fixture_data_from_file.keys())[1]
        facts_file = list(fixture_data_from_file.keys())[0]

    mocked_returns = {
        "VM.get_record.side_effect": lambda obj_ref: fixture_data_from_file[params_file]['VM'][obj_ref],
        "VM_metrics.get_record.side_effect": lambda obj_ref: fixture_data_from_file[params_file]['VM_metrics'][obj_ref],
        "VM_guest_metrics.get_record.side_effect": lambda obj_ref: fixture_data_from_file[params_file]['VM_guest_metrics'][obj_ref],
        "VBD.get_record.side_effect": lambda obj_ref: fixture_data_from_file[params_file]['VBD'][obj_ref],
        "VDI.get_record.side_effect": lambda obj_ref: fixture_data_from_file[params_file]['VDI'][obj_ref],
        "SR.get_record.side_effect": lambda obj_ref: fixture_data_from_file[params_file]['SR'][obj_ref],
        "VIF.get_record.side_effect": lambda obj_ref: fixture_data_from_file[params_file]['VIF'][obj_ref],
        "network.get_record.side_effect": lambda obj_ref: fixture_data_from_file[params_file]['network'][obj_ref],
        "host.get_record.side_effect": lambda obj_ref: fixture_data_from_file[params_file]['host'][obj_ref],
    }

    mocked_xenapi.configure_mock(**mocked_returns)

    mocker.patch('ansible.module_utils.xenserver.get_xenserver_version', return_value=[7, 2, 0])

    vm_ref = list(fixture_data_from_file[params_file]['VM'].keys())[0]

    assert xenserver.gather_vm_facts(fake_ansible_module, xenserver.gather_vm_params(fake_ansible_module, vm_ref)) == fixture_data_from_file[facts_file]
