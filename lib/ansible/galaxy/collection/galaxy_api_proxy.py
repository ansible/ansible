# -*- coding: utf-8 -*-
# Copyright: (c) 2020-2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""A facade for interfacing with multiple Galaxy instances."""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from typing import Dict, Iterable, Tuple
    from ansible.galaxy.api import CollectionVersionMetadata
    from ansible.galaxy.collection.concrete_artifact_manager import (
        ConcreteArtifactsManager,
    )
    from ansible.galaxy.dependency_resolution.dataclasses import (
        Candidate, Requirement,
    )

from ansible.galaxy.api import GalaxyAPI, GalaxyError


class MultiGalaxyAPIProxy:
    """A proxy that abstracts talking to multiple Galaxy instances."""

    def __init__(self, apis, concrete_artifacts_manager):
        # type: (Iterable[GalaxyAPI], ConcreteArtifactsManager) -> None
        """Initialize the target APIs list."""
        self._apis = apis
        self._concrete_art_mgr = concrete_artifacts_manager

    def get_collection_versions(self, requirement):
        # type: (Requirement) -> Iterable[Tuple[str, GalaxyAPI]]
        """Get a set of unique versions for FQCN on Galaxy servers."""
        if requirement.is_concrete_artifact:
            return {
                (
                    self._concrete_art_mgr.
                    get_direct_collection_version(requirement),
                    requirement.src,
                ),
            }

        api_lookup_order = (
            (requirement.src, )
            if isinstance(requirement.src, GalaxyAPI)
            else self._apis
        )
        return set(
            (version, api)
            for api in api_lookup_order
            for version in api.get_collection_versions(
                requirement.namespace, requirement.name,
            )
        )

    def get_collection_version_metadata(self, collection_candidate):
        # type: (Candidate) -> CollectionVersionMetadata
        """Retrieve collection metadata of a given candidate."""

        api_lookup_order = (
            (collection_candidate.src, )
            if isinstance(collection_candidate.src, GalaxyAPI)
            else self._apis
        )
        for api in api_lookup_order:
            try:
                version_metadata = api.get_collection_version_metadata(
                    collection_candidate.namespace,
                    collection_candidate.name,
                    collection_candidate.ver,
                )
            except GalaxyError as api_err:
                last_err = api_err
            else:
                self._concrete_art_mgr.save_collection_source(
                    collection_candidate,
                    version_metadata.download_url,
                    version_metadata.artifact_sha256,
                    api.token,
                )
                return version_metadata

        raise last_err

    def get_collection_dependencies(self, collection_candidate):
        # type: (Candidate) -> Dict[str, str]
        # FIXME: return Requirement instances instead?
        """Retrieve collection dependencies of a given candidate."""
        if collection_candidate.is_concrete_artifact:
            return (
                self.
                _concrete_art_mgr.
                get_direct_collection_dependencies
            )(collection_candidate)

        return (
            self.
            get_collection_version_metadata(collection_candidate).
            dependencies
        )
