"""Packaging compatibility."""
from __future__ import annotations

try:
    from packaging import (
        specifiers,
        version,
    )

    SpecifierSet = specifiers.SpecifierSet
    Version = version.Version
    PACKAGING_IMPORT_ERROR = None
except ImportError as ex:
    SpecifierSet = None  # pylint: disable=invalid-name
    Version = None  # pylint: disable=invalid-name
    PACKAGING_IMPORT_ERROR = ex
