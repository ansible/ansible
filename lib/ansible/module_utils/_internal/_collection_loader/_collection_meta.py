# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# CAUTION: This implementation of the collection loader is used by ansible-test.
#          Because of this, it must be compatible with all Python versions supported on the controller or remote.

from __future__ import annotations

import json
import os
import pathlib

from collections.abc import Mapping

MANIFEST_FILENAME = 'MANIFEST.json'
GALAXY_YML_FILENAME = 'galaxy.yml'


class CollectionMetadataError(ValueError):
    """A collection metadata file is present but could not be read as valid data."""


class CollectionMetadataNotMapping(CollectionMetadataError):
    """A collection metadata file parsed successfully but is not a mapping."""


def _meta_yml_to_dict(yaml_string_data: bytes | str, content_id):
    """
    Converts string YAML dictionary to a Python dictionary. This function may be monkeypatched to another implementation
    by some tools (eg the import sanity test).
    :param yaml_string_data: a bytes-ish YAML dictionary
    :param content_id: a unique ID representing the content to allow other implementations to cache the output
    :return: a Python dictionary representing the YAML dictionary content
    """
    # NB: content_id is passed in, but not used by this implementation

    # Import the `yaml` module only when needed, as it is not available for the module/module_utils import sanity tests.
    # This also avoids use of shared YAML infrastructure to eliminate any Ansible dependencies outside the collection loader itself.
    import yaml

    try:
        from yaml import CBaseLoader as BaseLoader
    except (ImportError, AttributeError):
        from yaml import BaseLoader  # type: ignore[assignment]

    # Using BaseLoader ensures that all scalars are strings.
    # Doing so avoids parsing unquoted versions as floats, dates as datetime.date, etc.
    routing_dict = yaml.load(yaml_string_data, Loader=BaseLoader)
    if not routing_dict:
        routing_dict = {}
    if not isinstance(routing_dict, Mapping):
        raise ValueError('collection metadata must be an instance of Python Mapping')
    return routing_dict


def _read_manifest_json(collection_path: str | os.PathLike) -> dict | None:
    """Read ``collection_info`` from an installed collection's ``MANIFEST.json``.

    :param collection_path: path to the collection directory
    :return: the raw ``collection_info`` mapping, or ``None`` when no
        ``MANIFEST.json`` is present
    :raises CollectionMetadataError: when ``MANIFEST.json`` exists but is not
        valid JSON, or does not contain a ``collection_info`` mapping
        (``CollectionMetadataNotMapping`` when the top-level JSON is not an
        object)
    """
    manifest_path = pathlib.Path(collection_path) / MANIFEST_FILENAME

    try:
        raw = manifest_path.read_text(encoding='utf-8', errors='surrogateescape')
    except (FileNotFoundError, NotADirectoryError):
        return None

    try:
        manifest = json.loads(raw)
    except ValueError as ex:
        raise CollectionMetadataError(f'{manifest_path} does not contain valid JSON: {ex}') from ex

    if not isinstance(manifest, dict):
        raise CollectionMetadataNotMapping(f'{manifest_path} must contain a JSON object')

    collection_info = manifest.get('collection_info')
    if not isinstance(collection_info, dict):
        raise CollectionMetadataError(f'{manifest_path} is missing a valid collection_info mapping')

    return collection_info


def _read_galaxy_yml(collection_path: str | os.PathLike) -> dict | None:
    """Read a source collection's ``galaxy.yml`` build metadata.

    :param collection_path: path to the collection directory
    :return: the raw parsed ``galaxy.yml`` mapping, or ``None`` when no
        ``galaxy.yml`` is present
    :raises CollectionMetadataError: when ``galaxy.yml`` exists but is not valid
        YAML (``CollectionMetadataNotMapping`` when it parses to a non-mapping)
    """
    # Import the `yaml` module only when needed, consistent with _meta_yml_to_dict,
    # to keep the collection loader usable where yaml is unavailable.
    import yaml

    galaxy_yml_path = pathlib.Path(collection_path) / GALAXY_YML_FILENAME

    try:
        raw = galaxy_yml_path.read_text(encoding='utf-8', errors='surrogateescape')
    except (FileNotFoundError, NotADirectoryError):
        return None

    try:
        manifest = yaml.safe_load(raw)
    except yaml.error.YAMLError as ex:
        raise CollectionMetadataError(f'{galaxy_yml_path} does not contain valid YAML: {ex}') from ex

    if not isinstance(manifest, dict):
        raise CollectionMetadataNotMapping(f'{galaxy_yml_path} must contain a YAML mapping')

    return manifest


def _read_collection_manifest(collection_path: str | os.PathLike) -> dict | None:
    """Read raw collection manifest from an installed or source collection directory.

    Prefers an installed collection's ``MANIFEST.json`` (returning its
    ``collection_info``) and falls back to a source collection's ``galaxy.yml``.

    :param collection_path: path to the collection directory
    :return: the raw metadata mapping, or ``None`` when neither file is present
    :raises ValueError: when a present metadata file is malformed
    """
    manifest = _read_manifest_json(collection_path)
    if manifest is not None:
        return manifest

    return _read_galaxy_yml(collection_path)
