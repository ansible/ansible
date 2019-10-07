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

from units.compat import mock
from units.modules.utils import (AnsibleExitJson, AnsibleFailJson,
                                 set_module_args)
import units.modules.remote_management.rsd.utilities as rsd_utils

RSD_LOOKUP_PARAMETRIZE_ARGS = [
    (False, 'Attached_resources'),
    (False, 'available_resources'),
    (True, 'Attached_resources'),
    (True, 'available_resources'),
]


def _get_expected_result(node_info):
    return {
        'changed': False,
        'node': node_info
    }


def _get_expected_node_resource_result(resource_name, resource_value):
    return _get_expected_result({resource_name: resource_value})


def _check_basic_node_info(result, node, system):
    node_info = {
        'Id': node.identity,
        'Name': node.name,
        'UUID': node.uuid,
        'ComposedNodeState': node.composed_node_state,
        'Status': node.status,
        'ClearOptaneDCPersistentMemoryOnDelete':
            node.persistent_memory_operation_on_delete,
        'ClearTPMOnDelete': node.clear_tpm_on_delete,
        'Memory': system.memory_summary,
        'Processor': system.processor_summary,
        'HostingRoles': system.hosting_roles
    }

    assert result == _get_expected_result(node_info)


def _check_boot_node_info(result, node):
    assert result == _get_expected_node_resource_result('Boot', node.boot)


def _check_links_node_info(result, node):
    assert result == _get_expected_node_resource_result('Links', node.links)


def _check_power_node_info(result, node):
    power_info = {
        "PowerState": node.power_state,
        "AllowableValues": node.get_allowed_reset_node_values()
    }

    assert result == _get_expected_node_resource_result('Power', power_info)


def _check_all_node_info(result, node):
    assert result == _get_expected_result(node.json)


def _check_node_info(result, node, system, node_info):
    if node_info == 'basic':
        _check_basic_node_info(result, node, system)
    elif node_info == 'boot':
        _check_boot_node_info(result, node)
    elif node_info == 'links':
        _check_links_node_info(result, node)
    elif node_info == 'power':
        _check_power_node_info(result, node)
    elif node_info == 'all':
        _check_all_node_info(result, node)


def _check_attached_volumes(result, volumes, details, resource_type):
    volumes_info = []
    for uri, mock_volume in volumes.items():
        if details:
            volume_info = {uri: mock_volume.json}
        else:
            volume_info = {
                uri: {
                    'Id': mock_volume.identity,
                    'DurableName': mock_volume.identifiers[0].durable_name,
                    'URI': uri,
                    'Name': mock_volume.name,
                    'Description': mock_volume.description,
                    'Bootable': mock_volume.bootable,
                    'CapacityBytes': mock_volume.capacity_bytes,
                }
            }
        volumes_info.append(volume_info)

    volumes = {'Volumes': volumes_info}
    assert result == _get_expected_node_resource_result(resource_type, volumes)


def _check_attached_drives(result, volumes, details, resource_type):
    drives_info = []
    for uri, mock_drive in volumes.items():
        if details:
            drive_info = {uri: mock_drive.json}
        else:
            drive_info = {
                uri: {
                    'Id': mock_drive.identity,
                    'DurableName': mock_drive.identifiers[0].durable_name,
                    'URI': uri,
                    'Name': mock_drive.name,
                    'Description': mock_drive.description,
                    'Protocol': mock_drive.protocol,
                    'CapacityBytes': mock_drive.capacity_bytes,
                }
            }
        drives_info.append(drive_info)

    drives = {'Drives': drives_info}
    assert result == _get_expected_node_resource_result(resource_type, drives)


def _check_attached_endpoints(result, endpoints, details, resource_type):
    endpoints_info = []
    for uri, mock_endpoint in endpoints.items():
        if details:
            endpoint_info = {uri: mock_endpoint.json}
        else:
            endpoint_info = {
                uri: {
                    'Id': mock_endpoint.identity,
                    'URI': uri,
                    'Name': mock_endpoint.name,
                    'Description': mock_endpoint.description,
                    'ConnectedEntities': {
                        'Type': [et.entity_type
                                 for et in mock_endpoint.connected_entities],
                        'Link': [et.entity_link
                                 for et in mock_endpoint.connected_entities]
                    }
                }
            }
        endpoints_info.append(endpoint_info)

    drives = {'Endpoints': endpoints_info}
    assert result == _get_expected_node_resource_result(resource_type, drives)


def _check_attached_processors(result, processors, details, resource_type):
    processors_info = []
    for uri, mock_processor in processors.items():
        fpga = mock_processor.oem.intel_rackscale.fpga
        if details:
            processor_info = {uri: mock_processor.json}
        else:
            processor_info = {
                uri: {
                    'Id': mock_processor.identity,
                    'URI': uri,
                    'Name': mock_processor.name,
                    'Description': mock_processor.description,
                    'ProcessorType': mock_processor.processor_type,
                    'Socket': mock_processor.socket,
                    'Oem': {
                        'Intel_RackScale': {
                            'FPGA': {
                                'Type': fpga.fpga_type,
                                'Model': fpga.fpga_model,
                                'ReconfigurationSlots':
                                    fpga.reconfiguration_slots
                            }
                        }
                    }
                }
            }
        processors_info.append(processor_info)

    processors = {'Processors': processors_info}
    assert result == _get_expected_node_resource_result(resource_type,
                                                        processors)


class TestRsdNodeLookup():
    def get_rsd_lookup_args(self, node_info):
        args = rsd_utils.get_rsd_common_args()
        args.update(dict(node_info=node_info))
        return args

    def get_rsd_lookup_args_resource(self, resource_type, resource, details):
        args = rsd_utils.get_rsd_common_args()
        extra_args = {
            resource_type.lower(): {
                'resource': resource,
                'details': details
            }
        }
        args.update(extra_args)
        return args

    def test_invalid_node(self, rsd_lookup, get_node_mock, sushy_import_mock):

        get_node_mock.side_effect = \
            sushy_import_mock.exceptions.ResourceNotFoundError
        with pytest.raises(AnsibleFailJson,
                           match='There is no node with such ID'):
            set_module_args(rsd_utils.get_rsd_common_args())
            rsd_lookup.main()

    @pytest.mark.parametrize('node_info', [
        'basic', 'boot', 'links', 'power', 'all',
    ])
    def test_get_node_info(self, rsd_lookup, get_sample_node,
                           get_sample_system, node_info):

        mock_node, get_node_mock = get_sample_node()
        mock_system, get_system_mock = get_sample_system
        with pytest.raises(AnsibleExitJson) as e:
            args = self.get_rsd_lookup_args(node_info)
            args.update(args)
            set_module_args(args)
            rsd_lookup.main()

        node_id = args['id']['value']
        node_uri = "v1/Nodes/" + str(node_id)
        get_node_mock.assert_called_once_with(node_uri)
        get_system_mock.assert_called_once_with(
            mock_node.links.computer_system)

        result = e.value.args[0]
        _check_node_info(result, mock_node, mock_system, node_info)

    @pytest.mark.parametrize('details, resource_type',
                             RSD_LOOKUP_PARAMETRIZE_ARGS)
    def test_get_node_resources_volumes(self, rsd_lookup, get_sample_node,
                                        get_sample_system, create_volume,
                                        get_storage_service_mock, details,
                                        resource_type):

        mock_node, get_node_mock = get_sample_node()
        storage_service_uri = \
            ['/redfish/v1/StorageServices/f9c7e17e-6682_1',
             '/redfish/v1/StorageServices/f9c7e17e-6682_2']
        volumes = {storage_uri + '/Volumes/1': create_volume(i)
                   for i, storage_uri in enumerate(storage_service_uri)}

        if resource_type.lower() == 'attached_resources':
            mock_node.get_allowed_detach_endpoints.return_value = \
                volumes.keys()
        elif resource_type.lower() == 'available_resources':
            mock_node.get_allowed_attach_endpoints.return_value = \
                volumes.keys()

        mock_system, get_system_mock = get_sample_system
        get_member_mock = \
            get_storage_service_mock.return_value.volumes.get_member
        # Map resource URI to mock resource
        get_member_mock.side_effect = lambda volume_uri: volumes[volume_uri]

        with pytest.raises(AnsibleExitJson) as e:
            args = self.get_rsd_lookup_args_resource(resource_type,
                                                     'volumes', details)
            set_module_args(args)
            rsd_lookup.main()

        node_id = args['id']['value']
        node_uri = "v1/Nodes/" + str(node_id)
        get_node_mock.assert_called_once_with(node_uri)
        get_system_mock.assert_called_once_with(
            mock_node.links.computer_system)

        expected_calls = [mock.call(uri) for uri in storage_service_uri]
        get_storage_service_mock.assert_has_calls(expected_calls,
                                                  any_order=True)
        expected_calls = [mock.call(uri) for uri in volumes.keys()]
        get_member_mock.assert_has_calls(expected_calls)

        result = e.value.args[0]
        _check_attached_volumes(result, volumes, details, resource_type)

    @pytest.mark.parametrize('details, resource_type',
                             RSD_LOOKUP_PARAMETRIZE_ARGS)
    def test_get_node_resources_drives(self, rsd_lookup, get_sample_node,
                                       get_sample_system, create_drive,
                                       get_storage_service_mock, details,
                                       resource_type):

        mock_node, get_node_mock = get_sample_node()
        storage_service_uri = \
            ['/redfish/v1/StorageServices/f9c7e17e-6682_1',
             '/redfish/v1/StorageServices/f9c7e17e-6682_2']
        drives = {storage_uri + '/Drives/1': create_drive(i)
                  for i, storage_uri in enumerate(storage_service_uri)}

        if resource_type.lower() == 'attached_resources':
            mock_node.get_allowed_detach_endpoints.return_value = \
                drives.keys()
        elif resource_type.lower() == 'available_resources':
            mock_node.get_allowed_attach_endpoints.return_value = \
                drives.keys()

        mock_system, get_system_mock = get_sample_system
        get_member_mock = \
            get_storage_service_mock.return_value.drives.get_member
        # Map resource URI to mock resource
        get_member_mock.side_effect = lambda drive_uri: drives[drive_uri]

        with pytest.raises(AnsibleExitJson) as e:
            args = self.get_rsd_lookup_args_resource(resource_type,
                                                     'drives', details)
            set_module_args(args)
            rsd_lookup.main()

        node_id = args['id']['value']
        node_uri = "v1/Nodes/" + str(node_id)
        get_node_mock.assert_called_once_with(node_uri)
        get_system_mock.assert_called_once_with(
            mock_node.links.computer_system)

        expected_calls = [mock.call(uri) for uri in storage_service_uri]
        get_storage_service_mock.assert_has_calls(expected_calls,
                                                  any_order=True)
        expected_calls = [mock.call(uri) for uri in drives.keys()]
        get_member_mock.assert_has_calls(expected_calls)

        result = e.value.args[0]
        _check_attached_drives(result, drives, details, resource_type)

    @pytest.mark.parametrize('details, resource_type',
                             RSD_LOOKUP_PARAMETRIZE_ARGS)
    def test_get_node_resources_endpoints(self, rsd_lookup, get_sample_node,
                                          get_sample_system, create_endpoint,
                                          get_fabric_mock, details,
                                          resource_type):

        mock_node, get_node_mock = get_sample_node()
        fabrics_uri = \
            ['/redfish/v1/Fabrics/a5b6af0c-8919-11e9-b709-033fe8413ff7_1',
             '/redfish/v1/Fabrics/a5b6af0c-8919-11e9-b709-033fe8413ff7_2', ]
        endpoints = {fabric_uri + '/Endpoints/1': create_endpoint(i)
                     for i, fabric_uri in enumerate(fabrics_uri)}

        if resource_type.lower() == 'attached_resources':
            mock_node.get_allowed_detach_endpoints.return_value = \
                endpoints.keys()
        elif resource_type.lower() == 'available_resources':
            mock_node.get_allowed_attach_endpoints.return_value = \
                endpoints.keys()

        mock_system, get_system_mock = get_sample_system
        get_member_mock = \
            get_fabric_mock.return_value.endpoints.get_member
        # Map resource URI to mock resource
        get_member_mock.side_effect = \
            lambda endpoint_uri: endpoints[endpoint_uri]

        with pytest.raises(AnsibleExitJson) as e:
            args = self.get_rsd_lookup_args_resource(resource_type,
                                                     'endpoints', details)
            set_module_args(args)
            rsd_lookup.main()

        node_id = args['id']['value']
        node_uri = "v1/Nodes/" + str(node_id)
        get_node_mock.assert_called_once_with(node_uri)
        get_system_mock.assert_called_once_with(
            mock_node.links.computer_system)

        expected_calls = [mock.call(uri) for uri in fabrics_uri]
        get_fabric_mock.assert_has_calls(expected_calls, any_order=True)
        expected_calls = [mock.call(uri) for uri in endpoints.keys()]
        get_member_mock.assert_has_calls(expected_calls)

        result = e.value.args[0]
        _check_attached_endpoints(result, endpoints, details, resource_type)

    @pytest.mark.parametrize('details, resource_type',
                             RSD_LOOKUP_PARAMETRIZE_ARGS)
    def test_get_node_resources_processors(self, rsd_lookup, get_sample_node,
                                           get_sample_system, create_processor,
                                           details, resource_type):

        mock_node, get_node_mock = get_sample_node()
        systems_uri = \
            ['/redfish/v1/Systems/a5b6af0c-8919-11e9-b709-033fe8413ff7_1',
             '/redfish/v1/Systems/a5b6af0c-8919-11e9-b709-033fe8413ff7_2', ]
        processors = {system_uri + '/Processors/1': create_processor(i)
                      for i, system_uri in enumerate(systems_uri)}

        if resource_type.lower() == 'attached_resources':
            mock_node.get_allowed_detach_endpoints.return_value = \
                processors.keys()
        elif resource_type.lower() == 'available_resources':
            mock_node.get_allowed_attach_endpoints.return_value = \
                processors.keys()

        mock_system, get_system_mock = get_sample_system
        get_member_mock = \
            get_system_mock.return_value.processors.get_member
        # Map resource URI to mock resource
        get_member_mock.side_effect = \
            lambda endpoint_uri: processors[endpoint_uri]

        with pytest.raises(AnsibleExitJson) as e:
            args = self.get_rsd_lookup_args_resource(resource_type,
                                                     'processors', details)
            set_module_args(args)
            rsd_lookup.main()

        node_id = args['id']['value']
        node_uri = "v1/Nodes/" + str(node_id)
        get_node_mock.assert_called_once_with(node_uri)

        expected_calls = \
            [mock.call(mock_node.links.computer_system)] + \
            [mock.call(uri) for uri in systems_uri]
        get_system_mock.assert_has_calls(expected_calls, any_order=True)
        expected_calls = [mock.call(uri) for uri in processors.keys()]
        get_member_mock.assert_has_calls(expected_calls)

        result = e.value.args[0]
        _check_attached_processors(result, processors, details, resource_type)
