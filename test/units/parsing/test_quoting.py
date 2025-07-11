# coding: utf-8
# (c) 2015, Toshio Kuratomi <tkuratomi@ansible.com>
# (c) 2025, Ansible Project
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

from ansible.parsing.quoting import is_quoted, unquote

import pytest


class TestIsQuoted:
    """Test the is_quoted function."""

    # Test cases where strings are properly quoted
    @pytest.mark.parametrize("data, expected", [
        # Double quotes
        ('"hello"', True),
        ('"hello world"', True),
        ('"1"', True),
        ('""', True),
        ('"multi\nline"', True),
        ('"with spaces"', True),
        ('"with\ttabs"', True),
        ('"with\'single\'quotes"', True),

        # Single quotes
        ("'hello'", True),
        ("'hello world'", True),
        ("'1'", True),
        ("''", True),
        ("'multi\nline'", True),
        ("'with spaces'", True),
        ("'with\ttabs'", True),
        ("'with\"double\"quotes'", True),

        # Quotes with internal quotes of same or different type
        ('"hello\'world"', True),
        ("'hello\"world'", True),
        ('"hello"world"', True),
        ("'hello'world'", True),
        ('""hello""', True),
        ("''hello''", True),
    ])
    def test_is_quoted_valid(self, data, expected):
        assert is_quoted(data) == expected

    # Test cases where strings are not properly quoted
    @pytest.mark.parametrize("data, expected", [
        # Not quoted at all
        ('hello', False),
        ('hello world', False),
        ('1', False),
        ('', False),
        ('multi\nline', False),

        # Single character (can't be quoted)
        ('"', False),
        ("'", False),
        ('a', False),
        ('1', False),

        # Mixed quotes
        ('"hello\'', False),
        ("'hello\"", False),

        # Escaped quotes at end (should not be considered quoted)
        ('"hello\\"', False),
        ("'hello\\'", False),

        # Partially quoted
        ('"hello', False),
        ("'hello", False),
        ('hello"', False),
        ("hello'", False),
    ])
    def test_is_quoted_invalid(self, data, expected):
        assert is_quoted(data) == expected

    def test_is_quoted_edge_cases(self):
        """Test edge cases for is_quoted."""
        # Empty string
        assert is_quoted('') is False

        # Single quote characters
        assert is_quoted('"') is False
        assert is_quoted("'") is False

        # Two different quote types
        assert is_quoted("\"'") is False
        assert is_quoted("'\"") is False


class TestUnquote:
    """Test the unquote function."""

    # Test cases for proper unquoting
    @pytest.mark.parametrize("quoted, expected", [
        # Double quotes
        ('"hello"', 'hello'),
        ('"hello world"', 'hello world'),
        ('"1"', '1'),
        ('""', ''),
        ('"multi\nline"', 'multi\nline'),
        ('"with spaces"', 'with spaces'),
        ('"with\ttabs"', 'with\ttabs'),
        ('"with\'single\'quotes"', "with'single'quotes"),

        # Single quotes
        ("'hello'", 'hello'),
        ("'hello world'", 'hello world'),
        ("'1'", '1'),
        ("''", ''),
        ("'multi\nline'", 'multi\nline'),
        ("'with spaces'", 'with spaces'),
        ("'with\ttabs'", 'with\ttabs'),
        ("'with\"double\"quotes'", 'with"double"quotes'),

        # Quotes with internal quotes of same or different type
        ('"hello\'world"', "hello'world"),
        ("'hello\"world'", 'hello"world'),
        ('"hello"world"', 'hello"world'),
        ("'hello'world'", "hello'world"),
        ('""hello""', '"hello"'),
        ("''hello''", "'hello'"),
    ])
    def test_unquote_valid(self, quoted, expected):
        assert unquote(quoted) == expected

    # Test cases where unquote should return the original string
    @pytest.mark.parametrize("data", [
        # Not quoted at all
        'hello',
        'hello world',
        '1',
        '',
        'multi\nline',

        # Single character
        '"',
        "'",
        'a',
        '1',

        # Mixed quotes
        '"hello\'',
        "'hello\"",

        # Escaped quotes at end
        '"hello\\"',
        "'hello\\'",

        # Partially quoted
        '"hello',
        "'hello",
        'hello"',
        "hello'",
    ])
    def test_unquote_unchanged(self, data):
        """Test that unquote returns the original string when not properly quoted."""
        assert unquote(data) == data

    def test_unquote_edge_cases(self):
        """Test edge cases for unquote."""
        # Empty string
        assert unquote('') == ''

        # Single quote characters
        assert unquote('"') == '"'
        assert unquote("'") == "'"

        # Two different quote types
        assert unquote("\"'") == "\"'"
        assert unquote("'\"") == "'\""

    def test_unquote_with_escaped_quotes(self):
        """Test unquote with escaped quotes (should not unquote)."""
        # These should not be unquoted due to escaped ending quotes
        assert unquote('"hello\\"') == '"hello\\"'
        assert unquote("'hello\\'") == "'hello\\'"

        # These should be unquoted (escaped quotes in middle)
        assert unquote('"hello \\"world\\""') == 'hello \\"world\\"'
        assert unquote("'hello \\'world\\''") == "hello \\'world\\'"

    def test_unquote_complex_cases(self):
        """Test complex unquoting scenarios."""
        # Nested quotes of different types
        assert unquote('"hello \'world\'"') == "hello 'world'"
        assert unquote("'hello \"world\"'") == 'hello "world"'

        # Multiple internal quotes
        assert unquote('"a \\"b\\" c"') == 'a \\"b\\" c'
        assert unquote("'a \\'b\\' c'") == "a \\'b\\' c"


class TestQuotingIntegration:
    """Test the interaction between is_quoted and unquote."""

    def test_is_quoted_unquote_consistency(self):
        """Test that is_quoted and unquote are consistent."""
        test_cases = [
            '"hello"',
            "'hello'",
            '"hello world"',
            "'hello world'",
            '""',
            "''",
            '"hello\\"',  # escaped quote at end
            "'hello\\'",  # escaped quote at end
            'hello',  # not quoted
            '"hello',  # partially quoted
            "'hello",  # partially quoted
            '"hello\'',  # mixed quotes
            "'hello\"",  # mixed quotes
        ]

        for case in test_cases:
            if is_quoted(case):
                # If is_quoted returns True, unquote should remove the quotes
                unquoted = unquote(case)
                assert unquoted == case[1:-1], f"Failed for case: {case}"
            else:
                # If is_quoted returns False, unquote should return the original
                assert unquote(case) == case, f"Failed for case: {case}"

    @pytest.mark.parametrize("quote_char", ['"', "'"])
    def test_roundtrip_quoting(self, quote_char):
        """Test that properly quoted strings can be unquoted correctly."""
        test_strings = [
            'hello',
            'hello world',
            'multi\nline',
            'with\ttabs',
            'with spaces',
            '',
            '123',
            'special!@#$%^&*()chars',
        ]

        for test_string in test_strings:
            quoted = f'{quote_char}{test_string}{quote_char}'
            assert is_quoted(quoted) is True, f"Failed is_quoted for: {quoted}"
            assert unquote(quoted) == test_string, f"Failed unquote for: {quoted}"
