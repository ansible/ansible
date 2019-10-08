#!/usr/bin/python
# -*- coding: utf-8 -*-

#######################################################
# Copyright (c) 2019 Intel Corporation. All rights reserved.
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Authors:
#   - Przemyslaw Szczerbik - <przemyslawx.szczerbik@intel.com>
#######################################################

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: rsd_volume

short_description: Manage RSD volumes and snapshots

version_added: "2.10"

description:
    - rsd_volume module manages Rack Scale Design volumes and snapshots.
    - 'Supported operations include: create/delete/clone/extend volume and
       create/delete snapshot.'

options:
    state:
        description:
            - This option is used to specify an operation to be performed.
            - I(state=present), is used to create a volume or a snapshot
              depending on value of I(type) option. Operation is not idempotent
              and will always result in a creation of new volume.
              Snapshot creation requires source volume to be specified with
              I(id) option.
              In case of volume creation, I(id) option can be used to specify
              source snapshot from which volume will be created. By default,
              size of new volume will be equal to the size of the snapshot.
              However, if I(size) option is specified as well, new volume will
              be extended to the requested size.
              If volume is not being created from a snapshot, I(size) option
              is required.
            - I(state=absent), is used to delete a volume or a snapshot.
              Resource to be deleted must be specified with I(id) option.
            - I(state=extended), is used to extend the size of a volume. If
              requested size is smaller than current size, operation will fail.
              Volume that should be modified, must be specified with I(id)
              option. Requires I(size) option.
            - I(state=cloned), is used to clone a volume. Requires I(id) and
              I(size) options.
        required: true
        type: str
        choices: [present, absent, extended, cloned]
    type:
        description:
            - Type of a resource to be created. Required if I(state=present).
              Defaults to C(volume).
        type: str
        choices: [volume, snapshot]
        default: volume
    id:
      description:
          - URI of a resource that will be affected. Required if
            I(state=absent), I(state=extended) or I(state=cloned).
      type: str
    size:
        description:
            - Size of a volume in GiB.
        type: int

extends_documentation_fragment:
    - rsd

requirements:
    - 'L(cinder, https://opendev.org/openstack/cinder) >=
      commit: cf0f5daad8'
    - enum34

author:
    - Przemyslaw Szczerbik (@pszczerx)

notes:
    - Due to the nature of the PODM API, check mode cannot be supported.
    - For the same reason the module is not idempotent at the moment, since any
      result depends on decisions actually made by PODM.
    - The Module requires RSD version v2.3+. Certain operations such as clone
      volume, create/delete snapshot, create volume from snapshot and extend
      volume require RSD v2.4+.
'''

EXAMPLES = '''
- name: Create volume
  rsd_volume:
    state: present
    size: 1

- name: Create snapshot
  rsd_volume:
    state: present
    type: snapshot
    id: "/redfish/v1/StorageServices/0/Volumes/1"

- name: Create volume from snapshot
  rsd_volume:
    state: present
    type: volume
    id: "/redfish/v1/StorageServices/0/Volumes/1"

- name: Delete volume or snapshot
  rsd_volume:
    state: absent
    id: "/redfish/v1/StorageServices/0/Volumes/1"

- name: Extend volume
  rsd_volume:
    state: extended
    id: "/redfish/v1/StorageServices/0/Volumes/1"
    size: 2

- name: Clone volume
  rsd_volume:
    state: cloned
    id: "/redfish/v1/StorageServices/0/Volumes/1"
'''

RETURN = '''
---
volumes:
    description: List of affected volumes or snapshots
    returned: On success
    type: list
    contains:
            volume:
                type: complex
                description: Volume details
                contains:
                    Id:
                        description: Volume identity
                        type: str
                    Description:
                        description: Volume description
                        type: str
                    Name:
                        description: Volume name
                        type: str
                    Model:
                        description: Assigned by the manufacturer. Represents a
                                     specific storage volume implementation.
                    Manufacturer:
                        description: Represents the manufacturer or implementer
                                     of the storage volume.
                    AccessCapabilities:
                        description: Represents current storage access
                                     capability.
                        type: list
                    CapacityBytes:
                        description: Size in bytes of the associated volume.
                    AllocatedBytes:
                        description: Allocated capacity of the volume in bytes.
                    CapacitySources:
                        description: Capacity allocation information from a
                                     named source resource.
                        type: list
                        ProvidingPools:
                            description: Reference to a contributing storage
                                         pool.
                            type: complex
                            Id:
                                description: ProvidingPool URI
                    ReplicaInfos:
                        description: Represents the replica relationship
                                     between this storage volume and a
                                     corresponding source and/or target volume.
                        type: list
                        ReplicaReadOnlyAccess:
                            description: Specifies whether the source, the
                                         target, or both elements are read
                                         only to the host.
                        ReplicaType:
                            description: Represents the intended outcome of
                                         the replication.
                        ReplicaRole:
                            description: Represents the source or target role
                                         of this replica.
                        Replica:
                            description: Reference to the source of this
                                         replica.
                    Status:
                        description: Volume Status
                        type: complex
                        Health:
                            description: Represents the health state of this
                                         resource in the absence of its
                                         dependent resources.
                        HealthRollup:
                            description: Represents overall health state from
                                         the view of this resource.
                        State:
                            description: Indicates the know state of the
                                         resource.
                    URI:
                        description: Volume Uniform Resource Identifier
'''

from ansible.module_utils.remote_management.rsd.rsd_common import RSD
from ansible.module_utils.basic import missing_required_lib

from collections import defaultdict
from functools import partial
from distutils.version import LooseVersion
import traceback
from enum import Enum, unique

try:
    import cinder.volume.drivers.rsd
    import cinder.exception
    from sushy import exceptions as sushy_exception
    from oslo_utils import units
    HAS_CINDER = True
    CINDER_IMP_ERR = None
except ImportError:
    HAS_CINDER = False
    CINDER_IMP_ERR = traceback.format_exc()


class RsdVolume(RSD):

    @unique
    class TYPE(Enum):
        VOLUME = 'volume'
        SNAPSHOT = 'snapshot'

        @classmethod
        def allowed_module_args(cls):
            return (
                cls.VOLUME.value,
                cls.SNAPSHOT.value
            )

    @unique
    class STATE(Enum):
        PRESENT = 'present'
        ABSENT = 'absent'
        EXTENDED = 'extended'
        CLONED = 'cloned'

        @classmethod
        def allowed_module_args(cls):
            return (
                cls.PRESENT.value,
                cls.ABSENT.value,
                cls.EXTENDED.value,
                cls.CLONED.value
            )

    def __init__(self):
        required_if = [
            ['state', self.STATE.PRESENT.value, ['id', 'size'], True],
            ['type', self.TYPE.SNAPSHOT.value, ['id']],
            ['state', self.STATE.ABSENT.value, ['id']],
            ['state', self.STATE.EXTENDED.value, ['id', 'size']],
            ['state', self.STATE.CLONED.value, ['id']],
        ]

        argument_spec = dict(
            state=dict(
                type='str',
                required=True,
                choices=self.STATE.allowed_module_args()
            ),
            type=dict(
                type='str',
                choices=self.TYPE.allowed_module_args(),
                default=self.TYPE.VOLUME.value
            ),
            # Override 'id' parameter from rsd_common
            id=dict(
                type='str',
            ),
            size=dict(
                type='int',
            )
        )

        super(RsdVolume, self).__init__(argument_spec, required_if=required_if)

    def _check_rsd_version(self, version, extra_err_msg=''):
        if LooseVersion(self.rsd._rsd_api_version) < LooseVersion(version):
            err_msg = extra_err_msg + \
                "Unsupported RSD version: {0} < {1}.".format(
                    self.rsd._rsd_api_version, version)
            self.module.fail_json(msg=err_msg)

    def _connect(self, podm_info, auth_info):

        if not HAS_CINDER:
            self.module.fail_json(msg=missing_required_lib(
                'cinder', url='https://opendev.org/openstack/cinder'),
                exception=CINDER_IMP_ERR)
        super(RsdVolume, self)._connect(podm_info, auth_info)

        # Module requires at least RSD v2.3+
        self._check_rsd_version("2.3.0")

        self.rsd_client = cinder.volume.drivers.rsd.RSDClient(self.rsd)

    def _dispatch(self, state, params):
        resource_type = self.module.params['type']
        # Optional parameters
        size_gb = self.module.params.get('size', None)
        resource = self.module.params.get('id', None)

        # Register default handler
        handlers = defaultdict(
            lambda: self.module.fail_json(msg="Invalid 'state' option."))

        handlers[self.STATE.PRESENT.value] = \
            partial(self._create_handler, resource_type, size_gb, resource)
        handlers[self.STATE.ABSENT.value] = \
            partial(self._delete_handler, resource)
        handlers[self.STATE.EXTENDED.value] = \
            partial(self._extend_handler, resource, size_gb)
        handlers[self.STATE.CLONED.value] = \
            partial(self._clone_handler, resource, size_gb)

        try:
            handlers[state]()
        except (cinder.exception.VolumeBackendAPIException,
                sushy_exception.ResourceNotFoundError) as e:
            self.module.fail_json(msg="Operation failed: {0}".format(str(e)))

    def _return_response(self, resources, changed=True):
        response = []
        for resource in resources:
            # Get Volume object if URI was passed
            if isinstance(resource, str):
                volume = self.rsd_client._get_volume(resource)
            else:
                volume = resource

            replica_infos = []
            for replica_info in volume.replica_infos:
                replica_infos.append({
                    'ReplicaReadOnlyAccess':
                        replica_info.replica_readonly_access,
                    'ReplicaType': replica_info.replica_type,
                    'ReplicaRole': replica_info.replica_role,
                    'Replica': replica_info.replica
                })

            capacity_sources = []
            for capacity_source in volume.capacity_sources:
                providing_pools = []
                for providing_pool in capacity_source.providing_pools:
                    providing_pools.append({'Id': providing_pool.path})
                capacity_sources.append({'ProvidingPools': providing_pools})

            response_element = {
                'Id': volume.identity,
                'Description': volume.description,
                'Name': volume.name,
                'Model': volume.model,
                'Manufacturer': volume.manufacturer,
                'AccessCapabilities': volume.access_capabilities,
                'CapacityBytes': volume.capacity_bytes,
                'AllocatedBytes': volume.allocated_Bytes,
                'CapacitySources': capacity_sources,
                'ReplicaInfos': replica_infos,
                'Status': {
                    'Health': volume.status.health,
                    'HealthRollup': volume.status.health_rollup,
                    'State': volume.status.state
                },
                'URI': volume.path
            }

            response.append(response_element)

        self.module.exit_json(changed=changed, volumes=response)

    def _create_volume(self, size_gb, snapshot_url=None):
        if not size_gb and not snapshot_url:
            self.module.fail_json(
                msg="'Size' parameter must be specified to create new volume.")

        if snapshot_url:
            self._check_rsd_version("2.4.0",
                                    "Create volume from snapshot failed.")
            # Even though create_volume_from_snap() allows to specify volume
            # size, we can't do that. RSD API will fail if volume size is
            # greater than snapshot size. However, volume can be extended after
            # it had been created.
            vol_url = self.rsd_client.create_volume_from_snap(snapshot_url)
            if size_gb:
                try:
                    self._extend_volume(vol_url, size_gb)
                except (cinder.exception.VolumeBackendAPIException,
                        sushy_exception.ResourceNotFoundError) as e:
                    # Extending volume failed. Clean up and report a failure.
                    self.rsd_client.delete_vol_or_snap(vol_url)
                    self.module.fail_json(
                        msg="Failed to create a volume with requested size: "
                            "{0}".format(str(e)))
            return vol_url
        else:
            return self.rsd_client.create_volume(size_gb)

    def _create_snapshot(self, volume_url):
        self._check_rsd_version("2.4.0", "Create snapshot failed.")
        if not volume_url:
            self.module.fail_json(
                msg="Source volume must be provided to create a snapshot.")
        return self.rsd_client.create_snap(volume_url)

    def _create_handler(self, resource_type, size_gb, src_resource_url=None):

        if resource_type == self.TYPE.VOLUME.value:
            resource_url = self._create_volume(size_gb, src_resource_url)
        elif resource_type == self.TYPE.SNAPSHOT.value:
            resource_url = self._create_snapshot(src_resource_url)

        self._return_response([resource_url])

    def _delete_handler(self, resource_url):
        try:
            # We need to return details of affected resource to Ansible.
            # Since we are deleting it, we have to query API for volume details
            # before sending delete request.
            volume = self.rsd_client._get_volume(resource_url)

            # capacity_sources and providing_pools properties are calculated
            # once when queried for the first time. Since those properties are
            # used later on to generate a response, we need to query them
            # before deletion to avoid an error.
            for capacity_source in volume.capacity_sources:
                unused = capacity_source.providing_pools  # noqa: F841

            self.rsd_client.delete_vol_or_snap(resource_url, volume.name)
            self._return_response([volume])
        except sushy_exception.ResourceNotFoundError:
            self.module.exit_json(
                changed=False, volumes=[{'URI': resource_url}],
                msg='Invalid resource URI or resource already deleted.')

    def _extend_volume(self, volume_url, size_gb):
        changed = False
        size_bytes = size_gb * units.Gi
        volume = self.rsd_client._get_volume(volume_url)

        if size_bytes < volume.capacity_bytes:
            self.module.fail_json(
                msg="Requested volume size '{0}' is lower than current volume "
                    "size '{1}'.".format(size_bytes, volume.capacity_bytes))
        elif size_bytes > volume.capacity_bytes:
            self.rsd_client.extend_volume(volume_url, size_gb)
            volume.refresh()
            changed = True
        return volume, changed

    def _extend_handler(self, volume_url, size_gb):
        self._check_rsd_version("2.4.0", "Extend volume failed.")

        volume, changed = self._extend_volume(volume_url, size_gb)
        self._return_response([volume], changed)

    def _clone_handler(self, src_volume_url, size_gb):
        self._check_rsd_version("2.4.0", "Clone volume failed.")
        # Even though clone_volume() allows to specify volume size, we can't do
        # that. RSD API will fail if volume size is greater than snapshot size.
        # However, volume can be extended after it had been created.
        vol_url, snap_url = self.rsd_client.clone_volume(src_volume_url)
        if size_gb:
            try:
                self._extend_volume(vol_url, size_gb)
            except (cinder.exception.VolumeBackendAPIException,
                    sushy_exception.ResourceNotFoundError) as e:
                # Extending volume failed. Clean up and report a failure.
                self.rsd_client.delete_vol_or_snap(vol_url)
                self.rsd_client.delete_vol_or_snap(snap_url)
                self.module.fail_json(
                    msg="Failed to clone a volume with requested size: {0}"
                        .format(str(e)))
        self._return_response([vol_url, snap_url])

    def run(self):
        state = self.module.params['state']
        self._dispatch(state, self.module.params)


def main():
    rsd_volume = RsdVolume()
    rsd_volume.run()


if __name__ == '__main__':
    main()
