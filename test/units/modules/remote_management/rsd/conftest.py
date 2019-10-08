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

import json
import os
import sys

import pytest

import units.modules.remote_management.rsd.mock_exceptions as mock_exceptions
from ansible.module_utils import six
from units.compat import mock
from units.modules.utils import basic, exit_json, fail_json

__metaclass__ = type


@pytest.fixture(autouse=True)
def sushy_import_mock():
    ''' Mock sushy module.

    This allows to run UTs even if sushy is not installed on the system.
    To prevent affecting other tests, wrap it in a fixture.
    '''
    sushy_mock = mock.MagicMock()
    exceptions_mock = mock.MagicMock()
    exceptions_mock.ResourceNotFoundError = \
        mock_exceptions.ResourceNotFoundError
    exceptions_mock.InvalidParameterValueError = \
        mock_exceptions.InvalidParameterValueError
    exceptions_mock.ConnectionError = mock_exceptions.ConnectionError
    exceptions_mock.ServerSideError = mock_exceptions.ServerSideError
    exceptions_mock.HTTPError = mock_exceptions.HTTPError
    sushy_mock.exceptions = exceptions_mock
    sys.modules['sushy'] = sushy_mock
    sys.modules['sushy.exceptions'] = exceptions_mock
    sys.modules['sushy.exceptions.ResourceNotFoundError'] = \
        exceptions_mock.ResourceNotFoundError
    sys.modules['sushy.exceptions.InvalidParameterValueError'] = \
        exceptions_mock.InvalidParameterValueError
    sys.modules['sushy.exceptions.ConnectionError'] = \
        exceptions_mock.ConnectionError
    sys.modules['sushy.exceptions.ServerSideError'] = \
        exceptions_mock.ServerSideError
    sys.modules['sushy.exceptions.HTTPError'] = \
        exceptions_mock.HTTPError
    return sushy_mock


@pytest.fixture(autouse=True)
def rsd_lib_import_mock(sushy_import_mock):
    ''' Mock rsd_lib module.

    This allows to run UTs even if rsd_lib is not installed on the system.
    To prevent affecting other tests, wrap it in a fixture.
    '''
    rsd_lib_mock = mock.MagicMock()
    sys.modules['rsd_lib'] = rsd_lib_mock
    return rsd_lib_mock


@pytest.fixture(autouse=True)
def cinder_import_mock(rsd_lib_import_mock):
    ''' Mock cinder module.

    This allows to run UTs even if cinder is not installed on the system.
    To prevent affecting other tests, wrap it in a fixture.
    '''
    cinder_mock = mock.MagicMock()
    volume_mock = mock.MagicMock()
    drivers_mock = mock.MagicMock()
    rsd_driver_mock = mock.MagicMock()
    cinder_mock.volume = volume_mock
    cinder_mock.volume.drivers = drivers_mock
    cinder_mock.volume.drivers.rsd = rsd_driver_mock
    exception_mock = mock.MagicMock()
    exception_mock.VolumeBackendAPIException = \
        mock_exceptions.VolumeBackendAPIException
    cinder_mock.exception = exception_mock
    sys.modules['cinder'] = cinder_mock
    sys.modules['cinder.volume'] = volume_mock
    sys.modules['cinder.volume.drivers'] = drivers_mock
    sys.modules['cinder.volume.drivers.rsd'] = rsd_driver_mock
    sys.modules['cinder.exception'] = exception_mock
    return cinder_mock


@pytest.fixture()
def rsd_compose(sushy_import_mock, rsd_lib_import_mock):
    ''' Wrapper for importing rsd_compose

    Since rsd_lib is mocked in a fixture, every module that depends on it has
    to be imported directly inside a test. Wrap import as well to avoid
    code repetition.
    '''
    from ansible.modules.remote_management.rsd import rsd_compose
    return rsd_compose


@pytest.fixture()
def rsd_power(sushy_import_mock, rsd_lib_import_mock):
    ''' Wrapper for importing rsd_power

    Since rsd_lib is mocked in a fixture, every module that depends on it has
    to be imported directly inside a test. Wrap import as well to avoid
    code repetition.
    '''
    from ansible.modules.remote_management.rsd import rsd_power
    return rsd_power


@pytest.fixture()
def rsd_boot(sushy_import_mock, rsd_lib_import_mock):
    ''' Wrapper for importing rsd_boot

    Since rsd_lib is mocked in a fixture, every module that depends on it has
    to be imported directly inside a test. Wrap import as well to avoid
    code repetition.
    '''
    from ansible.modules.remote_management.rsd import rsd_boot
    return rsd_boot


@pytest.fixture()
def rsd_resource(sushy_import_mock, rsd_lib_import_mock):
    ''' Wrapper for importing rsd_resource

    Since rsd_lib is mocked in a fixture, every module that depends on it has
    to be imported directly inside a test. Wrap import as well to avoid
    code repetition.
    '''
    from ansible.modules.remote_management.rsd import rsd_resource
    return rsd_resource


@pytest.fixture()
def rsd_volume(sushy_import_mock, rsd_lib_import_mock, cinder_import_mock):
    ''' Wrapper for importing rsd_volume

    Since cinder is mocked in a fixture, every module that depends on it has
    to be imported directly inside a test. Wrap import as well to avoid
    code repetition.
    '''
    from ansible.modules.remote_management.rsd import rsd_volume
    return rsd_volume


@pytest.fixture()
def rsd_lookup(sushy_import_mock, rsd_lib_import_mock):
    ''' Wrapper for importing rsd_lookup

    Since rsd_lib is mocked in a fixture, every module that depends on it has
    to be imported directly inside a test. Wrap import as well to avoid
    code repetition.
    '''
    from ansible.modules.remote_management.rsd import rsd_lookup
    return rsd_lookup


@pytest.fixture()
def rsd_common(sushy_import_mock, rsd_lib_import_mock):
    ''' Wrapper for importing rsd_common

    Since rsd_lib is mocked in a fixture, every module that depends on it has
    to be imported directly inside a test. Wrap import as well to avoid
    code repetition.
    '''
    from ansible.module_utils.remote_management.rsd import rsd_common
    return rsd_common


@pytest.fixture(autouse=True)
def ansible_module_mock(mocker):
    return mocker.patch.multiple(basic.AnsibleModule, exit_json=exit_json,
                                 fail_json=fail_json)


@pytest.fixture(autouse=True)
def sleep_mock(mocker):
    ''' sleep() mock

    It patches sleep() to make it return immediately, which allows to avoid
    unnecessary delay in tests.
    '''
    return mocker.patch('time.sleep', return_value=None, autospec=True)


@pytest.fixture()
def rsd_mock(mocker):
    return mocker.patch(
        'ansible.module_utils.remote_management.rsd.rsd_common.rsd_lib.RSDLib',
        autospec=True)


@pytest.fixture()
def factory_mock(rsd_mock):
    factory = rsd_mock.return_value.factory
    # Mock RSD version
    factory.return_value._rsd_api_version = '2.4.0'
    return factory


@pytest.fixture()
def get_node_mock(factory_mock):
    return factory_mock.return_value.get_node


@pytest.fixture()
def get_node_collection_mock(factory_mock):
    return factory_mock.return_value.get_node_collection


@pytest.fixture()
def get_members_mock(get_node_collection_mock):
    return get_node_collection_mock.return_value.get_members


@pytest.fixture()
def get_system_mock(factory_mock):
    return factory_mock.return_value.get_system


@pytest.fixture()
def get_storage_service_mock(factory_mock):
    return factory_mock.return_value.get_storage_service


@pytest.fixture()
def get_fabric_mock(factory_mock):
    return factory_mock.return_value.get_fabric


@pytest.fixture()
def create_node(node_json):
    ''' Fixture that returns a function to create mock node object'''

    def _create_node(node_id, node_state_transition, power_state='On'):
        '''

        :param node_id: An integer used to populate node attributes.
        :param node_state_transition: A string or a list of strings with node
                                      states. This attribute specifies node
                                      state that will be returned by
                                      consecutive calls to
                                      node.composed_node_state.lower(). If a
                                      string is passed, returned value is going
                                      to be always the same.
        :return: mock node object with populated attributes
        '''
        links = node_json['Links']
        boot = node_json['Boot']
        node = mock.MagicMock(
            uuid='00000000-0000-0000-0000-00000000000{0}'.format(node_id),
            description=node_json['Description'],
            identity='Node{0}'.format(node_id),
            power_state=power_state,
            status=mock.MagicMock(state=node_json['Status']['State'],
                                  health=node_json['Status']['Health']),
            links=mock.MagicMock(
                ethernet_interfaces=tuple(
                    [links['EthernetInterfaces'][0]['@odata.id']]),
                local_drives=[],
                remote_drives=[],
                computer_system=links['ComputerSystem']['@odata.id']),
            persistent_memory_operation_on_delete=node_json['PersistentMemoryOperationOnDelete'],
            clear_tpm_on_delete=node_json['ClearOptaneDCPersistentMemoryOnDelete'],
            boot=mock.MagicMock(
                boot_source_override_target=boot['BootSourceOverrideTarget'],
                boot_source_override_target_allowed_values=boot[
                    'BootSourceOverrideTarget@Redfish.AllowableValues'],
                boot_source_override_enabled=boot['BootSourceOverrideEnabled'],
                uefi_target_boot_source_override=None,
                boot_source_override_mode=boot['BootSourceOverrideMode'],
                boot_source_override_mode_allowed_values=boot['BootSourceOverrideMode@Redfish.AllowableValues']),
            json=node_json)

        node.get_allowed_reset_node_values.return_value = [
            "On",
            "ForceOff",
            "GracefulShutdown",
            "GracefulRestart",
            "ForceRestart"
        ]

        # 'name' is an argument to the MagicMock() constructor. If we want our
        # mock node object to have 'name' attribute we have to use
        # configure_mock() method.
        node.configure_mock(name='TestNode{0}'.format(node_id))

        # If side_effect is an iterable, then each call to mock returns the
        # next value from the iterable. This is why we need to check if
        # node_state_transition is a string. If yes, assign it to
        # return_value, which will prevent iterating over the string and making
        # function mock return individual characters each time it's called.
        if isinstance(node_state_transition, six.string_types):
            node.composed_node_state.lower.return_value = \
                node_state_transition
        else:
            node.composed_node_state.lower.side_effect = \
                node_state_transition
        return node
    return _create_node


@pytest.fixture()
def create_volume(volume_json):
    ''' Fixture that returns a function to create mock volume object'''

    def _create_volume(volume_id):
        '''
        :param volume_id: An integer used to populate volume attributes.
        :return: mock volume object with populated attributes
        '''
        replica_info = volume_json['ReplicaInfos'][0]
        providing_pool = volume_json['CapacitySources'][0]['ProvidingPools'][0]
        mock_volume = mock.MagicMock(
            identity=str(volume_id),
            description=volume_json['Description'],
            model=volume_json['Model'],
            manufacturer=volume_json['Manufacturer'],
            access_capabilities=volume_json['AccessCapabilities'],
            capacity_bytes=volume_json['CapacityBytes'],
            allocated_Bytes=volume_json['Capacity']['Data']['AllocatedBytes'],
            capacity_sources=[
                mock.MagicMock(
                    providing_pools=[
                        mock.MagicMock(
                            path=providing_pool['@odata.id'])
                    ]
                )
            ],
            replica_infos=[
                mock.MagicMock(
                    replica_readonly_access=replica_info['ReplicaReadOnlyAccess'],
                    replica_type=replica_info['ReplicaType'],
                    replica_role=replica_info['ReplicaRole'],
                    replica=replica_info['Replica']['@odata.id'])
            ],
            status=mock.MagicMock(
                health=volume_json['Status']['Health'],
                health_rollup=volume_json['Status']['HealthRollup'],
                state=volume_json['Status']['State']),
            path='/redfish/v1/StorageServices/f9c7e17e-6682_1/Volumes/{0}'
                 .format(volume_id),
            bootable=volume_json['Oem']['Intel_RackScale']['Bootable'],
            identifiers=[mock.MagicMock(
                durable_name='00000000-0000-0000-0000-00000000000{0}'.format(
                    volume_id),
                durable_name_format='UUID')],
            json=volume_json)

        mock_volume.configure_mock(name=volume_json['Name'])
        return mock_volume
    return _create_volume


@pytest.fixture()
def create_drive(drive_json):
    ''' Fixture that returns a function to create mock drive object'''

    def _create_drive(drive_id):
        '''
        :param drive_id: An integer used to populate drive attributes.
        :return: mock drive object with populated attributes
        '''
        mock_drive = mock.MagicMock(
            identity=str(drive_id),
            description=drive_json['Description'],
            identifiers=[mock.MagicMock(
                durable_name='00000000-0000-0000-0000-00000000000{0}'.format(
                    drive_id),
                durable_name_format='UUID')],
            capacity_bytes=drive_json['CapacityBytes'],
            protocol=drive_json['Protocol'],
            json=drive_json)

        mock_drive.configure_mock(name=drive_json['Name'])
        return mock_drive
    return _create_drive


@pytest.fixture()
def create_endpoint(endpoint_json):
    ''' Fixture that returns a function to create mock endpoint object'''

    def _create_endpoint(endpoint_id):
        '''
        :param endpoint_id: An integer used to populate endpoint attributes.
        :return: mock endpoint object with populated attributes
        '''
        connected_entity = endpoint_json['ConnectedEntities'][0]
        entity_link = connected_entity['EntityLink']['@odata.id']
        entity_type = connected_entity['EntityType']
        mock_endpoint = mock.MagicMock(
            identity=str(endpoint_id),
            description=endpoint_json['Description'],
            protocol=endpoint_json['EndpointProtocol'],
            connected_entities=[mock.MagicMock(entity_type=entity_type,
                                               entity_link=entity_link)],
            json=endpoint_json)

        mock_endpoint.configure_mock(name=endpoint_json['Name'])
        return mock_endpoint
    return _create_endpoint


@pytest.fixture()
def create_processor(processor_json):
    ''' Fixture that returns a function to create mock processor object'''

    def _create_processor(processor_id):
        '''
        :param processor_id: An integer used to populate processor attributes.
        :return: mock processor object with populated attributes
        '''
        fpga = processor_json['Oem']['Intel_RackScale']['FPGA']
        mock_fpga = mock.MagicMock(
            fpga_type=fpga['Type'],
            fpga_model=fpga['Model'],
            reconfiguration_slots=fpga['ReconfigurationSlots'])
        mock_oem = mock.MagicMock(
            oem=mock.MagicMock(intel_rackscale=mock_fpga))
        mock_processor = mock.MagicMock(
            identity=str(processor_id),
            description=processor_json['Description'],
            processor_type=processor_json['ProcessorType'],
            socket=processor_json['Socket'],
            oem=mock_oem,
            json=processor_json)

        mock_processor.configure_mock(name=processor_json['Name'])
        return mock_processor
    return _create_processor


@pytest.fixture()
def get_sample_node(get_node_mock, create_node):
    ''' A fixture that returns a function which mocks get_node() method

    get_node() method is configured to return sample mock node with populated
    attributes.
    '''
    def _get_sample_node(node_state_transition='allocated', power_state='On'):
        '''
        :param node_state_transition: A string or a list of strings with node
                                      states.
        :return tuple(mock_node, get_node_mock)
            - mock_node: Mocked node with dummy attributes.
            - get_node_mock: Mocked get_node() function that will return
                             mock_node object.
        '''
        mock_node = create_node(1, node_state_transition, power_state)
        get_node_mock.return_value = mock_node
        return mock_node, get_node_mock
    return _get_sample_node


@pytest.fixture()
def get_sample_nodes_collection_members(get_members_mock, create_node):
    ''' A fixture that returns a function which mocks get_members() method

    get_members() method is configured to return sample mock nodes with
    populated attributes.
    '''
    def _get_sample_nodes_collection_members(count, node_state_transition):
        '''
        :param count: Number of mocked nodes to be created.
        :param node_state_transition: A string or a list of strings with node
                                      states.
        :return tuple(mock_nodes, get_node_mock)
            - mock_nodes: List of mocked nodes with dummy attributes.
            - get_members_mock: Mocked get_members() function that will return
                                mock_nodes object.
        '''
        mock_nodes = \
            [create_node(i, node_state_transition) for i in range(count)]
        get_members_mock.return_value = mock_nodes
        return mock_nodes, get_members_mock
    return _get_sample_nodes_collection_members


@pytest.fixture()
def get_sample_system(get_system_mock):
    ''' A fixture that mocks get_system() to return sample mock system

    :return tuple(mock_system, get_system_mock)
        - mock_system:  Mock system with dummy attributes.
        - get_system_mock: Mocked get_system() method that will return
                           mock_system object.
    '''
    processor_mock = mock.MagicMock(count=1, model='Model Name')
    memory_mock = mock.MagicMock(total_system_memory_gib='4')
    sys_mock = mock.MagicMock(description='System Description',
                              identity='System ID',
                              processor_summary=processor_mock,
                              memory_summary=memory_mock,
                              hosting_roles=None)
    eth_iface_mock = mock.MagicMock(
        description='Interface Description',
        identity='Interface ID',
        mac_address='00-00-00-00-00-00',
        ipv4_addresses=[mock.MagicMock(address='127.0.0.1')],
        ipv6_addresses=[mock.MagicMock(address='::1')])

    # 'name' is an argument to the MagicMock() constructor. If we want our
    # mock node object to have 'name' attribute we have to use
    # configure_mock() method.
    sys_mock.configure_mock(name='System Name')
    eth_iface_mock.configure_mock(name='Interface Name')
    sys_mock.ethernet_interfaces.get_member.return_value = eth_iface_mock
    get_system_mock.return_value = sys_mock
    return sys_mock, get_system_mock


def _open_sample_file(filename):
    ''' A helper function for loading a file from json_samples

    :param filename: Filename of the sample file to be loaded
    '''
    curr_dir = os.path.dirname(__file__)
    with open(os.path.join(curr_dir, 'json_samples', filename), 'r') as f:
        content = f.read()
    return content


@pytest.fixture(scope='session')
def node_json():
    ''' A fixture that loads example node.json and returns its content'''
    return json.loads(_open_sample_file('node.json'))


@pytest.fixture(scope='session')
def volume_json():
    ''' A fixture that loads example node.json and returns its content'''
    return json.loads(_open_sample_file('volume.json'))


@pytest.fixture(scope='session')
def drive_json():
    ''' A fixture that loads example drive.json and returns its content'''
    return json.loads(_open_sample_file('drive.json'))


@pytest.fixture(scope='session')
def endpoint_json():
    ''' A fixture that loads example endpoint.json and returns its content'''
    return json.loads(_open_sample_file('endpoint.json'))


@pytest.fixture(scope='session')
def processor_json():
    ''' A fixture that loads example processor.json and returns its content'''
    return json.loads(_open_sample_file('processor.json'))


@pytest.fixture(scope='session')
def specfile_json_str():
    ''' A fixture that loads example specfile.json and returns its content'''
    return _open_sample_file('specfile.json')
