from __future__ import annotations

import pathlib
import tempfile

from unittest.mock import call

import typing as t

import pytest
import pytest_mock

from ansible import constants as C
from ansible._internal._errors._error_utils import format_exception_message
from ansible._internal._datatag._tags import Origin
from ansible.parsing.utils.yaml import from_yaml
from ansible._internal._yaml._errors import AnsibleYAMLParserError
from ansible.utils.display import Display


@pytest.mark.parametrize("content, expected_message, expect_help_text, line, col", (
    # cases with multiple permutations due to handling of multiple levels of list and up to one dict level

    ('{{ bar }}', 'This may be an issue with missing quotes around a template block.', True, 1, 1),
    ('foo: {{ bar }}', 'This may be an issue with missing quotes around a template block.', True, 1, 6),
    ('- {{ bar }}', 'This may be an issue with missing quotes around a template block.', True, 1, 3),
    ('- foo: {{ bar }}', 'This may be an issue with missing quotes around a template block.', True, 1, 8),
    (' -  - {{ bar }}', 'This may be an issue with missing quotes around a template block.', True, 1, 7),
    (' -  - foo: {{ bar }}', 'This may be an issue with missing quotes around a template block.', True, 1, 12),

    ('"foo" foo', 'Values starting with a quote must end with the same quote.', True, 1, 1),
    ('foo: "foo" foo', 'Values starting with a quote must end with the same quote.', True, 1, 6),
    ('- "foo" foo', 'Values starting with a quote must end with the same quote.', True, 1, 3),
    ('- foo: "foo" foo', 'Values starting with a quote must end with the same quote.', True, 1, 8),
    (' -  - "foo" foo', 'Values starting with a quote must end with the same quote.', True, 1, 7),
    (' -  - foo: "foo" foo', 'Values starting with a quote must end with the same quote.', True, 1, 12),

    ('"foo" "foo"', 'Values starting with a quote must end with the same quote, and not contain that quote.', True, 1, 1),
    ('foo: "foo" "foo"', 'Values starting with a quote must end with the same quote, and not contain that quote.', True, 1, 6),
    ('- "foo" "foo"', 'Values starting with a quote must end with the same quote, and not contain that quote.', True, 1, 3),
    ('- foo: "foo" "foo"', 'Values starting with a quote must end with the same quote, and not contain that quote.', True, 1, 8),
    (' -  - "foo" "foo"', 'Values starting with a quote must end with the same quote, and not contain that quote.', True, 1, 7),
    (' -  - foo: "foo" "foo"', 'Values starting with a quote must end with the same quote, and not contain that quote.', True, 1, 12),

    # cases without list/dict handling

    ('aaa: bbb:', 'Colons in unquoted values must be followed by a non-space character.', True, 1, 9),
    ('aaa: bbb: ccc', 'Colons in unquoted values must be followed by a non-space character.', True, 1, 9),
    ('''- value == "x: 'x' x"''', 'Colons in unquoted values must be followed by a non-space character.', True, 1, 14),

    ('!!map 1\t2\t3', 'Tabs are usually invalid in YAML.', False, 1, 8),
    ('{a: 1, a: 1}', "Found duplicate mapping key 'a'.", False, 1, 8),

    (1, 'a string or stream input is required', False, None, None),  # wrong type (misuse of API)

    # cases where the underling MarkedYAMLError is used

    ('k1: v1\n  k2: v2', 'Mapping values are not allowed in this context.', False, 2, 5),
    ('k1: v1\n  k2: ":"', 'Mapping values are not allowed in this context.', False, 2, 5),

    (':', 'While parsing a block mapping did not find expected key.', False, 1, 1),
    ('!!map 1', 'Expected a mapping node, but found scalar.', False, 1, 1),
    ('[]: bad', 'While constructing a mapping found unhashable key.', False, 1, 1),
    ('{}: bad', 'While constructing a mapping found unhashable key.', False, 1, 1),
    ('"\\"', 'While scanning a quoted scalar found unexpected end of stream.', False, 1, 4),

    # DTFIX-FUTURE: add tests that use comments
))
def test_yaml_parser_error(
        content: t.Any,
        expected_message: str,
        expect_help_text: bool,
        line: int | None,
        col: int | None,
        mocker: pytest_mock.MockerFixture,
) -> None:
    set_duplicate_yaml_dict_key_config(mocker, 'error')

    expected_message = f'YAML parsing failed: {expected_message}'

    with tempfile.TemporaryDirectory() as tempdir:
        source_path = pathlib.Path(tempdir) / 'source.yml'
        source_path.write_text(str(content))

        with pytest.raises(AnsibleYAMLParserError) as error:
            from_yaml(content, file_name=str(source_path))

    assert error.value.message == expected_message
    assert error.value._original_message == expected_message
    assert format_exception_message(error.value) == expected_message
    assert str(error.value) == expected_message

    assert error.value.obj == Origin(path=str(source_path), line_num=line, col_num=col)

    if expect_help_text:
        assert error.value._help_text is not None  # DTFIX-FUTURE: check the content later once it's less volatile
    else:
        assert error.value._help_text is None


def test_yaml_duplicate_key_warning(mocker: pytest_mock.MockerFixture) -> None:
    set_duplicate_yaml_dict_key_config(mocker, 'warn')

    patched_warning = mocker.patch.object(Display(), 'warning')

    assert from_yaml('{a: 1, b: 2, c: 3, b: 4, d: 5, b: 6}', file_name='/hello.yml')

    patched_warning.assert_has_calls((
        call(msg="Found duplicate mapping key 'b'.", obj="b", help_text="Using last defined value only."),
        call(msg="Found duplicate mapping key 'b'.", obj="b", help_text="Using last defined value only."),
    ))


def test_yaml_duplicate_key_ignore(mocker: pytest_mock.MockerFixture) -> None:
    set_duplicate_yaml_dict_key_config(mocker, 'ignore')

    warning_spy = mocker.spy(Display(), 'warning')

    assert from_yaml('{a: 1, a: 2}', file_name='/hello.yml')

    warning_spy.assert_not_called()


def set_duplicate_yaml_dict_key_config(mocker: pytest_mock.MockerFixture, value: str):
    original_get_config_value = C.config.get_config_value

    def mocked_get_config_value(config, *args, **kwargs):
        if config == 'DUPLICATE_YAML_DICT_KEY':
            return value

        return original_get_config_value(config, *args, **kwargs)

    mocker.patch.object(C.config, 'get_config_value', mocked_get_config_value)
