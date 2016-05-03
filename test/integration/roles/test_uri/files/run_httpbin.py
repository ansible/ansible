#!/usr/bin/python
"""helper script to run httpbin with a specified port and hostname."""

# As of httpbin 0.4.1, http.core doesn't support port options on the cli
# although it was added to upstream git master.
import sys
import optparse

import httpbin
import httpbin.core

def main(args=None):
    args = args or []
    parser = optparse.OptionParser()
    parser.add_option("--port", default=22222)
    parser.add_option("--host", default="localhost")
    options, args = parser.parse_args(args)
    return httpbin.core.app.run(port=options.port,
                                host=options.host)


if __name__ == "__main__":
    rc = main(sys.argv[:])
    sys.exit(rc)
