"""
Compatibility shim for mock imports in modules and module_utils.
This can be removed once support for Python 2.7 is dropped.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

try:
    from unittest.mock import (  # pylint: disable=unused-import
        call,
        patch,
        mock_open,
        MagicMock,
        Mock,
    )
except ImportError:
    from mock import (
        call,
        patch,
        mock_open,
        MagicMock,
        Mock,
    )
