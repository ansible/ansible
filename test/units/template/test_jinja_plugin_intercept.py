# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.plugins.loader import filter_loader, test_loader
from ansible.template import JinjaPluginIntercept, Templar


@pytest.fixture
def deprecations(mocker):
    """Capture calls to ``display.deprecated`` made from ``ansible.template``."""
    return mocker.patch('ansible.template.display.deprecated')


@pytest.mark.parametrize("value, expected", (
    ([1], True),
    ([], False),
    ("some string", True),
    ("", False),
    (1, True),
    (0, False),
    (None, False),
))
def test_non_boolean_test_result_is_deprecated(value, expected, deprecations):
    """A test plugin returning a non-boolean result is deprecated, and the result is coerced to a boolean."""
    intercept = JinjaPluginIntercept({'nonbool': lambda _value: value}, test_loader)

    result = intercept['nonbool']('ignored')

    assert result is expected

    deprecations.assert_called_once()

    assert f"The test plugin 'nonbool' returned a non-boolean result of type {type(value)!r}." in deprecations.call_args.kwargs['msg']
    assert "Test plugins must have a boolean result." in deprecations.call_args.kwargs['msg']
    assert deprecations.call_args.kwargs['version'] == '2.23'


@pytest.mark.parametrize("value", (True, False))
def test_boolean_test_result_is_not_deprecated(value, deprecations):
    """A test plugin returning a boolean result is returned as-is, without deprecation."""
    intercept = JinjaPluginIntercept({'boolish': lambda _value: value}, test_loader)

    assert intercept['boolish']('ignored') is value

    deprecations.assert_not_called()


def test_non_boolean_filter_result_is_not_deprecated(deprecations):
    """Only test plugins are subject to the boolean result requirement; filter plugins are unaffected."""
    intercept = JinjaPluginIntercept({'nonbool': lambda _value: [1]}, filter_loader)

    assert intercept['nonbool']('ignored') == [1]

    deprecations.assert_not_called()


def test_non_boolean_test_result_in_template(deprecations):
    """A non-boolean test result is deprecated and coerced when reached through normal templating."""
    templar = Templar(loader=None)
    templar.environment.tests['nonbool'] = lambda _value: [1]

    assert templar.template("{{ 'anything' is nonbool }}") is True

    deprecations.assert_called_once()

    assert "The test plugin 'nonbool' returned a non-boolean result" in deprecations.call_args.kwargs['msg']


@pytest.mark.parametrize("template, expected", (
    ("{{ 'anything' is defined }}", True),
    ("{{ 'anything' is string }}", True),
    ("{{ 1 is string }}", False),
    ("{{ [1, 2] is subset([1, 2, 3]) }}", True),
    ("{{ [1, 2] is contains(1) }}", True),
    ("{{ '1.0' is version('2.0', '<') }}", True),
))
def test_builtin_tests_are_not_deprecated(template, expected, deprecations):
    """Jinja and ansible-core provided tests already return booleans, so they must not trigger the deprecation."""
    assert Templar(loader=None).template(template) is expected

    deprecations.assert_not_called()
