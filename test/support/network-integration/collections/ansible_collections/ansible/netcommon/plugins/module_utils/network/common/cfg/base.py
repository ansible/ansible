#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The base class for all resource modules
"""

from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.network import (
    get_resource_connection,
)


class ConfigBase(object):
    """ The base class for all resource modules
    """

    ACTION_STATES = ["merged", "replaced", "overridden", "deleted"]

    def __init__(self, module):
        self._module = module
        self.state = module.params["state"]
        self._connection = None

        if self.state not in ["rendered", "parsed"]:
            self._connection = get_resource_connection(module)
