# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pathlib
import typing as t

import pytest
import pytest_mock
from jinja2 import pass_context
from jinja2.ext import Extension
from jinja2.runtime import Context

from ansible._internal._datatag._tags import Origin, TrustedAsTemplate
from ansible._internal._templating._engine import TemplateEngine, TemplateOptions, _ExpressionCacheContext
from ansible._internal._templating._jinja_bits import AnsibleCodeGenerator, AnsibleEnvironment
from ansible._internal._templating._utils import TemplateContext
from ansible.errors import AnsibleTemplateSyntaxError, AnsibleUndefinedVariable, TemplateTrustCheckFailedError


def _trusted(expression: str, path: str | None = None, line: int = 1) -> str:
    expression = TrustedAsTemplate().tag(expression)
    if path:
        expression = Origin(path=path, line_num=line, col_num=3).tag(expression)
    return expression


@pytest.fixture
def engine(collection_loader: None) -> TemplateEngine:
    return TemplateEngine()


def test_fresh_variables_and_local_variables(engine: TemplateEngine, mocker: pytest_mock.MockerFixture) -> None:
    compile_expression = mocker.spy(engine.environment, 'compile_expression')
    expression = _trusted("host ~ ':' ~ (offset + increment)")

    with engine.expression_cache():
        engine.available_variables = dict(host='first', offset=10)
        assert engine.evaluate_expression(expression, local_variables=dict(increment=1)) == 'first:11'
        engine.available_variables = dict(host='second', offset=20)
        assert engine.evaluate_expression(expression, local_variables=dict(increment=2)) == 'second:22'

    assert compile_expression.call_count == 1


def test_stateful_filter_with_literal_input_runs_each_time(engine: TemplateEngine, mocker: pytest_mock.MockerFixture) -> None:
    calls: list[str] = []

    def counter(value: str) -> str:
        calls.append(value)
        return f'{value}:{len(calls)}'

    engine.environment.filters['cache_test_counter'] = counter
    compile_expression = mocker.spy(engine.environment, 'compile_expression')
    expression = _trusted("'literal' | cache_test_counter")

    with engine.expression_cache():
        assert engine.evaluate_expression(expression) == 'literal:1'
        assert engine.evaluate_expression(expression) == 'literal:2'

    assert calls == ['literal', 'literal']
    assert compile_expression.call_count == 1


def test_context_aware_plugins_use_current_host_variables(engine: TemplateEngine, mocker: pytest_mock.MockerFixture) -> None:
    @pass_context
    def host_label(context: Context, value: str) -> str:
        return f'{context.resolve("host")}:{value}'

    @pass_context
    def matches_host(context: Context, value: str) -> bool:
        return value == context.resolve('host')

    engine.environment.filters['cache_test_host_label'] = host_label
    engine.environment.tests['cache_test_matches_host'] = matches_host
    compile_expression = mocker.spy(engine.environment, 'compile_expression')
    label_expression = _trusted('value | cache_test_host_label')
    test_expression = _trusted('value is cache_test_matches_host')

    with engine.expression_cache():
        for host, matches in [('first', True), ('second', False)]:
            engine.available_variables = dict(host=host, value='first')
            assert engine.evaluate_expression(label_expression) == f'{host}:first'
            assert engine.evaluate_expression(test_expression) is matches

    assert compile_expression.call_count == 2


def test_mutable_literal_containers_are_fresh_for_each_evaluation(engine: TemplateEngine, mocker: pytest_mock.MockerFixture) -> None:
    def append_value(value: dict[str, list[int]]) -> dict[str, list[int]]:
        value['items'].append(3)
        return value

    engine.environment.filters['cache_test_append'] = append_value
    compile_expression = mocker.spy(engine.environment, 'compile_expression')
    expression = _trusted("{'items': [1, 2]} | cache_test_append")

    with engine.expression_cache():
        for iteration in range(2):
            assert engine.evaluate_expression(expression) == dict(items=[1, 2, 3])

    assert compile_expression.call_count == 1


def test_lookup_runs_each_time(engine: TemplateEngine, monkeypatch: pytest.MonkeyPatch, mocker: pytest_mock.MockerFixture) -> None:
    compile_expression = mocker.spy(engine.environment, 'compile_expression')
    expression = _trusted("lookup('ansible.builtin.env', 'ANSIBLE_EXPRESSION_CACHE_TEST')")

    with engine.expression_cache():
        monkeypatch.setenv('ANSIBLE_EXPRESSION_CACHE_TEST', 'first')
        assert engine.evaluate_expression(expression) == 'first'
        monkeypatch.setenv('ANSIBLE_EXPRESSION_CACHE_TEST', 'second')
        assert engine.evaluate_expression(expression) == 'second'

    assert compile_expression.call_count == 1


def test_undefined_result_does_not_poison_later_evaluation(engine: TemplateEngine, mocker: pytest_mock.MockerFixture) -> None:
    compile_expression = mocker.spy(engine.environment, 'compile_expression')
    expression = _trusted('value + 1')

    with engine.expression_cache():
        with pytest.raises(AnsibleUndefinedVariable):
            engine.evaluate_expression(expression)
        engine.available_variables = dict(value=2)
        assert engine.evaluate_expression(expression) == 3

    assert compile_expression.call_count == 1


def test_trust_is_checked_for_every_evaluation(engine: TemplateEngine, mocker: pytest_mock.MockerFixture) -> None:
    engine.available_variables = dict(value='safe')
    compile_expression = mocker.spy(engine.environment, 'compile_expression')

    with engine.expression_cache():
        assert engine.evaluate_expression(_trusted('value')) == 'safe'
        with pytest.raises(TemplateTrustCheckFailedError):
            engine.evaluate_expression('value')
        assert engine.evaluate_expression(_trusted('value')) == 'safe'

    assert compile_expression.call_count == 1


def test_fresh_values_preserve_their_own_origins(engine: TemplateEngine, mocker: pytest_mock.MockerFixture) -> None:
    compile_expression = mocker.spy(engine.environment, 'compile_expression')
    expression = _trusted('value', '/inventory/constructed.yml', line=4)
    values = [Origin(path='/inventory/first.yml', line_num=6).tag('first'), Origin(path='/inventory/second.yml', line_num=8).tag('second')]

    with engine.expression_cache():
        for value in values:
            engine.available_variables = dict(value=value)
            result = engine.evaluate_expression(expression)
            assert result == value
            assert Origin.get_tag(result) == Origin.get_tag(value)

    assert compile_expression.call_count == 1


def test_equal_expression_text_at_distinct_origins_is_not_shared(engine: TemplateEngine, mocker: pytest_mock.MockerFixture) -> None:
    engine.available_variables = dict(value='result')
    compile_expression = mocker.spy(engine.environment, 'compile_expression')
    expressions = [_trusted('value', '/inventory/first.yml', line=2), _trusted('value', '/inventory/second.yml', line=9)]

    with engine.expression_cache():
        for expression in expressions:
            assert Origin.get_tag(engine.evaluate_expression(expression)) == Origin.get_tag(expression)
            assert Origin.get_tag(engine.evaluate_expression(expression)) == Origin.get_tag(expression)

    assert compile_expression.call_count == 2


def test_undefined_errors_preserve_expression_origins(engine: TemplateEngine, mocker: pytest_mock.MockerFixture) -> None:
    compile_expression = mocker.spy(engine.environment, 'compile_expression')

    with engine.expression_cache():
        for path in ('/inventory/first.yml', '/inventory/second.yml'):
            expression = _trusted('missing + 1', path)
            for iteration in range(2):
                with pytest.raises(AnsibleUndefinedVariable) as raised:
                    engine.evaluate_expression(expression)
                assert Origin.get_tag(raised.value.obj) == Origin.get_tag(expression)

    assert compile_expression.call_count == 2


def test_compile_errors_are_not_cached(engine: TemplateEngine, mocker: pytest_mock.MockerFixture) -> None:
    compile_expression = mocker.spy(engine.environment, 'compile_expression')
    expression = _trusted('value +', '/inventory/broken.yml', line=8)

    with engine.expression_cache():
        for iteration in range(2):
            with pytest.raises(AnsibleTemplateSyntaxError) as raised:
                engine.evaluate_expression(expression)
            assert Origin.get_tag(raised.value.obj) == Origin.get_tag(expression)

    assert compile_expression.call_count == 2


def test_backslash_options_are_not_shared(engine: TemplateEngine, mocker: pytest_mock.MockerFixture) -> None:
    expression = _trusted(r"'\n'")
    expected = [engine.evaluate_expression(expression, escape_backslashes=escape) for escape in (True, False)]
    compile_expression = mocker.spy(engine.environment, 'compile_expression')

    with engine.expression_cache():
        actual = [engine.evaluate_expression(expression, escape_backslashes=escape) for escape in (True, False)]
        assert actual == expected
        assert engine.evaluate_expression(expression, escape_backslashes=True) == expected[0]

    assert compile_expression.call_count == 2


class _CompileCounterExtension(Extension):
    def __init__(self, environment: t.Any) -> None:
        super().__init__(environment)
        self.compiles = 0

    def preprocess(self, source: str, name: str | None, filename: str | None = None) -> str:
        self.compiles += 1
        return str(self.compiles)


@pytest.mark.parametrize('add_after_first_evaluation', [False, True])
def test_compile_extensions_bypass_reuse(engine: TemplateEngine, add_after_first_evaluation: bool, mocker: pytest_mock.MockerFixture) -> None:
    expression = _trusted("'original'")
    compile_expression = mocker.spy(engine.environment, 'compile_expression')
    if not add_after_first_evaluation:
        engine.environment.add_extension(_CompileCounterExtension)

    with engine.expression_cache():
        if add_after_first_evaluation:
            assert engine.evaluate_expression(expression) == 'original'
            engine.environment.add_extension(_CompileCounterExtension)
        assert [engine.evaluate_expression(expression) for iteration in range(2)] == [1, 2]

    assert compile_expression.call_count == 2 + add_after_first_evaluation


@pytest.mark.parametrize('copy_method', ['copy', 'extend'])
def test_cache_applies_to_exact_engine_only(engine: TemplateEngine, copy_method: str, mocker: pytest_mock.MockerFixture) -> None:
    expression = _trusted('value')
    engine.available_variables = dict(value=1)
    compile_expression = mocker.spy(engine.environment, 'compile_expression')
    derived = getattr(engine, copy_method)()
    derived.available_variables = dict(value=2)
    derived_compile = compile_expression if copy_method == 'extend' else mocker.spy(derived.environment, 'compile_expression')

    with engine.expression_cache():
        assert engine.evaluate_expression(expression) == 1
        assert engine.evaluate_expression(expression) == 1
        assert derived.evaluate_expression(expression) == 2
        assert derived.evaluate_expression(expression) == 2

    if copy_method == 'extend':
        assert derived.environment is engine.environment
        assert compile_expression.call_count == 3
    else:
        assert derived.environment is not engine.environment
        assert compile_expression.call_count == 1
        assert derived_compile.call_count == 2


def test_no_reuse_outside_scope(engine: TemplateEngine, mocker: pytest_mock.MockerFixture) -> None:
    expression = _trusted('1')
    compile_expression = mocker.spy(engine.environment, 'compile_expression')

    assert engine.evaluate_expression(expression) == 1
    assert engine.evaluate_expression(expression) == 1

    assert compile_expression.call_count == 2


def test_nested_scope_restores_outer_compiled_expressions(engine: TemplateEngine, mocker: pytest_mock.MockerFixture) -> None:
    expression = _trusted('value')
    compile_expression = mocker.spy(engine.environment, 'compile_expression')

    with engine.expression_cache():
        engine.available_variables = dict(value='outer')
        assert engine.evaluate_expression(expression) == 'outer'
        with engine.expression_cache():
            engine.available_variables = dict(value='inner')
            assert engine.evaluate_expression(expression) == 'inner'
            assert engine.evaluate_expression(expression) == 'inner'
        engine.available_variables = dict(value='restored')
        assert engine.evaluate_expression(expression) == 'restored'
        assert compile_expression.call_count == 2

    assert engine.evaluate_expression(expression) == 'restored'
    assert compile_expression.call_count == 3


@pytest.mark.parametrize('raise_inside_scope', [False, True])
def test_scope_cleanup_and_new_scope(engine: TemplateEngine, raise_inside_scope: bool, mocker: pytest_mock.MockerFixture) -> None:
    expression = _trusted('1')
    compile_expression = mocker.spy(engine.environment, 'compile_expression')

    def evaluate_in_scope() -> None:
        with engine.expression_cache():
            assert engine.evaluate_expression(expression) == 1
            assert engine.evaluate_expression(expression) == 1
            if raise_inside_scope:
                raise RuntimeError('scope failure')

    if raise_inside_scope:
        with pytest.raises(RuntimeError, match='scope failure'):
            evaluate_in_scope()
    else:
        evaluate_in_scope()

    assert engine.evaluate_expression(expression) == 1
    with engine.expression_cache():
        assert engine.evaluate_expression(expression) == 1
        assert engine.evaluate_expression(expression) == 1

    assert compile_expression.call_count == 3


def test_custom_environment_bypasses_reuse(engine: TemplateEngine, mocker: pytest_mock.MockerFixture) -> None:
    class CustomEnvironment(AnsibleEnvironment):
        pass

    engine._environment = CustomEnvironment()
    compile_expression = mocker.spy(engine.environment, 'compile_expression')
    expression = _trusted('value')

    with engine.expression_cache():
        engine.available_variables = dict(value='first')
        assert engine.evaluate_expression(expression) == 'first'
        engine.available_variables = dict(value='second')
        assert engine.evaluate_expression(expression) == 'second'

    assert compile_expression.call_count == 2


@pytest.mark.parametrize('install_after_first_evaluation', [False, True])
def test_custom_code_generator_bypasses_reuse(
    engine: TemplateEngine, install_after_first_evaluation: bool, mocker: pytest_mock.MockerFixture
) -> None:
    values = iter((1, 2))

    class CustomCodeGenerator(AnsibleCodeGenerator):
        def visit_Const(self, node: t.Any, frame: t.Any) -> None:
            self.write(repr(next(values)))

    expression = _trusted("'original'")
    compile_expression = mocker.spy(engine.environment, 'compile_expression')
    if not install_after_first_evaluation:
        engine.environment.code_generator_class = CustomCodeGenerator

    with engine.expression_cache():
        if install_after_first_evaluation:
            assert engine.evaluate_expression(expression) == 'original'
            engine.environment.code_generator_class = CustomCodeGenerator
        assert [engine.evaluate_expression(expression) for iteration in range(2)] == [1, 2]

    assert compile_expression.call_count == 2 + install_after_first_evaluation


def test_source_debugging_bypasses_reuse(
    engine: TemplateEngine, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, mocker: pytest_mock.MockerFixture
) -> None:
    monkeypatch.setattr(engine.environment, '_debuggable_template_source', True)
    monkeypatch.setattr(engine.environment, '_debuggable_template_source_path', tmp_path)
    compile_expression = mocker.spy(engine.environment, 'compile_expression')
    expression = _trusted('value')

    with engine.expression_cache():
        engine.available_variables = dict(value='first')
        assert engine.evaluate_expression(expression) == 'first'
        engine.available_variables = dict(value='second')
        assert engine.evaluate_expression(expression) == 'second'

    assert compile_expression.call_count == 2
    assert list(tmp_path.glob('j2_src_*.py'))


def test_unhashable_options_bypass_reuse(engine: TemplateEngine, mocker: pytest_mock.MockerFixture) -> None:
    # value_for_omit accepts arbitrary objects, including unhashable containers.
    options = TemplateOptions(value_for_omit=[])
    expression = _trusted('value')
    compile_expression = mocker.spy(engine.environment, 'compile_expression')

    with engine.expression_cache(), TemplateContext(template_value=expression, templar=engine, options=options, stop_on_template=False):
        first = engine._compile_expression(expression, options)
        second = engine._compile_expression(expression, options)
        assert first(dict(value='first')) == 'first'
        assert second(dict(value='second')) == 'second'

    assert compile_expression.call_count == 2


def test_cache_is_bounded_and_recently_used_expression_is_retained(
    engine: TemplateEngine, monkeypatch: pytest.MonkeyPatch, mocker: pytest_mock.MockerFixture
) -> None:
    monkeypatch.setattr(_ExpressionCacheContext, 'MAX_ENTRIES', 2)
    engine.available_variables = dict(one=1, two=2, three=3)
    compile_expression = mocker.spy(engine.environment, 'compile_expression')

    with engine.expression_cache():
        for expression, expected in [('one', 1), ('two', 2), ('one', 1), ('three', 3), ('two', 2)]:
            assert engine.evaluate_expression(_trusted(expression)) == expected

    assert [call.args[0] for call in compile_expression.call_args_list] == ['one', 'two', 'three', 'two']
