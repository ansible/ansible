# -*- coding: utf-8 -*-

# Copyright (c) 2017, the Jinja Team
# BSD 3-Clause "New" or "Revised" License (see https://opensource.org/licenses/BSD-3-Clause)

# XXX: These tests exist for compatibility with Jinja < 2.10.  Once every
# platform has at least 2.10 version of jinja, this file can go away.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import operator


def test_in(value, seq):
    """Check if value is in seq.
    Copied from Jinja 2.10 https://github.com/pallets/jinja/pull/665

    .. versionadded:: 2.10
    """
    return value in seq


class TestModule:
    """copied from jinja 2.10 for consistent test behavior independent of the
    system jinja version
    """

    def tests(self):
        return {
            'in': test_in,
            '==': operator.eq,
            'eq': operator.eq,
            'equalto': operator.eq,
            '!=': operator.ne,
            'ne': operator.ne,
            '>': operator.gt,
            'gt': operator.gt,
            'greaterthan': operator.gt,
            'ge': operator.ge,
            '>=': operator.ge,
            '<': operator.lt,
            'lt': operator.lt,
            'lessthan': operator.lt,
            '<=': operator.le,
            'le': operator.le,
        }
