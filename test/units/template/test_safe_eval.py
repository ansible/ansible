# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

from collections import defaultdict
from functools import partial

from ansible.template.safe_eval import safe_eval

from jinja2 import UndefinedError

import pytest


TESTS = [v + (l,) for v in [
    # Valid
    (True, True, None),
    ({}, {}, None),
    ('True', True, None),
    ('False', False, None),
    ('0', 0, None),
    ('1.0', 1.0, None),
    ('[]', [], None),
    ('[True]', [True], None),
    ('{}', {}, None),
    ('{"foo": "bar"}', {"foo": "bar"}, None),
    ('{0}', set([0]), None),

    # Invalid
    ('[1] + [2]', '[1] + [2]', 'invalid expression ([1] + [2])'),
    ('len("foo")', 'len("foo")', 'invalid function: len'),
    ('Foo.bar("baz")', 'Foo.bar("baz")', 'invalid attribute: Foo.bar'),
    ('{}.fromkeys(["foo"])', '{}.fromkeys(["foo"])', 'invalid object: Dict'),
    ('{}.__name__', '{}.__name__', 'invalid object: Dict'),
    ('True.__name__', 'True.__name__', 'invalid object: Constant'),
    ('AnsibleUndefined(len("foo"))', 'AnsibleUndefined(len("foo"))', 'invalid function: len'),
    ('__builtins__', '__builtins__', 'invalid name: __builtins__'),
    ('__builtins__.__class__', '__builtins__.__class__', 'invalid attribute: __builtins__.__class__'),

    # Syntax Errors
    ('<map at 0x109952e80>', '<map at 0x109952e80>', None),
] for l in (None, dict, partial(defaultdict, dict))]


@pytest.mark.parametrize(('test_input', 'expected', 'error_message', 'locals_val'), TESTS)
def test_safe_eval_exceptions(test_input, expected, error_message, locals_val):
    if callable(locals_val):
        locals_val = locals_val()
    output, exception = safe_eval(test_input, locals=locals_val, include_exceptions=True)
    assert output == expected
    if error_message:
        assert str(exception) == error_message
    else:
        assert exception is None


@pytest.mark.parametrize(('test_input', 'expected', 'error_message', 'locals_val'), TESTS)
def test_safe_eval_no_exceptions(test_input, expected, error_message, locals_val):
    output = safe_eval(test_input, include_exceptions=False)
    assert output == expected


def test_safe_eval_AnsibleUndefined():
    with pytest.raises(UndefinedError) as excinfo:
        safe_eval('AnsibleUndefined(hint=None, obj={}, name="foo")', include_exceptions=True)

    assert str(excinfo.value) == "'dict object' has no attribute 'foo'"

    with pytest.raises(UndefinedError) as excinfo:
        safe_eval('AnsibleUndefined(None, {}, "foo")', include_exceptions=True)

    assert str(excinfo.value) == "'dict object' has no attribute 'foo'"


def test_safe_eval_defaultdict():
    # https://github.com/ansible/ansible/issues/12206
    # >>> eval('foo', {}, defaultdict(dict))
    # {}
    output, exception = safe_eval('foo', locals=defaultdict(dict), include_exceptions=True)
    assert output == 'foo'
