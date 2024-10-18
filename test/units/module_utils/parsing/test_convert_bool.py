# -*- coding: utf-8 -*-
# Copyright: (c) 2017 Ansible Project
# License: GNU General Public License v3 or later (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt )

from __future__ import annotations

import pytest

from ansible.module_utils.parsing.convert_bool import boolean


junk_values = ("flibbity", 42, 42.0, object(), None, 2, -1, 0.1)


@pytest.mark.parametrize(("test", "expected"), [
    (True, True),
    (False, False),
    (1, True),
    (0, False),
    (0.0, False),
    ("true", True),
    ("TRUE", True),
    ("t", True),
    ("yes", True),
    ("y", True),
    ("on", True),
])
def test_boolean(test, expected):
    assert boolean(test) is expected


@pytest.mark.parametrize("test", junk_values)
def test_junk_values_nonstrict(test):
    assert boolean(test, strict=False) is False


@pytest.mark.parametrize("test", junk_values)
def test_junk_values_strict(test):
    match = rf"^The value '{test}' is not"
    with pytest.raises(TypeError, match=match):
        boolean(test, strict=True)
