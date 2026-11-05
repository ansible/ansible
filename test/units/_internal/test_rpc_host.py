from __future__ import annotations

import pytest

from ansible._internal import _rpc_host


def test_startup_failure_is_surfaced(monkeypatch: pytest.MonkeyPatch) -> None:
    """The underlying server startup error must be raised, not a generic timeout."""
    _rpc_host._server_ready.clear()

    def fail(*args, **kwargs):
        raise PermissionError(1, "Operation not permitted")

    monkeypatch.setattr(_rpc_host.LocalServer, '__init__', fail)

    with pytest.raises(RuntimeError, match="failed to start") as exc_info:
        _rpc_host.LocalManager().start()

    assert isinstance(exc_info.value.__cause__, PermissionError)
    _rpc_host._server_ready.clear()
