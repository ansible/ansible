# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import pytest

from ansible.modules.debconf import get_password_value


password_testdata = [
    pytest.param(
        (
            "ddclient2	ddclient/password1	password	Sample",
            "ddclient2",
            "ddclient/password1",
            "password",
        ),
        "Sample",
        id="valid_password",
    ),
    pytest.param(
        (
            "ddclient2	ddclient/password1	password",
            "ddclient2",
            "ddclient/password1",
            "password",
        ),
        '',
        id="invalid_password",
    ),
    pytest.param(
        (
            "ddclient2	ddclient/password	password",
            "ddclient2",
            "ddclient/password1",
            "password",
        ),
        '',
        id="invalid_password_none",
    ),
    pytest.param(
        (
            "ddclient2	ddclient/password",
            "ddclient2",
            "ddclient/password",
            "password",
        ),
        '',
        id="invalid_line",
    ),
]


@pytest.mark.parametrize("test_input,expected", password_testdata)
def test_get_password_value(mocker, test_input, expected):
    module = mocker.MagicMock()
    mocker.patch.object(
        module, "get_bin_path", return_value="/usr/bin/debconf-get-selections"
    )
    mocker.patch.object(module, "run_command", return_value=(0, test_input[0], ""))

    res = get_password_value(module, *test_input[1:])
    assert res == expected
