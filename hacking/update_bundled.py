#!/usr/bin/python2 -tt

import glob
import json
import os.path
from distutils.version import LooseVersion

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
        pypi_data = json.loads(pypi_fh.read())
        if LooseVersion(metadata['version']) < LooseVersion(pypi_data['info']['version']):
            print('UPDATE: {0} from {1} to {2} {3}'.format(
                metadata['pypi_name'],
                metadata['version'],
                pypi_data['info']['version'],
                'https://pypi.python.org/pypi/{0}/'.format(metadata['pypi_name'])))
