# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


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
