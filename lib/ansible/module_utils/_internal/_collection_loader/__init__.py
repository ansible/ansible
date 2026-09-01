# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# CAUTION: This implementation of the collection loader is used by ansible-test.
#          Because of this, it must be compatible with all Python versions supported on the controller or remote.

from __future__ import annotations

import collections.abc as _c
import os as _os
import pathlib as _pathlib
import typing as _t
import warnings as _warnings

# FIXME: decide what of this we want to actually be public/toplevel, put other stuff on a utility class?
from ._collection_config import AnsibleCollectionConfig
from ._collection_finder import AnsibleCollectionRef
from ._collection_finder import _AnsibleCollectionFinder, _find_collection_paths, _split_collection_filter
from ._collection_meta import _read_collection_manifest
from ._utils import _EncryptedStringProtocol, _to_bytes, _to_text

__all__ = ['install_finder', 'find_collection_paths', 'read_collection_manifest', 'resource_from_fqcr', 'AnsibleCollectionConfig', 'AnsibleCollectionRef']


def resource_from_fqcr(ref: str) -> str:
    """
    Return resource from a fully-qualified collection reference,
    or from a simple resource name.
    For fully-qualified collection references, this is equivalent to
    ``AnsibleCollectionRef.from_fqcr(ref).resource``.
    """
    ref = _t.cast(str, _to_text(ref, strict=True))
    return ref.split(u'.')[-1]


def install_finder(paths: list[str], scan_sys_paths: bool = False, internal_collections: list[str] | None = None) -> None:
    """Install the Ansible collection finder into the Python import system.

    This registers the meta path and path hook finders that make installed
    collections importable under the ``ansible_collections`` namespace, enabling
    collection discovery (for example via ``find_collection_paths``) and loading.
    It must be called once before collections are imported or discovered.

    Calling this more than once is a no-op: if a finder is already configured, a
    warning is emitted and the existing finder is left in place. (The warning is
    a Python ``warnings`` warning so it can be filtered out by the import sanity
    test.)
    """
    if AnsibleCollectionConfig.collection_finder:
        # this must be a Python warning so that it can be filtered out by the import sanity test
        _warnings.warn('AnsibleCollectionFinder has already been configured')
        return

    finder = _AnsibleCollectionFinder(paths, scan_sys_paths, internal_collections=internal_collections)
    finder._install()


def read_collection_manifest(collection_path: str | _os.PathLike) -> dict | None:
    """Read raw manifest for a collection located at ``collection_path``.

    Prefers an installed collection's ``MANIFEST.json`` (returning its
    ``collection_info``) and falls back to a source collection's ``galaxy.yml``.
    Paths are typically obtained from ``find_collection_paths``.
    """
    if not AnsibleCollectionConfig.collection_finder:
        _warnings.warn('AnsibleCollectionFinder has not been installed, ensure calling "install_finder"')

    return _read_collection_manifest(collection_path)


def find_collection_paths(
    paths: list[str | _os.PathLike] | None = None,
    coll_filter: list[str] | None = None,
    dedupe: bool = True,
) -> _c.Iterator[_pathlib.Path]:
    """Yield the on-disk paths of installed collections as ``pathlib.Path``.

    Collections are discovered from the installed ``ansible_collections``
    namespace (the collection finder must be installed; see ``install_finder``).
    """
    if not AnsibleCollectionConfig.collection_finder:
        _warnings.warn('AnsibleCollectionFinder has not been installed, ensure calling "install_finder"')

    namespace_filter, collection_filter = _split_collection_filter(coll_filter)
    yield from _find_collection_paths(
        paths,
        namespace_filter=namespace_filter,
        collection_filter=collection_filter,
        dedupe=dedupe,
    )
