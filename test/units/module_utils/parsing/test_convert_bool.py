# -*- coding: utf-8 -*-
# Copyright: (c) 2017 Ansible Project
# License: GNU General Public License v3 or later (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt )

from __future__ import annotations

import pytest

from ansible.module_utils.parsing.convert_bool import boolean


class TestBoolean:
    def test_bools(self):
        assert boolean(True) is True
        assert boolean(False) is False

    def test_none(self):
        with pytest.raises(TypeError, match="The value 'None' is not"):
            boolean(None, strict=True)
        assert boolean(None, strict=False) is False

    def test_numbers(self):
        assert boolean(1) is True
        assert boolean(0) is False
        assert boolean(0.0) is False

# Current boolean() doesn't consider these to be true values
#    def test_other_numbers(self):
#        assert boolean(2) is True
#        assert boolean(-1) is True
#        assert boolean(0.1) is True

    def test_strings(self):
        assert boolean("true") is True
        assert boolean("TRUE") is True
        assert boolean("t") is True
        assert boolean("yes") is True
        assert boolean("y") is True
        assert boolean("on") is True

    def test_junk_values_nonstrict(self):
        assert boolean("flibbity", strict=False) is False
        assert boolean(42, strict=False) is False
        assert boolean(42.0, strict=False) is False
        assert boolean(object(), strict=False) is False

    def test_junk_values_strict(self):
        with pytest.raises(TypeError, match="The value 'flibbity' is not"):
            boolean("flibbity", strict=True)

        with pytest.raises(TypeError, match="The value '42' is not"):
            boolean(42, strict=True)

        with pytest.raises(TypeError, match="The value '42.0' is not"):
            boolean(42.0, strict=True)

        with pytest.raises(TypeError, match="The value '<object object"):
            boolean(object(), strict=True)
