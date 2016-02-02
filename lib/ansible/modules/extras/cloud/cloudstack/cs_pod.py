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
      - uuid of the exising pod.
    default: null
    required: false
  start_ip:
    description:
      - Starting IP address for the Pod.
      - Required on C(state=present)
    default: null
    required: false
  end_ip:
    description:
      - Ending IP address for the Pod.
    default: null
    required: false
  netmask:
    description:
      - Netmask for the Pod.
      - Required on C(state=present)
    default: null
    required: false
  gateway:
    description:
      - Gateway for the Pod.
      - Required on C(state=present)
    default: null
    required: false
  zone:
    description:
      - Name of the zone in which the pod belongs to.
      - If not set, default zone is used.
    required: false
    default: null
  state:
    description:
      - State of the pod.
    required: false
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

try:
    from cs import CloudStack, CloudStackException, read_config
    has_lib_cs = True
except ImportError:
    has_lib_cs = False

# import cloudstack common
from ansible.module_utils.cloudstack import *

class AnsibleCloudStackPod(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackPod, self).__init__(module)
        self.returns = {
            'endip':            'end_ip',
            'startip':          'start_ip',
            'gateway':          'gateway',
            'netmask':          'netmask',
            'allocationstate':  'allocation_state',
        }
        self.pod = None


    def _get_common_pod_args(self):
        args = {}
        args['name'] = self.module.params.get('name')
        args['zoneid'] = self.get_zone(key='id')
        args['startip'] = self.module.params.get('start_ip')
        args['endip'] = self.module.params.get('end_ip')
        args['netmask'] = self.module.params.get('netmask')
        args['gateway'] = self.module.params.get('gateway')
        state = self.module.params.get('state')
        if state in [ 'enabled', 'disabled']:
            args['allocationstate'] = state.capitalize()
        return args


    def get_pod(self):
        if not self.pod:
            args = {}

            uuid = self.module.params.get('id')
            if uuid:
                args['id'] = uuid
                args['zoneid'] = self.get_zone(key='id')
                pods = self.cs.listPods(**args)
                if pods:
                    self.pod = pods['pod'][0]
                    return self.pod

            args['name'] = self.module.params.get('name')
            args['zoneid'] = self.get_zone(key='id')
            pods = self.cs.listPods(**args)
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
            res = self.cs.createPod(**args)
            if 'errortext' in res:
                self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
            pod = res['pod']
        return pod


    def _update_pod(self):
        pod = self.get_pod()
        args = self._get_common_pod_args()
        args['id'] = pod['id']

        if self.has_changed(args, pod):
            self.result['changed'] = True

            if not self.module.check_mode:
                res = self.cs.updatePod(**args)
                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
                pod = res['pod']
        return pod


    def absent_pod(self):
        pod = self.get_pod()
        if pod:
            self.result['changed'] = True

            args = {}
            args['id'] = pod['id']

            if not self.module.check_mode:
                res = self.cs.deletePod(**args)
                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
        return pod


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        id = dict(default=None),
        name = dict(required=True),
        gateway = dict(default=None),
        netmask = dict(default=None),
        start_ip = dict(default=None),
        end_ip = dict(default=None),
        zone = dict(default=None),
        state = dict(choices=['present', 'enabled', 'disabled', 'absent'], default='present'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    if not has_lib_cs:
        module.fail_json(msg="python library cs required: pip install cs")

    try:
        acs_pod = AnsibleCloudStackPod(module)
        state = module.params.get('state')
        if state in ['absent']:
            pod = acs_pod.absent_pod()
        else:
            pod = acs_pod.present_pod()

        result = acs_pod.get_result(pod)

    except CloudStackException as e:
        module.fail_json(msg='CloudStackException: %s' % str(e))

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
