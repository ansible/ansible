# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import pytest

from .FakeAnsibleModule import FailJsonException
from .common import fake_xenapi_ref, testcase_bad_xenapi_refs


testcase_wait_for_vm_ip_address_bad_power_states = {
    "params": [
        'Halted',
        'Paused',
        'Suspended',
        'Other',
    ],
    "ids": [
        'state-halted',
        'state-paused',
        'state-suspended',
        'state-other',
    ]
}

testcase_wait_for_vm_ip_address_bad_guest_metrics = {
    "params": [
        ('OpaqueRef:NULL', {"networks": {}}),
        (fake_xenapi_ref('VM_guest_metrics'), {"networks": {}}),
    ],
    "ids": [
        'vm_guest_metrics_ref-null, no-ip',
        'vm_guest_metrics_ref-ok, no-ip',
    ],
}

testcase_wait_for_task_all_statuses = {
    "params": [
        ('Success', ''),
        ('Failure', 'failure'),
        ('Cancelling', 'cancelling'),
        ('Cancelled', 'cancelled'),
        ('Other', 'other'),
    ],
    "ids": [
        'task-success',
        'task-failure',
        'task-cancelling',
        'task-cancelled',
        'task-other',
    ]
}


@pytest.mark.parametrize('vm_ref', testcase_bad_xenapi_refs['params'], ids=testcase_bad_xenapi_refs['ids'])
def test_wait_for_vm_ip_address_bad_vm_ref(fake_ansible_module, xenserver, vm_ref):
    """Tests failure on bad vm_ref."""
    with pytest.raises(FailJsonException) as exc_info:
        xenserver.wait_for_vm_ip_address(fake_ansible_module, vm_ref)

    assert exc_info.value.kwargs['msg'] == "Cannot wait for VM IP address. Invalid VM reference supplied!"


def test_wait_for_vm_ip_address_xenapi_failure(mock_xenapi_failure, xenserver, fake_ansible_module):
    """Tests catching of XenAPI failures."""
    with pytest.raises(FailJsonException) as exc_info:
        xenserver.wait_for_vm_ip_address(fake_ansible_module, fake_xenapi_ref('VM'))

    assert exc_info.value.kwargs['msg'] == "XAPI ERROR: %s" % mock_xenapi_failure[1]


@pytest.mark.parametrize('bad_power_state',
                         testcase_wait_for_vm_ip_address_bad_power_states['params'],
                         ids=testcase_wait_for_vm_ip_address_bad_power_states['ids'])
def test_wait_for_vm_ip_address_bad_power_state(mocker, fake_ansible_module, XenAPI, xenserver, bad_power_state):
    """Tests failure on bad power state."""
    mocked_xenapi = mocker.patch.object(XenAPI.Session, 'xenapi', create=True)

    mocked_returns = {
        "VM.get_power_state.return_value": bad_power_state,
    }

    mocked_xenapi.configure_mock(**mocked_returns)

    with pytest.raises(FailJsonException) as exc_info:
        xenserver.wait_for_vm_ip_address(fake_ansible_module, fake_xenapi_ref('VM'))

    assert exc_info.value.kwargs['msg'] == ("Cannot wait for VM IP address when VM is in state '%s'!" %
                                            xenserver.xapi_to_module_vm_power_state(bad_power_state.lower()))


@pytest.mark.parametrize('bad_guest_metrics_ref, bad_guest_metrics',
                         testcase_wait_for_vm_ip_address_bad_guest_metrics['params'],
                         ids=testcase_wait_for_vm_ip_address_bad_guest_metrics['ids'])
def test_wait_for_vm_ip_address_timeout(mocker, fake_ansible_module, XenAPI, xenserver, bad_guest_metrics_ref, bad_guest_metrics):
    """Tests timeout."""
    mocked_xenapi = mocker.patch.object(XenAPI.Session, 'xenapi', create=True)

    mocked_returns = {
        "VM.get_power_state.return_value": "Running",
        "VM.get_guest_metrics.return_value": bad_guest_metrics_ref,
        "VM_guest_metrics.get_record.return_value": bad_guest_metrics,
    }

    mocked_xenapi.configure_mock(**mocked_returns)

    mocker.patch('time.sleep')

    with pytest.raises(FailJsonException) as exc_info:
        xenserver.wait_for_vm_ip_address(fake_ansible_module, fake_xenapi_ref('VM'), timeout=1)

    assert exc_info.value.kwargs['msg'] == "Timed out waiting for VM IP address!"


def test_wait_for_vm_ip_address(mocker, fake_ansible_module, XenAPI, xenserver):
    """Tests regular invocation."""
    mocked_xenapi = mocker.patch.object(XenAPI.Session, 'xenapi', create=True)

    # This mock simulates regular VM IP acquirement lifecycle:
    #
    # 1) First, no guest metrics are available because VM is not yet fully
    #    booted and guest agent is not yet started.
    # 2) Next, guest agent is started and guest metrics are available but
    #    IP address is still not acquired.
    # 3) Lastly, IP address is acquired by VM on its primary VIF.
    mocked_returns = {
        "VM.get_power_state.return_value": "Running",
        "VM.get_guest_metrics.side_effect": [
            'OpaqueRef:NULL',
            fake_xenapi_ref('VM_guest_metrics'),
            fake_xenapi_ref('VM_guest_metrics'),
        ],
        "VM_guest_metrics.get_record.side_effect": [
            {
                "networks": {},
            },
            {
                "networks": {
                    "0/ip": "192.168.0.1",
                    "1/ip": "10.0.0.1",
                },
            },
        ],
    }

    mocked_xenapi.configure_mock(**mocked_returns)

    mocker.patch('time.sleep')

    fake_guest_metrics = xenserver.wait_for_vm_ip_address(fake_ansible_module, fake_xenapi_ref('VM'))

    assert fake_guest_metrics == mocked_returns['VM_guest_metrics.get_record.side_effect'][1]


@pytest.mark.parametrize('task_ref', testcase_bad_xenapi_refs['params'], ids=testcase_bad_xenapi_refs['ids'])
def test_wait_for_task_bad_task_ref(fake_ansible_module, xenserver, task_ref):
    """Tests failure on bad task_ref."""
    with pytest.raises(FailJsonException) as exc_info:
        xenserver.wait_for_task(fake_ansible_module, task_ref)

    assert exc_info.value.kwargs['msg'] == "Cannot wait for task. Invalid task reference supplied!"


def test_wait_for_task_xenapi_failure(mock_xenapi_failure, fake_ansible_module, xenserver):
    """Tests catching of XenAPI failures."""
    with pytest.raises(FailJsonException) as exc_info:
        xenserver.wait_for_task(fake_ansible_module, fake_xenapi_ref('task'))

    assert exc_info.value.kwargs['msg'] == "XAPI ERROR: %s" % mock_xenapi_failure[1]


def test_wait_for_task_timeout(mocker, fake_ansible_module, XenAPI, xenserver):
    """Tests timeout."""
    mocked_xenapi = mocker.patch.object(XenAPI.Session, 'xenapi', create=True)

    mocked_returns = {
        "task.get_status.return_value": "Pending",
        "task.destroy.return_value": None,
    }

    mocked_xenapi.configure_mock(**mocked_returns)

    mocker.patch('time.sleep')

    fake_result = xenserver.wait_for_task(fake_ansible_module, fake_xenapi_ref('task'), timeout=1)

    mocked_xenapi.task.destroy.assert_called_once()
    assert fake_result == "timeout"


@pytest.mark.parametrize('task_status, result',
                         testcase_wait_for_task_all_statuses['params'],
                         ids=testcase_wait_for_task_all_statuses['ids'])
def test_wait_for_task(mocker, fake_ansible_module, XenAPI, xenserver, task_status, result):
    """Tests regular invocation."""
    mocked_xenapi = mocker.patch.object(XenAPI.Session, 'xenapi', create=True)

    # Mock will first return Pending status and on second invocation it will
    # return one of possible final statuses.
    mocked_returns = {
        "task.get_status.side_effect": [
            'Pending',
            task_status,
        ],
        "task.destroy.return_value": None,
    }

    mocked_xenapi.configure_mock(**mocked_returns)

    mocker.patch('time.sleep')

    fake_result = xenserver.wait_for_task(fake_ansible_module, fake_xenapi_ref('task'))

    mocked_xenapi.task.destroy.assert_called_once()
    assert fake_result == result
