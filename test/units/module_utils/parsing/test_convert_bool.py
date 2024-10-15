# -*- coding: utf-8 -*-
# Copyright: (c) 2017 Ansible Project
# License: GNU General Public License v3 or later (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt )

from __future__ import annotations

import pytest

from ansible.module_utils.parsing.convert_bool import boolean


class TestBoolean:
    @pytest.mark.parametrize(("test", "expected"), [
        (True, True),
        (False, False),
        (1, True),
        (0, False),
        (0.0, False),
    ])
    def test_numbers(self, test, expected):
        assert boolean(test) is expected

    @pytest.mark.skip(reason="Current boolean() doesn't consider these to be true values")
    @pytest.mark.parametrize("test", (2, -1, 0.1))
    def test_other_numbers(self, test):
        assert boolean(test) is True

    @pytest.mark.parametrize("test", ("true", "TRUE", "t", "yes", "y", "on"))
    def test_strings(self, test):
        assert boolean(test) is True

    @pytest.mark.parametrize("test", ("flibbity", 42, 42.0, object(), None))
    def test_junk_values_nonstrict(self, test):
        assert boolean(test, strict=False) is False

    @pytest.mark.parametrize(("test", "match"), [
        ("flibbity", r"^The value 'flibbity' is not"),
        (42, r"The value '42' is not"),
        (42.0, r"^The value '42\.0' is not"),
        (object(), r"^The value '\<object object"),
        (None, r"^The value 'None' is not")
    ])
    def test_junk_values_strict(self, test, match):
        with pytest.raises(TypeError, match=match):
            boolean(test, strict=True)
