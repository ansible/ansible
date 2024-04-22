from __future__ import annotations

from proxy.http.proxy import HttpProxyBasePlugin


class HamSandwichPlugin(HttpProxyBasePlugin):

    def handle_upstream_chunk(self, chunk):
        headers, sep, body = chunk.tobytes().partition(b'\r\n\r\n')
        if not sep:
            return chunk
        return memoryview(bytearray(headers + b'\r\nX-Sandwich: ham' + sep + body))
