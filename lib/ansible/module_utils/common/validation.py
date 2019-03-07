# -*- coding: utf-8 -*-
# Copyright (c) 2018 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.common.collections import is_iterable


def count_terms(terms, module_parameters):
    """Count the number of occurrences of a key in a given dictionary

    :arg terms: String or iterable of values to check
    :arg module_parameters: Dictionary of module parameters

    :returns: An integer that is the number of occurrences of the terms values
        in the provided dictionary.
    """

    if not is_iterable(terms):
        terms = [terms]

    return len(set(terms).intersection(module_parameters))


def check_mutually_exclusive(terms, module_parameters):
    """Check mutually exclusive terms against argument parameters. Accepts
    a single list or list of lists that are groups of terms that should be
    mutually exclusive with one another

    :arg terms: List of mutually exclusive module parameters
    :arg module_parameters: Dictionary of module parameters

    :returns: A list of terms that are mutually exclusive.
    """

    if terms is None:
        return []

    result = []
    for check in terms:
        count = count_terms(check, module_parameters)
        if count > 1:
            result.append(check)

    return result


def check_required_one_of(terms, module_parameters):
    """Check each list of terms to ensure at least one exists in the given module
    parameters. Accepts a list of lists or tuples.

    :arg terms: List of lists of terms to check. For each list of terms, at
        least is required.
    :arg module_parameters: Dictionary of module parameters

    :returns: list of terms that should be present in module parameters but
              are missing
    """

    result = []
    for term in terms:

        count = count_terms(term, module_parameters)
        if count == 0:
            result.append(term)

    return result
