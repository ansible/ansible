from __future__ import annotations

import pytest


def test_failed_non_interactive_captured_command() -> None:
    """Verify failed non-interactive captured commands raise a `SubprocessError` with `stdout` and `stderr` set."""
    from ansible_test._internal.util import raw_command, SubprocessError

    with pytest.raises(SubprocessError, match='Command "ls /dev/null /does/not/exist" returned exit status [0-9]+.\n>>> Standard Error\n') as error:
        raw_command(['ls', '/dev/null', '/does/not/exist'], True)

    assert '/dev/null' in error.value.stdout
    assert '/does/not/exist' in error.value.stderr


def test_failed_non_interactive_command() -> None:
    """Verify failed non-interactive non-captured commands raise a `SubprocessError` with `stdout` and `stderr` set to an empty string."""
    from ansible_test._internal.util import raw_command, SubprocessError

    with pytest.raises(SubprocessError, match='Command "ls /dev/null /does/not/exist" returned exit status [0-9]+.') as error:
        raw_command(['ls', '/dev/null', '/does/not/exist'], False)

    assert error.value.stdout == ''
    assert error.value.stderr == ''


def test_failed_interactive_command() -> None:
    """Verify failed interactive commands raise a `SubprocessError` with `stdout` and `stderr` set to `None`."""
    from ansible_test._internal.util import raw_command, SubprocessError

    with pytest.raises(SubprocessError, match='Command "ls /dev/null /does/not/exist" returned exit status [0-9]+.') as error:
        raw_command(['ls', '/dev/null', '/does/not/exist'], False, interactive=True)

    assert error.value.stdout is None
    assert error.value.stderr is None


@pytest.mark.parametrize("args,filters,expected", (
    (
        # args after a known option must be separated from existing args
        ['--color', '--docker', 'default', 'ping', 'split'],
        {'--docker': 1},
        ['--color', '--', 'ping', 'split'],
    ),
    (
        # args after '--' are not options
        ['--', '--color'],
        {'--color': 1},
        ['--', '--color'],
    ),
    (
        # args after a known option must be separated from existing args without conflicting with an explicit '--'
        ['--color', '--docker', 'default', 'ping', '--', 'split'],
        {'--docker': 1},
        ['--color', '--', 'ping', 'split'],
    ),
    (
        # args before options are properly handled
        ['ping', '--docker', 'default', '-v'],
        {'--docker': 1},
        ['ping', '-v'],
    ),
    (
        # no options
        ['ping', 'split'],
        {'--docker': 1},
        ['ping', 'split'],
    ),
    (
        # only options
        ['--color', '--docker', 'default', '-v'],
        {'--docker': 1},
        ['--color', '-v'],
    )
))
def test_filter_args(args: list[str], filters: dict[str, int], expected: list[str]) -> None:
    """Verify arg filtering properly handles various scenarios."""
    from ansible_test._internal.util import filter_args

    assert filter_args(args, filters) == expected
