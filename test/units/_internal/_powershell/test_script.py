from __future__ import annotations

import pytest

from ansible._internal._powershell import _script


# print_argv is a binary that echoes back the argv it receives.
ENCODED_CMD_CASES = [
    (
        # print_argv {'foo'}
        "'foo'",
        [],
        ['-EncodedCommand', 'JwBmAG8AbwAnAA=='],
    ),
    (
        # print_argv {'foo'} -args 'simple', '_x005F_', ([char]::ConvertFromUtf32(0x1F3B5))
        "'foo'",
        ['simple', '_x005F_', "\U0001F3B5"],
        ['-EncodedCommand', 'JwBmAG8AbwAnAA==', '-EncodedArguments', (
            'PABPAGIAagBzACAAeABtAGwAbgBzAD0AIgBoAHQAdABwADoALwAvAHMAYwBoAGUAbQBhAHMALgBtAGkAYwByAG8AcwBvAGYAdAAuAGMAb'
            'wBtAC8AcABvAHcAZQByAHMAaABlAGwAbAAvADIAMAAwADQALwAwADQAIgAgAFYAZQByAHMAaQBvAG4APQAiADEALgAxAC4AMAAuADEAIg'
            'A+ADwATwBiAGoAIABSAGUAZgBJAGQAPQAiADAAIgA+ADwAVABOACAAUgBlAGYASQBkAD0AIgAwACIAPgA8AFQAPgBTAHkAcwB0AGUAbQA'
            'uAEMAbwBsAGwAZQBjAHQAaQBvAG4AcwAuAEEAcgByAGEAeQBMAGkAcwB0ADwALwBUAD4APABUAD4AUwB5AHMAdABlAG0ALgBPAGIAagBl'
            'AGMAdAA8AC8AVAA+ADwALwBUAE4APgA8AEwAUwBUAD4APABTAD4AcwBpAG0AcABsAGUAPAAvAFMAPgA8AFMAPgBfAHgAMAAwADUARgBfA'
            'HgAMAAwADUARgBfADwALwBTAD4APABTAD4AXwB4AEQAOAAzAEMAXwBfAHgARABGAEIANQBfADwALwBTAD4APAAvAEwAUwBUAD4APAAvAE'
            '8AYgBqAD4APAAvAE8AYgBqAHMAPgA='
        )],
    )
]


@pytest.mark.parametrize('value, expected', [
    ('foo', 'foo'),
    ('foo_bar', 'foo_bar'),
    ('foo-bar', 'foo-bar'),
    ('123', '123'),
    (r'C:\temp\pwsh.exe', r'C:\temp\pwsh.exe'),
    ('C:/temp/pwsh.exe', 'C:/temp/pwsh.exe'),
    ('', "''"),
    ('foo bar', "'foo bar'"),
    ('@foo', "'@foo'"),
    ("foo'bar", "'foo''bar'"),
    ("foo\u2018bar", "'foo\u2018\u2018bar'"),
    ("foo\u2019bar", "'foo\u2019\u2019bar'"),
    ("foo\u201abar", "'foo\u201a\u201abar'"),
    ("foo\u201bbar", "'foo\u201b\u201bbar'"),
])
def test_quote_argument(value, expected):
    actual = _script.quote_pwsh_argument(value)
    assert actual == expected


def test_quote_argument_force():
    actual = _script.quote_pwsh_argument('foo', force_quote=True)
    assert actual == "'foo'"


@pytest.mark.parametrize('cmd, args, expected', ENCODED_CMD_CASES)
def test_build_encoded_command(cmd, args, expected):
    actual = _script._get_encoded_arguments(cmd, args)
    assert actual == expected


@pytest.mark.parametrize('expected_cmd, expected_args, cmd_args', ENCODED_CMD_CASES)
def test_parse_encoded_command(expected_cmd, expected_args, cmd_args):
    actual_cmd, actual_args = _script.parse_encoded_cmdline(" ".join(cmd_args))
    assert actual_cmd == expected_cmd
    assert actual_args == expected_args


def test_parse_encoded_command_no_encoded_command():
    actual = _script.parse_encoded_cmdline('pwsh -EncodedArguments YQA=')
    assert actual is None


def test_parse_encoded_command_no_value():
    actual = _script.parse_encoded_cmdline('pwsh -EncodedCommand')
    assert actual is None


def test_parse_encoded_command_no_args():
    actual_script, actual_args = _script.parse_encoded_cmdline('pwsh -EncodedCommand YQA= foo')
    assert actual_script == 'a'
    assert actual_args == []


def test_parse_encoded_command_quoted():
    actual_script, actual_args = _script.parse_encoded_cmdline("pwsh '-EncodedCommand' YQA= foo")
    assert actual_script == 'a'
    assert actual_args == []


def test_parse_encoded_command_no_value_after_args():
    actual = _script.parse_encoded_cmdline('pwsh -EncodedCommand YQA= -EncodedArguments')
    assert actual is None


@pytest.mark.parametrize(
    ('cmd', 'args', 'expected'),
    (
        pytest.param(
            'foo.exe',
            None,
            'foo.exe',
            id='no-args-relative-path',
        ),
        pytest.param(
            r'C:\Program Files\foo.exe',
            None,
            r"& 'C:\Program Files\foo.exe'",
            id='no-args-absolute-path',
        ),
        pytest.param(
            'foo.exe',
            ['simple', 'with space'],
            "foo.exe simple 'with space'",
            id='whitespace',
        ),
        pytest.param(
            'foo.exe',
            ["with 'single' quote"],
            "foo.exe 'with ''single'' quote'",
            id='single-quote',
        ),
        pytest.param(
            'C:/path with space/test',
            ['arg1', 'arg 2'],
            "& 'C:/path with space/test' arg1 'arg 2'",
            id='spaced-path',
        ),
    ),
)
def test_build_pwsh_cmd_statement(cmd, args, expected):
    actual = _script.build_pwsh_cmd_statement(cmd, args)
    assert actual == expected
