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

result = dict(warnings=[])

if len(sys.argv) != 2:
    print('Expect exactly one argument: path to the collection')
    sys.exit(-1)

collection_path = sys.argv[1]

# Try reading galaxy.yml
fn = os.path.join(collection_path, 'galaxy.yml')
if os.path.exists(fn):
    if yaml is None:
        result['no-pyyaml'] = True
    else:
        try:
            with open(fn) as galaxy_file:
                galaxy = yaml.safe_load(galaxy_file)
                result['version'] = galaxy.get('version')
        except IOError as exc:
            result['warnings'].append('Error while reading {0}: {1}'.format(fn, exc))

# Try reading MANIFEST.json
fn = os.path.join(collection_path, 'MANIFEST.json')
if os.path.exists(fn):
    try:
        with open(fn) as manifest_file:
            manifest = json.load(manifest_file)
            collection_info = manifest.get('collection_info') or dict()
            result['version'] = collection_info.get('version')
    except IOError as exc:
        result['warnings'].append('Error while reading {0}: {1}'.format(fn, exc))

print(json.dumps(result))
