# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.six import iteritems


def cmp_simple_list(want, have):
    if want is None:
        return None
    if have is None and want in ['', 'none']:
        return None
    if have is not None and want in ['', 'none']:
        return []
    if have is None:
        return want
    if set(want) != set(have):
        return want
    return None


def cmp_str_with_none(want, have):
    if want is None:
        return None
    if have is None and want == '':
        return None
    if want != have:
        return want


def compare_complex_list(want, have):
    """Performs a complex list comparison

    A complex list is a list of dictionaries

    Args:
        want (list): List of dictionaries to compare with second parameter.
        have (list): List of dictionaries compare with first parameter.

    Returns:
        bool:
    """
    if want == [] and have is None:
        return None
    if want is None:
        return None
    w = []
    h = []
    for x in want:
        tmp = [(str(k), str(v)) for k, v in iteritems(x)]
        w += tmp
    for x in have:
        tmp = [(str(k), str(v)) for k, v in iteritems(x)]
        h += tmp
    if set(w) == set(h):
        return None
    else:
        return want


def compare_dictionary(want, have):
    """Performs a dictionary comparison

    Args:
        want (dict): Dictionary to compare with second parameter.
        have (dict): Dictionary to compare with first parameter.

    Returns:
        bool:
    """
    if want == {} and have is None:
        return None
    if want is None:
        return None
    w = [(str(k), str(v)) for k, v in iteritems(want)]
    h = [(str(k), str(v)) for k, v in iteritems(have)]
    if set(w) == set(h):
        return None
    else:
        return want
