"""Packaging compatibility."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

try:
    from packaging.specifiers import SpecifierSet
    from packaging.version import Version
    PACKAGING_IMPORT_ERROR = None
except ImportError as ex:
    SpecifierSet = None
    Version = None
    PACKAGING_IMPORT_ERROR = ex
