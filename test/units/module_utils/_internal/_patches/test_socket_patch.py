from __future__ import annotations

import socket

from ansible.module_utils._internal._datatag._tags import Deprecated


def test_getaddrinfo() -> None:
    """Verify that `socket.getaddrinfo` works with a tagged port."""
    # DTFIX5: add additional args and validate output shape (ensure passthru is working)
    socket.getaddrinfo('localhost', Deprecated(msg='').tag(22))
