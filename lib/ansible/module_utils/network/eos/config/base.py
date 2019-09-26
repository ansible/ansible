# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The facts class for eos
this file validates each subset of facts and selectively
calls the appropriate facts gathering function
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.eos.eos import get_connection

class Config(ConfigBase):

    def __init__(self, module):
        super(Config, self).__init__(module)

        if self._connection:
            capabilities = json.loads(self._connection.get_capabilities())
            if capabilities.get("network_api") == "eapi":
                # Redirect connection to something that understands httpapi
                self._connection = get_connection(module)
