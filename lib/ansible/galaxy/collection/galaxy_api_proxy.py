# -*- coding: utf-8 -*-
# Copyright: (c) 2020-2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""A facade for interfacing with multiple Galaxy instances."""

from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:
    from ansible.galaxy.api import CollectionVersionMetadata
    from ansible.galaxy.collection.concrete_artifact_manager import (
        ConcreteArtifactsManager,
    )
    from ansible.galaxy.dependency_resolution.dataclasses import (
        Candidate, Requirement,
    )

from ansible.galaxy.api import GalaxyAPI, GalaxyError
from ansible.module_utils.common.text.converters import to_text
from ansible.utils.display import Display


display = Display()


class MultiGalaxyAPIProxy:
    """A proxy that abstracts talking to multiple Galaxy instances."""

    def __init__(self, apis: t.Iterable[GalaxyAPI], concrete_artifacts_manager: ConcreteArtifactsManager, offline: bool = False) -> None:
        """Initialize the target APIs list."""
        self._apis = apis
        self._concrete_art_mgr = concrete_artifacts_manager
        self._offline = offline  # Prevent all GalaxyAPI calls

    @property
    def is_offline_mode_requested(self):
        return self._offline

    def _assert_that_offline_mode_is_not_requested(self) -> None:
        if self.is_offline_mode_requested:
            raise NotImplementedError("The calling code is not supposed to be invoked in 'offline' mode.")

    def _get_collection_versions(self, requirement: Requirement) -> t.Iterator[tuple[GalaxyAPI, str]]:
        """Helper for get_collection_versions.

        Yield api, version pairs for all APIs,
        and reraise the last error if no valid API was found.
        """
        if self._offline:
            return

        found_api = False
        last_error: Exception | None = None

        api_lookup_order = (
            (requirement.src, )
            if isinstance(requirement.src, GalaxyAPI)
            else self._apis
        )

        for api in api_lookup_order:
            try:
                versions = api.get_collection_versions(requirement.namespace, requirement.name)
            except GalaxyError as api_err:
                last_error = api_err
            except Exception as unknown_err:
                display.warning(
                    "Skipping Galaxy server {server!s}. "
                    "Got an unexpected error when getting "
                    "available versions of collection {fqcn!s}: {err!s}".
                    format(
                        server=api.api_server,
                        fqcn=requirement.fqcn,
                        err=to_text(unknown_err),
                    )
                )
                last_error = unknown_err
            else:
                found_api = True
                for version in versions:
                    yield api, version

        if not found_api and last_error is not None:
            raise last_error

    def get_collection_versions(self, requirement: Requirement) -> t.Iterable[tuple[str, GalaxyAPI]]:
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
            for api, version in self._get_collection_versions(
                requirement,
            )
        )

    def get_collection_version_metadata(self, collection_candidate: Candidate) -> CollectionVersionMetadata:
        """Retrieve collection metadata of a given candidate."""
        self._assert_that_offline_mode_is_not_requested()

        api_lookup_order = (
            (collection_candidate.src, )
            if isinstance(collection_candidate.src, GalaxyAPI)
            else self._apis
        )

        last_err: t.Optional[Exception]

        for api in api_lookup_order:
            try:
                version_metadata = api.get_collection_version_metadata(
                    collection_candidate.namespace,
                    collection_candidate.name,
                    collection_candidate.ver,
                )
            except GalaxyError as api_err:
                last_err = api_err
            except Exception as unknown_err:
                # `verify` doesn't use `get_collection_versions` since the version is already known.
                # Do the same as `install` and `download` by trying all APIs before failing.
                # Warn for debugging purposes, since the Galaxy server may be unexpectedly down.
                last_err = unknown_err
                display.warning(
                    "Skipping Galaxy server {server!s}. "
                    "Got an unexpected error when getting "
                    "available versions of collection {fqcn!s}: {err!s}".
                    format(
                        server=api.api_server,
                        fqcn=collection_candidate.fqcn,
                        err=to_text(unknown_err),
                    )
                )
            else:
                self._concrete_art_mgr.save_collection_source(
                    collection_candidate,
                    version_metadata.download_url,
                    version_metadata.artifact_sha256,
                    api.token,
                    version_metadata.signatures_url,
                    version_metadata.signatures,
                )
                return version_metadata

        raise last_err

    def get_collection_dependencies(self, collection_candidate: Candidate) -> dict[str, str]:
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

    def get_signatures(self, collection_candidate: Candidate) -> list[str]:
        self._assert_that_offline_mode_is_not_requested()
        namespace = collection_candidate.namespace
        name = collection_candidate.name
        version = collection_candidate.ver
        last_err: Exception | None = None

        api_lookup_order = (
            (collection_candidate.src, )
            if isinstance(collection_candidate.src, GalaxyAPI)
            else self._apis
        )

        for api in api_lookup_order:
            try:
                return api.get_collection_signatures(namespace, name, version)
            except GalaxyError as api_err:
                last_err = api_err
            except Exception as unknown_err:
                # Warn for debugging purposes, since the Galaxy server may be unexpectedly down.
                last_err = unknown_err
                display.warning(
                    "Skipping Galaxy server {server!s}. "
                    "Got an unexpected error when getting "
                    "available versions of collection {fqcn!s}: {err!s}".
                    format(
                        server=api.api_server,
                        fqcn=collection_candidate.fqcn,
                        err=to_text(unknown_err),
                    )
                )
        if last_err:
            raise last_err

        return []
