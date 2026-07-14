from __future__ import annotations

import pytest

from ansible.errors import AnsibleTemplateError
from ansible.template import Templar, trust_as_template


@pytest.mark.parametrize("value", (
    "not_defined is not defined",  # direct rendered undefined template
    "not_defined is undefined",
    "chained_undefined is not defined",  # chain rendered undefined template
    "chained_undefined is undefined",
    "valid_scalar is defined",  # valid scalar
    "valid_scalar is not undefined",
    "valid_template is defined",  # valid chain rendered template
    "valid_template is not undefined",  # valid chain rendered template
))
def test_defined_undefined_success(value):
    """Validate success behavior for the `defined` and `undefined` Jinja test implementations."""
    variables = dict(
        valid_scalar="valid",
        valid_template=trust_as_template("{{ 'hey' }}"),
        chained_undefined=trust_as_template("{{ bogus }}"),
    )

    assert Templar(variables=variables).evaluate_conditional(trust_as_template(value))


@pytest.mark.parametrize("value", (
    "syntax_error is defined",
    "syntax_error is undefined",
    "div_by_zero is defined",
    "div_by_zero is undefined",
))
def test_defined_undefined_failure(value):
    variables = dict(
        syntax_error=trust_as_template("{{ / }}"),
        div_by_zero=trust_as_template("{{ 1 / 0 }}"),
    )

    with pytest.raises(AnsibleTemplateError):
        Templar(variables=variables).evaluate_conditional(trust_as_template(value))
