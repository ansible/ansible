from __future__ import annotations

import io
import keyword
import pathlib

import typing as t

import pytest
import pytest_mock

from contextlib import nullcontext

from ansible import constants
from ansible import errors as _errors
from ansible import template as _template
from ansible._internal._templating import _engine, _jinja_bits
from ansible._internal._templating._jinja_common import UndefinedMarker
from ansible.errors import AnsibleUndefinedVariable
from ansible.module_utils._internal._datatag import NotTaggableError
from ansible.template import Templar, trust_as_template, is_trusted_as_template
from ansible._internal._datatag._tags import TrustedAsTemplate
from ansible._internal._templating import _lazy_containers

from ..test_utils.controller.display import emits_warnings

TRUST = TrustedAsTemplate()


def test_templar_do_template_trusted_template_str() -> None:
    """Verify `Templar.do_template` processes a trusted template and emits a deprecation warning."""
    data = TRUST.tag('{{ 1 }}')

    with emits_warnings(deprecation_pattern='do_template.* is deprecated'):
        result = Templar().do_template(data)

    assert result == 1


def test_templar_do_template_non_str() -> None:
    """Verify `Templar.do_template` returns non-string inputs as-is and emits a deprecation warning."""
    trusted_template = TRUST.tag('{{ 1 }}')
    data = dict(value=trusted_template)

    with emits_warnings(deprecation_pattern='do_template.* is deprecated'):
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

    with emits_warnings(deprecation_pattern='Falling back to `True` for `fail_on_undefined'), pytest.raises(_errors.AnsibleUndefinedVariable):
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
    with emits_warnings(deprecation_pattern='convert_bare.* is deprecated'):
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
    with emits_warnings(deprecation_pattern='convert_data.* is deprecated'):
        assert Templar().template(TRUST.tag("{{123}}"), convert_data=True) == 123


def test_templar_template_disable_lookups() -> None:
    with emits_warnings(deprecation_pattern='disable_lookups.* is deprecated'):
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

    assert templar.basedir == templar._engine.basedir


def test_environment() -> None:
    templar = Templar()

    with emits_warnings(deprecation_pattern='environment.* is deprecated'):
        assert templar.environment is templar._engine.environment


def test_available_variables() -> None:
    variables: _template._VariableContainer = dict()
    templar = Templar(variables=variables)

    assert variables is templar.available_variables
    assert templar.available_variables is templar._engine.available_variables

    with emits_warnings(deprecation_pattern='_available_variables.* internal attribute is deprecated'):
        assert variables is templar._available_variables

    variables = dict(a=1)
    templar.available_variables = variables

    assert templar.available_variables is variables
    assert templar._available_variables is variables
    assert templar._engine.available_variables is variables


def test_loader() -> None:
    templar = Templar()

    with emits_warnings(deprecation_pattern='_loader.* is deprecated'):
        assert templar._loader is templar._engine._loader


def test_copy_with_new_env_environment_class() -> None:
    with emits_warnings(deprecation_pattern='environment_class.* is ignored'):
        Templar().copy_with_new_env(environment_class=_jinja_bits.AnsibleEnvironment)


def test_copy_with_new_env_overrides() -> None:
    with emits_warnings(deprecation_pattern='overrides.*copy_with_new_env.* is deprecated'):
        assert Templar().copy_with_new_env(variable_start_string='!!').template(TRUST.tag('!! 1 }}')) == 1


def test_copy_with_new_env_invalid_overrides() -> None:
    with emits_warnings(deprecation_pattern='overrides.* is deprecated'):
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

    with emits_warnings(deprecation_pattern='set_temporary_context.* is deprecated'):
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


class CustomStr(str): ...


@pytest.mark.parametrize("value", (
    "yep",
    lambda tmppath: pathlib.Path(tmppath / "afile").open("w"),
    io.StringIO("blee"),
    io.BytesIO(b"blee"),
))
def test_trust_as_template(value: str | io.IOBase, tmp_path: pytest.TempPathFactory) -> None:
    """Validate expected success behavior for `trust_value`."""
    if callable(value):
        value = value(tmp_path)

    result = trust_as_template(value)

    assert result is not value
    assert TrustedAsTemplate.is_tagged_on(result)
    assert isinstance(result, type(value))
    assert is_trusted_as_template(result)


@pytest.mark.parametrize("value", (
    None,
    123,
    dict(x=TrustedAsTemplate().tag("nope")),
    [123],
))
def test_not_is_trusted_as_template(value: object) -> None:
    """Validate that types incorrectly tagged with trust are not reported as trusted."""
    result = TrustedAsTemplate().tag(value)  # force application of trust

    assert not is_trusted_as_template(value)
    assert not is_trusted_as_template(result)


@pytest.mark.parametrize("value, error_type, error_pattern", (
    (123, TypeError, "cannot be applied to"),
    (CustomStr("hey"), NotTaggableError, "is not taggable"),
))
def test_trust_as_template_errors(value: object, error_type: t.Type[Exception], error_pattern: str | None) -> None:
    """Validate expected error behavior for `trust_value`."""
    with pytest.raises(error_type, match=error_pattern):
        trust_as_template(value)  # type: ignore


def test_templar_finalize_lazy() -> None:
    """Ensure that containers returned via the `Templar.template` public API shim are always finalized, even under a TemplateContext."""
    variables = dict(
        indirect=TRUST.tag('{{ to_lazy_dict }}'),
        to_lazy_dict=dict(t1=TRUST.tag('{{ "t1value" }}'), t2=TRUST.tag('{{ "t2value" }}'), scalar=42),
    )

    templar = _template.Templar(variables=variables)

    with _engine.TemplateContext(template_value="bogus", templar=templar._engine, options=_engine.TemplateOptions.DEFAULT):
        template = TRUST.tag('{{ indirect }}')

        # self-test to ensure that this test would fail against the engine by default
        assert type(templar._engine.template(template)) is _lazy_containers._AnsibleLazyTemplateDict  # pylint: disable=unidiomatic-typecheck

        result = templar.template(template)

        assert type(result) is dict  # pylint: disable=unidiomatic-typecheck
        assert result['t1'] == 't1value'
        assert result['t2'] == 't2value'
        assert result['scalar'] == 42


def test_templar_finalize_undefined() -> None:
    """Ensure that undefined values returned via the `Templar.template` public API are always finalized, even under a TemplateContext."""
    templar = _template.Templar()

    with _engine.TemplateContext(template_value="bogus", templar=templar._engine, options=_engine.TemplateOptions.DEFAULT):
        undef_template = TRUST.tag('{{ with_undefined }}')

        # self-test to ensure that this test would fail against the engine by default
        assert isinstance(templar._engine.template(undef_template), UndefinedMarker)

        with pytest.raises(AnsibleUndefinedVariable):
            templar.template(undef_template)


def test_set_temporary_context_with_none() -> None:
    """Verify that `set_temporary_context` ignores `None` overrides."""
    templar = _template.Templar()

    with templar.set_temporary_context(variable_start_string=None):
        assert templar.template(trust_as_template('{{ True }}')) is True


def test_copy_with_new_env_with_none() -> None:
    """Verify that `copy_with_new_env` ignores `None` overrides."""
    templar = _template.Templar()

    copied = templar.copy_with_new_env(variable_start_string=None)

    assert copied.template(trust_as_template('{{ True }}')) is True


def test_generate_ansible_template_vars(mocker: pytest_mock.MockerFixture, tmp_path: pathlib.Path) -> None:
    """Verify public API passes through ansible_managed."""
    mocker.patch.object(constants.config, 'get_config_value', return_value='value from config')

    tvars = _template.generate_ansible_template_vars(path="path", fullpath=str(tmp_path), dest_path=str(tmp_path))

    assert tvars['ansible_managed'] == 'value from config'


_ALLOWED_PYTHON_KEYWORDS = sorted(set(keyword.kwlist) - _jinja_bits.JINJA_KEYWORDS)
"""Python keywords which Jinja allows as variable names."""


@pytest.mark.parametrize("keyword_name", _ALLOWED_PYTHON_KEYWORDS)
def test_set_get_keyword(keyword_name: str) -> None:
    """Verify Python keywords that are not Jinja keywords can be freely used to set and get variables in templates."""
    template_set_get = TRUST.tag(f"{{% set {keyword_name} = 42 %}}{{{{ {keyword_name} }}}}")

    assert Templar().template(template_set_get) == 42


@pytest.mark.parametrize("keyword_name", _ALLOWED_PYTHON_KEYWORDS)
def test_if_get_keyword(keyword_name: str) -> None:
    """Verify Python keywords that are not Jinja keywords can be freely used as variables in templates and template conditionals."""
    template_set_get = TRUST.tag(f"{{% if {keyword_name} == 42 %}}{{{{ {keyword_name} }}}}{{% endif %}}")

    assert Templar(variables={keyword_name: 42}).template(template_set_get) == 42
