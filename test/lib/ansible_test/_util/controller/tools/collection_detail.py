"""Retrieve collection detail."""

from __future__ import annotations

import json
import os
import re
import sys

import yaml


# See semantic versioning specification (https://semver.org/)
NUMERIC_IDENTIFIER = r'(?:0|[1-9][0-9]*)'
ALPHANUMERIC_IDENTIFIER = r'(?:[0-9]*[a-zA-Z-][a-zA-Z0-9-]*)'

PRE_RELEASE_IDENTIFIER = r'(?:' + NUMERIC_IDENTIFIER + r'|' + ALPHANUMERIC_IDENTIFIER + r')'
BUILD_IDENTIFIER = r'[a-zA-Z0-9-]+'  # equivalent to r'(?:[0-9]+|' + ALPHANUMERIC_IDENTIFIER + r')'

VERSION_CORE = NUMERIC_IDENTIFIER + r'\.' + NUMERIC_IDENTIFIER + r'\.' + NUMERIC_IDENTIFIER
PRE_RELEASE = r'(?:-' + PRE_RELEASE_IDENTIFIER + r'(?:\.' + PRE_RELEASE_IDENTIFIER + r')*)?'
BUILD = r'(?:\+' + BUILD_IDENTIFIER + r'(?:\.' + BUILD_IDENTIFIER + r')*)?'

SEMVER_REGULAR_EXPRESSION = r'^' + VERSION_CORE + PRE_RELEASE + BUILD + r'$'


def validate_version(version):
    """Raise exception if the provided version is not None or a valid semantic version."""
    if version is None:
        return
    if not re.match(SEMVER_REGULAR_EXPRESSION, version):
        raise Exception('Invalid version number "{0}". Collection version numbers must '
                        'follow semantic versioning (https://semver.org/).'.format(version))


def read_manifest_json(collection_path):
    """Return collection information from the MANIFEST.json file."""
    manifest_path = os.path.join(collection_path, 'MANIFEST.json')

    if not os.path.exists(manifest_path):
        return None

    try:
        with open(manifest_path, encoding='utf-8') as manifest_file:
            manifest = json.load(manifest_file)

        collection_info = manifest.get('collection_info') or {}

        result = dict(
            version=collection_info.get('version'),
        )
        validate_version(result['version'])
    except Exception as ex:  # pylint: disable=broad-except
        raise Exception('{0}: {1}'.format(os.path.basename(manifest_path), ex)) from None

    return result


def read_galaxy_yml(collection_path):
    """Return collection information from the galaxy.yml file."""
    galaxy_path = os.path.join(collection_path, 'galaxy.yml')

    if not os.path.exists(galaxy_path):
        return None

    try:
        with open(galaxy_path, encoding='utf-8') as galaxy_file:
            galaxy = yaml.safe_load(galaxy_file)

        result = dict(
            version=galaxy.get('version'),
        )
        validate_version(result['version'])
    except Exception as ex:  # pylint: disable=broad-except
        raise Exception('{0}: {1}'.format(os.path.basename(galaxy_path), ex)) from None

    return result


def main():
    """Retrieve collection detail."""
    collection_path = sys.argv[1]

    try:
        result = read_manifest_json(collection_path) or read_galaxy_yml(collection_path) or {}
    except Exception as ex:  # pylint: disable=broad-except
        result = dict(
            error='{0}'.format(ex),
        )

    print(json.dumps(result))


if __name__ == '__main__':
    main()
