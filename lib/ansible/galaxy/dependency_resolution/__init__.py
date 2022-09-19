# -*- coding: utf-8 -*-
# Copyright: (c) 2020-2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Dependency resolution machinery."""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import typing as t

if t.TYPE_CHECKING:
    from ansible.galaxy.api import GalaxyAPI
    from ansible.galaxy.collection.concrete_artifact_manager import (
        ConcreteArtifactsManager,
    )
    from ansible.galaxy.dependency_resolution.dataclasses import (
        Candidate,
        Requirement,
    )

from ansible.galaxy.collection.galaxy_api_proxy import MultiGalaxyAPIProxy
from ansible.galaxy.dependency_resolution.providers import CollectionDependencyProvider
from ansible.galaxy.dependency_resolution.reporters import CollectionDependencyReporter
from ansible.galaxy.dependency_resolution.resolvers import CollectionDependencyResolver


def build_collection_dependency_resolver(
        galaxy_apis,  # type: t.Iterable[GalaxyAPI]
        concrete_artifacts_manager,  # type: ConcreteArtifactsManager
        user_requirements,  # type: t.Iterable[Requirement]
        preferred_candidates=None,  # type: t.Iterable[Candidate]
        with_deps=True,  # type: bool
        with_pre_releases=False,  # type: bool
        upgrade=False,  # type: bool
        include_signatures=True,  # type: bool
        offline=False,  # type: bool
):  # type: (...) -> CollectionDependencyResolver
    """Return a collection dependency resolver.

    The returned instance will have a ``resolve()`` method for
    further consumption.
    """
    return CollectionDependencyResolver(
        CollectionDependencyProvider(
            apis=MultiGalaxyAPIProxy(galaxy_apis, concrete_artifacts_manager, offline=offline),
            concrete_artifacts_manager=concrete_artifacts_manager,
            user_requirements=user_requirements,
            preferred_candidates=preferred_candidates,
            with_deps=with_deps,
            with_pre_releases=with_pre_releases,
            upgrade=upgrade,
            include_signatures=include_signatures,
        ),
        CollectionDependencyReporter(),
    )
