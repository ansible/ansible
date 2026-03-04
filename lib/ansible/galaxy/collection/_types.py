# Copyright: (c) 2025, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""A collection of shared types for ``ansible.galaxy.collection``."""

from __future__ import annotations

import queue as _q
import typing as _t

import ansible.module_utils.compat.typing as _tc
from ansible.module_utils.common.sentinel import Sentinel as _Sentinel


DisplayQueueItemType: _t.TypeAlias = tuple[
    str,
    tuple[_t.Any, ...],
    dict[str, _t.Any],
]
DisplayQueueType: _t.TypeAlias = _q.Queue[DisplayQueueItemType]


class DisplayThreadProto(_t.Protocol):
    def __init__(self, display_queue: DisplayQueueType) -> None:
        ...

    def __getattr__(self, attr: str) -> _t.Callable:
        ...


# FIXME: Use `TypedDict` from `typing_extension` with `closed=True` once
# FIXME: it's fixed for subclasses.
# Ref: https://github.com/python/typing_extensions/issues/686
class ManifestMetadataType(_t.TypedDict, total=False):
    directives: _tc.ReadOnly[_t.Required[list[str]]]
    omit_default_directives: _tc.ReadOnly[bool]


class _CollectionInfoTypeBase(_t.TypedDict, total=False):
    namespace: _tc.ReadOnly[_t.Required[str]]
    name: _tc.ReadOnly[_t.Required[str]]
    # NOTE: `version: null` is only allowed for `galaxy.yml`
    # NOTE: and not `MANIFEST.json`. The use-case for it is collections
    # NOTE: that generate the version from Git before building a
    # NOTE: distributable tarball artifact.
    version: _tc.ReadOnly[_t.Required[str | None]]
    authors: _tc.ReadOnly[_t.Required[list[str]]]
    readme: _tc.ReadOnly[_t.Required[str]]
    tags: _tc.ReadOnly[list[str]]
    description: _tc.ReadOnly[str]
    license: _tc.ReadOnly[str]
    license_file: _tc.ReadOnly[str]
    dependencies: _tc.ReadOnly[dict[str, str]]
    repository: _tc.ReadOnly[str]
    documentation: _tc.ReadOnly[str]
    homepage: _tc.ReadOnly[str]
    issues: _tc.ReadOnly[str]


# FIXME: Use `TypedDict` from `typing_extension` with `closed=True` once
# FIXME: it's fixed for subclasses.
# Ref: https://github.com/python/typing_extensions/issues/686
class _CollectionInfoWithBuildIgnoreType(_CollectionInfoTypeBase):
    # `build_ignore` is mutually exclusive with `manifest`
    build_ignore: _tc.ReadOnly[list[str]]


# FIXME: Use `TypedDict` from `typing_extension` with `closed=True` once
# FIXME: it's fixed for subclasses.
# Ref: https://github.com/python/typing_extensions/issues/686
class _CollectionInfoWithManifestType(_CollectionInfoTypeBase):
    # `manifest` is mutually exclusive with `build_ignore`
    manifest: _tc.ReadOnly[ManifestMetadataType | _t.Type[_Sentinel]]


CollectionInfoType = (
    _CollectionInfoTypeBase
    | _CollectionInfoWithBuildIgnoreType
    | _CollectionInfoWithManifestType
)


class _FileManifestEntryType(_t.TypedDict):
    name: _tc.ReadOnly[str]
    ftype: _tc.ReadOnly[str]
    chksum_type: _tc.ReadOnly[str | None]
    chksum_sha256: _tc.ReadOnly[str | None]
    format: _tc.ReadOnly[int]


class CollectionManifestType(_t.TypedDict):
    collection_info: CollectionInfoType
    file_manifest_file: _FileManifestEntryType
    format: int


class FilesManifestType(_t.TypedDict):
    files: list[_FileManifestEntryType]
    format: int
