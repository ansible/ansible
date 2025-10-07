# -*- coding: utf-8 -*-
# Copyright: (c) 2020-2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Dependency resolution exceptions."""

from __future__ import annotations

try:
    from resolvelib.resolvers import (  # pylint: disable=unused-import
        ResolverException as CollectionDependencyResolverRuntimeError,
        RequirementsConflicted as CollectionDependencyRequirementsConflicted,
        InconsistentCandidate as CollectionDependencyInconsistentCandidate,
        ResolutionError as CollectionDependencyResolutionError,
        ResolutionImpossible as CollectionDependencyResolutionImpossible,
        ResolutionTooDeep as CollectionDependencyResolutionTooDeep,
    )
except ImportError:
    class CollectionDependencyResolverRuntimeError(Exception):  # type: ignore[no-redef]
        """A resolvelib base exception.

        This exception is intended to be handled within resolvelib itself. If
        it leaks into our runtime, a bug must be filed against resolvelib.
        """

    class CollectionDependencyRequirementsConflicted(CollectionDependencyResolverRuntimeError):  # type: ignore[no-redef]
        """Supplied requirements have no candidates satisfying all.

        Happens when ``find_matches()`` returns empty candidate list.
        It seems to be always handled by resolvelib internally.
        """

    class CollectionDependencyInconsistentCandidate(CollectionDependencyResolverRuntimeError):  # type: ignore[no-redef]
        """Signal that package index returned non-matching candidate.

        This generally happens with an index is broken.
        """

    class CollectionDependencyResolutionError(CollectionDependencyResolverRuntimeError):  # type: ignore[no-redef]
        """Base exception for unsuccessful resolution."""

    class CollectionDependencyResolutionImpossible(CollectionDependencyResolutionError):  # type: ignore[no-redef]
        """Dependency has with no fully compatible candidate combos.

        This happens when the dependency resolver determines that it will never
        find a combination of collection candidates that would satisfy all the
        requirements and compatibility constraint across each other. Every
        possibility is exhausted.
        """

    class CollectionDependencyResolutionTooDeep(CollectionDependencyResolutionError):  # type: ignore[no-redef]
        """Resolution didn't complete on time.

        This happens when the dependency resolver's gone through the maximum
        number of iterations and did not manage to complete its job by then.
        """
