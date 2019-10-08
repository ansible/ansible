# -*- coding: utf-8 -*-

#######################################################
# Copyright (c) 2019 Intel Corporation. All rights reserved.
#
# GNU General Public License v3.0+
# (see LICENSE.GPL or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Authors:
#   - Przemyslaw Szczerbik - <przemyslawx.szczerbik@intel.com>
#######################################################

from __future__ import absolute_import, division, print_function
__metaclass__ = type


RSD_NODES_ENDPOINT = 'v1/Nodes/'
PODM_PORT = 8443
RSD_NODE_URL = \
    'https://127.0.0.1:{0}/redfish/{1}'.format(PODM_PORT, RSD_NODES_ENDPOINT)


def get_common_args():
    return dict(
        podm=dict(host='127.0.0.1', port=PODM_PORT),
        auth=dict(user='admin', password='admin'))


def get_rsd_common_args(name='TestNode0', id_type='identity'):
    args = get_common_args()
    args.update(dict(id=dict(value=name, type=id_type)))
    return args
