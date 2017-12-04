#
# (c) 2017 Michael Tinning
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

import json
from copy import deepcopy

import pytest

from ansible.module_utils._text import to_bytes
from ansible.module_utils import basic
from ansible.module_utils.ec2 import HAS_BOTO3

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_elb_application_lb.py requires the `boto3` and `botocore` modules")

import ansible.modules.cloud.amazon.elb_application_lb as elb_module


@pytest.fixture
def listener():
    return {
        'Protocol': 'HTTP',
        'Port': 80,
        'DefaultActions': [{
            'Type': 'forward',
            'TargetGroupName': 'target-group'
        }],
        'Rules': [{
            'Conditions': [{
                'Field': 'host-header',
                'Values': [
                    'www.example.com'
                ]
            }],
            'Priority': 1,
            'Actions': [{
                'TargetGroupName': 'other-target-group',
                'Type': 'forward'
            }]
        }]
    }


@pytest.fixture
def compare_listeners(mocker):
    return mocker.Mock()


@pytest.fixture
def ensure_listeners(mocker):
    ensure_listeners_mock = mocker.Mock()
    ensure_listeners_mock.return_value = []
    return ensure_listeners_mock


@pytest.fixture
def compare_rules(mocker):
    compare_rules_mock = mocker.Mock()
    compare_rules_mock.return_value = ([], [], [])
    return compare_rules_mock


@pytest.fixture
def get_elb_listeners(mocker):
    get_elb_listeners_mock = mocker.Mock()
    get_elb_listeners_mock.return_value = []
    return get_elb_listeners_mock


@pytest.fixture
def elb(mocker, monkeypatch, compare_listeners, ensure_listeners, compare_rules, get_elb_listeners):
    monkeypatch.setattr(elb_module, "ensure_listeners_default_action_has_arn", ensure_listeners)
    monkeypatch.setattr(elb_module, "get_elb_listeners", get_elb_listeners)
    monkeypatch.setattr(elb_module, "ensure_rules_action_has_arn", mocker.Mock())
    monkeypatch.setattr(elb_module, "get_listener", mocker.Mock())
    monkeypatch.setattr(elb_module, "compare_rules", compare_rules)
    monkeypatch.setattr(elb_module, "compare_listeners", compare_listeners)
    return elb_module


@pytest.fixture
def created_listener(mocker, listener):
    return {
        'Port': listener['Port'],
        'ListenerArn': 'new-listener-arn'
    }


@pytest.fixture
def connection(mocker, created_listener):
    connection_mock = mocker.Mock()
    connection_mock.create_listener.return_value = {
        'Listeners': [created_listener]
    }
    return connection_mock


@pytest.fixture
def existing_elb():
    return {'LoadBalancerArn': 'fake'}


def test_create_listeners_called_with_correct_args(mocker, connection, listener, elb, compare_listeners, existing_elb):
    compare_listeners.return_value = ([listener], [], [])

    elb.create_or_update_elb_listeners(connection, mocker.Mock(), existing_elb)

    connection.create_listener.assert_called_once_with(
        Protocol=listener['Protocol'],
        Port=listener['Port'],
        DefaultActions=listener['DefaultActions'],
        LoadBalancerArn=existing_elb['LoadBalancerArn']
    )


def test_modify_listeners_called_with_correct_args(mocker, connection, listener, elb, compare_listeners, existing_elb):
    # In the case of modify listener, LoadBalancerArn is set in compare_listeners
    listener['LoadBalancerArn'] = existing_elb['LoadBalancerArn']
    compare_listeners.return_value = ([], [listener], [])

    elb.create_or_update_elb_listeners(connection, mocker.Mock(), existing_elb)

    connection.modify_listener.assert_called_once_with(
        Protocol=listener['Protocol'],
        Port=listener['Port'],
        DefaultActions=listener['DefaultActions'],
        LoadBalancerArn=existing_elb['LoadBalancerArn']
    )


def test_compare_rules_called_with_new_listener(
    mocker,
    connection,
    listener,
    elb,
    compare_listeners,
    ensure_listeners,
    compare_rules,
    existing_elb,
    created_listener
):
    compare_listeners.return_value = ([listener], [], [])
    listener_from_ensure_listeners = deepcopy(listener)
    ensure_listeners.return_value = [listener_from_ensure_listeners]

    elb.create_or_update_elb_listeners(connection, mocker.Mock(), existing_elb)

    (_conn, _module, current_listeners, _listener), _kwargs = compare_rules.call_args

    assert created_listener in current_listeners
