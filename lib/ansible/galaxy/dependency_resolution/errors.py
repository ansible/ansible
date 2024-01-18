# -*- coding: utf-8 -*-
# Copyright: (c) 2020-2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Dependency resolution exceptions."""

from __future__ import annotations

try:
    from resolvelib.resolvers import (  # pylint: disable=unused-import
        ResolutionImpossible as CollectionDependencyResolutionImpossible,
        InconsistentCandidate as CollectionDependencyInconsistentCandidate,
    )
except ImportError:
    class CollectionDependencyResolutionImpossible(Exception):  # type: ignore[no-redef]
        pass

    class CollectionDependencyInconsistentCandidate(Exception):  # type: ignore[no-redef]
        pass
