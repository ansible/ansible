# -*- coding: utf-8 -*-
# Copyright: (c) 2020-2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Dependency resolution machinery."""

from __future__ import annotations

import collections.abc as _c
import typing as t

if t.TYPE_CHECKING:
    from ansible.galaxy.api import GalaxyAPI
    from ansible.galaxy.collection.concrete_artifact_manager import (
        ConcreteArtifactsManager,
    )
    from ansible.galaxy.dependency_resolution.dataclasses import Candidate

from ansible.galaxy.collection.galaxy_api_proxy import MultiGalaxyAPIProxy
from ansible.galaxy.dependency_resolution.providers import CollectionDependencyProvider
from ansible.galaxy.dependency_resolution.reporters import CollectionDependencyReporter
from ansible.galaxy.dependency_resolution.resolvers import CollectionDependencyResolver


def build_collection_dependency_resolver(
        galaxy_apis: _c.Iterable[GalaxyAPI],
        concrete_artifacts_manager: ConcreteArtifactsManager,
        preferred_candidates: _c.Iterable[Candidate] | None = None,
        with_deps: bool = True,
        with_pre_releases: bool = False,
        upgrade: bool = False,
        include_signatures: bool = True,
        offline: bool = False,
) -> CollectionDependencyResolver:
    """Return a collection dependency resolver.

    The returned instance will have a ``resolve()`` method for
    further consumption.
    """
    return CollectionDependencyResolver(
        CollectionDependencyProvider(
            apis=MultiGalaxyAPIProxy(galaxy_apis, concrete_artifacts_manager, offline=offline),
            concrete_artifacts_manager=concrete_artifacts_manager,
            preferred_candidates=preferred_candidates,
            with_deps=with_deps,
            with_pre_releases=with_pre_releases,
            upgrade=upgrade,
            include_signatures=include_signatures,
        ),
        CollectionDependencyReporter(),
    )
