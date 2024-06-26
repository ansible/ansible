from __future__ import annotations

import tempfile

try:
    import urllib2  # intentionally trigger pylint ansible-bad-import error  # pylint: disable=unused-import
except ImportError:
    urllib2 = None

try:
    from urllib2 import Request  # intentionally trigger pylint ansible-bad-import-from error  # pylint: disable=unused-import
except ImportError:
    Request = None

tempfile.mktemp()  # intentionally trigger pylint ansible-bad-function error
