# Copyright (c) Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import sys
from unittest.mock import Mock

import pytest

from ansible._internal._prompt import build_prompt_validator
from ansible._internal._templating._engine import TemplateEngine
from ansible._internal._datatag._tags import TrustedAsTemplate
from ansible.errors import AnsibleError
from ansible.playbook.play import Play
from ansible.utils.display import Display


pytestmark = pytest.mark.usefixtures('collection_loader')


def validator(expression: str, varname: str = 'number', variables: dict | None = None):
    return build_prompt_validator(TrustedAsTemplate().tag(expression), varname, TemplateEngine(variables=variables))


@pytest.mark.parametrize('expression', [42, False, [], {}, '', 'number is', '{{ number == 123 }}'])
def test_invalid_validation_expression(expression: object) -> None:
    with pytest.raises(AnsibleError, match='vars_prompt validate'):
        build_prompt_validator(expression, 'number', TemplateEngine())


def test_missing_validation_expression() -> None:
    assert build_prompt_validator(None, 'number', TemplateEngine()) is None


def test_play_accepts_validate() -> None:
    play = Play.load(dict(hosts='localhost', vars_prompt=[dict(name='phone', validate="phone is match('^[0-9]{10}$')")]))
    assert play.vars_prompt[0]['validate'] == "phone is match('^[0-9]{10}$')"


@pytest.fixture
def prompt_display(monkeypatch, display_resource):
    display = Display()
    monkeypatch.setattr(sys, '__stdin__', Mock(isatty=Mock(return_value=True)))
    monkeypatch.setattr(display, 'display', Mock())
    monkeypatch.setattr(display, 'warning', Mock())
    return display


def test_retry_requires_full_match(monkeypatch, prompt_display) -> None:
    prompt = Mock(side_effect=['prefix123suffix', '123'])
    monkeypatch.setattr(prompt_display, 'prompt', prompt)
    result = prompt_display.do_var_prompt('number', private=False, validate=validator("number is match('^[0-9]{3}$')"))
    assert result == '123'
    assert prompt.call_count == 2
    assert TrustedAsTemplate.is_tagged_on(result)
    prompt_display.display.assert_called_once()
    assert 'prefix123suffix' not in prompt_display.display.call_args.args[0]


def test_confirmation_and_validation(monkeypatch, prompt_display) -> None:
    prompt = Mock(side_effect=['123', '456', 'bad', 'bad', '789', '789'])
    monkeypatch.setattr(prompt_display, 'prompt', prompt)
    result = prompt_display.do_var_prompt('number', confirm=True, validate=validator("number is match('^[0-9]{3}$')"))
    assert result == '789'
    assert prompt.call_count == 6


@pytest.mark.parametrize('default, answers, expected', [('123', [''], '123'), ('bad', ['', '456'], '456')])
def test_interactive_default(monkeypatch, prompt_display, default: str, answers: list[str], expected: str) -> None:
    monkeypatch.setattr(prompt_display, 'prompt', Mock(side_effect=answers))
    assert prompt_display.do_var_prompt('number', default=default, validate=validator("number is match('^[0-9]{3}$')")) == expected


@pytest.mark.parametrize('default', ['bad', None])
def test_noninteractive_invalid_value(monkeypatch, prompt_display, default: str | None) -> None:
    monkeypatch.setattr(sys, '__stdin__', Mock(isatty=Mock(return_value=False)))
    prompt = Mock(side_effect=AssertionError('must not prompt'))
    monkeypatch.setattr(prompt_display, 'prompt', prompt)
    with pytest.raises(AnsibleError, match='non-interactive mode') as exc:
        prompt_display.do_var_prompt('number', default=default, validate=validator("number is match('^[0-9]{3}$')"))
    assert "'bad'" not in str(exc.value)
    prompt.assert_not_called()
    prompt_display.warning.assert_called_once()


def test_noninteractive_valid_default(monkeypatch, prompt_display) -> None:
    monkeypatch.setattr(sys, '__stdin__', Mock(isatty=Mock(return_value=False)))
    assert prompt_display.do_var_prompt('number', default='123', validate=validator("number is match('^[0-9]{3}$')")) == '123'


def test_validation_precedes_hashing(monkeypatch, prompt_display) -> None:
    from ansible.utils import encrypt

    monkeypatch.setattr(prompt_display, 'prompt', Mock(side_effect=['bad', '123']))
    hashing = Mock(return_value='hashed-value')
    monkeypatch.setattr(encrypt, 'do_encrypt', hashing)
    result = prompt_display.do_var_prompt('password', encrypt='sha512_crypt', validate=validator("password is match('^[0-9]{3}$')", 'password'))
    assert result == 'hashed-value'
    hashing.assert_called_once_with('123', 'sha512_crypt', salt_size=None, salt=None)


def test_empty_input_and_unsafe(monkeypatch, prompt_display) -> None:
    monkeypatch.setattr(prompt_display, 'prompt', Mock(return_value=''))
    result = prompt_display.do_var_prompt('value', unsafe=True, validate=validator("value == ''", 'value'))
    assert result == ''
    assert not TrustedAsTemplate.is_tagged_on(result)


def test_unicode_input(monkeypatch, prompt_display) -> None:
    monkeypatch.setattr(prompt_display, 'prompt', Mock(return_value='caf\u00e9'))
    assert prompt_display.do_var_prompt('value', validate=validator("value is match('^\\\\w+$')", 'value')) == 'caf\u00e9'


@pytest.mark.parametrize('expression, candidate, expected', [
    ("url is match('^https://')", 'https://example.org', True),
    ("url is match('^https://')", 'http://example.org', False),
    ("url in ['dev', 'staging', 'prod']", 'prod', True),
    ("url in ['dev', 'staging', 'prod']", 'unknown', False),
    ("url | length == 3", 'abc', True),
])
def test_jinja_tests_filters_and_membership(expression: str, candidate: str, expected: bool) -> None:
    assert validator(expression, 'url')(candidate) is expected


def test_candidate_overrides_existing_value_without_mutating_vars() -> None:
    variables = dict(number='old', allowed=['new'])
    validate = validator('number in allowed', variables=variables)
    assert validate('new')
    assert not validate('old')
    assert variables['number'] == 'old'


def test_lookup_in_validation(monkeypatch) -> None:
    monkeypatch.setenv('ANSIBLE_PROMPT_TEST_VALUE', 'expected')
    validate = validator("number == lookup('ansible.builtin.env', 'ANSIBLE_PROMPT_TEST_VALUE')")
    assert validate('expected')
    assert not validate('different')


def test_input_is_not_evaluated_as_template() -> None:
    assert validator('number | length == 11')('{{ 1 + 1 }}')


@pytest.mark.parametrize('expression', ['missing_variable == number', 'number | length', 'number is missing_test'])
def test_evaluation_errors_stop_prompt(monkeypatch, prompt_display, expression: str) -> None:
    prompt = Mock(return_value='private-input')
    monkeypatch.setattr(prompt_display, 'prompt', prompt)
    with pytest.raises(AnsibleError, match='Error evaluating vars_prompt validation'):
        prompt_display.do_var_prompt('number', validate=validator(expression))
    prompt.assert_called_once()
    prompt_display.display.assert_not_called()


def test_untrusted_expression_is_not_promoted_to_template() -> None:
    validate = build_prompt_validator("number == '123'", 'number', TemplateEngine())
    with pytest.raises(AnsibleError, match='Error evaluating vars_prompt validation'):
        validate('123')
