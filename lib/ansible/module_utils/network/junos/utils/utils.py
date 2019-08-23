#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# utils
from ncclient.xml_ import new_ele, to_ele, to_xml


def get_resource_config(connection, config_filter=None, attrib={'inherit': 'inherit'}):
    get_ele = new_ele('get-configuration', attrib)
    if config_filter:
        get_ele.append(to_ele(config_filter))

    return connection.execute_rpc(to_xml(get_ele))
