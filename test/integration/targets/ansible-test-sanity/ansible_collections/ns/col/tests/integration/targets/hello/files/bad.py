from __future__ import annotations

import tempfile

try:
    import ansible.module_utils.six  # intentionally trigger pylint ansible-bad-import error  # pylint: disable=unused-import
except ImportError:
    pass

try:
    from ansible.module_utils.six import PY3  # intentionally trigger pylint ansible-bad-import-from error  # pylint: disable=unused-import
except ImportError:
    pass

tempfile.mktemp()  # intentionally trigger pylint ansible-bad-function error
