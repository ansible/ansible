# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The base class for all eos resource modules
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.connection import Connection


class ConfigBase(object): #pylint: disable=R0205,R0903
    """ The base class for all eos resource modules
    """
    _connection = None

    def __init__(self, module):
        self._module = module
        self._connection = self._get_connection()

    def _get_connection(self):
        if self._connection:
            return self._connection
        self._connection = Connection(self._module._socket_path)
        return self._connection
