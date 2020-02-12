#
# -*- coding: utf-8 -*-
# Copyright 2020 Allied Telesis
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
"""
The arg spec for the awplus_static_lag_interfaces module
"""


class Static_Lag_interfacesArgs(object):  # pylint: disable=R0903
    """The arg spec for the awplus_static_lag_interfaces module
    """

    def __init__(self, **kwargs):
        pass

    argument_spec = {'config': {'elements': 'dict',
                                'options': {'members': {'options': {'member': {'type': 'str'},
                                                                    'member_filters': {'type': 'bool', 'default': False}},
                                                        'type': 'list'},
                                            'name': {'required': True, 'type': 'str'}},
                                'type': 'list'},
                     'state': {'choices': ['merged', 'replaced', 'overridden', 'deleted'],
                               'default': 'merged',
                               'type': 'str'}}  # pylint: disable=C0301
