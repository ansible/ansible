#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2016, René Moser <mail@renemoser.net>
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
module: cs_host
short_description: Manages hosts on Apache CloudStack based clouds.
description:
  - Create, update and remove hosts.
version_added: "2.3"
author: "René Moser (@resmo)"
options:
  name:
    description:
      - Name of the host.
    required: true
    aliases: [ 'url' ]
  username:
    description:
      - Username for the host.
      - Required if C(state=present) and host does not yet exist.
    required: false
    default: null
  password:
    description:
      - Password for the host.
      - Required if C(state=present) and host does not yet exist.
    required: false
    default: null
  pod:
    description:
      - Name of the pod.
      - Required if C(state=present) and host does not yet exist.
    required: false
    default: null
  cluster:
    description:
      - Name of the cluster.
    required: false
    default: null
  hypervisor:
    description:
      - Name of the cluster.
      - Required if C(state=present) and host does not yet exist.
    choices: [ 'KVM', 'VMware', 'BareMetal', 'XenServer', 'LXC', 'HyperV', 'UCS', 'OVM', 'Simulator' ]
    required: false
    default: null
  allocation_state:
    description:
      - Allocation state of the host.
    choices: [ 'enabled', 'disabled' ]
    required: false
    default: null
  host_tags:
    description:
      - Tags of the host.
    required: false
    default: null
  state:
    description:
      - State of the host.
    required: false
    default: 'present'
    choices: [ 'present', 'absent' ]
  zone:
    description:
      - Name of the zone in which the host should be deployed.
      - If not set, default zone is used.
    required: false
    default: null
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# Ensure a host is present but disabled
- local_action:
    module: cs_host
    name: ix-pod01-esx01.example.com
    cluster: vcenter.example.com/ch-zrh-ix/pod01-cluster01
    pod: pod01
    zone: ch-zrh-ix-01
    hypervisor: VMware
    allocation_state: disabled
    host_tags:
    - perf
    - gpu

# Ensure an existing host is disabled
- local_action:
    module: cs_host
    name: ix-pod01-esx01.example.com
    zone: ch-zrh-ix-01
    allocation_state: disabled

# Ensure an existing host is disabled
- local_action:
    module: cs_host
    name: ix-pod01-esx01.example.com
    zone: ch-zrh-ix-01
    allocation_state: enabled

# Ensure a host is absent
- local_action:
    module: cs_host
    name: ix-pod01-esx01.example.com
    zone: ch-zrh-ix-01
    state: absent
'''

RETURN = '''
---
capabilities:
  description: Capabilities of the host.
  returned: success
  type: string
  sample: hvm
cluster:
  description: Cluster of the host.
  returned: success
  type: string
  sample: vcenter.example.com/zone/cluster01
cluster_type:
  description: Type of the cluster of the host.
  returned: success
  type: string
  sample: ExternalManaged
cpu_allocated:
  description: Amount in percent of the host's CPU currently allocated.
  returned: success
  type: string
  sample: 166.25%
cpu_number:
  description: Number of CPUs of the host.
  returned: success
  type: string
  sample: 24
cpu_sockets:
  description: Number of CPU sockets of the host.
  returned: success
  type: int
  sample: 2
cpu_speed:
  description: CPU speed in Mhz
  returned: success
  type: int
  sample: 1999
cpu_used:
  description: Amount of the host's CPU currently used.
  returned: success
  type: string
  sample: 33.6%
cpu_with_overprovisioning:
  description: Amount of the host's CPU after applying the cpu.overprovisioning.factor.
  returned: success
  type: string
  sample: 959520.0
created:
  description: Date when the host was created.
  returned: success
  type: string
  sample: 2015-05-03T15:05:51+0200
disconnected:
  description: Date when the host was disconnected.
  returned: success
  type: string
  sample: 2015-05-03T15:05:51+0200
disk_size_allocated:
  description: Host's currently allocated disk size.
  returned: success
  type: int
  sample: 2593
disk_size_total:
  description: Total disk size of the host
  returned: success
  type: int
  sample: 259300
events:
  description: Events available for the host
  returned: success
  type: string
  sample: "Ping; HostDown; AgentConnected; AgentDisconnected; PingTimeout; ShutdownRequested; Remove; StartAgentRebalance; ManagementServerDown"
ha_host:
  description: Whether the host is a HA host.
  returned: success
  type: bool
  sample: false
has_enough_capacity:
  description: Whether the host has enough CPU and RAM capacity to migrate a VM to it.
  returned: success
  type: bool
  sample: true
host_tags:
  description: Comma-separated list of tags for the host.
  returned: success
  type: string
  sample: "perf"
hypervisor:
  description: Host's hypervisor.
  returned: success
  type: string
  sample: VMware
hypervisor_version:
  description: Hypervisor version.
  returned: success
  type: string
  sample: 5.1
ip_address:
  description: IP address of the host
  returned: success
  type: string
  sample: 10.10.10.1
is_local_storage_active:
  description: Whether the local storage is available or not.
  returned: success
  type: bool
  sample: false
last_pinged:
  description: Date and time the host was last pinged.
  returned: success
  type: string
  sample: "1970-01-17T17:27:32+0100"
management_server_id:
  description: Management server ID of the host.
  returned: success
  type: int
  sample: 345050593418
memory_allocated:
  description: Amount of the host's memory currently allocated.
  returned: success
  type: int
  sample: 69793218560
memory_total:
  description: Total of memory of the host.
  returned: success
  type: int
  sample: 206085263360
memory_used:
  description: Amount of the host's memory currently used.
  returned: success
  type: int
  sample: 65504776192
name:
  description: Name of the host.
  returned: success
  type: string
  sample: esx32.example.com
network_kbs_read:
  description: Incoming network traffic on the host.
  returned: success
  type: int
  sample: 0
network_kbs_write:
  description: Outgoing network traffic on the host.
  returned: success
  type: int
  sample: 0
os_category:
  description: OS category name of the host.
  returned: success
  type: string
  sample: ...
out_of_band_management:
  description: Host out-of-band management information.
  returned: success
  type: string
  sample: ...
pod:
  description: Pod name of the host.
  returned: success
  type: string
  sample: Pod01
removed:
  description: Date and time the host was removed.
  returned: success
  type: string
  sample: "1970-01-17T17:27:32+0100"
resource_state:
  description: Resource state of the host.
  returned: success
  type: string
  sample: Enabled
state:
  description: State of the host.
  returned: success
  type: string
  sample: Up
suitable_for_migration:
  description: Whether this host is suitable (has enough capacity and satisfies all conditions like hosttags, max guests VM limit, etc) to migrate a VM to it or not.
  returned: success
  type: string
  sample: true
host_type:
  description: Type of the host.
  returned: success
  type: string
  sample: Routing
host_version:
  description: Version of the host.
  returned: success
  type: string
  sample: 4.5.2
gpu_group:
  description: GPU cards present in the host.
  returned: success
  type: list
  sample: []
zone:
  description: Zone of the host.
  returned: success
  type: string
  sample: zone01
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import AnsibleCloudStack, CloudStackException, cs_argument_spec, cs_required_together, CS_HYPERVISORS


class AnsibleCloudStackHost(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackHost, self).__init__(module)
        self.returns = {
            'averageload': 'average_load',
            'capabilities': 'capabilities',
            'clustername': 'cluster',
            'clustertype': 'cluster_type',
            'cpuallocated': 'cpu_allocated',
            'cpunumber': 'cpu_number',
            'cpusockets': 'cpu_sockets',
            'cpuspeed': 'cpu_speed',
            'cpuused': 'cpu_used',
            'cpuwithoverprovisioning': 'cpu_with_overprovisioning',
            'disconnected': 'disconnected',
            'details': 'details',
            'disksizeallocated': 'disk_size_allocated',
            'disksizetotal': 'disk_size_total',
            'events': 'events',
            'hahost': 'ha_host',
            'hasenoughcapacity': 'has_enough_capacity',
            'hosttags': 'host_tags',
            'hypervisor': 'hypervisor',
            'hypervisorversion': 'hypervisor_version',
            'ipaddress': 'ip_address',
            'islocalstorageactive': 'is_local_storage_active',
            'lastpinged': 'last_pinged',
            'managementserverid': 'management_server_id',
            'memoryallocated': 'memory_allocated',
            'memorytotal': 'memory_total',
            'memoryused': 'memory_used',
            'networkkbsread': 'network_kbs_read',
            'networkkbswrite': 'network_kbs_write',
            'oscategoryname': 'os_category',
            'outofbandmanagement': 'out_of_band_management',
            'podname': 'pod',
            'removed': 'removed',
            'resourcestate': 'resource_state',
            'suitableformigration': 'suitable_for_migration',
            'type': 'host_type',
            'version': 'host_version',
            'gpugroup': 'gpu_group',

        }
        self.allocation_states = {
            'enabled': 'enable',
            'disabled': 'disable',
        }

    def get_pod(self, key=None):
        pod_name = self.module.params.get('pod')
        if not pod_name:
            return None
        args = {
            'name': pod_name,
            'zoneid': self.get_zone(key='id'),
        }
        pods = self.cs.listPods(**args)
        if pods:
            return self._get_by_key(key, pods['pod'][0])
        self.module.fail_json(msg="Pod %s not found" % pod_name)

    def get_cluster(self, key=None):
        cluster_name = self.module.params.get('cluster')
        if not cluster_name:
            return None
        args = {
            'name': cluster_name,
            'zoneid': self.get_zone(key='id'),
        }
        clusters = self.cs.listClusters(**args)
        if clusters:
            return self._get_by_key(key, clusters['cluster'][0])
        self.module.fail_json(msg="Cluster %s not found" % cluster_name)

    def get_host_tags(self):
        host_tags = self.module.params.get('host_tags')
        if host_tags is None:
            return None
        return ','.join(host_tags)

    def get_allocation_state(self):
        allocation_state = self.module.params.get('allocation_state')
        if allocation_state is None:
            return None
        return self.allocation_states[allocation_state]

    def get_host(self):
        host = None
        args = {
            'zoneid': self.get_zone(key='id'),
            'name': self.module.params.get('name'),
        }
        hosts = self.cs.listHosts(**args)
        if hosts:
            host = hosts['host'][0]
        return host

    def present_host(self):
        host = self.get_host()
        if not host:
            host = self._create_host(host)
        else:
            host = self._update_host(host)
        return host

    def _create_host(self, host):
        required_params = [
            'password',
            'username',
            'hypervisor',
            'pod',
        ]
        self.module.fail_on_missing_params(required_params=required_params)
        self.result['changed'] = True
        args = {
            'hypervisor': self.module.params.get('hypervisor'),
            'url': self.module.params.get('name'),
            'username': self.module.params.get('username'),
            'password': self.module.params.get('password'),
            'podid': self.get_pod(key='id'),
            'zoneid': self.get_zone(key='id'),
            'clusterid': self.get_cluster(key='id'),
            'allocationstate': self.get_allocation_state(),
            'hosttags': self.get_host_tags(),
        }
        if not self.module.check_mode:
            host = self.cs.addHost(**args)
            if 'errortext' in host:
                self.module.fail_json(msg="Failed: '%s'" % host['errortext'])
            host = host['host']
        return host

    def _update_host(self, host):
        args = {
            'id': host['id'],
            'hosttags': self.get_host_tags(),
            'allocationstate': self.module.params.get('allocation_state'),
        }
        host['allocationstate'] = host['resourcestate'].lower()
        if self.has_changed(args, host):
            args['allocationstate'] = self.get_allocation_state()
            self.result['changed'] = True
            if not self.module.check_mode:
                host = self.cs.updateHost(**args)
                if 'errortext' in host:
                    self.module.fail_json(msg="Failed: '%s'" % host['errortext'])
                host = host['host']
        return host

    def absent_host(self):
        host = self.get_host()
        if host:
            self.result['changed'] = True
            args = {
                'id': host['id'],
            }
            if not self.module.check_mode:
                res = self.cs.deleteHost(**args)
                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
        return host


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True, aliases=['url']),
        password=dict(default=None, no_log=True),
        username=dict(default=None),
        hypervisor=dict(choices=CS_HYPERVISORS, default=None),
        allocation_state=dict(default=None),
        pod=dict(default=None),
        cluster=dict(default=None),
        host_tags=dict(default=None, type='list'),
        zone=dict(default=None),
        state=dict(choices=['present', 'absent'], default='present'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    try:
        acs_host = AnsibleCloudStackHost(module)

        state = module.params.get('state')
        if state == 'absent':
            host = acs_host.absent_host()
        else:
            host = acs_host.present_host()

        result = acs_host.get_result(host)

    except CloudStackException as e:
        module.fail_json(msg='CloudStackException: %s' % str(e))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
