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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.parsing.splitter import split_args, parse_kv

import pytest

SPLIT_DATA = (
    (u'a',
        [u'a'],
        {u'_raw_params': u'a'}),
    (u'a=b',
        [u'a=b'],
        {u'a': u'b'}),
    (u'a="foo bar"',
        [u'a="foo bar"'],
        {u'a': u'foo bar'}),
    (u'"foo bar baz"',
        [u'"foo bar baz"'],
        {u'_raw_params': '"foo bar baz"'}),
    (u'foo bar baz',
        [u'foo', u'bar', u'baz'],
        {u'_raw_params': u'foo bar baz'}),
    (u'a=b c="foo bar"',
        [u'a=b', u'c="foo bar"'],
        {u'a': u'b', u'c': u'foo bar'}),
    (u'a="echo \\"hello world\\"" b=bar',
        [u'a="echo \\"hello world\\""', u'b=bar'],
        {u'a': u'echo "hello world"', u'b': u'bar'}),
    (u'a="multi\nline"',
        [u'a="multi\nline"'],
        {u'a': u'multi\nline'}),
    (u'a="blank\n\nline"',
        [u'a="blank\n\nline"'],
        {u'a': u'blank\n\nline'}),
    (u'a="blank\n\n\nlines"',
        [u'a="blank\n\n\nlines"'],
        {u'a': u'blank\n\n\nlines'}),
    (u'a="a long\nmessage\\\nabout a thing\n"',
        [u'a="a long\nmessage\\\nabout a thing\n"'],
        {u'a': u'a long\nmessage\\\nabout a thing\n'}),
    (u'a="multiline\nmessage1\\\n" b="multiline\nmessage2\\\n"',
        [u'a="multiline\nmessage1\\\n"', u'b="multiline\nmessage2\\\n"'],
        {u'a': 'multiline\nmessage1\\\n', u'b': u'multiline\nmessage2\\\n'}),
    (u'a={{jinja}}',
        [u'a={{jinja}}'],
        {u'a': u'{{jinja}}'}),
    (u'a={{ jinja }}',
        [u'a={{ jinja }}'],
        {u'a': u'{{ jinja }}'}),
    (u'a="{{jinja}}"',
        [u'a="{{jinja}}"'],
        {u'a': u'{{jinja}}'}),
    (u'a={{ jinja }}{{jinja2}}',
        [u'a={{ jinja }}{{jinja2}}'],
        {u'a': u'{{ jinja }}{{jinja2}}'}),
    (u'a="{{ jinja }}{{jinja2}}"',
        [u'a="{{ jinja }}{{jinja2}}"'],
        {u'a': u'{{ jinja }}{{jinja2}}'}),
    (u'a={{jinja}} b={{jinja2}}',
        [u'a={{jinja}}', u'b={{jinja2}}'],
        {u'a': u'{{jinja}}', u'b': u'{{jinja2}}'}),
    (u'a="{{jinja}}\n" b="{{jinja2}}\n"',
        [u'a="{{jinja}}\n"', u'b="{{jinja2}}\n"'],
        {u'a': u'{{jinja}}\n', u'b': u'{{jinja2}}\n'}),
    (u'a="café eñyei"',
        [u'a="café eñyei"'],
        {u'a': u'café eñyei'}),
    (u'a=café b=eñyei',
        [u'a=café', u'b=eñyei'],
        {u'a': u'café', u'b': u'eñyei'}),
    (u'a={{ foo | some_filter(\' \', " ") }} b=bar',
        [u'a={{ foo | some_filter(\' \', " ") }}', u'b=bar'],
        {u'a': u'{{ foo | some_filter(\' \', " ") }}', u'b': u'bar'}),
    (u'One\n  Two\n    Three\n',
        [u'One\n ', u'Two\n   ', u'Three\n'],
        {u'_raw_params': u'One\n  Two\n    Three\n'}),
)

SPLIT_ARGS = ((test[0], test[1]) for test in SPLIT_DATA)
PARSE_KV = ((test[0], test[2]) for test in SPLIT_DATA)


@pytest.mark.parametrize("args, expected", SPLIT_ARGS)
def test_split_args(args, expected):
    assert split_args(args) == expected


@pytest.mark.parametrize("args, expected", PARSE_KV)
def test_parse_kv(args, expected):
    assert parse_kv(args) == expected
