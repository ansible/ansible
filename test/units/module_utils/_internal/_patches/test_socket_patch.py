from __future__ import annotations

import socket

from ansible.module_utils._internal._datatag._tags import Deprecated
from ansible.module_utils._internal._patches._socket_patch import GetAddrInfoPatch


def test_getaddrinfo() -> None:
    """Verify that `socket.getaddrinfo` works with a tagged port."""
    # DTFIX5: add additional args and validate output shape (ensure passthru is working)
    socket.getaddrinfo('localhost', Deprecated(msg='').tag(22))


def test_is_patch_needed_when_idna_codec_missing(monkeypatch) -> None:
    """Missing idna codec must not make the probe raise or apply the patch."""
    def boom(*args, **kwargs):
        raise LookupError('unknown encoding: idna')

    monkeypatch.setattr(socket, 'getaddrinfo', boom)

    assert GetAddrInfoPatch.is_patch_needed() is False
    GetAddrInfoPatch.patch()
