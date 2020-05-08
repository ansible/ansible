"""Retrieve collection detail."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import os
import sys

import yaml


def read_manifest_json(collection_path):
    """Return collection information from the MANIFEST.json file."""
    manifest_path = os.path.join(collection_path, 'MANIFEST.json')

    if not os.path.exists(manifest_path):
        return None

    try:
        with open(manifest_path) as manifest_file:
            manifest = json.load(manifest_file)

        collection_info = manifest.get('collection_info') or dict()

        result = dict(
            version=collection_info.get('version'),
        )
    except Exception as ex:  # pylint: disable=broad-except
        raise Exception('{0}: {1}'.format(os.path.basename(manifest_path), ex))

    return result


def read_galaxy_yml(collection_path):
    """Return collection information from the galaxy.yml file."""
    galaxy_path = os.path.join(collection_path, 'galaxy.yml')

    if not os.path.exists(galaxy_path):
        return None

    try:
        with open(galaxy_path) as galaxy_file:
            galaxy = yaml.safe_load(galaxy_file)

        result = dict(
            version=galaxy.get('version'),
        )
    except Exception as ex:  # pylint: disable=broad-except
        raise Exception('{0}: {1}'.format(os.path.basename(galaxy_path), ex))

    return result


def main():
    """Retrieve collection detail."""
    collection_path = sys.argv[1]

    try:
        result = read_manifest_json(collection_path) or read_galaxy_yml(collection_path)
        if result is None:
            result = dict()
    except Exception as ex:  # pylint: disable=broad-except
        result = dict(
            error='{0}'.format(ex),
        )

    print(json.dumps(result))


if __name__ == '__main__':
    main()
