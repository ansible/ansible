#!/usr/bin/env python

import glob
import json
import os.path

try:
    from packaging.version import Version
except ImportError:
    try:
        from pip._vendor.packaging.version import Version
    except ImportError:
        from distutils.version import LooseVersion as Version

from ansible.module_utils.urls import open_url

basedir = os.path.dirname(__file__)

for filename in glob.glob(os.path.join(basedir, '../lib/ansible/compat/*/__init__.py')):
    if 'compat/tests' in filename:
        # compat/tests doesn't bundle any code
        continue

    filename = os.path.normpath(filename)
    with open(filename, 'r') as module:
        for line in module:
            if line.strip().startswith('_BUNDLED_METADATA'):
                data = line[line.index('{'):].strip()
                break
        else:
            print('WARNING: {0} contained no metadata.  Could not check for updates'.format(filename))
            continue
        metadata = json.loads(data)
        pypi_fh = open_url('https://pypi.python.org/pypi/{0}/json'.format(metadata['pypi_name']))
        pypi_data = json.loads(pypi_fh.read().decode('utf-8'))
        if Version(metadata['version']) < Version(pypi_data['info']['version']):
            print('UPDATE: {0} from {1} to {2} {3}'.format(
                metadata['pypi_name'],
                metadata['version'],
                pypi_data['info']['version'],
                'https://pypi.python.org/pypi/{0}/'.format(metadata['pypi_name'])))
