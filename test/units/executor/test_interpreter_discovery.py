# -*- coding: utf-8 -*-
# (c) 2019, Jordan Borean <jborean@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import MagicMock

from ansible.executor.interpreter_discovery import discover_interpreter
from ansible.module_utils._text import to_text

mock_ubuntu_platform_res = to_text(
    r'{"osrelease_content": "NAME=\"Ubuntu\"\nVERSION=\"16.04.5 LTS (Xenial Xerus)\"\nID=ubuntu\nID_LIKE=debian\n'
    r'PRETTY_NAME=\"Ubuntu 16.04.5 LTS\"\nVERSION_ID=\"16.04\"\nHOME_URL=\"http://www.ubuntu.com/\"\n'
    r'SUPPORT_URL=\"http://help.ubuntu.com/\"\nBUG_REPORT_URL=\"http://bugs.launchpad.net/ubuntu/\"\n'
    r'VERSION_CODENAME=xenial\nUBUNTU_CODENAME=xenial\n", "platform_dist_result": ["Ubuntu", "16.04", "xenial"]}'
)


def test_discovery_interpreter_linux_auto_legacy():
    res1 = u'PLATFORM\nLinux\nFOUND\n/usr/bin/python\n/usr/bin/python3.5\n/usr/bin/python3\nENDFOUND'

    mock_action = MagicMock()
    mock_action._low_level_execute_command.side_effect = [{'stdout': res1}, {'stdout': mock_ubuntu_platform_res}]

    actual = discover_interpreter(mock_action, 'python', 'auto_legacy', {'inventory_hostname': u'host-fóöbär'})

    assert actual == u'/usr/bin/python'
    assert len(mock_action.method_calls) == 3
    assert mock_action.method_calls[2][0] == '_discovery_deprecation_warnings.append'
    assert u'Distribution Ubuntu 16.04 on host host-fóöbär should use /usr/bin/python3, but is using /usr/bin/python' \
           u' for backward compatibility' in mock_action.method_calls[2][1][0]['msg']
    assert mock_action.method_calls[2][1][0]['version'] == '2.12'


def test_discovery_interpreter_linux_auto_legacy_silent():
    res1 = u'PLATFORM\nLinux\nFOUND\n/usr/bin/python\n/usr/bin/python3.5\n/usr/bin/python3\nENDFOUND'

    mock_action = MagicMock()
    mock_action._low_level_execute_command.side_effect = [{'stdout': res1}, {'stdout': mock_ubuntu_platform_res}]

    actual = discover_interpreter(mock_action, 'python', 'auto_legacy_silent', {'inventory_hostname': u'host-fóöbär'})

    assert actual == u'/usr/bin/python'
    assert len(mock_action.method_calls) == 2


def test_discovery_interpreter_linux_auto():
    res1 = u'PLATFORM\nLinux\nFOUND\n/usr/bin/python\n/usr/bin/python3.5\n/usr/bin/python3\nENDFOUND'

    mock_action = MagicMock()
    mock_action._low_level_execute_command.side_effect = [{'stdout': res1}, {'stdout': mock_ubuntu_platform_res}]

    actual = discover_interpreter(mock_action, 'python', 'auto', {'inventory_hostname': u'host-fóöbär'})

    assert actual == u'/usr/bin/python3'
    assert len(mock_action.method_calls) == 2


def test_discovery_interpreter_non_linux():
    mock_action = MagicMock()
    mock_action._low_level_execute_command.return_value = \
        {'stdout': u'PLATFORM\nDarwin\nFOUND\n/usr/bin/python\nENDFOUND'}

    actual = discover_interpreter(mock_action, 'python', 'auto_legacy', {'inventory_hostname': u'host-fóöbär'})

    assert actual == u'/usr/bin/python'
    assert len(mock_action.method_calls) == 2
    assert mock_action.method_calls[1][0] == '_discovery_warnings.append'
    assert u'Platform darwin on host host-fóöbär is using the discovered Python interpreter at /usr/bin/python, ' \
           u'but future installation of another Python interpreter could change the meaning of that path' \
           in mock_action.method_calls[1][1][0]


def test_no_interpreters_found():
    mock_action = MagicMock()
    mock_action._low_level_execute_command.return_value = {'stdout': u'PLATFORM\nWindows\nFOUND\nENDFOUND'}

    actual = discover_interpreter(mock_action, 'python', 'auto_legacy', {'inventory_hostname': u'host-fóöbär'})

    assert actual == u'/usr/bin/python'
    assert len(mock_action.method_calls) == 2
    assert mock_action.method_calls[1][0] == '_discovery_warnings.append'
    assert u'No python interpreters found for host host-fóöbär (tried' \
           in mock_action.method_calls[1][1][0]
