#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# utils
from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.network.junos.junos import tostring
try:
    from ncclient.xml_ import new_ele, to_ele
    HAS_NCCLIENT = True
except ImportError:
    HAS_NCCLIENT = False


def get_resource_config(connection, config_filter=None, attrib=None):

    if attrib is None:
        attrib = {'inherit': 'inherit'}

    get_ele = new_ele('get-configuration', attrib)
    if config_filter:
        get_ele.append(to_ele(config_filter))

    return connection.execute_rpc(tostring(get_ele))
