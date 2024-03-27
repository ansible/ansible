# coding: utf-8
# (c) 2015, Toshio Kuratomi <tkuratomi@ansible.com>
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

from ansible.parsing.splitter import split_args, parse_kv
from ansible.errors import AnsibleParserError

import pytest

SPLIT_DATA = (
    (None, [], {}),
    ("", [], {}),
    ("a", ["a"], {"_raw_params": "a"}),
    ("a=b", ["a=b"], {"a": "b"}),
    ('a="foo bar"', ['a="foo bar"'], {"a": "foo bar"}),
    ('"foo bar baz"', ['"foo bar baz"'], {"_raw_params": '"foo bar baz"'}),
    ("foo bar baz", ["foo", "bar", "baz"], {"_raw_params": "foo bar baz"}),
    ('a=b c="foo bar"', ["a=b", 'c="foo bar"'], {"a": "b", "c": "foo bar"}),
    (
        'a="echo \\"hello world\\"" b=bar',
        ['a="echo \\"hello world\\""', "b=bar"],
        {"a": 'echo "hello world"', "b": "bar"},
    ),
    ('a="nest\'ed"', ['a="nest\'ed"'], {"a": "nest'ed"}),
    (" ", [" "], {"_raw_params": " "}),
    ("\\ ", [" "], {"_raw_params": " "}),
    ("a\\=escaped", ["a\\=escaped"], {"_raw_params": "a=escaped"}),
    ('a="multi\nline"', ['a="multi\nline"'], {"a": "multi\nline"}),
    ('a="blank\n\nline"', ['a="blank\n\nline"'], {"a": "blank\n\nline"}),
    ('a="blank\n\n\nlines"', ['a="blank\n\n\nlines"'], {"a": "blank\n\n\nlines"}),
    (
        'a="a long\nmessage\\\nabout a thing\n"',
        ['a="a long\nmessage\\\nabout a thing\n"'],
        {"a": "a long\nmessage\\\nabout a thing\n"},
    ),
    (
        'a="multiline\nmessage1\\\n" b="multiline\nmessage2\\\n"',
        ['a="multiline\nmessage1\\\n"', 'b="multiline\nmessage2\\\n"'],
        {"a": "multiline\nmessage1\\\n", "b": "multiline\nmessage2\\\n"},
    ),
    (
        "line \\\ncontinuation",
        ["line", "continuation"],
        {"_raw_params": "line continuation"},
    ),
    ("not jinja}}", ["not", "jinja}}"], {"_raw_params": "not jinja}}"}),
    (
        "a={{multiline\njinja}}",
        ["a={{multiline\njinja}}"],
        {"a": "{{multiline\njinja}}"},
    ),
    ("a={{jinja}}", ["a={{jinja}}"], {"a": "{{jinja}}"}),
    ("a={{ jinja }}", ["a={{ jinja }}"], {"a": "{{ jinja }}"}),
    ("a={% jinja %}", ["a={% jinja %}"], {"a": "{% jinja %}"}),
    ("a={# jinja #}", ["a={# jinja #}"], {"a": "{# jinja #}"}),
    ('a="{{jinja}}"', ['a="{{jinja}}"'], {"a": "{{jinja}}"}),
    (
        "a={{ jinja }}{{jinja2}}",
        ["a={{ jinja }}{{jinja2}}"],
        {"a": "{{ jinja }}{{jinja2}}"},
    ),
    (
        'a="{{ jinja }}{{jinja2}}"',
        ['a="{{ jinja }}{{jinja2}}"'],
        {"a": "{{ jinja }}{{jinja2}}"},
    ),
    (
        "a={{jinja}} b={{jinja2}}",
        ["a={{jinja}}", "b={{jinja2}}"],
        {"a": "{{jinja}}", "b": "{{jinja2}}"},
    ),
    (
        'a="{{jinja}}\n" b="{{jinja2}}\n"',
        ['a="{{jinja}}\n"', 'b="{{jinja2}}\n"'],
        {"a": "{{jinja}}\n", "b": "{{jinja2}}\n"},
    ),
    ('a="café eñyei"', ['a="café eñyei"'], {"a": "café eñyei"}),
    ("a=café b=eñyei", ["a=café", "b=eñyei"], {"a": "café", "b": "eñyei"}),
    (
        "a={{ foo | some_filter(' ', \" \") }} b=bar",
        ["a={{ foo | some_filter(' ', \" \") }}", "b=bar"],
        {"a": "{{ foo | some_filter(' ', \" \") }}", "b": "bar"},
    ),
    (
        "One\n  Two\n    Three\n",
        ["One\n ", "Two\n   ", "Three\n"],
        {"_raw_params": "One\n  Two\n    Three\n"},
    ),
    (
        "\nOne\n  Two\n    Three\n",
        ["\n", "One\n ", "Two\n   ", "Three\n"],
        {"_raw_params": "\nOne\n  Two\n    Three\n"},
    ),
)

PARSE_KV_CHECK_RAW = (
    ("raw=yes", {"_raw_params": "raw=yes"}),
    ("creates=something", {"creates": "something"}),
)

PARSER_ERROR = (
    '"',
    "'",
    "{{",
    "{%",
    "{#",
)

SPLIT_ARGS = tuple((test[0], test[1]) for test in SPLIT_DATA)
PARSE_KV = tuple((test[0], test[2]) for test in SPLIT_DATA)


@pytest.mark.parametrize(
    "args, expected", SPLIT_ARGS, ids=[str(arg[0]) for arg in SPLIT_ARGS]
)
def test_split_args(args, expected):
    assert split_args(args) == expected


@pytest.mark.parametrize(
    "args, expected", PARSE_KV, ids=[str(arg[0]) for arg in PARSE_KV]
)
def test_parse_kv(args, expected):
    assert parse_kv(args) == expected


@pytest.mark.parametrize(
    "args, expected",
    PARSE_KV_CHECK_RAW,
    ids=[str(arg[0]) for arg in PARSE_KV_CHECK_RAW],
)
def test_parse_kv_check_raw(args, expected):
    assert parse_kv(args, check_raw=True) == expected


@pytest.mark.parametrize("args", PARSER_ERROR)
def test_split_args_error(args):
    with pytest.raises(AnsibleParserError):
        split_args(args)


@pytest.mark.parametrize("args", PARSER_ERROR)
def test_parse_kv_error(args):
    with pytest.raises(AnsibleParserError):
        parse_kv(args)
