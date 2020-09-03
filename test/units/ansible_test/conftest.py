from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import os
import pytest
import sys


@pytest.fixture(autouse=True, scope='session')
def ansible_test():
    """Make ansible_test available on sys.path for unit testing ansible-test."""
    test_lib = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'runner')
    sys.path.insert(0, test_lib)
