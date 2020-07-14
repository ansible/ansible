from __future__ import absolute_import, division, print_function
__metaclass__ = type

from .....plugins.modules.hello import say_hello


def test_say_hello():
    assert say_hello('Ansibull') == dict(message='Hello Ansibull')
