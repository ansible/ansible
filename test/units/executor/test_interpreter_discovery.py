# -*- coding: utf-8 -*-
# (c) 2019, Jordan Borean <jborean@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import re
import typing as t

from unittest.mock import Mock

import pytest
import pytest_mock

from ansible.executor.interpreter_discovery import discover_interpreter
from ansible.module_utils.common.text.converters import to_text
from ansible.errors import AnsibleConnectionFailure


mock_ubuntu_platform_res = to_text(
    r'{"osrelease_content": "NAME=\"Ansible Test\"\nVERSION=\"100\"\nID=ansible-test\nID_LIKE=debian\n'
    r'PRETTY_NAME=\"Ansible Test 100\"\nVERSION_ID=\"100\"\nHOME_URL=\"http://ansible.com/\"\n'
    r'SUPPORT_URL=\"http://github.com/ansible/ansible\"\nBUG_REPORT_URL=\"http://github.com/ansible/ansible/\"\n'
    r'VERSION_CODENAME=beans\nUBUNTU_CODENAME=beans\n", "platform_dist_result": ["Ansible Test", "100", "beans"]}'
)


@pytest.fixture
def mock_display(mocker: pytest_mock.MockerFixture) -> t.Iterator[Mock]:
    yield mocker.patch('ansible.executor.interpreter_discovery.display', Mock())


def test_discovery_interpreter_linux_auto_legacy(mock_display: Mock) -> None:
    res1 = u'PLATFORM\nLinux\nFOUND\n/usr/bin/python99\n/usr/bin/python3\nENDFOUND'

    mock_action = Mock()
    mock_action._low_level_execute_command.side_effect = [{'stdout': res1}, {'stdout': mock_ubuntu_platform_res}]

    actual = discover_interpreter(mock_action, 'python', 'auto_legacy', {'inventory_hostname': u'host-fóöbär'})

    assert actual == u'/usr/bin/python3'
    assert len(mock_action.method_calls) > 1
    assert len(mock_display.warning.mock_calls) >= 1

    expected_warning = ("Distribution 'Ansible Test' '100' on host 'host-fóöbär' should use '/usr/bin/python99', "
                        "but is using '/usr/bin/python3' for backward compatibility with prior Ansible releases.")

    # this is broken out to allow pytest assert rewrite to show the candidate values instead of `<genexpr>` on failure
    candidate_msgs = [call.kwargs['msg'] for call in mock_display.warning.mock_calls if 'msg' in call.kwargs]
    assert expected_warning in candidate_msgs


def test_discovery_interpreter_linux_auto_legacy_silent() -> None:
    res1 = u'PLATFORM\nLinux\nFOUND\n/usr/bin/python3.9\n/usr/bin/python3\nENDFOUND'

    mock_action = Mock()
    mock_action._low_level_execute_command.side_effect = [{'stdout': res1}, {'stdout': mock_ubuntu_platform_res}]

    actual = discover_interpreter(mock_action, 'python', 'auto_legacy_silent', {'inventory_hostname': u'host-fóöbär'})

    assert actual == u'/usr/bin/python3'
    assert len(mock_action.method_calls) == 2


def test_discovery_interpreter_linux_auto() -> None:
    res1 = u'PLATFORM\nLinux\nFOUND\n/usr/bin/python99\n/usr/bin/python3\nENDFOUND'

    mock_action = Mock()
    mock_action._low_level_execute_command.side_effect = [{'stdout': res1}, {'stdout': mock_ubuntu_platform_res}]

    actual = discover_interpreter(mock_action, 'python', 'auto', {'inventory_hostname': u'host-fóöbär'})

    assert actual == u'/usr/bin/python99'
    assert len(mock_action.method_calls) == 2


def test_discovery_interpreter_non_linux(mock_display: Mock) -> None:
    mock_action = Mock()
    mock_action._low_level_execute_command.return_value = \
        {'stdout': u'PLATFORM\nDarwin\nFOUND\n/usr/bin/python3\nENDFOUND'}

    actual = discover_interpreter(mock_action, 'python', 'auto_legacy', {'inventory_hostname': u'host-fóöbär'})

    assert actual == u'/usr/bin/python3'
    assert len(mock_action.method_calls) == 1
    expected_warning = ("Platform 'darwin' on host 'host-fóöbär' is using the discovered Python interpreter at '/usr/bin/python3', "
                        "but future installation of another Python interpreter could cause a different interpreter to be discovered.")

    # this is broken out to allow pytest assert rewrite to show the candidate values instead of `<genexpr>` on failure
    candidate_msgs = [call.kwargs['msg'] for call in mock_display.warning.mock_calls if 'msg' in call.kwargs]
    assert expected_warning in candidate_msgs


def test_no_interpreters_found(mock_display: Mock) -> None:
    mock_action = Mock()
    mock_action._low_level_execute_command.return_value = {'stdout': u'PLATFORM\nWindows\nFOUND\nENDFOUND'}

    actual = discover_interpreter(mock_action, 'python', 'auto_legacy', {'inventory_hostname': u'host-fóöbär'})

    assert actual == u'/usr/bin/python3'
    assert len(mock_action.method_calls) == 1

    expected_warning = "No python interpreters found for host 'host-fóöbär'"

    # lop off the part that changes over time, if present
    # this is broken out to allow pytest assert rewrite to show the candidate values instead of `<genexpr>` on failure
    candidate_msgs = [re.sub(r' \(tried .*\)\.$', '', call.kwargs['msg']) for call in mock_display.warning.mock_calls if 'msg' in call.kwargs]
    assert expected_warning in candidate_msgs


def test_ansible_error_exception() -> None:
    mock_action = Mock()
    mock_action._low_level_execute_command.side_effect = AnsibleConnectionFailure("host key mismatch")

    with pytest.raises(AnsibleConnectionFailure) as context:
        discover_interpreter(mock_action, 'python', 'auto_legacy', {'inventory_hostname': u'host'})

    assert 'host key mismatch' == str(context.value)
