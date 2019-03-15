#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_pod
short_description: Manages pods on Apache CloudStack based clouds.
description:
    - Create, update, delete pods.
version_added: '2.1'
author: René Moser (@resmo)
options:
  name:
    description:
      - Name of the pod.
    type: str
    required: true
  id:
    description:
      - uuid of the existing pod.
    type: str
  start_ip:
    description:
      - Starting IP address for the Pod.
      - Required on I(state=present)
    type: str
  end_ip:
    description:
      - Ending IP address for the Pod.
    type: str
  netmask:
    description:
      - Netmask for the Pod.
      - Required on I(state=present)
    type: str
  gateway:
    description:
      - Gateway for the Pod.
      - Required on I(state=present)
    type: str
  zone:
    description:
      - Name of the zone in which the pod belongs to.
      - If not set, default zone is used.
    type: str
  state:
    description:
      - State of the pod.
    type: str
    default: present
    choices: [ present, enabled, disabled, absent ]
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: Ensure a pod is present
  cs_pod:
    name: pod1
    zone: ch-zrh-ix-01
    start_ip: 10.100.10.101
    gateway: 10.100.10.1
    netmask: 255.255.255.0
  delegate_to: localhost

- name: Ensure a pod is disabled
  cs_pod:
    name: pod1
    zone: ch-zrh-ix-01
    state: disabled
  delegate_to: localhost

- name: Ensure a pod is enabled
  cs_pod:
    name: pod1
    zone: ch-zrh-ix-01
    state: enabled
  delegate_to: localhost

- name: Ensure a pod is absent
  cs_pod:
    name: pod1
    zone: ch-zrh-ix-01
    state: absent
  delegate_to: localhost
'''

RETURN = '''
---
id:
  description: UUID of the pod.
  returned: success
  type: str
  sample: 04589590-ac63-4ffc-93f5-b698b8ac38b6
name:
  description: Name of the pod.
  returned: success
  type: str
  sample: pod01
start_ip:
  description: Starting IP of the pod.
  returned: success
  type: str
  sample: 10.100.1.101
end_ip:
  description: Ending IP of the pod.
  returned: success
  type: str
  sample: 10.100.1.254
netmask:
  description: Netmask of the pod.
  returned: success
  type: str
  sample: 255.255.255.0
gateway:
  description: Gateway of the pod.
  returned: success
  type: str
  sample: 10.100.1.1
allocation_state:
  description: State of the pod.
  returned: success
  type: str
  sample: Enabled
zone:
  description: Name of zone the pod is in.
  returned: success
  type: str
  sample: ch-gva-2
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together
)


class AnsibleCloudStackPod(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackPod, self).__init__(module)
        self.returns = {
            'endip': 'end_ip',
            'startip': 'start_ip',
            'gateway': 'gateway',
            'netmask': 'netmask',
            'allocationstate': 'allocation_state',
        }
        self.pod = None

    def _get_common_pod_args(self):
        args = {
            'name': self.module.params.get('name'),
            'zoneid': self.get_zone(key='id'),
            'startip': self.module.params.get('start_ip'),
            'endip': self.module.params.get('end_ip'),
            'netmask': self.module.params.get('netmask'),
            'gateway': self.module.params.get('gateway')
        }
        state = self.module.params.get('state')
        if state in ['enabled', 'disabled']:
            args['allocationstate'] = state.capitalize()
        return args

    def get_pod(self):
        if not self.pod:
            args = {
                'zoneid': self.get_zone(key='id')
            }

            uuid = self.module.params.get('id')
            if uuid:
                args['id'] = uuid
            else:
                args['name'] = self.module.params.get('name')

            pods = self.query_api('listPods', **args)
            if pods:
                for pod in pods['pod']:
                    if not args['name']:
                        self.pod = self._transform_ip_list(pod)
                        break
                    elif args['name'] == pod['name']:
                        self.pod = self._transform_ip_list(pod)
                        break
        return self.pod

    def present_pod(self):
        pod = self.get_pod()
        if pod:
            pod = self._update_pod()
        else:
            pod = self._create_pod()
        return pod

    def _create_pod(self):
        required_params = [
            'start_ip',
            'netmask',
            'gateway',
        ]
        self.module.fail_on_missing_params(required_params=required_params)

        pod = None
        self.result['changed'] = True
        args = self._get_common_pod_args()
        if not self.module.check_mode:
            res = self.query_api('createPod', **args)
            pod = res['pod']
        return pod

    def _update_pod(self):
        pod = self.get_pod()
        args = self._get_common_pod_args()
        args['id'] = pod['id']

        if self.has_changed(args, pod):
            self.result['changed'] = True

            if not self.module.check_mode:
                res = self.query_api('updatePod', **args)
                pod = res['pod']
        return pod

    def absent_pod(self):
        pod = self.get_pod()
        if pod:
            self.result['changed'] = True

            args = {
                'id': pod['id']
            }
            if not self.module.check_mode:
                self.query_api('deletePod', **args)
        return pod

    def _transform_ip_list(self, resource):
        """ Workaround for 4.11 return API break """
        keys = ['endip', 'startip']
        if resource:
            for key in keys:
                if key in resource and isinstance(resource[key], list):
                    resource[key] = resource[key][0]
        return resource

    def get_result(self, pod):
        pod = self._transform_ip_list(pod)
        super(AnsibleCloudStackPod, self).get_result(pod)
        return self.result


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        id=dict(),
        name=dict(required=True),
        gateway=dict(),
        netmask=dict(),
        start_ip=dict(),
        end_ip=dict(),
        zone=dict(),
        state=dict(choices=['present', 'enabled', 'disabled', 'absent'], default='present'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    acs_pod = AnsibleCloudStackPod(module)
    state = module.params.get('state')
    if state in ['absent']:
        pod = acs_pod.absent_pod()
    else:
        pod = acs_pod.present_pod()

    result = acs_pod.get_result(pod)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
