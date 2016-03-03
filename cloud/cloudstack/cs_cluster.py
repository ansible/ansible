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

DOCUMENTATION = '''
---
module: cs_cluster
short_description: Manages host clusters on Apache CloudStack based clouds.
description:
    - Create, update and remove clusters.
version_added: "2.1"
author: "René Moser (@resmo)"
options:
  name:
    description:
      - name of the cluster.
    required: true
  zone:
    description:
      - Name of the zone in which the cluster belongs to.
      - If not set, default zone is used.
    required: false
    default: null
  pod:
    description:
      - Name of the pod in which the cluster belongs to.
    required: false
    default: null
  cluster_type:
    description:
      - Type of the cluster.
      - Required if C(state=present)
    required: false
    default: null
    choices: [ 'CloudManaged', 'ExternalManaged' ]
  hypervisor:
    description:
      - Name the hypervisor to be used.
      - Required if C(state=present).
    required: false
    default: none
    choices: [ 'KVM', 'VMware', 'BareMetal', 'XenServer', 'LXC', 'HyperV', 'UCS', 'OVM' ]
  url:
    description:
      - URL for the cluster
    required: false
    default: null
  username:
    description:
      - Username for the cluster.
    required: false
    default: null
  password:
    description:
      - Password for the cluster.
    required: false
    default: null
  guest_vswitch_name:
    description:
      - Name of virtual switch used for guest traffic in the cluster.
      - This would override zone wide traffic label setting.
    required: false
    default: null
  guest_vswitch_type:
    description:
      - Type of virtual switch used for guest traffic in the cluster.
      - Allowed values are, vmwaresvs (for VMware standard vSwitch) and vmwaredvs (for VMware distributed vSwitch)
    required: false
    default: null
    choices: [ 'vmwaresvs', 'vmwaredvs' ]
  public_vswitch_name:
    description:
      - Name of virtual switch used for public traffic in the cluster.
      - This would override zone wide traffic label setting.
    required: false
    default: null
  public_vswitch_type:
    description:
      - Type of virtual switch used for public traffic in the cluster.
      - Allowed values are, vmwaresvs (for VMware standard vSwitch) and vmwaredvs (for VMware distributed vSwitch)
    required: false
    default: null
    choices: [ 'vmwaresvs', 'vmwaredvs' ]
  vms_ip_address:
    description:
      - IP address of the VSM associated with this cluster.
    required: false
    default: null
  vms_username:
    description:
      - Username for the VSM associated with this cluster.
    required: false
    default: null
  vms_password:
    description:
      - Password for the VSM associated with this cluster.
    required: false
    default: null
  ovm3_cluster:
    description:
      - Ovm3 native OCFS2 clustering enabled for cluster.
    required: false
    default: null
  ovm3_pool:
    description:
      - Ovm3 native pooling enabled for cluster.
    required: false
    default: null
  ovm3_vip:
    description:
      - Ovm3 vip to use for pool (and cluster).
    required: false
    default: null
  state:
    description:
      - State of the cluster.
    required: false
    default: 'present'
    choices: [ 'present', 'absent', 'disabled', 'enabled' ]
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# Ensure a cluster is present
- local_action:
    module: cs_cluster
    name: kvm-cluster-01
    zone: ch-zrh-ix-01
    hypervisor: KVM
    cluster_type: CloudManaged

# Ensure a cluster is disabled
- local_action:
    module: cs_cluster
    name: kvm-cluster-01
    zone: ch-zrh-ix-01
    state: disabled

# Ensure a cluster is enabled
- local_action:
    module: cs_cluster
    name: kvm-cluster-01
    zone: ch-zrh-ix-01
    state: enabled

# Ensure a cluster is absent
- local_action:
    module: cs_cluster
    name: kvm-cluster-01
    zone: ch-zrh-ix-01
    state: absent
'''

RETURN = '''
---
id:
  description: UUID of the cluster.
  returned: success
  type: string
  sample: 04589590-ac63-4ffc-93f5-b698b8ac38b6
name:
  description: Name of the cluster.
  returned: success
  type: string
  sample: cluster01
allocation_state:
  description: State of the cluster.
  returned: success
  type: string
  sample: Enabled
cluster_type:
  description: Type of the cluster.
  returned: success
  type: string
  sample: ExternalManaged
cpu_overcommit_ratio:
  description: The CPU overcommit ratio of the cluster.
  returned: success
  type: string
  sample: 1.0
memory_overcommit_ratio:
  description: The memory overcommit ratio of the cluster.
  returned: success
  type: string
  sample: 1.0
managed_state:
  description: Whether this cluster is managed by CloudStack.
  returned: success
  type: string
  sample: Managed
ovm3_vip:
  description: Ovm3 VIP to use for pooling and/or clustering
  returned: success
  type: string
  sample: 10.10.10.101
hypervisor:
  description: Hypervisor of the cluster
  returned: success
  type: string
  sample: VMware
zone:
  description: Name of zone the cluster is in.
  returned: success
  type: string
  sample: ch-gva-2
pod:
  description: Name of pod the cluster is in.
  returned: success
  type: string
  sample: pod01
'''

try:
    from cs import CloudStack, CloudStackException, read_config
    has_lib_cs = True
except ImportError:
    has_lib_cs = False

# import cloudstack common
from ansible.module_utils.cloudstack import *

class AnsibleCloudStackCluster(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackCluster, self).__init__(module)
        self.returns = {
            'allocationstate':       'allocation_state',
            'hypervisortype':        'hypervisor',
            'clustertype':           'cluster_type',
            'podname':               'pod',
            'managedstate':          'managed_state',
            'memoryovercommitratio': 'memory_overcommit_ratio',
            'cpuovercommitratio':    'cpu_overcommit_ratio',
            'ovm3vip':               'ovm3_vip',
        }
        self.cluster = None


    def _get_common_cluster_args(self):
        args = {}
        args['clustername'] = self.module.params.get('name')
        args['hypervisor'] = self.module.params.get('hypervisor')
        args['clustertype'] = self.module.params.get('cluster_type')

        state = self.module.params.get('state')
        if state in [ 'enabled', 'disabled']:
            args['allocationstate'] = state.capitalize()
        return args


    def get_pod(self, key=None):
        args = {}
        args['name'] = self.module.params.get('pod')
        args['zoneid'] = self.get_zone(key='id')
        pods = self.cs.listPods(**args)
        if pods:
            return self._get_by_key(key, pods['pod'][0])
        self.module.fail_json(msg="Pod %s not found in zone %s." % (self.module.params.get('pod'), self.get_zone(key='name')))


    def get_cluster(self):
        if not self.cluster:
            args = {}

            uuid = self.module.params.get('id')
            if uuid:
                args['id'] = uuid
                clusters = self.cs.listClusters(**args)
                if clusters:
                    self.cluster = clusters['cluster'][0]
                    return self.cluster

            args['name'] = self.module.params.get('name')
            clusters = self.cs.listClusters(**args)
            if clusters:
                self.cluster = clusters['cluster'][0]
                # fix differnt return from API then request argument given
                self.cluster['hypervisor'] = self.cluster['hypervisortype']
                self.cluster['clustername'] = self.cluster['name']
        return self.cluster


    def present_cluster(self):
        cluster = self.get_cluster()
        if cluster:
            cluster = self._update_cluster()
        else:
            cluster = self._create_cluster()
        return cluster


    def _create_cluster(self):
        required_params = [
            'cluster_type',
            'hypervisor',
        ]
        self.module.fail_on_missing_params(required_params=required_params)

        args = self._get_common_cluster_args()
        args['zoneid'] = self.get_zone(key='id')
        args['podid'] = self.get_pod(key='id')
        args['url'] = self.module.params.get('url')
        args['username'] = self.module.params.get('username')
        args['password'] = self.module.params.get('password')
        args['guestvswitchname'] = self.module.params.get('guest_vswitch_name')
        args['guestvswitchtype'] = self.module.params.get('guest_vswitch_type')
        args['publicvswitchtype'] = self.module.params.get('public_vswitch_name')
        args['publicvswitchtype'] = self.module.params.get('public_vswitch_type')
        args['vsmipaddress'] = self.module.params.get('vms_ip_address')
        args['vsmusername'] = self.module.params.get('vms_username')
        args['vmspassword'] = self.module.params.get('vms_password')
        args['ovm3cluster'] = self.module.params.get('ovm3_cluster')
        args['ovm3pool'] = self.module.params.get('ovm3_pool')
        args['ovm3vip'] = self.module.params.get('ovm3_vip')

        self.result['changed'] = True

        cluster = None
        if not self.module.check_mode:
            res = self.cs.addCluster(**args)
            if 'errortext' in res:
                self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
            # API returns a list as result CLOUDSTACK-9205
            if isinstance(res['cluster'], list):
                cluster = res['cluster'][0]
            else:
                cluster = res['cluster']
        return cluster


    def _update_cluster(self):
        cluster = self.get_cluster()

        args = self._get_common_cluster_args()
        args['id'] = cluster['id']

        if self.has_changed(args, cluster):
            self.result['changed'] = True

            if not self.module.check_mode:
                res = self.cs.updateCluster(**args)
                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
                cluster = res['cluster']
        return cluster


    def absent_cluster(self):
        cluster = self.get_cluster()
        if cluster:
            self.result['changed'] = True

            args = {}
            args['id'] = cluster['id']

            if not self.module.check_mode:
                res = self.cs.deleteCluster(**args)
                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
        return cluster


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        name = dict(required=True),
        zone = dict(default=None),
        pod = dict(default=None),
        cluster_type = dict(choices=['CloudManaged', 'ExternalManaged'], default=None),
        hypervisor = dict(choices=CS_HYPERVISORS, default=None),
        state = dict(choices=['present', 'enabled', 'disabled', 'absent'], default='present'),
        url = dict(default=None),
        username = dict(default=None),
        password = dict(default=None, no_log=True),
        guest_vswitch_name = dict(default=None),
        guest_vswitch_type = dict(choices=['vmwaresvs', 'vmwaredvs'], default=None),
        public_vswitch_name = dict(default=None),
        public_vswitch_type = dict(choices=['vmwaresvs', 'vmwaredvs'], default=None),
        vms_ip_address = dict(default=None),
        vms_username = dict(default=None),
        vms_password = dict(default=None, no_log=True),
        ovm3_cluster = dict(default=None),
        ovm3_pool = dict(default=None),
        ovm3_vip = dict(default=None),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    if not has_lib_cs:
        module.fail_json(msg="python library cs required: pip install cs")

    try:
        acs_cluster = AnsibleCloudStackCluster(module)

        state = module.params.get('state')
        if state in ['absent']:
            cluster = acs_cluster.absent_cluster()
        else:
            cluster = acs_cluster.present_cluster()

        result = acs_cluster.get_result(cluster)

    except CloudStackException as e:
        module.fail_json(msg='CloudStackException: %s' % str(e))

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
