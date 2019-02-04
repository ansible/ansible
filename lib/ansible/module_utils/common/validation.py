# -*- coding: utf-8 -*-
# Copyright (c) 2018 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


def count_terms(check, params):
    """Count the number of occurrences of a key in a given dictionary

    :arg params: Dictionary of module parameters
    :arg check: List of values to check

    :returns: An integer that is the number of occurrences of the check values
        in the provided dictionary.
    """
    count = 0
    for term in check:
        if term in params:
            count += 1
    return count
