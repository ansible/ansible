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

import pytest

from units.modules.utils import (AnsibleExitJson, AnsibleFailJson,
                                 set_module_args)
import units.modules.remote_management.rsd.utilities as rsd_utils


class TestRsdNodeResource():

    def get_rsd_resource_args(self, state):
        args = rsd_utils.get_rsd_common_args()
        args.update(dict(
            resource='/redfish/v1/StorageServices/f9c7e17e-6682_1/Volumes/1'),
            state=state)
        return args

    def _check_returned_output(self, result, node, resource, attached=True,
                               changed=True):
        expected_result = dict(
            changed=changed,
            node=dict(
                id=node.identity,
                name=node.name,
                uuid=node.uuid))
        if changed:
            if attached:
                expected_result['node']['endpoint_attached'] = resource
            else:
                expected_result['node']['endpoint_detached'] = resource
        assert result == expected_result

    def test_without_required_parameters(self, rsd_mock, rsd_resource):
        with pytest.raises(AnsibleFailJson,
                           match='missing required arguments'):
            set_module_args(rsd_utils.get_rsd_common_args())
            rsd_resource.main()

        rsd_mock.assert_not_called()

    @pytest.mark.parametrize('state', [('detached'), ('attached')])
    def test_invalid_endpoint(self, rsd_mock, rsd_resource,
                              get_sample_node, state):
        mock_node, get_node_mock = get_sample_node('allocating')
        mock_node.get_allowed_attach_endpoints.return_value = []
        mock_node.get_allowed_detach_endpoints.return_value = []

        with pytest.raises(AnsibleFailJson, match='Invalid Endpoint'):
            set_module_args(self.get_rsd_resource_args(state))
            rsd_resource.main()

        mock_node.detach_endpoint.assert_not_called()
        mock_node.detach_endpoint.assert_not_called()

    def test_attach_resource_successful(self, rsd_mock, rsd_resource,
                                        get_sample_node):
        mock_node, get_node_mock = get_sample_node('allocating')
        mock_node.get_allowed_attach_endpoints.return_value = \
            ['/redfish/v1/StorageServices/f9c7e17e-6682_1/Volumes/1']
        mock_node.get_allowed_detach_endpoints.return_value = \
            ['/redfish/v1/StorageServices/f9c7e17e-6682_1/Volumes/2',
             '/redfish/v1/StorageServices/f9c7e17e-6682_1/Volumes/3',
             '/redfish/v1/StorageServices/f9c7e17e-6682_1/Volumes/4']

        with pytest.raises(AnsibleExitJson) as e:
            module_args = self.get_rsd_resource_args('attached')
            set_module_args(module_args)
            rsd_resource.main()

        mock_node.attach_endpoint.assert_called_once_with(
            module_args['resource'])

        # Check return values
        result = e.value.args[0]
        self._check_returned_output(
            result, mock_node, module_args['resource'], True, True)

    def test_attach_resource_already_attached(self, rsd_mock, rsd_resource,
                                              get_sample_node):
        mock_node, get_node_mock = get_sample_node('allocating')
        mock_node.get_allowed_attach_endpoints.return_value = []
        mock_node.get_allowed_detach_endpoints.return_value = \
            ['/redfish/v1/StorageServices/f9c7e17e-6682_1/Volumes/1',
             '/redfish/v1/StorageServices/f9c7e17e-6682_1/Volumes/2',
             '/redfish/v1/StorageServices/f9c7e17e-6682_1/Volumes/3',
             '/redfish/v1/StorageServices/f9c7e17e-6682_1/Volumes/4']

        with pytest.raises(AnsibleExitJson) as e:
            module_args = self.get_rsd_resource_args('attached')
            set_module_args(module_args)
            rsd_resource.main()

        mock_node.attach_endpoint.assert_not_called()

        # Check return values
        result = e.value.args[0]
        self._check_returned_output(
            result, mock_node, module_args['resource'], True, False)

    def test_attach_api_exception(self, rsd_mock, rsd_resource,
                                  get_sample_node, sushy_import_mock):
        mock_node, get_node_mock = get_sample_node('allocating')
        mock_node.get_allowed_attach_endpoints.return_value = \
            ['/redfish/v1/StorageServices/f9c7e17e-6682_1/Volumes/1']
        mock_node.get_allowed_detach_endpoints.return_value = []
        mock_node.attach_endpoint.side_effect = \
            sushy_import_mock.exceptions.InvalidParameterValueError

        with pytest.raises(AnsibleFailJson, match='Invalid Endpoint'):
            module_args = self.get_rsd_resource_args('attached')
            set_module_args(module_args)
            rsd_resource.main()

        mock_node.attach_endpoint.assert_called_once_with(
            module_args['resource'])

    def test_detach_resource_successful(self, rsd_mock, rsd_resource,
                                        get_sample_node):
        mock_node, get_node_mock = get_sample_node('allocating')
        mock_node.get_allowed_attach_endpoints.return_value = []
        mock_node.get_allowed_detach_endpoints.return_value = \
            ['/redfish/v1/StorageServices/f9c7e17e-6682_1/Volumes/1']

        with pytest.raises(AnsibleExitJson) as e:
            module_args = self.get_rsd_resource_args('detached')
            set_module_args(module_args)
            rsd_resource.main()

        mock_node.detach_endpoint.assert_called_once_with(
            module_args['resource'])

        # Check return values
        result = e.value.args[0]
        self._check_returned_output(
            result, mock_node, module_args['resource'], False, True)

    def test_detach_resource_already_detached(self, rsd_mock, rsd_resource,
                                              get_sample_node):
        mock_node, get_node_mock = get_sample_node('allocating')
        mock_node.get_allowed_attach_endpoints.return_value = \
            ['/redfish/v1/StorageServices/f9c7e17e-6682_1/Volumes/1']
        mock_node.get_allowed_detach_endpoints.return_value = []

        with pytest.raises(AnsibleExitJson) as e:
            module_args = self.get_rsd_resource_args('detached')
            set_module_args(module_args)
            rsd_resource.main()

        mock_node.detach_endpoint.assert_not_called()

        # Check return values
        result = e.value.args[0]
        self._check_returned_output(
            result, mock_node, module_args['resource'], False, False)

    def test_detach_api_exception(self, rsd_mock, rsd_resource,
                                  get_sample_node, sushy_import_mock):
        mock_node, get_node_mock = get_sample_node('allocating')
        mock_node.get_allowed_attach_endpoints.return_value = []
        mock_node.get_allowed_detach_endpoints.return_value = \
            ['/redfish/v1/StorageServices/f9c7e17e-6682_1/Volumes/1']
        mock_node.detach_endpoint.side_effect = \
            sushy_import_mock.exceptions.InvalidParameterValueError

        with pytest.raises(AnsibleFailJson, match='Invalid Endpoint'):
            module_args = self.get_rsd_resource_args('detached')
            set_module_args(module_args)
            rsd_resource.main()

        mock_node.detach_endpoint.assert_called_once_with(
            module_args['resource'])
