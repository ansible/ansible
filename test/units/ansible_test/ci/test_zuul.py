#!/usr/bin/env python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from .util import common_auth_test


def test_zuul():
    # noinspection PyProtectedMember
    from ansible_test._internal.ci.zuul import (
        Zuul,
    )

    zuul_driver = Zuul()
    # some AWS services won't accept a longer prefix.
    assert len(zuul_driver.generate_resource_prefix()) < 64
