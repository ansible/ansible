# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The arg spec for the eos facts module.
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

CHOICES = [
    'all',
    '!all',
    'interfaces',
    '!interfaces',
    'l2_interfaces',
    '!l2_interfaces',
    'lacp',
    '!lacp',
    'lag_interfaces',
    '!lag_interfaces',
    'vlans',
    '!vlans',
]


class FactsArgs(object):
    """ The arg spec for the eos facts module
    """

    def __init__(self, **kwargs):
        pass

    argument_spec = {
        'gather_subset': dict(default=['!config'], type='list'),
        'gather_network_resources': dict(choices=CHOICES, type='list'),
    }
