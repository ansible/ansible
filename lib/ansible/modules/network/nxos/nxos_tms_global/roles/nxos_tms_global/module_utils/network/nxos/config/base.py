#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The base class for all nxos resource modules
"""

from ansible.module_utils.connection import Connection
from ansible.module_utils.network.nxos.nxos import Cli, LocalNxapi, HttpApi, get_connection


class ConfigBase(object):  # pylint: disable=R0903
    """ The base class for all nxos resource modules
    """
    _connection = None

    def __init__(self, module):
        self._module = module
        #self._connection = self._get_connection()
        self._connection = get_connection(module)

    def _get_connection(self):
        if self._connection:
            return self._connection
        # pylint: disable=W0212
        self._connection = Connection(self._module._socket_path)
        # pylint: enable=W0212
        return self._connection
