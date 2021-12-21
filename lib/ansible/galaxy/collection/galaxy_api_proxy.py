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
    from typing import Dict, Iterable, Iterator, Tuple
    from ansible.galaxy.api import CollectionVersionMetadata
    from ansible.galaxy.collection.concrete_artifact_manager import (
        ConcreteArtifactsManager,
    )
    from ansible.galaxy.dependency_resolution.dataclasses import (
        Candidate, Requirement,
    )

from ansible.errors import AnsibleError
from ansible.galaxy.api import GalaxyAPI, GalaxyError
from ansible.module_utils._text import to_text
from ansible.module_utils.six import string_types
from ansible.utils.display import Display
from ansible.utils.version import SemanticVersion


display = Display()


class MultiGalaxyAPIProxy:
    """A proxy that abstracts talking to multiple Galaxy instances."""

    def __init__(self, apis, concrete_artifacts_manager):
        # type: (Iterable[GalaxyAPI], ConcreteArtifactsManager) -> None
        """Initialize the target APIs list."""
        self._apis = apis
        self._concrete_art_mgr = concrete_artifacts_manager

    def _get_collection_versions(self, requirement):
        # type: (Requirement) -> Iterator[Tuple[GalaxyAPI, str]]
        """Helper for get_collection_versions.

        Yield api, version pairs for all APIs,
        and reraise the last error if no valid API was found.
        """
        found_api = False
        last_error = None

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

    def get_collection_versions(self, requirement):
        # type: (Requirement) -> Iterable[Tuple[str, GalaxyAPI]]
        """Get a set of unique versions for FQCN on Galaxy servers."""
        if requirement.is_concrete_artifact:
            version = self._concrete_art_mgr.get_direct_collection_version(requirement)

            err = f"Invalid version found for requirement '{requirement}': {version} ({type(version)}). "
            err += "The version should be a semantic version string (or '*')."
            # NOTE: The known cases causing the version to be a non-string object come from
            # NOTE: the differences in how the YAML parser normalizes ambiguous values and
            # NOTE: how the end-users sometimes expect them to be parsed. Unless the users
            # NOTE: explicitly use the double quotes of one of the multiline string syntaxes
            # NOTE: in the collection metadata file, PyYAML will parse a value containing
            # NOTE: two dot-separated integers as `float`, a single integer as `int`, and 3+
            # NOTE: integers as a `str`. In some cases, they may also use an empty value
            # NOTE: which is normalized as `null` and turned into `None` in the Python-land.
            # NOTE: Another known mistake is setting a minor part of the SemVer notation
            # NOTE: skipping the "patch" bit like "1.0" which is assumed non-compliant even
            # NOTE: after the conversion to string.
            if not isinstance(version, string_types):
                raise AnsibleError(err)
            elif version != "*":
                try:
                    SemanticVersion(version)
                except ValueError as ex:
                    raise AnsibleError(err) from ex

            return {(version, requirement.src)}

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
