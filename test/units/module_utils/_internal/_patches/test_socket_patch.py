from __future__ import annotations

import socket

from ansible.module_utils.datatag.tags import Deprecated


def test_getaddrinfo() -> None:
    """Verify that `socket.getaddrinfo` works with a tagged port."""
    # DTFIX-MERGE: add additional args and validate output shape (ensure passthru is working)
    socket.getaddrinfo('localhost', Deprecated(msg='').tag(22))
