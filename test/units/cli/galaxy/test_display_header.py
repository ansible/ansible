# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.cli.galaxy import _display_header


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        pytest.param(
            ("/collections/path", "h1", "h2"),
            ["", "# /collections/path", "h1         h2     ", "---------- -------"],
            id="default",
        ),
        pytest.param(
            ("/collections/path", "Collection", "Version", 18, 18),
            [
                "",
                "# /collections/path",
                "Collection         Version           ",
                "------------------ ------------------",
            ],
            id="widths",
        ),
        pytest.param(
            ("/collections/path", "Col", "Ver", 1, 1),
            ["", "# /collections/path", "Col Ver", "--- ---"],
            id="small_widths",
        ),
    ],
)
def test_display_header_default(capsys, args, expected):
    _display_header(*args)
    out, dummy = capsys.readouterr()
    out_lines = out.splitlines()

    assert out_lines == expected
