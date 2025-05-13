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
