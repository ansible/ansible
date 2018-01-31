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

ANSIBLE_METADATA = {'metadata_version': '1.1',
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
    aliases: [ 'ip_address' ]
  url:
    description:
      - Url of the host used to create a host.
      - If not provided, C(http://) and param C(name) is used as url.
      - Only considered if C(state=present) and host does not yet exist.
  username:
    description:
      - Username for the host.
      - Required if C(state=present) and host does not yet exist.
  password:
    description:
      - Password for the host.
      - Required if C(state=present) and host does not yet exist.
  pod:
    description:
      - Name of the pod.
      - Required if C(state=present) and host does not yet exist.
  cluster:
    description:
      - Name of the cluster.
  hypervisor:
    description:
      - Name of the cluster.
      - Required if C(state=present) and host does not yet exist.
    choices: [ 'KVM', 'VMware', 'BareMetal', 'XenServer', 'LXC', 'HyperV', 'UCS', 'OVM', 'Simulator' ]
  allocation_state:
    description:
      - Allocation state of the host.
    choices: [ 'enabled', 'disabled' ]
  host_tags:
    description:
      - Tags of the host.
    aliases: [ host_tag ]
  state:
    description:
      - State of the host.
    default: 'present'
    choices: [ 'present', 'absent' ]
  zone:
    description:
      - Name of the zone in which the host should be deployed.
      - If not set, default zone is used.
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: Ensure a host is present but disabled
  local_action:
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

- name: Ensure an existing host is disabled
  local_action:
    module: cs_host
    name: ix-pod01-esx01.example.com
    zone: ch-zrh-ix-01
    allocation_state: disabled

- name: Ensure an existing host is disabled
  local_action:
    module: cs_host
    name: ix-pod01-esx01.example.com
    zone: ch-zrh-ix-01
    allocation_state: enabled

- name: Ensure a host is absent
  local_action:
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
allocation_state::
  description: Allocation state of the host.
  returned: success
  type: string
  sample: enabled
state:
  description: State of the host.
  returned: success
  type: string
  sample: Up
suitable_for_migration:
  description: Whether this host is suitable (has enough capacity and satisfies all conditions like hosttags, max guests VM limit, etc) to migrate a VM
               to it or not.
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
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together,
    CS_HYPERVISORS
)
import time


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
        # States only usable by the updateHost API
        self.allocation_states_for_update = {
            'enabled': 'Enable',
            'disabled': 'Disable',
        }
        self.host = None

    def get_pod(self, key=None):
        pod_name = self.module.params.get('pod')
        if not pod_name:
            return None
        args = {
            'name': pod_name,
            'zoneid': self.get_zone(key='id'),
        }
        pods = self.query_api('listPods', **args)
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
        clusters = self.query_api('listClusters', **args)
        if clusters:
            return self._get_by_key(key, clusters['cluster'][0])
        self.module.fail_json(msg="Cluster %s not found" % cluster_name)

    def get_host_tags(self):
        host_tags = self.module.params.get('host_tags')
        if host_tags is None:
            return None
        return ','.join(host_tags)

    def get_host(self, refresh=False):
        if self.host is not None and not refresh:
            return self.host

        name = self.module.params.get('name')
        args = {
            'zoneid': self.get_zone(key='id'),
        }
        res = self.query_api('listHosts', **args)
        if res:
            for h in res['host']:
                if name in [h['ipaddress'], h['name']]:
                    self.host = h
        return self.host

    def _handle_allocation_state(self, host):
        allocation_state = self.module.params.get('allocation_state')
        if not allocation_state:
            return host

        host = self._set_host_allocation_state(host)

        # In case host in maintenance and target is maintenance
        if host['allocationstate'].lower() == allocation_state and allocation_state == 'maintenance':
            return host

        # Cancel maintenance if target state is enabled/disabled
        elif allocation_state in list(self.allocation_states_for_update.keys()):
            host = self.disable_maintenance(host)
            host = self._update_host(host, self.allocation_states_for_update[allocation_state])

        # Only an enabled host can put in maintenance
        elif allocation_state == 'maintenance':
            host = self._update_host(host, 'Enable')
            host = self.enable_maintenance(host)

        return host

    def _set_host_allocation_state(self, host):
        if host is None:
            host['allocationstate'] = 'Enable'

        # Set host allocationstate to be disabled/enabled
        elif host['resourcestate'].lower() in list(self.allocation_states_for_update.keys()):
            host['allocationstate'] = self.allocation_states_for_update[host['resourcestate'].lower()]

        else:
            host['allocationstate'] = host['resourcestate']

        return host

    def present_host(self):
        host = self.get_host()

        if not host:
            host = self._create_host(host)
        else:
            host = self._update_host(host)

        if host:
            host = self._handle_allocation_state(host)

        return host

    def _get_url(self):
        url = self.module.params.get('url')
        if url:
            return url
        else:
            return "http://%s" % self.module.params.get('name')

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
            'url': self._get_url(),
            'username': self.module.params.get('username'),
            'password': self.module.params.get('password'),
            'podid': self.get_pod(key='id'),
            'zoneid': self.get_zone(key='id'),
            'clusterid': self.get_cluster(key='id'),
            'hosttags': self.get_host_tags(),
        }
        if not self.module.check_mode:
            host = self.query_api('addHost', **args)
            host = host['host'][0]
        return host

    def _update_host(self, host, allocation_state=None):
        args = {
            'id': host['id'],
            'hosttags': self.get_host_tags(),
            'allocationstate': allocation_state,
        }

        if allocation_state is not None:
            host = self._set_host_allocation_state(host)

        if self.has_changed(args, host):
            self.result['changed'] = True
            if not self.module.check_mode:
                host = self.query_api('updateHost', **args)
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
                res = self.enable_maintenance(host)
                if res:
                    res = self.query_api('deleteHost', **args)
        return host

    def enable_maintenance(self, host):
        if host['resourcestate'] not in ['PrepareForMaintenance', 'Maintenance']:
            self.result['changed'] = True
            args = {
                'id': host['id'],
            }
            if not self.module.check_mode:
                res = self.query_api('prepareHostForMaintenance', **args)
                self.poll_job(res, 'host')
                host = self._poll_for_maintenance()
        return host

    def disable_maintenance(self, host):
        if host['resourcestate'] in ['PrepareForMaintenance', 'Maintenance']:
            self.result['changed'] = True
            args = {
                'id': host['id'],
            }
            if not self.module.check_mode:
                res = self.query_api('cancelHostMaintenance', **args)
                host = self.poll_job(res, 'host')
        return host

    def _poll_for_maintenance(self):
        for i in range(0, 300):
            time.sleep(2)
            host = self.get_host(refresh=True)
            if not host:
                return None
            elif host['resourcestate'] != 'PrepareForMaintenance':
                return host
        self.fail_json(msg="Polling for maintenance timed out")

    def get_result(self, host):
        super(AnsibleCloudStackHost, self).get_result(host)
        if host:
            self.result['allocation_state'] = host['resourcestate'].lower()
            self.result['host_tags'] = host['hosttags'].split(',') if host.get('hosttags') else []
        return self.result


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True, aliases=['ip_address']),
        url=dict(),
        password=dict(no_log=True),
        username=dict(),
        hypervisor=dict(choices=CS_HYPERVISORS),
        allocation_state=dict(choices=['enabled', 'disabled', 'maintenance']),
        pod=dict(),
        cluster=dict(),
        host_tags=dict(type='list', aliases=['host_tag']),
        zone=dict(),
        state=dict(choices=['present', 'absent'], default='present'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    acs_host = AnsibleCloudStackHost(module)

    state = module.params.get('state')
    if state == 'absent':
        host = acs_host.absent_host()
    else:
        host = acs_host.present_host()

    result = acs_host.get_result(host)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
