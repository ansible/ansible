#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The arg spec for the eos facts module.
"""

class FactsArgs(object): #pylint: disable=R0903
    """ The arg spec for the eos facts module
    """

    def __init__(self, **kwargs):
        pass

    choices = [
        'all',
        'net_configuration_interfaces',
    ]

    argument_spec = {
        'gather_subset': dict(default=['all'], choices=choices, type='list')
    }
