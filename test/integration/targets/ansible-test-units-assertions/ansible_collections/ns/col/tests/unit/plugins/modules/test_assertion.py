from __future__ import absolute_import, division, print_function
__metaclass__ = type


def test_assertion():
    assert dict(yes=True) == dict(no=False)
