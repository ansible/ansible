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

from units.compat import mock
from units.modules.utils import set_module_args, AnsibleExitJson, \
    AnsibleFailJson
import units.modules.remote_management.rsd.utilities as rsd_utils

import json
import pytest


class TestRsdNodeCompose():

    @pytest.fixture()
    def open_specfile_mock(self, mocker, specfile_json_str):
        ''' A fixture that mocks open() function to return specfile_json_str'''
        specfile_mock = mocker.mock_open(read_data=specfile_json_str)
        try:
            # Python 2.7
            return mocker.patch('__builtin__.open', specfile_mock, create=True)
        except ImportError:
            # Python 3.x
            return mocker.patch('builtins.open', specfile_mock, create=True)

    def get_rsd_compose_args(self, state, id_type='identity'):
        args = rsd_utils.get_rsd_common_args(id_type=id_type)
        args.update(dict(state=state))
        return args

    def get_rsd_compose_args_specfile(self, state, specfile):
        args = rsd_utils.get_common_args()
        args.update(dict(state=state, specfile=specfile))
        return args

    def get_rsd_compose_args_spec(self, state):
        args = rsd_utils.get_common_args()
        spec = dict(
            name='TestNode0',
            description='Node #0',
            processors=[{"ProcessorType": "CPU", "AchievableSpeedMHz": 3000}],
            memory=[{"CapacityMiB": 16000, "MemoryDeviceType": "DDR3"}],
            remote_drives=[{"CapacityGiB": 80, "Protocol": "iSCSI"}],
            local_drives=[{"CapacityGiB": 100, "Type": "HDD"}],
            eth_ifaces=[{"SpeedMbps": 1000, "PrimaryVLAN": 100}],
            security=dict(TpmPresent=True),
            total_cores=2,
            total_mem=4096)
        args.update(dict(state=state, spec=spec))
        return args

    def test_without_required_parameters(self, rsd_mock, rsd_compose):
        with pytest.raises(
                AnsibleFailJson,
                match='one of the following is required: id, spec, specfile'):
            set_module_args({})
            rsd_compose.main()

        rsd_mock.assert_not_called()

    def test_delete_node_resource_not_found(self, sushy_import_mock,
                                            rsd_compose, get_node_mock,
                                            get_members_mock):
        get_node_mock.side_effect = sushy_import_mock.exceptions.ResourceNotFoundError
        with pytest.raises(
                AnsibleFailJson,
                match='There is no node with such ID'):
            args = self.get_rsd_compose_args('absent', 'identity')
            set_module_args(args)
            rsd_compose.main()

        node_endpoint = \
            rsd_utils.RSD_NODES_ENDPOINT + args['id']['value']
        get_node_mock.assert_called_with(node_endpoint)
        get_members_mock.assert_not_called()

    def test_delete_node_in_allocating_state_wait_transition_timeout(
            self, get_sample_node, get_members_mock, rsd_compose):
        mock_node, get_node_mock = get_sample_node('allocating')

        err_msg_regex = 'Cannot delete node in \'(allocating|assembling)\' state'
        with pytest.raises(AnsibleFailJson, match=err_msg_regex):
            args = self.get_rsd_compose_args('absent', 'identity')
            set_module_args(args)
            rsd_compose.main()

        node_endpoint = \
            rsd_utils.RSD_NODES_ENDPOINT + args['id']['value']
        get_node_mock.assert_called_with(node_endpoint)
        get_members_mock.assert_not_called()
        mock_node.refresh.assert_called_with()
        mock_node.delete_node.assert_not_called()

    @pytest.mark.parametrize(
        'node_state_transition',
        [(['allocating', 'allocated']),
         (['assembling', 'assembling', 'assembled'])])
    def test_delete_node_successful(self, get_sample_node,
                                    get_members_mock, rsd_compose,
                                    node_state_transition):
        mock_node, get_node_mock = get_sample_node(node_state_transition)

        with pytest.raises(AnsibleExitJson, match='Node deleted') as e:
            args = self.get_rsd_compose_args('absent', 'identity')
            set_module_args(args)
            rsd_compose.main()

        node_endpoint = \
            rsd_utils.RSD_NODES_ENDPOINT + args['id']['value']
        get_node_mock.assert_called_with(node_endpoint)
        get_members_mock.assert_not_called()
        mock_node.refresh.assert_called_with()
        mock_node.delete_node.assert_called_once_with()

        # Check return values
        result = e.value.args[0]
        assert result['changed']

    @staticmethod
    def _check_returned_output(result, node, system, changed=True):
        '''Asserts that result matches expected values

        :param result: Dictionary returned by Ansible after module exit.
        :param node: Mock node.
        :param system: Mock system.
        :param changed: Boolean value. Used to assert value of
                        result['changed']. Defaults to True.
        '''
        # TODO: Uncomment when rsd_compose module is going to retrieve
        # interfaces information.
        # eth_iface_mock = system.ethernet_interfaces.get_member.return_value
        # mock_eth_iface = dict(
        #     Name=eth_iface_mock.name,
        #     Description=eth_iface_mock.description,
        #     Id=eth_iface_mock.identity,
        #     MACAddress=eth_iface_mock.mac_address,
        #     IPv4Addresses=[a.address for a in eth_iface_mock.ipv4_addresses],
        #     IPv6Addresses=[a.address for a in eth_iface_mock.ipv6_addresses])
        mock_system = dict(
            Name=system.name,
            Description=system.description,
            Id=system.identity,
            ProcessorSummary=dict(
                Count=system.processor_summary.count,
                Model=system.processor_summary.model),
            TotalSystemMemoryGiB=system.memory_summary.total_system_memory_gib)

        expected_result = dict(changed=changed,
                               node=dict(Id=node.identity,
                                         Name=node.name,
                                         Description=node.description,
                                         UUID=node.uuid,
                                         ComposedNodeState=node.composed_node_state,
                                         PowerState=node.power_state,
                                         Status=dict(
                                             State=node.status.state,
                                             Health=node.status.health),
                                         Details=dict(
                                             System=mock_system,
                                             # TODO: Uncomment when rsd_compose
                                             # module is going to retrieve
                                             # interfaces information.
                                             # Interfaces=[mock_eth_iface],
                                         )))
        assert result == expected_result

    def test_assemble_node_successful(self,
                                      get_sample_nodes_collection_members,
                                      get_sample_system,
                                      get_node_mock, rsd_compose):
        mock_nodes, get_members_mock = get_sample_nodes_collection_members(
            3, ['allocating', 'allocated', 'assembled'])
        # First node is going to be selected from node collection because its
        # name matches RSD_ASSEMBLE_NODE_ARGS
        mock_node = mock_nodes[0]
        mock_system, get_system_mock = get_sample_system

        with pytest.raises(AnsibleExitJson) as e:
            set_module_args(self.get_rsd_compose_args('assembled', 'name'))
            rsd_compose.main()

        # Check return values
        result = e.value.args[0]
        TestRsdNodeCompose._check_returned_output(result, mock_node,
                                                  mock_system)

        get_members_mock.assert_called_with()
        get_node_mock.assert_not_called()
        mock_node.refresh.assert_called_with()
        mock_node.assemble_node.assert_called_once_with()
        get_system_mock.assert_called_once_with(
            mock_node.links.computer_system)

    def test_assemble_node_already_in_desired_state(
            self, get_sample_nodes_collection_members, get_sample_system,
            get_node_mock, rsd_compose):
        mock_nodes, get_members_mock = get_sample_nodes_collection_members(
            3, ['allocating', 'assembled'])
        # First node is going to be selected from node collection because its
        # name matches RSD_ASSEMBLE_NODE_ARGS
        mock_node = mock_nodes[0]
        mock_system, get_system_mock = get_sample_system

        with pytest.raises(AnsibleExitJson) as e:
            set_module_args(self.get_rsd_compose_args('assembled', 'name'))
            rsd_compose.main()

        # Check return values
        result = e.value.args[0]
        TestRsdNodeCompose._check_returned_output(result, mock_node,
                                                  mock_system, False)

        get_members_mock.assert_called_with()
        get_node_mock.assert_not_called()
        mock_node.refresh.assert_called_with()
        mock_node.assemble_node.assert_not_called()
        get_system_mock.assert_called_once_with(
            mock_node.links.computer_system)

    @pytest.mark.parametrize(
        'node_state_transition, err_msg',
        [(['allocated', 'failed'], 'Failed to assemble node'),
         (['allocated', 'absent'], 'cannot assemble'),
         (['failed'], 'Cannot assemble node in \'Failed\' state')])
    def test_assemble_node_unsuccessful(self,
                                        get_sample_nodes_collection_members,
                                        get_node_mock, rsd_compose,
                                        node_state_transition, err_msg):
        mock_nodes, get_members_mock = get_sample_nodes_collection_members(
            1, node_state_transition)
        # First node is going to be selected from node collection because its
        # name matches RSD_ASSEMBLE_NODE_ARGS
        mock_node = mock_nodes[0]

        with pytest.raises(AnsibleFailJson, match=err_msg):
            set_module_args(self.get_rsd_compose_args('assembled', 'name'))
            rsd_compose.main()

        get_members_mock.assert_called_with()
        get_node_mock.assert_not_called()

        # Node is going to be assembled only if its in 'allocated' state.
        if 'allocated' in node_state_transition:
            mock_node.assemble_node.assert_called_once_with()
            mock_node.refresh.assert_called_once_with()

    def test_allocate_new_node_specfile(self, rsd_compose,
                                        get_node_collection_mock,
                                        get_sample_node, get_sample_system,
                                        specfile_json_str,
                                        open_specfile_mock):
        mock_nodes = mock.MagicMock()
        node_uri = rsd_utils.RSD_NODE_URL
        mock_nodes.compose_node.return_value = node_uri
        get_node_collection_mock.return_value = mock_nodes
        mock_node, get_node_mock = get_sample_node('allocated')
        mock_system, get_system_mock = get_sample_system

        with pytest.raises(AnsibleExitJson) as e:
            args = self.get_rsd_compose_args_specfile('allocated',
                                                      'specfile.json')
            set_module_args(args)
            rsd_compose.main()

        # Asserts for _parse_node_specfile()
        filename = args['specfile']
        open_specfile_mock.assert_called_once_with(filename, 'r')

        # Asserts for _do_allocate_node()
        get_node_collection_mock.assert_called_once_with()
        spec = json.loads(specfile_json_str)
        mock_nodes.compose_node.assert_called_once_with(
            description=spec['Description'],
            name=spec['Name'],
            processor_req=spec['Processors'],
            memory_req=spec['Memory'],
            remote_drive_req=spec['RemoteDrives'],
            local_drive_req=spec['LocalDrives'],
            ethernet_interface_req=spec['EthernetInterfaces'],
            security_req=spec['Security'],
            total_system_core_req=spec['TotalSystemCoreCount'],
            total_system_memory_req=spec['TotalSystemMemoryMiB'])
        get_node_mock.assert_called_once_with(node_uri)
        mock_node.refresh.assert_called_with()

        # Asserts for _return_ok_node_response()
        get_system_mock.assert_called_once_with(
            mock_node.links.computer_system)

        # Check return values
        result = e.value.args[0]
        TestRsdNodeCompose._check_returned_output(result, mock_node,
                                                  mock_system, True)

    def test_allocate_new_node_specfile_not_a_json_file(self, rsd_compose):

        with pytest.raises(ValueError,
                           match='File must end with .json extension'):
            set_module_args(
                self.get_rsd_compose_args_specfile('allocated',
                                                   'not_a_json_file.sh'))
            rsd_compose.main()

    def test_allocate_new_node_spec(self, rsd_compose,
                                    get_node_collection_mock,
                                    get_sample_system, get_sample_node,
                                    open_specfile_mock):
        mock_nodes = mock.MagicMock()
        node_uri = rsd_utils.RSD_NODE_URL
        mock_nodes.compose_node.return_value = node_uri
        get_node_collection_mock.return_value = mock_nodes
        mock_node, get_node_mock = get_sample_node('allocated')
        mock_system, get_system_mock = get_sample_system

        with pytest.raises(AnsibleExitJson) as e:
            args = self.get_rsd_compose_args_spec('allocated')
            set_module_args(args)
            rsd_compose.main()

        # Asserts for _parse_node_specfile()
        open_specfile_mock.assert_not_called()

        # Asserts for _do_allocate_node()
        get_node_collection_mock.assert_called_once_with()
        spec = args['spec']
        mock_nodes.compose_node.assert_called_once_with(
            description=spec['description'],
            name=spec['name'],
            processor_req=spec['processors'],
            memory_req=spec['memory'],
            remote_drive_req=spec['remote_drives'],
            local_drive_req=spec['local_drives'],
            ethernet_interface_req=spec['eth_ifaces'],
            security_req=spec['security'],
            total_system_core_req=spec['total_cores'],
            total_system_memory_req=spec['total_mem'])
        get_node_mock.assert_called_once_with(node_uri)
        mock_node.refresh.assert_called_with()

        # Asserts for _return_ok_node_response()
        get_system_mock.assert_called_once_with(
            mock_node.links.computer_system)

        # Check return values
        result = e.value.args[0]
        TestRsdNodeCompose._check_returned_output(result, mock_node,
                                                  mock_system, True)

    def test_allocate_and_assemble_new_node(self, rsd_compose,
                                            get_node_collection_mock,
                                            get_sample_node,
                                            get_sample_system,
                                            specfile_json_str,
                                            open_specfile_mock):
        mock_nodes = mock.MagicMock()
        node_uri = rsd_utils.RSD_NODE_URL
        mock_nodes.compose_node.return_value = node_uri
        get_node_collection_mock.return_value = mock_nodes
        mock_node, get_node_mock = get_sample_node(['allocated', 'allocated',
                                                    'assembled'])
        mock_system, get_system_mock = get_sample_system

        with pytest.raises(AnsibleExitJson) as e:
            args = self.get_rsd_compose_args_specfile('assembled',
                                                      'specfile.json')
            set_module_args(args)
            rsd_compose.main()

        # Asserts for _parse_node_specfile()
        filename = args['specfile']
        open_specfile_mock.assert_called_once_with(filename, 'r')

        # Asserts for _do_allocate_node()
        get_node_collection_mock.assert_called_once_with()
        spec = json.loads(specfile_json_str)
        mock_nodes.compose_node.assert_called_once_with(
            description=spec['Description'],
            name=spec['Name'],
            processor_req=spec['Processors'],
            memory_req=spec['Memory'],
            remote_drive_req=spec['RemoteDrives'],
            local_drive_req=spec['LocalDrives'],
            ethernet_interface_req=spec['EthernetInterfaces'],
            security_req=spec['Security'],
            total_system_core_req=spec['TotalSystemCoreCount'],
            total_system_memory_req=spec['TotalSystemMemoryMiB'])
        get_node_mock.assert_called_once_with(node_uri)

        # Asserts for _do_assemble_node()
        mock_node.assemble_node.assert_called_once_with()
        mock_node.refresh.assert_called_with()

        # Asserts for _return_ok_node_response()
        get_system_mock.assert_called_once_with(
            mock_node.links.computer_system)

        # Check return values
        result = e.value.args[0]
        TestRsdNodeCompose._check_returned_output(result, mock_node,
                                                  mock_system, True)
