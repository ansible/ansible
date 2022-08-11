from __future__ import absolute_import, division, print_function
__metaclass__ = type

from .....plugins.module_utils.my_util import hello


def test_hello():
    assert hello('Ansibull') == 'Hello Ansibull'
