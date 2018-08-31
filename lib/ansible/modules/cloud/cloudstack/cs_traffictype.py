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
module: cs_traffictype
short_description: Manages physical networks on Apache CloudStack based clouds.
description:
    - Create, update and remove networks.
version_added: "2.4"
author: "Netservers Ltd. (@netservers)"
options:
  physical_network:
    description:
      - physical network.
    required: true
  traffictype:
    description:
      - Type of traffic.
    required: true
    default: none
    choices: [ 'Guest', 'Public', 'Management', 'Storage' ]
  isolation_method:
    description:
      - Used if physical network has multiple isolation types and traffic type is public
      - Valid options currently 'vlan' or 'vxlan', defaults to 'vlan'.
    required: false
    default: none
    choices: [ 'vlan', 'vxlan' ]
  vlan:
    description:
      - The VLAN id to be used for Management traffic by VMware host
    required: false
    default: null
  vmware_network_label:
    description:
      - The network name label of the physical device dedicated to this traffic on a VMware host
    required: false
    default: null
  xen_network_label:
    description:
      - The network name label of the physical device dedicated to this traffic on a XenServer host
    required: false
    default: null
  kvm_network_label:
    description:
      - The network name label of the physical device dedicated to this traffic on a KVM host
    required: false
    default: null
  ovm3_network_label:
    description:
      - The network name label of the physical device dedicated to this traffic on a OVM3 host
    required: false
    default: null
  hyperv_network_label:
    description:
      - The network name label of the physical device dedicated to this traffic on a HyperV host
    required: false
    default: null
  url:
    description:
      - URL for the cluster
    required: false
    default: null
  poll_async:
    description:
      - "Poll async jobs until job has finished."
    required: false
    default: true
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# Ensure a traffictype is present
- local_action:
    module: cs_traffictype
    physical_network: net01
    traffictype: Guest
    kvm_networklabel: cloudbr1

# Ensure a traffictype is absent
- local_action:
    module: cs_traffictype
    physical_network: net01
    traffictype: Guest
    state: absent
'''

RETURN = '''
---
id:
  description: UUID of the network provider.
  returned: success
  type: string
  sample: da2b45b3-32dc-45d0-abba-d8d4b625bc8f
traffictype:
  description: The trafficType.
  returned: success
  type: string
  sample: Guest
isolation_method:
  description: isolationmethod of the network [vlan,vxlan].
  returned: success
  type: string
  sample: VLAN
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    CloudStackException,
    cs_argument_spec,
    cs_required_together,
)


class AnsibleCloudStackTrafficType(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackTrafficType, self).__init__(module)
        self.returns = {
            'traffictype': 'traffictype',
            'isolationmethod': 'isolation_method',
            'kvmnetworklabel': 'kvm_networklabel',
            'xennetworklabel': 'xen_networklabel',
            'vmwarenetworklabel': 'vmware_networklabel',
            'hypervnetworklabel': 'hyperv_networklabel',
            'ovm3networklabel': 'ovm3_networklabel',
            'vlan': 'vlan',
        }
        self.traffictype = None
        self.physical_network = None

    def _get_common_cluster_args(self):
        args = {
            'physicalnetworkid': self.get_physical_network(key='id'),
            'traffictype': self.module.params.get('traffictype'),
            'isolationmethod': self.module.params.get('isolation_method'),
            'kvmnetworklabel': self.module.params.get('kvm_networklabel'),
            'xennetworklabel': self.module.params.get('xen_networklabel'),
            'vmwarenetworklabel': self.module.params.get('vmware_networklabel'),
            'hypervnetworklabel': self.module.params.get('hyperv_networklabel'),
            'ovm3networklabel': self.module.params.get('ovm3_networklabel'),
            'vlan': self.module.params.get('vlan'),
        }
        return args

    def get_traffictype(self, key=None):
        if self.traffictype:
            return self.traffictype
        traffictype = self.module.params.get('traffictype')
        args = {
            'physicalnetworkid': self.get_physical_network(key='id'),
        }
        ttypes = self.cs.listTrafficTypes(**args)
        if ttypes:
            for t in ttypes['traffictype']:
                if traffictype.lower() in [t['traffictype'].lower(), t['id']]:
                    self.traffictype = t
                    break
        return self.traffictype

    def present_traffictype(self):
        ttype = self.get_traffictype()
        if ttype:
            ttype = self._update_traffictype()
        else:
            ttype = self._create_traffictype()
        return ttype

    def _create_traffictype(self):
        required_params = [
            'physical_network',
            'traffictype',
        ]
        self.module.fail_on_missing_params(required_params=required_params)

        args = self._get_common_cluster_args()

        self.result['changed'] = True

        ttype = args
        if not self.module.check_mode:
            res = self.cs.addTrafficType(**args)
            if 'errortext' in res:
                self.module.fail_json(msg="Failed: '%s'" % res['errortext'])

            ttype['id'] = res['id']
            poll_async = self.module.params.get('poll_async')
            if poll_async:
                ttype = self.poll_job(res, 'traffictype')

        return ttype

    def _update_traffictype(self):
        ttype = self.get_traffictype()

        args = self._get_common_cluster_args()
        args['id'] = ttype['id']

        if self.has_changed(args, ttype):
            self.result['changed'] = True

            if not self.module.check_mode:
                res = self.cs.updateTrafficType(**args)
                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])

                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    ttype = self.poll_job(res, 'traffictype')

        return ttype

    def absent_traffictype(self):
        ttype = self.get_traffictype()
        if ttype:
            self.result['changed'] = True

            args = {
                'id': ttype['id'],
            }
            if not self.module.check_mode:
                res = self.cs.deleteTrafficType(**args)
                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])

                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    success = self.poll_job(res, 'success')

        return ttype

    def get_physical_network(self, key=None):
        if self.physical_network:
            return self._get_by_key(key, self.physical_network)

        physical_network = self.module.params.get('physical_network')
        networks = self.cs.listPhysicalNetworks()

        if not networks:
            self.module.fail_json(msg="No physical networks available. Please create a physical network first")

        # use the first network if no physical_network param given
        if not physical_network:
            self.physical_network = networks['physicalnetwork'][0]
            return self._get_by_key(key, self.physical_network)

        if networks:
            for n in networks['physicalnetwork']:
                if physical_network.lower() in [n['name'].lower(), n['id']]:
                    self.physical_network = n
                    return self._get_by_key(key, self.physical_network)
        self.module.fail_json(msg="physical network '%s' not found" % zone)


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        traffictype=dict(required=True, choices=['Guest', 'Public', 'Management', 'Storage']),
        physical_network=dict(required=True),
        vlan=dict(default=None),
        kvm_networklabel=dict(default=None),
        xen_networklabel=dict(default=None),
        vmware_networklabel=dict(default=None),
        hyperv_networklabel=dict(default=None),
        ovm3_networklabel=dict(default=None),
        isolation_method=dict(choices=['vlan', 'vxlan'], default=None),
        state=dict(choices=['present', 'enabled', 'disabled', 'absent'], default='present'),
        url=dict(default=None),
        poll_async=dict(type='bool', default=True),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    try:
        acs_traffictype = AnsibleCloudStackTrafficType(module)

        state = module.params.get('state')
        if state in ['absent']:
            network = acs_traffictype.absent_traffictype()
        else:
            network = acs_traffictype.present_traffictype()

        result = acs_traffictype.get_result(network)

    except CloudStackException as e:
        module.fail_json(msg='CloudStackException: %s' % str(e))

    module.exit_json(**result)

if __name__ == '__main__':
    main()
