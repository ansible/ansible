#!/usr/bin/env python
"""Make sure the Azure requirements files match."""

import filecmp

src = 'packaging/requirements/requirements-azure.txt'
dst = 'test/runner/requirements/integration.cloud.azure.txt'

if not filecmp.cmp(src, dst):
    print('Update the Azure integration test requirements with the packaging test requirements:')
    print('cp %s %s' % (src, dst))
    exit(1)
