from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys

# latin1 encoded bytes
# to ensure wait_for doesn't have any encoding errors
data = b'premi\xe8re is first\npremie?re is slightly different\n????????? is Cyrillic\n? am Deseret\n'

with open(sys.argv[1], 'wb') as f:
    f.write(data)
