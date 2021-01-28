"""Block the sphinx module from being loaded."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

raise ImportError('The sphinx module has been prevented from loading to maintain consistent test results.')
