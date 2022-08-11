from __future__ import absolute_import, division, print_function
__metaclass__ = type

import botocore


def test_constraints():
    assert botocore.__version__ == '1.13.50'
