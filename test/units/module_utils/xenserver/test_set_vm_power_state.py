# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import pytest

from .FakeAnsibleModule import FailJsonException
from .common import fake_xenapi_ref, testcase_bad_xenapi_refs


testcase_set_vm_power_state_bad_transitions = {
    "params": [
        ('restarted', 'Halted', "Cannot restart VM in state 'poweredoff'!"),
        ('restarted', 'Suspended', "Cannot restart VM in state 'suspended'!"),
        ('suspended', 'Halted', "Cannot suspend VM in state 'poweredoff'!"),
        ('suspended', 'Paused', "Cannot suspend VM in state 'paused'!"),
        ('shutdownguest', 'Halted', "Cannot shutdown guest when VM is in state 'poweredoff'!"),
        ('shutdownguest', 'Suspended', "Cannot shutdown guest when VM is in state 'suspended'!"),
        ('shutdownguest', 'Paused', "Cannot shutdown guest when VM is in state 'paused'!"),
        ('rebootguest', 'Halted', "Cannot reboot guest when VM is in state 'poweredoff'!"),
        ('rebootguest', 'Suspended', "Cannot reboot guest when VM is in state 'suspended'!"),
        ('rebootguest', 'Paused', "Cannot reboot guest when VM is in state 'paused'!"),
    ],
    "ids": [
        "poweredoff->restarted",
        "suspended->restarted",
        "poweredoff->suspended",
        "paused->suspended",
        "poweredoff->shutdownguest",
        "suspended->shutdownguest",
        "paused->shutdownguest",
        "poweredoff->rebootguest",
        "suspended->rebootguest",
        "paused->rebootguest",
    ],
}

testcase_set_vm_power_state_task_timeout = {
    "params": [
        ('shutdownguest', "Guest shutdown task failed: 'timeout'!"),
        ('rebootguest', "Guest reboot task failed: 'timeout'!"),
    ],
    "ids": [
        "shutdownguest-timeout",
        "rebootguest-timeout",
    ],
}

testcase_set_vm_power_state_no_transitions = {
    "params": [
        ('poweredon', "Running"),
        ('Poweredon', "Running"),
        ('powered-on', "Running"),
        ('Powered_on', "Running"),
        ('poweredoff', "Halted"),
        ('Poweredoff', "Halted"),
        ('powered-off', "Halted"),
        ('powered_off', "Halted"),
        ('suspended', "Suspended"),
        ('Suspended', "Suspended"),
    ],
    "ids": [
        "poweredon",
        "poweredon-cap",
        "poweredon-dash",
        "poweredon-under",
        "poweredoff",
        "poweredoff-cap",
        "poweredoff-dash",
        "poweredoff-under",
        "suspended",
        "suspended-cap",
    ],
}

testcase_set_vm_power_state_transitions = {
    "params": [
        ('poweredon', 'Halted', 'running', 'VM.start'),
        ('Poweredon', 'Halted', 'running', 'VM.start'),
        ('powered-on', 'Halted', 'running', 'VM.start'),
        ('Powered_on', 'Halted', 'running', 'VM.start'),
        ('poweredon', 'Suspended', 'running', 'VM.resume'),
        ('Poweredon', 'Suspended', 'running', 'VM.resume'),
        ('powered-on', 'Suspended', 'running', 'VM.resume'),
        ('Powered_on', 'Suspended', 'running', 'VM.resume'),
        ('poweredon', 'Paused', 'running', 'VM.unpause'),
        ('Poweredon', 'Paused', 'running', 'VM.unpause'),
        ('powered-on', 'Paused', 'running', 'VM.unpause'),
        ('Powered_on', 'Paused', 'running', 'VM.unpause'),
        ('poweredoff', 'Running', 'halted', 'VM.hard_shutdown'),
        ('Poweredoff', 'Running', 'halted', 'VM.hard_shutdown'),
        ('powered-off', 'Running', 'halted', 'VM.hard_shutdown'),
        ('powered_off', 'Running', 'halted', 'VM.hard_shutdown'),
        ('poweredoff', 'Suspended', 'halted', 'VM.hard_shutdown'),
        ('Poweredoff', 'Suspended', 'halted', 'VM.hard_shutdown'),
        ('powered-off', 'Suspended', 'halted', 'VM.hard_shutdown'),
        ('powered_off', 'Suspended', 'halted', 'VM.hard_shutdown'),
        ('poweredoff', 'Paused', 'halted', 'VM.hard_shutdown'),
        ('Poweredoff', 'Paused', 'halted', 'VM.hard_shutdown'),
        ('powered-off', 'Paused', 'halted', 'VM.hard_shutdown'),
        ('powered_off', 'Paused', 'halted', 'VM.hard_shutdown'),
        ('restarted', 'Running', 'running', 'VM.hard_reboot'),
        ('Restarted', 'Running', 'running', 'VM.hard_reboot'),
        ('restarted', 'Paused', 'running', 'VM.hard_reboot'),
        ('Restarted', 'Paused', 'running', 'VM.hard_reboot'),
        ('suspended', 'Running', 'suspended', 'VM.suspend'),
        ('Suspended', 'Running', 'suspended', 'VM.suspend'),
        ('shutdownguest', 'Running', 'halted', 'VM.clean_shutdown'),
        ('Shutdownguest', 'Running', 'halted', 'VM.clean_shutdown'),
        ('shutdown-guest', 'Running', 'halted', 'VM.clean_shutdown'),
        ('shutdown_guest', 'Running', 'halted', 'VM.clean_shutdown'),
        ('rebootguest', 'Running', 'running', 'VM.clean_reboot'),
        ('rebootguest', 'Running', 'running', 'VM.clean_reboot'),
        ('reboot-guest', 'Running', 'running', 'VM.clean_reboot'),
        ('reboot_guest', 'Running', 'running', 'VM.clean_reboot'),
    ],
    "ids": [
        "poweredoff->poweredon",
        "poweredoff->poweredon-cap",
        "poweredoff->poweredon-dash",
        "poweredoff->poweredon-under",
        "suspended->poweredon",
        "suspended->poweredon-cap",
        "suspended->poweredon-dash",
        "suspended->poweredon-under",
        "paused->poweredon",
        "paused->poweredon-cap",
        "paused->poweredon-dash",
        "paused->poweredon-under",
        "poweredon->poweredoff",
        "poweredon->poweredoff-cap",
        "poweredon->poweredoff-dash",
        "poweredon->poweredoff-under",
        "suspended->poweredoff",
        "suspended->poweredoff-cap",
        "suspended->poweredoff-dash",
        "suspended->poweredoff-under",
        "paused->poweredoff",
        "paused->poweredoff-cap",
        "paused->poweredoff-dash",
        "paused->poweredoff-under",
        "poweredon->restarted",
        "poweredon->restarted-cap",
        "paused->restarted",
        "paused->restarted-cap",
        "poweredon->suspended",
        "poweredon->suspended-cap",
        "poweredon->shutdownguest",
        "poweredon->shutdownguest-cap",
        "poweredon->shutdownguest-dash",
        "poweredon->shutdownguest-under",
        "poweredon->rebootguest",
        "poweredon->rebootguest-cap",
        "poweredon->rebootguest-dash",
        "poweredon->rebootguest-under",
    ],
}

testcase_set_vm_power_state_transitions_async = {
    "params": [
        ('shutdownguest', 'Running', 'halted', 'Async.VM.clean_shutdown'),
        ('Shutdownguest', 'Running', 'halted', 'Async.VM.clean_shutdown'),
        ('shutdown-guest', 'Running', 'halted', 'Async.VM.clean_shutdown'),
        ('shutdown_guest', 'Running', 'halted', 'Async.VM.clean_shutdown'),
        ('rebootguest', 'Running', 'running', 'Async.VM.clean_reboot'),
        ('rebootguest', 'Running', 'running', 'Async.VM.clean_reboot'),
        ('reboot-guest', 'Running', 'running', 'Async.VM.clean_reboot'),
        ('reboot_guest', 'Running', 'running', 'Async.VM.clean_reboot'),
    ],
    "ids": [
        "poweredon->shutdownguest",
        "poweredon->shutdownguest-cap",
        "poweredon->shutdownguest-dash",
        "poweredon->shutdownguest-under",
        "poweredon->rebootguest",
        "poweredon->rebootguest-cap",
        "poweredon->rebootguest-dash",
        "poweredon->rebootguest-under",
    ],
}


@pytest.mark.parametrize('vm_ref', testcase_bad_xenapi_refs['params'], ids=testcase_bad_xenapi_refs['ids'])
def test_set_vm_power_state_bad_vm_ref(fake_ansible_module, xenserver, vm_ref):
    """Tests failure on bad vm_ref."""
    with pytest.raises(FailJsonException) as exc_info:
        xenserver.set_vm_power_state(fake_ansible_module, vm_ref, None)

    assert exc_info.value.kwargs['msg'] == "Cannot set VM power state. Invalid VM reference supplied!"


def test_set_vm_power_state_xenapi_failure(mock_xenapi_failure, fake_ansible_module, xenserver):
    """Tests catching of XenAPI failures."""
    with pytest.raises(FailJsonException) as exc_info:
        xenserver.set_vm_power_state(fake_ansible_module, fake_xenapi_ref('VM'), "poweredon")

    assert exc_info.value.kwargs['msg'] == "XAPI ERROR: %s" % mock_xenapi_failure[1]


def test_set_vm_power_state_bad_power_state(mocker, fake_ansible_module, XenAPI, xenserver):
    """Tests failure on unsupported power state."""
    mocked_xenapi = mocker.patch.object(XenAPI.Session, 'xenapi', create=True)

    mocked_returns = {
        "VM.get_power_state.return_value": "Running",
    }

    mocked_xenapi.configure_mock(**mocked_returns)

    with pytest.raises(FailJsonException) as exc_info:
        xenserver.set_vm_power_state(fake_ansible_module, fake_xenapi_ref('VM'), "bad")

    # Beside VM.get_power_state() no other method should have been
    # called additionally.
    assert len(mocked_xenapi.method_calls) == 1

    assert exc_info.value.kwargs['msg'] == "Requested VM power state 'bad' is unsupported!"


@pytest.mark.parametrize('power_state_desired, power_state_current, error_msg',
                         testcase_set_vm_power_state_bad_transitions['params'],
                         ids=testcase_set_vm_power_state_bad_transitions['ids'])
def test_set_vm_power_state_bad_transition(mocker, fake_ansible_module, XenAPI, xenserver, power_state_desired, power_state_current, error_msg):
    """Tests failure on bad power state transition."""
    mocked_xenapi = mocker.patch.object(XenAPI.Session, 'xenapi', create=True)

    mocked_returns = {
        "VM.get_power_state.return_value": power_state_current,
    }

    mocked_xenapi.configure_mock(**mocked_returns)

    with pytest.raises(FailJsonException) as exc_info:
        xenserver.set_vm_power_state(fake_ansible_module, fake_xenapi_ref('VM'), power_state_desired)

    # Beside VM.get_power_state() no other method should have been
    # called additionally.
    assert len(mocked_xenapi.method_calls) == 1

    assert exc_info.value.kwargs['msg'] == error_msg


@pytest.mark.parametrize('power_state, error_msg',
                         testcase_set_vm_power_state_task_timeout['params'],
                         ids=testcase_set_vm_power_state_task_timeout['ids'])
def test_set_vm_power_state_task_timeout(mocker, fake_ansible_module, XenAPI, xenserver, power_state, error_msg):
    """Tests failure on async task timeout."""
    mocked_xenapi = mocker.patch.object(XenAPI.Session, 'xenapi', create=True)

    mocked_returns = {
        "VM.get_power_state.return_value": "Running",
        "Async.VM.clean_shutdown.return_value": fake_xenapi_ref('task'),
        "Async.VM.clean_reboot.return_value": fake_xenapi_ref('task'),
    }

    mocked_xenapi.configure_mock(**mocked_returns)

    mocker.patch('ansible.module_utils.xenserver.wait_for_task', return_value="timeout")

    with pytest.raises(FailJsonException) as exc_info:
        xenserver.set_vm_power_state(fake_ansible_module, fake_xenapi_ref('VM'), power_state, timeout=1)

    # Beside VM.get_power_state() only one of Async.VM.clean_shutdown or
    # Async.VM.clean_reboot should have been called additionally.
    assert len(mocked_xenapi.method_calls) == 2

    assert exc_info.value.kwargs['msg'] == error_msg


@pytest.mark.parametrize('power_state_desired, power_state_current',
                         testcase_set_vm_power_state_no_transitions['params'],
                         ids=testcase_set_vm_power_state_no_transitions['ids'])
def test_set_vm_power_state_no_transition(mocker, fake_ansible_module, XenAPI, xenserver, power_state_desired, power_state_current):
    """Tests regular invocation without power state transition."""
    mocked_xenapi = mocker.patch.object(XenAPI.Session, 'xenapi', create=True)

    mocked_returns = {
        "VM.get_power_state.return_value": power_state_current,
    }

    mocked_xenapi.configure_mock(**mocked_returns)

    result = xenserver.set_vm_power_state(fake_ansible_module, fake_xenapi_ref('VM'), power_state_desired)

    # Beside VM.get_power_state() no other method should have been
    # called additionally.
    assert len(mocked_xenapi.method_calls) == 1

    assert result[0] is False
    assert result[1] == power_state_current.lower()


@pytest.mark.parametrize('power_state_desired, power_state_current, power_state_resulting, activated_xenapi_method',
                         testcase_set_vm_power_state_transitions['params'],
                         ids=testcase_set_vm_power_state_transitions['ids'])
def test_set_vm_power_state_transition(mocker,
                                       fake_ansible_module,
                                       XenAPI,
                                       xenserver,
                                       power_state_desired,
                                       power_state_current,
                                       power_state_resulting,
                                       activated_xenapi_method):
    """Tests regular invocation with power state transition."""
    mocked_xenapi = mocker.patch.object(XenAPI.Session, 'xenapi', create=True)

    mocked_returns = {
        "VM.get_power_state.return_value": power_state_current,
    }

    mocked_xenapi.configure_mock(**mocked_returns)

    result = xenserver.set_vm_power_state(fake_ansible_module, fake_xenapi_ref('VM'), power_state_desired, timeout=0)

    mocked_xenapi_method = mocked_xenapi

    for activated_xenapi_class in activated_xenapi_method.split('.'):
        mocked_xenapi_method = getattr(mocked_xenapi_method, activated_xenapi_class)

    mocked_xenapi_method.assert_called_once()

    # Beside VM.get_power_state() only activated_xenapi_method should have
    # been called additionally.
    assert len(mocked_xenapi.method_calls) == 2

    assert result[0] is True
    assert result[1] == power_state_resulting


@pytest.mark.parametrize('power_state_desired, power_state_current, power_state_resulting, activated_xenapi_method',
                         testcase_set_vm_power_state_transitions_async['params'],
                         ids=testcase_set_vm_power_state_transitions_async['ids'])
def test_set_vm_power_state_transition_async(mocker,
                                             fake_ansible_module,
                                             XenAPI,
                                             xenserver,
                                             power_state_desired,
                                             power_state_current,
                                             power_state_resulting,
                                             activated_xenapi_method):
    """
    Tests regular invocation with async power state transition
    (shutdownguest and rebootguest only).
    """
    mocked_xenapi = mocker.patch.object(XenAPI.Session, 'xenapi', create=True)

    mocked_returns = {
        "VM.get_power_state.return_value": power_state_current,
        "%s.return_value" % activated_xenapi_method: fake_xenapi_ref('task'),
    }

    mocked_xenapi.configure_mock(**mocked_returns)

    mocker.patch('ansible.module_utils.xenserver.wait_for_task', return_value="")

    result = xenserver.set_vm_power_state(fake_ansible_module, fake_xenapi_ref('VM'), power_state_desired, timeout=1)

    mocked_xenapi_method = mocked_xenapi

    for activated_xenapi_class in activated_xenapi_method.split('.'):
        mocked_xenapi_method = getattr(mocked_xenapi_method, activated_xenapi_class)

    mocked_xenapi_method.assert_called_once()

    # Beside VM.get_power_state() only activated_xenapi_method should have
    # been called additionally.
    assert len(mocked_xenapi.method_calls) == 2

    assert result[0] is True
    assert result[1] == power_state_resulting


@pytest.mark.parametrize('power_state_desired, power_state_current, power_state_resulting, activated_xenapi_method',
                         testcase_set_vm_power_state_transitions['params'],
                         ids=testcase_set_vm_power_state_transitions['ids'])
def test_set_vm_power_state_transition_check_mode(mocker,
                                                  fake_ansible_module,
                                                  XenAPI,
                                                  xenserver,
                                                  power_state_desired,
                                                  power_state_current,
                                                  power_state_resulting,
                                                  activated_xenapi_method):
    """Tests regular invocation with power state transition in check mode."""
    mocked_xenapi = mocker.patch.object(XenAPI.Session, 'xenapi', create=True)

    mocked_returns = {
        "VM.get_power_state.return_value": power_state_current,
    }

    mocked_xenapi.configure_mock(**mocked_returns)

    fake_ansible_module.check_mode = True
    result = xenserver.set_vm_power_state(fake_ansible_module, fake_xenapi_ref('VM'), power_state_desired, timeout=0)

    mocked_xenapi_method = mocked_xenapi

    for activated_xenapi_class in activated_xenapi_method.split('.'):
        mocked_xenapi_method = getattr(mocked_xenapi_method, activated_xenapi_class)

    mocked_xenapi_method.assert_not_called()

    # Beside VM.get_power_state() no other method should have been
    # called additionally.
    assert len(mocked_xenapi.method_calls) == 1

    assert result[0] is True
    assert result[1] == power_state_resulting
