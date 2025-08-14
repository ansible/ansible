# -*- coding: utf-8 -*-
# Copyright: (c) 2020-2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""A facade for interfacing with multiple Galaxy instances."""

from __future__ import annotations

import functools
import typing as t
from dataclasses import dataclass

if t.TYPE_CHECKING:
    from ansible.galaxy.api import CollectionVersionMetadata
    from ansible.galaxy.collection.concrete_artifact_manager import (
        ConcreteArtifactsManager,
    )
    from ansible.galaxy.dependency_resolution.dataclasses import (
        Candidate, Requirement,
    )

from ansible.errors import AnsibleError
from ansible.galaxy.api import GalaxyAPI, GalaxyError
from ansible.module_utils.common.text.converters import to_text
from ansible.utils.display import Display


display = Display()


@dataclass(slots=True, frozen=True)
class ProxyResponse[T]:
    """Wrapper for proxy responses that includes both data and the API that succeeded."""
    data: T
    api: GalaxyAPI | None


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

    def _get_api_lookup_order(self, src: t.Union[GalaxyAPI, t.Any]) -> tuple[GalaxyAPI, ...]:
        """Get the API lookup order for a given source."""
        return (
            (src, )
            if isinstance(src, GalaxyAPI)
            else tuple(self._apis)
        )

    def _try_apis[T](
        self,
        src: t.Union[GalaxyAPI, t.Any],
        collection_identifier: str,
        api_callback: t.Callable[[GalaxyAPI], T],
        operation_description: str = "operation"
    ) -> ProxyResponse[T]:
        """Try multiple APIs and return the first successful result."""
        last_err: t.Optional[Exception] = None

        for api in self._get_api_lookup_order(src):
            try:
                result = api_callback(api)
                return ProxyResponse(result, api)
            except GalaxyError as api_err:
                last_err = api_err
            except Exception as unknown_err:
                last_err = unknown_err
                display.warning(
                    "Skipping Galaxy server {server!s}. "
                    "Got an unexpected error when {operation} "
                    "for collection {collection}: {err!s}".
                    format(
                        server=api.api_server,
                        operation=operation_description,
                        collection=collection_identifier,
                        err=to_text(unknown_err),
                    )
                )

        if last_err is not None:
            raise last_err
        else:
            raise AnsibleError(f"No APIs available for {operation_description} on {collection_identifier}")

    def _get_collection_versions(self, requirement: Requirement) -> t.Iterator[tuple[GalaxyAPI, str]]:
        """Helper for get_collection_versions.

        Yield api, version pairs for all APIs,
        and reraise the last error if no valid API was found.
        """
        if self._offline:
            return

        found_api = False
        last_error: Exception | None = None

        for api in self._get_api_lookup_order(requirement.src):
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

    @functools.lru_cache(maxsize=128)
    def get_collection_versions(self, requirement: Requirement) -> t.Iterable[ProxyResponse[str]]:
        """Get a set of unique versions for FQCN on Galaxy servers."""
        if requirement.is_concrete_artifact:
            version = self._concrete_art_mgr.get_direct_collection_version(requirement)
            return {
                ProxyResponse(version, requirement.src)
            }

        return set(
            ProxyResponse(version, api)
            for api, version in self._get_collection_versions(
                requirement,
            )
        )

    @functools.lru_cache(maxsize=128)
    def get_collection_metadata(self, requirement: Requirement) -> ProxyResponse[dict]:
        """Retrieve general collection metadata."""
        self._assert_that_offline_mode_is_not_requested()

        return self._try_apis(
            requirement.src,
            requirement.fqcn,
            lambda api: api.get_collection_metadata(requirement.namespace, requirement.name),
            "getting collection metadata"
        )

    @functools.lru_cache(maxsize=128)
    def get_collection_version_metadata(self, collection_candidate: Candidate) -> ProxyResponse[CollectionVersionMetadata]:
        """Retrieve collection metadata of a given candidate."""
        self._assert_that_offline_mode_is_not_requested()

        def get_and_save_metadata(api):
            version_metadata = api.get_collection_version_metadata(
                collection_candidate.namespace,
                collection_candidate.name,
                collection_candidate.ver,
            )
            self._concrete_art_mgr.save_collection_source(
                collection_candidate,
                version_metadata.download_url,
                version_metadata.artifact_sha256,
                api.token,
                version_metadata.signatures_url,
                version_metadata.signatures,
            )
            return version_metadata

        return self._try_apis(
            collection_candidate.src,
            collection_candidate.fqcn,
            get_and_save_metadata,
            "getting collection version metadata"
        )

    @functools.lru_cache(maxsize=128)
    def get_collection_dependencies(self, collection_candidate: Candidate) -> ProxyResponse[dict[str, str]]:
        # FIXME: return Requirement instances instead?
        """Retrieve collection dependencies of a given candidate."""
        if collection_candidate.is_concrete_artifact:
            dependencies = (
                self.
                _concrete_art_mgr.
                get_direct_collection_dependencies
            )(collection_candidate)
            return ProxyResponse(dependencies, collection_candidate.src)

        response = self.get_collection_version_metadata(collection_candidate)
        return ProxyResponse(response.data.dependencies, response.api)

    @functools.lru_cache(maxsize=128)
    def get_signatures(self, collection_candidate: Candidate) -> ProxyResponse[list[str]]:
        self._assert_that_offline_mode_is_not_requested()

        try:
            response = self._try_apis(
                collection_candidate.src,
                collection_candidate.fqcn,
                lambda api: api.get_collection_signatures(
                    collection_candidate.namespace,
                    collection_candidate.name,
                    collection_candidate.ver
                ),
                "getting collection signatures"
            )
            return response
        except Exception:
            return ProxyResponse([], None)
