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

import pytest
from ansible.parsing.splitter import split_args, parse_kv
from ansible.errors import AnsibleParserError, AnsibleError

# Cases that should still parse successfully
SPLIT_DATA: tuple[tuple[str | None, list[str], dict[str, str]], ...] = (
    (None, [], {}),
    ("", [], {}),
    ("a=b", ["a=b"], {"a": "b"}),
    ('a="foo bar"', ['a="foo bar"'], {"a": "foo bar"}),
    ('a="echo \\"hello world\\"" b=bar',
        ['a="echo \\"hello world\\""', 'b=bar'],
        {"a": 'echo "hello world"', "b": "bar"}),
    ('a="nest\'ed"', ['a="nest\'ed"'], {"a": "nest'ed"}),
    ('a="multi\nline"', ['a="multi\nline"'], {"a": "multi\nline"}),
    ('a="blank\n\nline"', ['a="blank\n\nline"'], {"a": "blank\n\nline"}),
    ('a="café eñyei"', ['a="café eñyei"'], {"a": "café eñyei"}),
    ('a=café b=eñyei', ['a=café', 'b=eñyei'], {"a": "café", "b": "eñyei"}),
)

# Cases that should now raise AnsibleError (invalid freeform args)
INVALID_FREEFORM = (
    "a",                
    '"foo bar baz"',    
    "foo bar baz",      
    " ",                
    "\\ ",              
    "line \\\ncontinuation",
    "not jinja}}",
    "One\n  Two\n    Three\n",
    "\nOne\n  Two\n    Three\n",
)


# Cases that should raise AnsibleParserError (unbalanced quotes/jinja)
PARSER_ERROR = (
    '"',
    "'",
    "{{",
    "{%",
    "{#",
)

@pytest.mark.parametrize("args, expected", [(test[0], test[1]) for test in SPLIT_DATA], ids=[str(test[0]) for test in SPLIT_DATA])
def test_split_args(args, expected):
    assert split_args(args) == expected

@pytest.mark.parametrize("args, expected", [(test[0], test[2]) for test in SPLIT_DATA], ids=[str(test[0]) for test in SPLIT_DATA])
def test_parse_kv_valid(args, expected):
    assert parse_kv(args) == expected

@pytest.mark.parametrize("args", INVALID_FREEFORM, ids=[str(arg) for arg in INVALID_FREEFORM])
def test_parse_kv_invalid_freeform(args):
    with pytest.raises(AnsibleError):
        parse_kv(args)

@pytest.mark.parametrize("args", PARSER_ERROR, ids=[str(arg) for arg in PARSER_ERROR])
def test_split_args_error(args):
    with pytest.raises(AnsibleParserError):
        split_args(args)

@pytest.mark.parametrize("args", PARSER_ERROR, ids=[str(arg) for arg in PARSER_ERROR])
def test_parse_kv_error(args):
    with pytest.raises(AnsibleParserError):
        parse_kv(args)
