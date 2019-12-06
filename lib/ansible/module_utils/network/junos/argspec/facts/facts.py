#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The arg spec for the junos facts module.
"""


class FactsArgs(object):
    """ The arg spec for the junos facts module
    """

    def __init__(self, **kwargs):
        pass

    argument_spec = {
        'gather_subset': dict(default=['!config'], type='list'),
        'config_format': dict(default='text', choices=['xml', 'text', 'set', 'json']),
        'gather_network_resources': dict(type='list'),
    }
