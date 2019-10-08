# -*- coding: utf-8 -*-

#######################################################
# Copyright (c) 2019 Intel Corporation. All rights reserved.
#
# GNU General Public License v3.0+
# (see LICENSE.GPL or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Authors:
#   - Radoslaw Kuschel - <radoslaw.kuschel@intel.com>
#   - Przemyslaw Szczerbik - <przemyslawx.szczerbik@intel.com>
#######################################################

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from units.compat import mock
from units.modules.utils import set_module_args, AnsibleFailJson
import units.modules.remote_management.rsd.utilities as rsd_utils

import pytest


class TestRsdCommon():

    def test_without_endpoint_host_parameter(self, mocker, rsd_mock,
                                             ansible_module_mock, rsd_common):
        is_valid_mock = mocker.patch(
            'ansible.module_utils.remote_management.rsd.rsd_common.RSD.'
            'PodmInfo.is_valid',
            return_value=False, autospec=True)

        with pytest.raises(AnsibleFailJson, match='Invalid PODM info'):
            set_module_args(rsd_utils.get_rsd_common_args())
            rsd_common.RSD({})

        is_valid_mock.assert_called_once_with(mock.ANY)
        rsd_mock.assert_not_called()

    def test_podm_connection_failure(self, rsd_mock, factory_mock, rsd_common,
                                     sushy_import_mock):

        factory_mock.side_effect = sushy_import_mock.exceptions.ConnectionError

        with pytest.raises(
                AnsibleFailJson,
                match='Failed to setup and endpoint connection'):
            args = rsd_utils.get_rsd_common_args()
            set_module_args(args)
            rsd_common.RSD({})

        rsd_mock.assert_called_once_with(
            base_url='https://{0}:{1}/redfish/v1'.format(args['podm']['host'],
                                                         args['podm']['port']),
            validate_cert=False,
            **rsd_utils.get_rsd_common_args())
        factory_mock.assert_called_once_with()
