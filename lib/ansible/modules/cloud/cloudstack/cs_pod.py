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
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_pod
short_description: Manages pods on Apache CloudStack based clouds.
description:
    - Create, update, delete pods.
version_added: "2.1"
author: "René Moser (@resmo)"
options:
  name:
    description:
      - Name of the pod.
    required: true
  id:
    description:
      - uuid of the existing pod.
  start_ip:
    description:
      - Starting IP address for the Pod.
      - Required on C(state=present)
  end_ip:
    description:
      - Ending IP address for the Pod.
  netmask:
    description:
      - Netmask for the Pod.
      - Required on C(state=present)
  gateway:
    description:
      - Gateway for the Pod.
      - Required on C(state=present)
  zone:
    description:
      - Name of the zone in which the pod belongs to.
      - If not set, default zone is used.
  state:
    description:
      - State of the pod.
    default: 'present'
    choices: [ 'present', 'enabled', 'disabled', 'absent' ]
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# Ensure a pod is present
- local_action:
    module: cs_pod
    name: pod1
    zone: ch-zrh-ix-01
    start_ip: 10.100.10.101
    gateway: 10.100.10.1
    netmask: 255.255.255.0

# Ensure a pod is disabled
- local_action:
    module: cs_pod
    name: pod1
    zone: ch-zrh-ix-01
    state: disabled

# Ensure a pod is enabled
- local_action:
    module: cs_pod
    name: pod1
    zone: ch-zrh-ix-01
    state: enabled

# Ensure a pod is absent
- local_action:
    module: cs_pod
    name: pod1
    zone: ch-zrh-ix-01
    state: absent
'''

RETURN = '''
---
id:
  description: UUID of the pod.
  returned: success
  type: string
  sample: 04589590-ac63-4ffc-93f5-b698b8ac38b6
name:
  description: Name of the pod.
  returned: success
  type: string
  sample: pod01
start_ip:
  description: Starting IP of the pod.
  returned: success
  type: string
  sample: 10.100.1.101
end_ip:
  description: Ending IP of the pod.
  returned: success
  type: string
  sample: 10.100.1.254
netmask:
  description: Netmask of the pod.
  returned: success
  type: string
  sample: 255.255.255.0
gateway:
  description: Gateway of the pod.
  returned: success
  type: string
  sample: 10.100.1.1
allocation_state:
  description: State of the pod.
  returned: success
  type: string
  sample: Enabled
zone:
  description: Name of zone the pod is in.
  returned: success
  type: string
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
            args = {}

            uuid = self.module.params.get('id')
            if uuid:
                args['id'] = uuid
                args['zoneid'] = self.get_zone(key='id')
                pods = self.query_api('listPods', **args)
                if pods:
                    self.pod = pods['pod'][0]
                    return self.pod

            args['name'] = self.module.params.get('name')
            args['zoneid'] = self.get_zone(key='id')
            pods = self.query_api('listPods', **args)
            if pods:
                self.pod = pods['pod'][0]
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
