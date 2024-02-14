# -*- coding: utf-8 -*-
# (c) 2019, Jordan Borean <jborean@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from ansible.executor.interpreter_discovery import discover_interpreter
from ansible.module_utils.common.text.converters import to_text
from ansible.errors import AnsibleConnectionFailure

mock_ubuntu_platform_res = to_text(
    r'{"osrelease_content": "NAME=\"Ansible Test\"\nVERSION=\"100\"\nID=ansible-test\nID_LIKE=debian\n'
    r'PRETTY_NAME=\"Ansible Test 100\"\nVERSION_ID=\"100\"\nHOME_URL=\"http://ansible.com/\"\n'
    r'SUPPORT_URL=\"http://github.com/ansible/ansible\"\nBUG_REPORT_URL=\"http://github.com/ansible/ansible/\"\n'
    r'VERSION_CODENAME=beans\nUBUNTU_CODENAME=beans\n", "platform_dist_result": ["Ansible Test", "100", "beans"]}'
)


def test_discovery_interpreter_linux_auto_legacy():
    res1 = u'PLATFORM\nLinux\nFOUND\n/usr/bin/python99\n/usr/bin/python3\nENDFOUND'

    mock_action = MagicMock()
    mock_action._low_level_execute_command.side_effect = [{'stdout': res1}, {'stdout': mock_ubuntu_platform_res}]

    actual = discover_interpreter(mock_action, 'python', 'auto_legacy', {'inventory_hostname': u'host-fóöbär'})

    assert actual == u'/usr/bin/python3'
    assert len(mock_action.method_calls) == 3
    assert mock_action.method_calls[2][0] == '_discovery_warnings.append'
    assert u'Distribution Ansible Test 100 on host host-fóöbär should use /usr/bin/python99, but is using /usr/bin/python3' \
           u' for backward compatibility' in mock_action.method_calls[2][1][0]


def test_discovery_interpreter_linux_auto_legacy_silent():
    res1 = u'PLATFORM\nLinux\nFOUND\n/usr/bin/python3.9\n/usr/bin/python3\nENDFOUND'

    mock_action = MagicMock()
    mock_action._low_level_execute_command.side_effect = [{'stdout': res1}, {'stdout': mock_ubuntu_platform_res}]

    actual = discover_interpreter(mock_action, 'python', 'auto_legacy_silent', {'inventory_hostname': u'host-fóöbär'})

    assert actual == u'/usr/bin/python3'
    assert len(mock_action.method_calls) == 2


def test_discovery_interpreter_linux_auto():
    res1 = u'PLATFORM\nLinux\nFOUND\n/usr/bin/python99\n/usr/bin/python3\nENDFOUND'

    mock_action = MagicMock()
    mock_action._low_level_execute_command.side_effect = [{'stdout': res1}, {'stdout': mock_ubuntu_platform_res}]

    actual = discover_interpreter(mock_action, 'python', 'auto', {'inventory_hostname': u'host-fóöbär'})

    assert actual == u'/usr/bin/python99'
    assert len(mock_action.method_calls) == 2


def test_discovery_interpreter_non_linux():
    mock_action = MagicMock()
    mock_action._low_level_execute_command.return_value = \
        {'stdout': u'PLATFORM\nDarwin\nFOUND\n/usr/bin/python3\nENDFOUND'}

    actual = discover_interpreter(mock_action, 'python', 'auto_legacy', {'inventory_hostname': u'host-fóöbär'})

    assert actual == u'/usr/bin/python3'
    assert len(mock_action.method_calls) == 2
    assert mock_action.method_calls[1][0] == '_discovery_warnings.append'
    assert u'Platform darwin on host host-fóöbär is using the discovered Python interpreter at /usr/bin/python3, ' \
           u'but future installation of another Python interpreter could change the meaning of that path' \
           in mock_action.method_calls[1][1][0]


def test_no_interpreters_found():
    mock_action = MagicMock()
    mock_action._low_level_execute_command.return_value = {'stdout': u'PLATFORM\nWindows\nFOUND\nENDFOUND'}

    actual = discover_interpreter(mock_action, 'python', 'auto_legacy', {'inventory_hostname': u'host-fóöbär'})

    assert actual == u'/usr/bin/python3'
    assert len(mock_action.method_calls) == 2
    assert mock_action.method_calls[1][0] == '_discovery_warnings.append'
    assert u'No python interpreters found for host host-fóöbär (tried' \
           in mock_action.method_calls[1][1][0]


def test_ansible_error_exception():
    mock_action = MagicMock()
    mock_action._low_level_execute_command.side_effect = AnsibleConnectionFailure("host key mismatch")

    with pytest.raises(AnsibleConnectionFailure) as context:
        discover_interpreter(mock_action, 'python', 'auto_legacy', {'inventory_hostname': u'host'})

    assert 'host key mismatch' == str(context.value)
