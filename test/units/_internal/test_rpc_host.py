"""Unit tests for ansible._internal._rpc_host."""

from __future__ import annotations

import threading
from unittest import mock

import pytest

from ansible._internal import _rpc_host


@pytest.fixture(autouse=True)
def reset_shared_instance():
    """Reset the LocalManager singleton between tests."""
    _rpc_host.LocalManager._shared_instance = None
    _rpc_host._server_ready.clear()
    yield
    _rpc_host.LocalManager._shared_instance = None
    _rpc_host._server_ready.clear()


def test_local_not_a_process_surfaces_startup_exception():
    """Exceptions raised inside the server thread must propagate to the caller."""

    def failing_target(*args, **kwargs):
        raise PermissionError("[Errno 1] Operation not permitted")

    proc = _rpc_host.LocalNotAProcess(target=failing_target, args=())

    with pytest.raises(PermissionError, match="Operation not permitted"):
        proc.start()


def test_local_not_a_process_timeout_when_no_exception():
    """If the server never sets _server_ready and no exception occurs, raise TimeoutError."""

    def silent_target(*args, **kwargs):
        # Simulate a target that blocks forever without setting _server_ready
        threading.Event().wait()

    proc = _rpc_host.LocalNotAProcess(target=silent_target, args=())

    # Patch the wait timeout to make the test fast
    original_wait = _rpc_host._server_ready.wait
    try:
        _rpc_host._server_ready.wait = lambda timeout: False
        with pytest.raises(TimeoutError, match="Local RPC server did not start"):
            proc.start()
    finally:
        _rpc_host._server_ready.wait = original_wait


def test_shared_instance_surfaces_permission_error():
    """LocalManager.shared_instance() must surface PermissionError from socket binding."""

    # Mock the Server to raise PermissionError during initialization
    original_server = _rpc_host.LocalManager._Server

    def failing_server(*args, **kwargs):
        raise PermissionError("[Errno 1] Operation not permitted")

    with mock.patch.object(_rpc_host.LocalManager, "_Server", failing_server):
        with pytest.raises(PermissionError, match="Operation not permitted"):
            _rpc_host.LocalManager.shared_instance()
