"""Block the sphinx module from being loaded."""

from __future__ import annotations

raise ImportError('The sphinx module has been prevented from loading to maintain consistent test results.')
