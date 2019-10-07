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
from oslo_utils import units

from units.compat import mock
from units.modules.utils import (AnsibleExitJson, AnsibleFailJson,
                                 set_module_args)
import units.modules.remote_management.rsd.utilities as rsd_utils


class TestRsdVolume():

    @pytest.fixture()
    def rsd_client_mock(self, mocker):
        return mocker.patch('ansible.modules.remote_management.rsd.rsd_volume.'
                            'cinder.volume.drivers.rsd.RSDClient')

    @pytest.fixture()
    def create_volume_mock(self, rsd_client_mock):
        return rsd_client_mock.return_value.create_volume

    @pytest.fixture()
    def create_volume_from_snap_mock(self, rsd_client_mock):
        return rsd_client_mock.return_value.create_volume_from_snap

    @pytest.fixture()
    def create_snapshot_mock(self, rsd_client_mock):
        return rsd_client_mock.return_value.create_snap

    @pytest.fixture()
    def delete_volume_mock(self, rsd_client_mock):
        return rsd_client_mock.return_value.delete_vol_or_snap

    @pytest.fixture()
    def extend_volume_mock(self, rsd_client_mock):
        return rsd_client_mock.return_value.extend_volume

    @pytest.fixture()
    def clone_volume_mock(self, rsd_client_mock):
        return rsd_client_mock.return_value.clone_volume

    @pytest.fixture()
    def get_volume_mock(self, rsd_client_mock):
        return rsd_client_mock.return_value._get_volume

    def _check_returned_output(self, result, volumes, changed=True):
        volume_elements = []
        for volume in volumes:
            replica_infos = []
            for replica_info in volume.replica_infos:
                replica_infos.append({
                    'ReplicaReadOnlyAccess':
                        replica_info.replica_readonly_access,
                    'ReplicaType': replica_info.replica_type,
                    'ReplicaRole': replica_info.replica_role,
                    'Replica': replica_info.replica})
            capacity_sources = []
            for capacity_source in volume.capacity_sources:
                providing_pools = []
                for providing_pool in capacity_source.providing_pools:
                    providing_pools.append({'Id': providing_pool.path})
                capacity_sources.append({'ProvidingPools': providing_pools})

            volume_element = \
                dict(Id=volume.identity,
                     Name=volume.name,
                     Description=volume.description,
                     Model=volume.model,
                     Manufacturer=volume.manufacturer,
                     AccessCapabilities=volume.access_capabilities,
                     CapacityBytes=volume.capacity_bytes,
                     AllocatedBytes=volume.allocated_Bytes,
                     CapacitySources=capacity_sources,
                     ReplicaInfos=replica_infos,
                     Status=dict(
                         Health=volume.status.health,
                         HealthRollup=volume.status.health_rollup,
                         State=volume.status.state),
                     URI=volume.path)
            volume_elements.append(volume_element)

        expected_result = dict(changed=changed, volumes=volume_elements)
        assert result == expected_result

    @pytest.fixture()
    def get_sample_volume(self, get_volume_mock, create_volume):
        mock_volume = create_volume(1)
        get_volume_mock.return_value = mock_volume
        return mock_volume, get_volume_mock

    def get_rsd_volume_args(self, state, resource_id=None, size=None,
                            resource_type='volume'):
        args = rsd_utils.get_common_args()
        args.update(dict(state=state, type=resource_type))
        if resource_id:
            args.update(dict(id=resource_id))
        if size:
            args.update(dict(size=size))
        return args

    def test_without_required_parameters(self, rsd_mock, rsd_volume):
        err_regex = 'missing required arguments: state'
        with pytest.raises(AnsibleFailJson, match=err_regex):
            set_module_args(rsd_utils.get_rsd_common_args())
            rsd_volume.main()

        rsd_mock.assert_not_called()

    def test_unsupported_rsd_version(self, factory_mock, rsd_volume,
                                     rsd_client_mock):
        factory_mock.return_value._rsd_api_version = '2.2.0'

        with pytest.raises(AnsibleFailJson, match='Unsupported RSD version'):
            set_module_args(self.get_rsd_volume_args('present', size=1))
            rsd_volume.main()

        rsd_client_mock.assert_not_called()

    def test_create_new_volume(self, factory_mock, rsd_volume,
                               create_volume_mock, get_sample_volume):

        mock_volume, get_volume_mock = get_sample_volume
        create_volume_mock.return_value = mock_volume.path

        with pytest.raises(AnsibleExitJson) as e:
            volume_size = 1
            set_module_args(self.get_rsd_volume_args('present',
                                                     size=volume_size))
            rsd_volume.main()

        create_volume_mock.assert_called_once_with(volume_size)
        get_volume_mock.assert_called_once_with(mock_volume.path)

        result = e.value.args[0]
        self._check_returned_output(result, [mock_volume], True)

    @pytest.mark.parametrize('volume_size', [
        # Create volume without extending it.
        None,
        # Create volume and extend it. Requested size matches current size.
        1,
        # Create volume and extend it. Requested size is greater than current
        # size.
        5,
    ])
    def test_create_volume_from_snap_and_extend(self, factory_mock, rsd_volume,
                                                create_volume_from_snap_mock,
                                                get_sample_volume,
                                                extend_volume_mock,
                                                volume_size):

        mock_volume, get_volume_mock = get_sample_volume
        # Set capacity of mock volume to 1 GiB
        mock_volume.capacity_bytes = 1 * units.Gi
        create_volume_from_snap_mock.return_value = mock_volume.path
        src_snap_url = '/redfish/v1/StorageServices/f9c7e17e-6682_1/Volumes/2'

        with pytest.raises(AnsibleExitJson) as e:
            set_module_args(self.get_rsd_volume_args('present',
                                                     size=volume_size,
                                                     resource_id=src_snap_url))
            rsd_volume.main()

        create_volume_from_snap_mock.assert_called_once_with(src_snap_url)
        get_volume_mock.assert_called_with(mock_volume.path)
        # Check if volume was resized if requested size was greater than
        # current volume size.
        if volume_size and \
           volume_size > (mock_volume.capacity_bytes / units.Gi):
            extend_volume_mock.assert_called_once_with(mock_volume.path,
                                                       volume_size)
        else:
            extend_volume_mock.assert_not_called()

        result = e.value.args[0]
        self._check_returned_output(result, [mock_volume], True)

    def test_create_volume_from_snap_extend_failed(self, factory_mock,
                                                   rsd_volume,
                                                   sushy_import_mock,
                                                   create_volume_from_snap_mock,
                                                   get_volume_mock,
                                                   extend_volume_mock,
                                                   delete_volume_mock):

        get_volume_mock.side_effect = \
            sushy_import_mock.exceptions.ResourceNotFoundError
        new_vol_url = '/redfish/v1/StorageServices/f9c7e17e-6682_1/Volumes/1'
        create_volume_from_snap_mock.return_value = new_vol_url
        src_snap_url = '/redfish/v1/StorageServices/f9c7e17e-6682_1/Volumes/2'
        volume_size = 1

        with pytest.raises(AnsibleFailJson,
                           match='Failed to create a volume with requested '
                                 'size'):
            set_module_args(self.get_rsd_volume_args('present',
                                                     size=volume_size,
                                                     resource_id=src_snap_url))
            rsd_volume.main()

        create_volume_from_snap_mock.assert_called_once_with(src_snap_url)
        get_volume_mock.assert_called_with(new_vol_url)
        extend_volume_mock.assert_not_called()
        delete_volume_mock.assert_called_once_with(new_vol_url)

    def test_create_snapshot(self, factory_mock, rsd_volume,
                             create_snapshot_mock,
                             get_sample_volume,
                             extend_volume_mock):

        mock_volume, get_volume_mock = get_sample_volume
        create_snapshot_mock.return_value = mock_volume.path
        get_volume_mock.return_value = mock_volume
        volume_url = '/redfish/v1/StorageServices/f9c7e17e-6682_1/Volumes/2'

        with pytest.raises(AnsibleExitJson) as e:
            set_module_args(self.get_rsd_volume_args('present',
                                                     resource_id=volume_url,
                                                     resource_type='snapshot'))
            rsd_volume.main()

        create_snapshot_mock.assert_called_once_with(volume_url)
        get_volume_mock.assert_called_with(mock_volume.path)

        result = e.value.args[0]
        self._check_returned_output(result, [mock_volume], True)

    def test_delete_volume(self, factory_mock, rsd_volume,
                           delete_volume_mock,
                           get_sample_volume,
                           extend_volume_mock):

        mock_volume, get_volume_mock = get_sample_volume
        get_volume_mock.return_value = mock_volume
        volume_url = '/redfish/v1/StorageServices/f9c7e17e-6682_1/Volumes/2'

        with pytest.raises(AnsibleExitJson) as e:
            set_module_args(self.get_rsd_volume_args('absent',
                                                     resource_id=volume_url))
            rsd_volume.main()

        delete_volume_mock.assert_called_once_with(volume_url, mock.ANY)
        get_volume_mock.assert_called_with(volume_url)

        result = e.value.args[0]
        self._check_returned_output(result, [mock_volume], True)

    def test_delete_invalid_resource(self, factory_mock, rsd_volume,
                                     delete_volume_mock, get_volume_mock,
                                     sushy_import_mock):

        get_volume_mock.side_effect = \
            sushy_import_mock.exceptions.ResourceNotFoundError
        volume_url = '/redfish/v1/StorageServices/f9c7e17e-6682_1/Volumes/2'

        with pytest.raises(AnsibleExitJson,
                           match='Invalid resource URI or resource already '
                                 'deleted') as e:
            set_module_args(self.get_rsd_volume_args('absent',
                                                     resource_id=volume_url))
            rsd_volume.main()

        get_volume_mock.assert_called_with(volume_url)
        delete_volume_mock.assert_not_called()

        result = e.value.args[0]
        assert not result['changed']
        assert result['volumes'][0]['URI'] == volume_url

    @pytest.mark.parametrize('volume_size, changed', [
        # Requested volume size matches current size.
        (1, False),
        # Requested volume size is greater than current size.
        (5, True)
    ])
    def test_extend_volume(self, factory_mock, rsd_volume,
                           get_sample_volume, extend_volume_mock,
                           volume_size, changed):

        mock_volume, get_volume_mock = get_sample_volume
        # Set capacity of mock volume to 1 GiB
        mock_volume.capacity_bytes = 1 * units.Gi
        get_volume_mock.return_value = mock_volume
        volume_url = '/redfish/v1/StorageServices/f9c7e17e-6682_1/Volumes/2'

        with pytest.raises(AnsibleExitJson) as e:
            set_module_args(self.get_rsd_volume_args('extended',
                                                     resource_id=volume_url,
                                                     size=volume_size))
            rsd_volume.main()

        get_volume_mock.assert_called_with(volume_url)
        if changed:
            extend_volume_mock.assert_called_once_with(volume_url, volume_size)
        else:
            extend_volume_mock.assert_not_called()

        result = e.value.args[0]
        self._check_returned_output(result, [mock_volume], changed)

    def test_extend_volume_size_lower_than_current(self, factory_mock,
                                                   rsd_volume,
                                                   get_sample_volume,
                                                   extend_volume_mock):

        mock_volume, get_volume_mock = get_sample_volume
        # Set capacity of mock volume to 1 GiB
        mock_volume.capacity_bytes = 2 * units.Gi
        # Make sure that requested volume size is lower than current size.
        volume_size = int((mock_volume.capacity_bytes / units.Gi) / 2)
        get_volume_mock.return_value = mock_volume
        volume_url = '/redfish/v1/StorageServices/f9c7e17e-6682_1/Volumes/2'

        with pytest.raises(AnsibleFailJson,
                           match='Requested volume size .* is lower than '
                                 'current volume size'):
            set_module_args(self.get_rsd_volume_args('extended',
                                                     resource_id=volume_url,
                                                     size=volume_size))
            rsd_volume.main()

        get_volume_mock.assert_called_with(volume_url)
        extend_volume_mock.assert_not_called()

    @pytest.mark.parametrize('volume_size', [
        # Clone volume without extending it.
        None,
        # Clone volume and extend it. Requested size matches current size.
        1,
        # Clone volume and extend it. Requested size is greater than current
        # size.
        5,
    ])
    def test_clone_volume(self, factory_mock, rsd_volume,
                          get_volume_mock,
                          clone_volume_mock,
                          volume_size,
                          extend_volume_mock,
                          create_volume):

        mock_volume = create_volume(0)
        # Set capacity of mock volume to 1 GiB
        mock_volume.capacity_bytes = 1 * units.Gi
        volume_url = mock_volume.path
        mock_snapshot = create_volume(1)
        snapshot_url = mock_snapshot.path
        # Sequence of returned volumes.
        # If size is specified _extend_volume() retrieves volume details to
        # determine whether it's necessary to extend the volume. We need to
        # accommodate for the extra call to _get_volume().
        if volume_size:
            mock_volumes = [mock_volume, mock_volume, mock_snapshot]
        else:
            mock_volumes = [mock_volume, mock_snapshot]
        get_volume_mock.side_effect = mock_volumes
        clone_volume_mock.return_value = (volume_url, snapshot_url)
        source_vol_url = \
            '/redfish/v1/StorageServices/f9c7e17e-6682_1/Volumes/3'

        with pytest.raises(AnsibleExitJson) as e:
            set_module_args(self.get_rsd_volume_args('cloned',
                                                     resource_id=source_vol_url,
                                                     size=volume_size))
            rsd_volume.main()

        clone_volume_mock.assert_called_once_with(source_vol_url)
        # Check if volume was resized if requested size was greater than
        # current volume size.
        if volume_size and \
           volume_size > (mock_volume.capacity_bytes / units.Gi):
            extend_volume_mock.assert_called_once_with(volume_url, volume_size)
        else:
            extend_volume_mock.assert_not_called()
        get_volume_mock.assert_has_calls([
            mock.call(volume_url), mock.call(snapshot_url)])

        result = e.value.args[0]
        self._check_returned_output(
            result, [mock_volume, mock_snapshot], True)

    def test_clone_volume_extend_failed(self, factory_mock, rsd_volume,
                                        get_volume_mock,
                                        clone_volume_mock,
                                        extend_volume_mock,
                                        create_volume,
                                        sushy_import_mock):

        get_volume_mock.side_effect = \
            sushy_import_mock.exceptions.ResourceNotFoundError
        mock_volume = create_volume(0)
        volume_url = mock_volume.path
        mock_snapshot = create_volume(1)
        snapshot_url = mock_snapshot.path
        clone_volume_mock.return_value = (volume_url, snapshot_url)
        source_vol_url = \
            '/redfish/v1/StorageServices/f9c7e17e-6682_1/Volumes/3'
        volume_size = 1

        with pytest.raises(AnsibleFailJson,
                           match='Failed to clone a volume with requested size'):
            set_module_args(self.get_rsd_volume_args('cloned',
                                                     resource_id=source_vol_url,
                                                     size=volume_size))
            rsd_volume.main()

        clone_volume_mock.assert_called_once_with(source_vol_url)
        extend_volume_mock.assert_not_called()
        get_volume_mock.assert_called_once_with(volume_url)
