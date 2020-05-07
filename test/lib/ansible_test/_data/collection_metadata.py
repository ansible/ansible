#!/usr/bin/env python
"""Retrieve some collection metadata."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import os
import sys

try:
    import yaml
except ImportError:
    yaml = None


def load_metadata(collection_path):
    """
    Retrieve some collection metadata.
    """
    result = dict(warnings=[])

    # Try reading MANIFEST.json first
    manifest_path = os.path.join(collection_path, 'MANIFEST.json')
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path) as manifest_file:
                manifest = json.load(manifest_file)
                collection_info = manifest.get('collection_info') or dict()
                result['version'] = collection_info.get('version')
        except IOError as exc:
            result['warnings'].append('Error while reading {0}: {1}'.format(manifest_path, exc))
        return result

    # Try reading galaxy.yml next
    galaxy_path = os.path.join(collection_path, 'galaxy.yml')
    if os.path.exists(galaxy_path):
        if yaml is None:
            result['no-pyyaml'] = True
        else:
            try:
                with open(galaxy_path) as galaxy_file:
                    galaxy = yaml.safe_load(galaxy_file)
                    result['version'] = galaxy.get('version')
            except IOError as exc:
                result['warnings'].append('Error while reading {0}: {1}'.format(galaxy_path, exc))
        return result

    result['warnings'].append(
        'Found neither galaxy.yml nor MANIFEST.json in {0}'.format(collection_path))
    return result


if len(sys.argv) != 2:
    print('Expect exactly one argument: path to the collection')
    sys.exit(-1)

print(json.dumps(load_metadata(sys.argv[1])))
