from __future__ import annotations

import os

import pytest
import pytest_mock

from ansible.constants import config
from ansible.errors import AnsibleUndefinedConfigEntry
from ansible._internal._errors._handler import ErrorHandler, ErrorAction, Skippable, _SkipException
from ansible.utils.display import Display


def test_skippable_ignore_skips_body() -> None:
    """Verify that `skip_on_ignore=True` skips the body within the context manager when `action=ErrorAction.IGNORE`."""
    body_ran = False
    assert not body_ran  # satisfy static analysis which assumes the context manager body will run

    with Skippable, ErrorHandler(ErrorAction.IGNORE).handle(Exception, skip_on_ignore=True):
        body_ran = True

    assert not body_ran


def test_skippable_without_skip_on_ignore() -> None:
    """
    Verify using `Skippable` without invoking a handler with `skip_on_ignore=True` will fail.
    This protects against accidental use of `Skippable` by itself, or forgetting to use `skip_on_ignore=True` -- both of which have no effect.
    """
    body_ran = False
    assert not body_ran  # satisfy static analysis which assumes the context manager body will run

    with pytest.raises(RuntimeError) as err:
        with Skippable:
            body_ran = True

    assert body_ran
    assert 'handler was never invoked' in str(err.value)


def test_skippable_non_skip_exception() -> None:
    """Verify that `Skippable` does not interfere with exceptions."""
    ex_to_raise = RuntimeError('let me through')

    with pytest.raises(RuntimeError) as err:
        with Skippable:
            raise ex_to_raise

    assert err.value is ex_to_raise


@pytest.mark.parametrize("error_action", (ErrorAction.IGNORE, ErrorAction.WARNING, ErrorAction.ERROR))
def test_skip_on_ignore_missing_skippable(error_action: ErrorAction) -> None:
    """Verify that a `_SkipException` is raised when `skip_on_ignore=True` and no `Skippable` context was used to suppress it."""
    body_ran = False
    assert not body_ran  # satisfy static analysis which assumes the context manager body will run

    with pytest.raises(_SkipException):
        with ErrorHandler(error_action).handle(Exception, skip_on_ignore=True):
            body_ran = True

    if error_action is ErrorAction.IGNORE:
        assert not body_ran
    else:
        assert body_ran


@pytest.mark.parametrize("exception_type", (RuntimeError, NotImplementedError))
def test_ignore_success(exception_type: type[Exception]) -> None:
    """Verify that `ErrorAction.IGNORE` suppresses the specified exception types."""
    body_ran = False
    assert not body_ran  # satisfy static analysis which assumes the context manager body will run

    with ErrorHandler(ErrorAction.IGNORE).handle(RuntimeError, NotImplementedError):
        body_ran = True
        raise exception_type('should be ignored')

    assert body_ran


def test_ignore_passes_other_exceptions() -> None:
    """Verify that `ErrorAction.IGNORE` does not suppress exception types not passed to `handle`."""
    with pytest.raises(NotImplementedError):
        with ErrorHandler(ErrorAction.IGNORE).handle(TypeError, ValueError):
            raise NotImplementedError()


@pytest.mark.parametrize("exception_type", (RuntimeError, NotImplementedError))
def test_warn_success(exception_type: type[Exception], mocker: pytest_mock.MockerFixture) -> None:
    """Verify that `ErrorAction.WARNING` eats the specified error type and calls `error_as_warning` with the exception instance raised."""
    eaw = mocker.patch.object(Display(), 'error_as_warning')
    with ErrorHandler(ErrorAction.WARNING).handle(RuntimeError, NotImplementedError):
        raise exception_type()

    assert isinstance(eaw.call_args.kwargs['exception'], exception_type)


def test_warn_passes_other_exceptions(mocker: pytest_mock.MockerFixture) -> None:
    """Verify that `ErrorAction.WARNING` does not suppress exception types not passed to `handle`, and that `error_as_warning` is not called for them."""
    eaw = mocker.patch.object(Display(), 'error_as_warning')

    with pytest.raises(NotImplementedError):
        with ErrorHandler(ErrorAction.WARNING).handle(TypeError, ValueError):
            raise NotImplementedError()

    assert not eaw.called


@pytest.mark.parametrize("exception_type", (AttributeError, NotImplementedError, ValueError))
def test_fail(exception_type: type[Exception]) -> None:
    """Verify that `ErrorAction.ERROR` passes through all exception types, regardless of what was passed to `handle`."""
    with pytest.raises(exception_type):
        with ErrorHandler(ErrorAction.ERROR).handle(AttributeError, NotImplementedError):
            raise exception_type()


def test_no_exceptions_to_handle():
    """Verify that passing no exceptions to `handle` fails."""
    with pytest.raises(ValueError):
        with ErrorHandler(ErrorAction.IGNORE).handle():
            pass


@pytest.mark.parametrize("value", ('ignore', 'warning', 'error'))
def test_from_config_env_success(value: str, mocker: pytest_mock.MockerFixture) -> None:
    """Verify that `from_config` correctly creates handlers with the requested error action config string."""
    mocker.patch.dict(os.environ, dict(_ANSIBLE_CALLBACK_DISPATCH_ERROR_BEHAVIOR=value))

    assert config.get_config_value("_CALLBACK_DISPATCH_ERROR_BEHAVIOR") == value
    eh = ErrorHandler.from_config("_CALLBACK_DISPATCH_ERROR_BEHAVIOR")
    assert eh.action == ErrorAction[value.upper()]


def test_from_config_fail() -> None:
    """Verify that `from_config` fails on an invalid config entry name."""
    with pytest.raises(AnsibleUndefinedConfigEntry):
        ErrorHandler.from_config("invalid")
