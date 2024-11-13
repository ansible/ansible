# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.cli.galaxy import _display_role

import pytest


@pytest.mark.parametrize(
    ("role_metadata", "expected"),
    [
        pytest.param(
            {"name": "testrole", "install_info": None},
            "- testrole, (unknown version)",
            id="unknown-version",
        ),
        pytest.param(
            {"name": "testrole", "install_info": {"version": "1.0.0"}},
            "- testrole, 1.0.0",
            id="known-version",
        ),
    ],
)
def test_display_role(mocker, capsys, role_metadata, expected):
    mocked_galaxy_role = mocker.Mock(**role_metadata)
    mocked_galaxy_role.name = role_metadata["name"]
    _display_role(mocked_galaxy_role)
    out, dummy = capsys.readouterr()
    out_lines = out.splitlines()

    assert out_lines[0] == expected
