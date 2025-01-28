from __future__ import annotations

import typing as t

import pytest

from contextlib import nullcontext

from ansible import errors as _errors
from ansible import template as _template
from ansible._internal._templating import _engine, _jinja_bits
from ansible.template import Templar
from ansible.utils.datatag.tags import TrustedAsTemplate

from ..test_utils.controller.display import emits_deprecation_warning

TRUST = TrustedAsTemplate()


def test_templar_do_template_trusted_template_str() -> None:
    """Verify `Templar.do_template` processes a trusted template and emits a deprecation warning."""
    data = TRUST.tag('{{ 1 }}')

    with emits_deprecation_warning(match='do_template.* is deprecated'):
        result = Templar().do_template(data)

    assert result == 1


def test_templar_do_template_non_str() -> None:
    """Verify `Templar.do_template` returns non-string inputs as-is and emits a deprecation warning."""
    trusted_template = TRUST.tag('{{ 1 }}')
    data = dict(value=trusted_template)

    with emits_deprecation_warning(match='do_template.* is deprecated'):
        result = Templar().do_template(data)

    assert result is data
    assert result == dict(value=trusted_template)
    assert result['value'] is trusted_template


@pytest.mark.parametrize("value, result", (
    (TRUST.tag('{{ 1 )}'), True),
    ('{{ 1 }}', False),
    (TRUST.tag('{{ invalid'), True),
    (dict(value=TRUST.tag('{{ invalid')), True),
))
def test_is_template(value: t.Any, result: bool) -> None:
    """Verify `Templar.is_template` works as expected."""
    assert Templar().is_template(value) is result


@pytest.mark.parametrize("value, overrides, result", (
    ('foo {{ 123 }} bar', {}, True),
    ('}}', {}, False),
    ('<< blah >>', dict(variable_start_string='<<', variable_end_string='>>'), True),
))
def test_is_possibly_template(value: t.Any, overrides: dict[str, t.Any], result: bool) -> None:
    templar = Templar()
    assert templar.is_possibly_template(value, overrides) is result


def test_is_possibly_template_override_merge() -> None:
    """Verify override merge in `Templar.is_possibly_template` works as expected."""
    templar = Templar()

    with templar.set_temporary_context(variable_start_string='<<'):
        assert templar.is_possibly_template('{{ nope }}') is False  # temporary global override
        assert templar.is_possibly_template('<< yep >>') is True  # temporary global override
        assert templar.is_possibly_template('<< nope >>', overrides=dict(variable_start_string='!!')) is False  # local override masks global
        assert templar.is_possibly_template('<< !!yep >>', overrides=dict(variable_start_string='!!')) is True  # local override masks global


def test_templar_template_non_template_str() -> None:
    """Verify `Templar.template` returns non-template strings as-is."""
    data = TRUST.tag('hello')
    result = Templar().template(data)

    assert result is data


def test_templar_template_untrusted_template() -> None:
    """
    Verify `Templar.template` on an untrusted template triggers an exception.
    The exception is due to unit tests setting the default trust behavior to error on untrusted templates, the default is to warn instead.
    """
    templar = Templar()
    data = '{{ 1 }}'

    with pytest.raises(_errors.TemplateTrustCheckFailedError):
        templar.template(data)


def test_templar_template_fail_on_undefined_truthy_falsey() -> None:
    """Verify `fail_on_undefined` compat behaviors behave as expected."""
    template = TRUST.tag('{{ bogusvar }}')

    with emits_deprecation_warning('Falling back to `True` for `fail_on_undefined'), pytest.raises(_errors.AnsibleUndefinedVariable):
        # fail_on_undefined None == True + dep warning
        Templar().template(template, fail_on_undefined=None)  # type: ignore

    assert Templar().template(template, fail_on_undefined=False) is template

    with pytest.raises(_errors.AnsibleUndefinedVariable):
        Templar().template(template, fail_on_undefined=1)  # type: ignore

    assert Templar().template(template, fail_on_undefined=0) is template  # type: ignore


@pytest.mark.parametrize("template, fail_on_undefined, result", (
    ("somevar", True, "somevar value"),  # success, starts with identifier that's a valid var
    ("123 | int", True, 123),  # success, has filter
    ("bogusvar.somevar", True, "bogusvar.somevar"),  # fail silently, starts with identifier that is not a var, so no-op
    ("somevar.bogusvar", True, _errors.AnsibleUndefinedVariable),  # fail with exception, starts with valid var, but the overall expression results in undefined
    ("somevar.bogusvar", False, "somevar.bogusvar"),  # fail silently, starts with valid var, but the overall expression results in undefined
    ("1notavar", True, "1notavar"),  # fail silently, does not start with a valid identifier
    ("somevar | notafilter", True, _errors.AnsibleTemplateError),  # fail with exception, has a filter-looking expression that is invalid
))
def test_templar_template_convert_bare(template: str, fail_on_undefined: bool, result: t.Any) -> None:
    """Verify the `convert_bare` selection heuristics behave properly."""
    with emits_deprecation_warning('convert_bare.* is deprecated'):
        with pytest.raises(result) if isinstance(result, type) and issubclass(result, Exception) else nullcontext():
            assert Templar(
                variables=dict(somevar='somevar value'),
            ).template(TRUST.tag(template), convert_bare=True, fail_on_undefined=fail_on_undefined) == result


def test_templar_template_convert_bare_truthy_falsey() -> None:
    templar = Templar(variables=dict(somevar=1))
    template = TRUST.tag('somevar')

    assert templar.template(template, convert_bare=1) == 1  # type: ignore
    assert templar.template(template, convert_bare=0) == 'somevar'  # type: ignore


def test_templar_template_convert_data() -> None:
    with emits_deprecation_warning('convert_data.* is deprecated'):
        assert Templar().template(TRUST.tag("{{123}}"), convert_data=True) == 123


def test_templar_template_disable_lookups() -> None:
    with emits_deprecation_warning('disable_lookups.* is deprecated'):
        assert Templar().template(TRUST.tag("{{lookup('list', [1,2])}}"), disable_lookups=True) == [1, 2]


def test_resolve_variable_expression() -> None:
    assert Templar().resolve_variable_expression('a_local', local_variables=dict(a_local=1)) == 1


def test_evaluate_expression() -> None:
    assert Templar().evaluate_expression(TRUST.tag('a_local'), local_variables=dict(a_local=1)) == 1


def test_evaluate_conditional() -> None:
    assert Templar().evaluate_conditional(True) is True


def test_from_template_engine() -> None:
    engine = _engine.TemplateEngine()
    templar = Templar._from_template_engine(engine)

    assert templar._engine is not engine
    assert isinstance(templar._engine, _engine.TemplateEngine)
    assert templar._overrides is _engine.TemplateOverrides.DEFAULT


def test_basedir() -> None:
    templar = Templar()

    # DTFIX-MERGE: test deprecation once this is actually deprecated
    assert templar.basedir == templar._engine.basedir


def test_environment() -> None:
    templar = Templar()

    with emits_deprecation_warning(match='environment.* is deprecated'):
        assert templar.environment is templar._engine.environment


def test_available_variables() -> None:
    variables: _template._VariableContainer = dict()
    templar = Templar(variables=variables)

    assert variables is templar.available_variables
    assert templar.available_variables is templar._engine.available_variables

    with emits_deprecation_warning(match='_available_variables.* internal attribute is deprecated'):
        assert variables is templar._available_variables

    variables = dict(a=1)
    templar.available_variables = variables

    assert templar.available_variables is variables
    assert templar._available_variables is variables
    assert templar._engine.available_variables is variables


def test_loader() -> None:
    templar = Templar()

    with emits_deprecation_warning(match='_loader.* is deprecated'):
        assert templar._loader is templar._engine._loader


def test_copy_with_new_env_environment_class() -> None:
    with emits_deprecation_warning(match='environment_class.* is ignored'):
        Templar().copy_with_new_env(environment_class=_jinja_bits.AnsibleEnvironment)


def test_copy_with_new_env_overrides() -> None:
    with emits_deprecation_warning(match='overrides.*copy_with_new_env.* is deprecated'):
        assert Templar().copy_with_new_env(variable_start_string='!!').template(TRUST.tag('!! 1 }}')) == 1


def test_copy_with_new_env_invalid_overrides() -> None:
    with emits_deprecation_warning(match='overrides.* is deprecated'):
        with pytest.raises(TypeError, match='variable_start_string must be'):
            Templar().copy_with_new_env(variable_start_string=1)


def test_copy_with_new_env_available_variables() -> None:
    templar = Templar()
    new_variables: _template._VariableContainer = {}

    assert templar.available_variables == {}  # trigger lazy creation of available_variables
    assert templar.copy_with_new_env().available_variables is templar.available_variables
    assert templar.copy_with_new_env(available_variables={}).available_variables is not templar.available_variables
    assert templar.copy_with_new_env(available_variables=new_variables).available_variables is new_variables


def test_copy_with_new_searchpath() -> None:
    assert Templar().copy_with_new_env(searchpath='hello')._engine.environment.loader.searchpath == 'hello'


def test_set_temporary_context_overrides() -> None:
    templar = Templar()

    with emits_deprecation_warning(match='overrides.*set_temporary_context.* is deprecated'):
        with templar.set_temporary_context(variable_start_string='!!'):
            assert templar.template(TRUST.tag('!! 1 }}')) == 1


def test_set_temporary_context_searchpath() -> None:
    templar = Templar()

    with templar.set_temporary_context(searchpath='hello'):
        assert templar._engine.environment.loader.searchpath == 'hello'


def test_set_temporary_context_available_variables() -> None:
    templar = Templar()
    available_variables = templar.available_variables
    new_variables: _template._VariableContainer = {}

    assert templar.available_variables == {}

    with templar.set_temporary_context():
        assert templar.available_variables is available_variables

    with templar.set_temporary_context(available_variables={}):
        assert templar.available_variables is not available_variables

    with templar.set_temporary_context(available_variables=new_variables):
        assert templar.available_variables is new_variables
