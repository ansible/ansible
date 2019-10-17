#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2019, Patryk D. Cichy <patryk.d.cichy@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: cs_traffic_type
short_description: Manages traffic types on CloudStack Physical Networks
description:
 - Add, remove, update Traffic Types associated with CloudStack Physical Networks.
extends_documentation_fragment: cloudstack
version_added: "2.8"
author:
 - Patryk Cichy (@PatTheSilent)
options:
  physical_network:
    description:
      - the name of the Physical Network
    required: true
    type: str
  zone:
    description:
      - Name of the zone with the physical network.
      - Default zone will be used if this is empty.
    type: str
  traffic_type:
    description:
      - the trafficType to be added to the physical network.
    required: true
    choices: [Management, Guest, Public, Storage]
    type: str
  state:
    description:
      - State of the traffic type
    choices: [present, absent]
    default: present
    type: str
  hyperv_networklabel:
    description:
      - The network name label of the physical device dedicated to this traffic on a HyperV host.
    type: str
  isolation_method:
    description:
      - Use if the physical network has multiple isolation types and traffic type is public.
    choices: [vlan, vxlan]
    type: str
  kvm_networklabel:
    description:
      - The network name label of the physical device dedicated to this traffic on a KVM host.
    type: str
  ovm3_networklabel:
    description:
      - The network name of the physical device dedicated to this traffic on an OVM3 host.
    type: str
  vlan:
    description:
      - The VLAN id to be used for Management traffic by VMware host.
    type: str
  vmware_networklabel:
    description:
      - The network name label of the physical device dedicated to this traffic on a VMware host.
    type: str
  xen_networklabel:
    description:
      - The network name label of the physical device dedicated to this traffic on a XenServer host.
    type: str
  poll_async:
    description:
      - Poll async jobs until job has finished.
    default: yes
    type: bool
'''

EXAMPLES = '''
- name: add a traffic type
  cs_traffic_type:
    physical_network: public-network
    traffic_type: Guest
    zone: test-zone
  delegate_to: localhost

- name: update traffic type
  cs_traffic_type:
    physical_network: public-network
    traffic_type: Guest
    kvm_networklabel: cloudbr0
    zone: test-zone
  delegate_to: localhost

- name: remove traffic type
  cs_traffic_type:
    physical_network: public-network
    traffic_type: Public
    state: absent
    zone: test-zone
  delegate_to: localhost
'''

RETURN = '''
---
id:
  description: ID of the network provider
  returned: success
  type: str
  sample: 659c1840-9374-440d-a412-55ca360c9d3c
traffic_type:
  description: the trafficType that was added to the physical network
  returned: success
  type: str
  sample: Public
hyperv_networklabel:
  description: The network name label of the physical device dedicated to this traffic on a HyperV host
  returned: success
  type: str
  sample: HyperV Internal Switch
kvm_networklabel:
  description: The network name label of the physical device dedicated to this traffic on a KVM host
  returned: success
  type: str
  sample: cloudbr0
ovm3_networklabel:
  description: The network name of the physical device dedicated to this traffic on an OVM3 host
  returned: success
  type: str
  sample: cloudbr0
physical_network:
  description: the physical network this belongs to
  returned: success
  type: str
  sample: 28ed70b7-9a1f-41bf-94c3-53a9f22da8b6
vmware_networklabel:
  description: The network name label of the physical device dedicated to this traffic on a VMware host
  returned: success
  type: str
  sample: Management Network
xen_networklabel:
  description: The network name label of the physical device dedicated to this traffic on a XenServer host
  returned: success
  type: str
  sample: xenbr0
zone:
  description: Name of zone the physical network is in.
  returned: success
  type: str
  sample: ch-gva-2
'''

from ansible.module_utils.cloudstack import AnsibleCloudStack, cs_argument_spec, cs_required_together
from ansible.module_utils.basic import AnsibleModule


class AnsibleCloudStackTrafficType(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackTrafficType, self).__init__(module)
        self.returns = {
            'traffictype': 'traffic_type',
            'hypervnetworklabel': 'hyperv_networklabel',
            'kvmnetworklabel': 'kvm_networklabel',
            'ovm3networklabel': 'ovm3_networklabel',
            'physicalnetworkid': 'physical_network',
            'vmwarenetworklabel': 'vmware_networklabel',
            'xennetworklabel': 'xen_networklabel'
        }

        self.traffic_type = None

    def _get_label_args(self):
        label_args = dict()
        if self.module.params.get('hyperv_networklabel'):
            label_args.update(dict(hypervnetworklabel=self.module.params.get('hyperv_networklabel')))
        if self.module.params.get('kvm_networklabel'):
            label_args.update(dict(kvmnetworklabel=self.module.params.get('kvm_networklabel')))
        if self.module.params.get('ovm3_networklabel'):
            label_args.update(dict(ovm3networklabel=self.module.params.get('ovm3_networklabel')))
        if self.module.params.get('vmware_networklabel'):
            label_args.update(dict(vmwarenetworklabel=self.module.params.get('vmware_networklabel')))
        return label_args

    def _get_additional_args(self):
        additional_args = dict()

        if self.module.params.get('isolation_method'):
            additional_args.update(dict(isolationmethod=self.module.params.get('isolation_method')))

        if self.module.params.get('vlan'):
            additional_args.update(dict(vlan=self.module.params.get('vlan')))

        additional_args.update(self._get_label_args())

        return additional_args

    def get_traffic_types(self):
        args = {
            'physicalnetworkid': self.get_physical_network(key='id')
        }
        traffic_types = self.query_api('listTrafficTypes', **args)
        return traffic_types

    def get_traffic_type(self):
        if self.traffic_type:
            return self.traffic_type

        traffic_type = self.module.params.get('traffic_type')

        traffic_types = self.get_traffic_types()

        if traffic_types:
            for t_type in traffic_types['traffictype']:
                if traffic_type.lower() in [t_type['traffictype'].lower(), t_type['id']]:
                    self.traffic_type = t_type
                    break
        return self.traffic_type

    def present_traffic_type(self):
        traffic_type = self.get_traffic_type()
        if traffic_type:
            self.traffic_type = self.update_traffic_type()
        else:
            self.result['changed'] = True
            self.traffic_type = self.add_traffic_type()

        return self.traffic_type

    def add_traffic_type(self):
        traffic_type = self.module.params.get('traffic_type')
        args = {
            'physicalnetworkid': self.get_physical_network(key='id'),
            'traffictype': traffic_type
        }
        args.update(self._get_additional_args())
        if not self.module.check_mode:
            resource = self.query_api('addTrafficType', **args)
            poll_async = self.module.params.get('poll_async')
            if poll_async:
                self.traffic_type = self.poll_job(resource, 'traffictype')
        return self.traffic_type

    def absent_traffic_type(self):
        traffic_type = self.get_traffic_type()
        if traffic_type:

            args = {
                'id': traffic_type['id']
            }
            self.result['changed'] = True
            if not self.module.check_mode:
                resource = self.query_api('deleteTrafficType', **args)
                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    self.poll_job(resource, 'traffictype')

        return traffic_type

    def update_traffic_type(self):

        traffic_type = self.get_traffic_type()
        args = {
            'id': traffic_type['id']
        }
        args.update(self._get_label_args())
        if self.has_changed(args, traffic_type):
            self.result['changed'] = True
            if not self.module.check_mode:
                resource = self.query_api('updateTrafficType', **args)
                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    self.traffic_type = self.poll_job(resource, 'traffictype')

        return self.traffic_type


def setup_module_object():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        physical_network=dict(required=True),
        zone=dict(),
        state=dict(choices=['present', 'absent'], default='present'),
        traffic_type=dict(required=True, choices=['Management', 'Guest', 'Public', 'Storage']),
        hyperv_networklabel=dict(),
        isolation_method=dict(choices=['vlan', 'vxlan']),
        kvm_networklabel=dict(),
        ovm3_networklabel=dict(),
        vlan=dict(),
        vmware_networklabel=dict(),
        xen_networklabel=dict(),
        poll_async=dict(type='bool', default=True)
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )
    return module


def execute_module(module):
    actt = AnsibleCloudStackTrafficType(module)
    state = module.params.get('state')

    if state in ['present']:
        result = actt.present_traffic_type()
    else:
        result = actt.absent_traffic_type()

    return actt.get_result(result)


def main():
    module = setup_module_object()
    result = execute_module(module)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
