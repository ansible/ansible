#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2017, Netservers Ltd. <support@netservers.co.uk>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_storage_pool
short_description: Manages Primary Storage Pools on Apache CloudStack based clouds.
description:
    - Create and remove storage pools.
    - Updates are only possible on enabled, tags, capacity_bytes and capacity_iops.
version_added: "2.4"
author: "Netservers Ltd. (@netservers)"
options:
  name:
    description:
      - Pool name.
    required: true
  zone:
    description:
      - Zone name.
    required: true
  storage_url:
    description:
      - Storage URL.
  pod:
    description:
      - Pod name.
  cluster:
    description:
      - Cluster name.
  scope:
    description:
      - The scope of the storage [cluster or zone]
      - Defaults to cluster when provided, otherwise zone
  hypervisor:
    description:
      - Required when creating a Zone scoped pool. [KVM, VMware]
  tags:
    description:
      - Tags associated with this pool
  provider:
    description:
      - Storage provider name [SolidFire, SolidFireShared, DefaultPrimary, CloudByte]
    default: 'DefaultPrimary'
  capacity_bytes:
    description:
      - Bytes CloudStack can provision from this storage pool
  capacity_iops:
    description:
      - Bytes CloudStack can provision from this storage pool
  url:
    description:
      - URL for the cluster
  username:
    description:
      - Username for the cluster
  password:
    description:
      - Password for the cluster
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# Ensure a Zone scoped storage_pool is present
- local_action:
    module: cs_storage_pool
    zone: zone01
    storage_url: rbd://admin:SECRET@ceph-mons.domain/poolname
    provider: DefaultPrimary
    name: Ceph RBD
    scope: ZONE
    hypervisor: KVM

# Ensure a Cluster scoped storage_pool is present
- local_action:
    module: cs_storage_pool
    zone: zone01
    cluster: cluster01
    storage_url: rbd://admin:SECRET@ceph-the-mons.domain/poolname
    provider: DefaultPrimary
    name: Ceph RBD
    scope: CLUSTER

# Ensure a storage_pool is absent
- local_action:
    module: cs_storage_pool
    name: Ceph RBD
    state: absent
'''

RETURN = '''
---
id:
    description: UUID of the pool.
    returned: success
    type: string
    sample: a3fca65a-7db1-4891-b97c-48806a978a96
capacity_iops:
    description: IOPS CloudStack can provision from this storage pool
    returned: when available
    type: int
    sample: 60000
zone_id:
    description: UUID of the zone.
    returned: success
    type: string
    sample: a3fca65a-7db1-4891-b97c-48806a978a96
zone:
    description: The name of the zone.
    returned: success
    type: string
    sample: Zone01
cluster_id:
    description: UUID of the cluster.
    returned: when scope is cluster
    type: string
    sample: a3fca65a-7db1-4891-b97c-48806a978a96
cluster:
    description: The name of the cluster.
    returned: when scope is cluster
    type: string
    sample: Cluster01
pod_id:
    description: UUID of the pod.
    returned: when scope is cluster
    type: string
    sample: a3fca65a-7db1-4891-b97c-48806a978a96
pod:
    description: The name of the pod.
    returned: when scope is cluster
    type: string
    sample: Cluster01
disk_size_allocated:
    description: The pool's currently allocated disk space
    returned: success
    type: int
    sample: 2443517624320
disk_size_total:
    description: The total size of the pool
    returned: success
    type: int
    sample: 3915055693824
disk_size_used:
    description: The pool's currently used disk size
    returned: success
    type: int
    sample: 1040862622180
scope:
    description: "The scope of the storage pool [ZONE / CLUSTER]"
    returned: success
    type: string
    sample: CLUSTER
state:
    description: The state of the storage pool
    returned: success
    type: string
    sample: Up
tags:
    description: the Tags for the storage pool
    returned: success
    type: list
    sample: rbd
'''

# import cloudstack common
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    CloudStackException,
    cs_argument_spec,
    cs_required_together,
)


class AnsibleCloudStackStoragePool(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackStoragePool, self).__init__(module)
        self.returns = {
            'id': 'id',
            'capacityiops': 'capacity_iops',
            'podname': 'pod',
            'clustername': 'cluster',
            'disksizeallocated': 'disk_size_allocated',
            'disksizetotal': 'disk_size_total',
            'disksizeused': 'disk_size_used',
            'scope': 'scope',
            'hypervisor': 'hypervisor',
            'state': 'state',
            'tags': 'tags',
        }
        self.storage_pool = None
        self.pod = None
        self.cluster = None

    def _get_common_args(self):
        args = {
            'name': self.module.params.get('name'),
            'url': self.module.params.get('storage_url'),
            'zoneid': self.get_zone(key='id'),
            'provider': self.module.params.get('provider'),
            'scope': self.module.params.get('scope'),
            'hypervisor': self.module.params.get('hypervisor'),
            'capacitybytes': self.module.params.get('capacity_bytes'),
            'capacityiops': self.module.params.get('capacity_iops'),
        }
        return args

    def get_storage_pool(self, key=None):
        if self.storage_pool is None:
            zoneid = self.get_zone(key='id')
            clusterid = self.get_cluster(key='id')
            podid = self.get_pod(key='id')

            args = {
                'zoneid': zoneid,
                'podid': podid,
                'clusterid': clusterid,
                'name': self.module.params.get('name'),
            }

            res = self.cs.listStoragePools(**args)
            if 'errortext' in res:
                self.module.fail_json(msg="Failed: '%s'" % res['errortext'])

            elif 'storagepool' not in res:
                return None

            self.storage_pool = res['storagepool'][0]

        return self.storage_pool

    def present_storage_pool(self):
        pool = self.get_storage_pool()
        if pool:
            pool = self._update_storage_pool()
        else:
            pool = self._create_storage_pool()
        return pool

    def _create_storage_pool(self):

        cluster = self.get_cluster(key='id')
        pod = self.get_pod(key='id')
        scope = self.module.params.get('scope')
        args = self._get_common_args()
        args['clusterid'] = cluster
        args['podid'] = pod

        if scope is None:
            args['scope'] = 'CLUSTER' if cluster else 'ZONE'

        self.result['changed'] = True

        if not self.module.check_mode:
            res = self.cs.createStoragePool(**args)
            if 'errortext' in res:
                self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
            pool = res['storagepool']
        return pool

    def _update_storage_pool(self):
        pool = self.get_storage_pool()

        args = {}

        args['id'] = pool['id']
        args['capacitybytes'] = self.module.params.get('capacity_bytes')
        args['capacityiops'] = self.module.params.get('capacity_iops')
        args['tags'] = self.module.params.get('tags')
        state = self.module.params.get('state')
        if state in ['enabled', 'disabled']:
            args['state'] = state.capitalize()

        if self.has_changed(args, pool):
            self.result['changed'] = True

            if not self.module.check_mode:
                res = self.cs.updateStoragePool(**args)
                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
        return pool

    def absent_storage_pool(self):
        pool = self.get_storage_pool()
        if pool:
            self.result['changed'] = True

            args = {
                'id': pool['id'],
            }
            if not self.module.check_mode:
                res = self.cs.deleteStoragePool(**args)
                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
        return pool

    def get_pod(self, key=None):
        pod = self.module.params.get('pod')
        if not pod:
            return None
        args = {
            'name': pod,
            'zoneid': self.get_zone(key='id'),
        }
        pods = self.cs.listPods(**args)
        if pods:
            return self._get_by_key(key, pods['pod'][0])
        self.module.fail_json(msg="Pod %s not found in zone %s." % (
            self.module.params.get('pod'),
            self.get_zone(key='name')))

    def get_cluster(self, key=None):
        cluster = self.module.params.get('cluster')
        if not cluster:
            return None
        args = {
            'name': cluster,
            'zoneid': self.get_zone(key='id'),
        }
        clusters = self.cs.listClusters(**args)
        if clusters:
            return self._get_by_key(key, clusters['cluster'][0])
        self.module.fail_json(msg="Cluster %s not found" % cluster)


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        storage_url=dict(default=None),
        zone=dict(required=True),
        pod=dict(default=None),
        cluster=dict(default=None),
        scope=dict(default=None, choices=['ZONE', 'CLUSTER']),
        hypervisor=dict(default=None),
        provider=dict(default='DefaultPrimary'),
        capacity_bytes=dict(default=None),
        capacity_iops=dict(default=None),
        tags=dict(type='list', aliases=['tag'], default=None),
        state=dict(choices=['present', 'enabled', 'disabled', 'absent'], default='present'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    try:
        acs_storage_pool = AnsibleCloudStackStoragePool(module)

        state = module.params.get('state')
        if state in ['absent']:
            pool = acs_storage_pool.absent_storage_pool()
        else:
            pool = acs_storage_pool.present_storage_pool()

        result = acs_storage_pool.get_result(pool)

    except CloudStackException as e:
        module.fail_json(msg='CloudStackException: %s' % str(e))

    module.exit_json(**result)

if __name__ == '__main__':
    main()
