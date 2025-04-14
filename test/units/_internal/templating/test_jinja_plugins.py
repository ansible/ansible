from __future__ import annotations

import typing as t

import pytest

from ansible.errors import AnsibleUndefinedVariable
from ansible._internal._datatag._tags import TrustedAsTemplate
from ansible._internal._templating._engine import TemplateEngine

TRUST = TrustedAsTemplate()


@pytest.mark.parametrize("expr, expected", (
    ('["ok", bogus_var, "also ok"] | select("defined")', ["ok", "also ok"]),
    ('[{"a": "ok"}, {"a": bogus_var}, {"a": "also ok"}] | selectattr("a", "defined")', [{"a": "ok"}, {"a": "also ok"}]),
    ('["ok", bogus_var, "also ok"] | reject("undefined")', ["ok", "also ok"]),
    ('[{"a": "ok"}, {"a": bogus_var}, {"a": "also ok"}] | rejectattr("a", "undefined")', [{"a": "ok"}, {"a": "also ok"}]),
    ('[["ok"], [bogus_var], ["also ok"]] | map("select", "defined")', [["ok"], [], ["also ok"]]),
    ('"abc" is defined', True),
    ('"abc" is undefined', False),
    ('bogus_var is defined', False),
    ('bogus_var is undefined', True),
))
def test_wrapped_plugins_undefined_arg_passthru(expr: str, expected: t.Any) -> None:
    assert TemplateEngine().evaluate_expression(TRUST.tag(expr)) == expected


@pytest.mark.parametrize("expr", (
    "['abc'] | selectattr('a', 'equalto', bogus_var)",
    "['abc'] | selectattr(attr=bogus_var)",
    "['abc'] | select('sameas', bogus_var)",
    "['abc'] | reject('sameas', bogus_var)",
    "['abc'] | rejectattr('a', 'equalto', bogus_var)",
    "['abc'] | rejectattr(attr=bogus_var)",
    "['abc'] | map(bogus_var)",
    "['abc'] | map(default=bogus_var)",
    'bogus_var is string',
    'bogus_var is float',
    'bogus_var is integer',
    'bogus_var is number',
    'bogus_var is none',
    'bogus_var is boolean',
    'bogus_var is false',
    'bogus_var is true',
    'bogus_var is mapping',
    'bogus_var is sameas(123)',
    '123 is sameas(bogus_var)',
    'bogus_var is escaped',
))
def test_wrapped_plugins_undefined_arg_fail(expr: str) -> None:
    with pytest.raises(AnsibleUndefinedVariable):
        TemplateEngine().evaluate_expression(TRUST.tag(expr))
