from __future__ import annotations

from proxy.http.proxy import HttpProxyBasePlugin
from proxy.http.parser import HttpParser, httpParserStates


class HamSandwichPlugin(HttpProxyBasePlugin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser = None
        self.parsable = True

    def handle_upstream_chunk(self, chunk):
        if not self.parsable:
            return chunk

        if not self.parser:
            self.parser = HttpParser.response(chunk)
        else:
            self.parser.parse(chunk)

        if self.parser.state == httpParserStates.INITIALIZED:
            # This is likely TLS without interception
            self.parsable = False
            return chunk

        if not self.parser.is_complete:
            return None

        self.parser.add_header(b'X-Sandwich', b'ham')
        return memoryview(bytearray(self.parser.build_response()))
