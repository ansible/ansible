from __future__ import annotations

import typing as t

import pytest

from ansible._internal import _rpc_host


@pytest.fixture(autouse=True)
def reset_server_ready() -> t.Iterator[None]:
    _rpc_host._server_ready.clear()
    yield
    _rpc_host._server_ready.clear()


def test_local_process_start_reraises_server_startup_exception() -> None:
    expected = PermissionError("AF_UNIX sockets are blocked")

    def fail_to_start() -> None:
        raise expected

    process = _rpc_host.LocalNotAProcess(target=fail_to_start, args=())

    with pytest.raises(PermissionError, match="AF_UNIX sockets are blocked") as error:
        process.start()

    assert error.value is expected


def test_local_process_start_rejects_server_exit_before_ready() -> None:
    process = _rpc_host.LocalNotAProcess(target=lambda: None, args=())

    with pytest.raises(RuntimeError, match="stopped during startup"):
        process.start()
