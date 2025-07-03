from __future__ import annotations

import pathlib
import tempfile

import pytest

from ansible.errors import AnsibleJSONParserError
from ansible._internal._errors._error_utils import format_exception_message
from ansible._internal._datatag._tags import Origin
from ansible.parsing.utils.yaml import from_yaml


def test_json_parser_error() -> None:
    # This is basically a copy of test_yaml_parser_error in test/units/parsing/yaml/test_errors.py.
    # Most of the coverage for parsing.utils.yaml is achieved while testing parsing.yaml.errors.

    content = 'x'
    expected_message = 'JSON parsing failed: Expecting value: line 1 column 1 (char 0)'
    line = 1
    col = 1
    expect_help_text = False

    with tempfile.TemporaryDirectory() as tempdir:
        source_path = pathlib.Path(tempdir) / 'source.yml'
        source_path.write_text(str(content))

        with pytest.raises(AnsibleJSONParserError) as error:
            from_yaml(content, file_name=str(source_path), json_only=True)

    assert error.value.message == expected_message
    assert error.value._original_message == expected_message
    assert format_exception_message(error.value) == expected_message
    assert str(error.value) == expected_message

    assert error.value.obj == Origin(path=str(source_path), line_num=line, col_num=col)

    if expect_help_text:
        assert error.value._help_text is not None  # DTFIX-FUTURE: check the content later once it's less volatile
    else:
        assert error.value._help_text is None
