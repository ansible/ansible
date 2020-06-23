from __future__ import absolute_import, division, print_function
__metaclass__ = type

import tempfile

try:
    import urllib2  # intentionally trigger pylint ansible-bad-import error
except ImportError:
    urllib2 = None

try:
    from collections import MappingView  # intentionally trigger pylint ansible-bad-import-from error
except ImportError:
    MappingView = None

tempfile.mktemp()  # intentionally trigger pylint ansible-bad-function error
