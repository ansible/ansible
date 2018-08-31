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
module: cs_storage_ip_range
short_description: Manages Storage IP ranges on Apache CloudStack based clouds.
description:
    - Create updates and remove Storage IP ranges.
version_added: "2.4"
author: "Netservers Ltd. (@netservers)"
options:
  pod:
    description:
      - Pod name.
    required: true
  ipv4_start:
    description:
      - Start address for ipv4 range.
    required: true
    default: none
  ipv4_end:
    description:
      - End address for ipv4 range.
    required: false
    default: none
  ipv4_gateway:
    description:
      - Gateway IP for ipv4 range.
    required: true
    default: none
  ipv4_netmask:
    description:
      - Gateway IP for ipv4 range.
    required: true
    default: none
  vlan:
    description:
      - Optional. The vlan the ip range sits on, default to Null when it is not specificed
      - This is mainly for Vmware as other hypervisors can directly retrieve bridge from physical network traffic type table
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
# Ensure a storage_ip_range is present
- local_action:
    module: cs_storage_ip_range
    pod: pod01
    ipv4_start: 1.0.0.10
    ipv4_end: 1.0.0.100
    ipv4_netmask: 255.255.255.0
    ipv4_gateway: 1.0.0.1

# Ensure a storage_ip_range is absent
- local_action:
    module: cs_storage_ip_range
    pod: pod01
    ipv4_start: 1.0.0.10
    state: absent
'''

RETURN = '''
---
id:
  description: UUID of the Storage IP range.
  returned: success
  type: string
  sample: a3fca65a-7db1-4891-b97c-48806a978a96
ipv4_start:
  description: The start IP for the range.
  returned: success
  type: string
  sample: 10.0.0.10
ipv4_end:
  description: The end IP for the range.
  returned: success
  type: string
  sample: 10.0.0.20
ipv4_gateway:
  description: The gateway IP for the range.
  returned: success
  type: string
  sample: 10.0.0.1
ipv4_netmask:
  description: The gateway IP for the range.
  returned: success
  type: string
  sample: 255.255.255.0
vlan:
  description: The VLAN id for the range.
  returned: success
  type: string
  sample: 200
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    CloudStackException,
    cs_argument_spec,
    cs_required_together,
)


class AnsibleCloudStackStorageIpRange(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackStorageIpRange, self).__init__(module)
        self.returns = {
            'startip': 'ipv4_start',
            'endip': 'ipv4_end',
            'gateway': 'ipv4_gateway',
            'netmask': 'ipv4_netmask',
            'vlan': 'vlan',
        }
        self.storage_ip_range = None
        self.pod = None

    def _get_common_args(self):
        args = {
            'podid': self.get_pod(key='id'),
            'vlan': self.module.params.get('vlan'),
            'startip': self.module.params.get('ipv4_start'),
            'endip': self.module.params.get('ipv4_end'),
            'gateway': self.module.params.get('ipv4_gateway'),
            'netmask': self.module.params.get('ipv4_netmask'),
        }
        return args

    def get_storage_ip_range(self, key=None):
        if self.storage_ip_range:
            return self.storage_ip_range
        pod = self.module.params.get('pod')
        ipv4_start = self.module.params.get('ipv4_start')

        args = {'podid': self.get_pod(key='id')}

        ranges = self.cs.listStorageNetworkIpRange(**args)
        if ranges:
            for r in ranges['storagenetworkiprange']:
                if ipv4_start == r['startip']:
                    self.storage_ip_range = r
                    break

        return self.storage_ip_range

    def present_storage_ip_range(self):
        range = self.get_storage_ip_range()
        if range:
            range = self._update_storage_ip_range()
        else:
            range = self._create_storage_ip_range()
        return range

    def _create_storage_ip_range(self):
        args = self._get_common_args()

        self.result['changed'] = True

        range = None
        if not self.module.check_mode:
            res = self.cs.createStorageNetworkIpRange(**args)
            if 'errortext' in res:
                self.module.fail_json(msg="Failed: '%s'" % res['errortext'])

            poll_async = self.module.params.get('poll_async')
            if poll_async:
                range = self.poll_job(res, 'storagenetworkiprange')

        self.result['changed'] = True
        return range

    def _update_storage_ip_range(self):
        range = self.get_storage_ip_range()

        args = self._get_common_args()
        args['id'] = range['id']

        if self.has_changed(args, range):
            self.result['changed'] = True

            if not self.module.check_mode:
                res = self.cs.updateStorageNetworkIpRange(**args)
                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])

                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    range = self.poll_job(res, 'storagenetworkiprange')
        return range

    def absent_storage_ip_range(self):
        range = self.get_storage_ip_range()
        if range:
            self.result['changed'] = True

            args = {
                'id': range['id'],
            }
            if not self.module.check_mode:
                res = self.cs.deleteStorageNetworkIpRange(**args)
                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])

                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    success = self.poll_job(res, 'success')

        return range

    def get_pod(self, key=None):
        pod = self.module.params.get('pod')
        args = {
            'name': pod,
            'zoneid': self.get_zone(key='id'),
        }
        pods = self.cs.listPods(**args)
        if pods:
            return self._get_by_key(key, pods['pod'][0])
        self.module.fail_json(msg="Pod %s not found in zone %s." % (pod, self.get_zone(key='name')))


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        pod=dict(required=True),
        vlan=dict(type='int', default=None),
        ipv4_start=dict(default=None),
        ipv4_end=dict(default=None),
        ipv4_gateway=dict(default=None),
        ipv4_netmask=dict(default=None),
        state=dict(choices=['present', 'absent'], default='present'),
        poll_async=dict(type='bool', default=True),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    try:
        acs_storage_ip_range = AnsibleCloudStackStorageIpRange(module)

        state = module.params.get('state')
        if state in ['absent']:
            range = acs_storage_ip_range.absent_storage_ip_range()
        else:
            range = acs_storage_ip_range.present_storage_ip_range()

        result = acs_storage_ip_range.get_result(range)

    except CloudStackException as e:
        module.fail_json(msg='CloudStackException: %s' % str(e))

    module.exit_json(**result)

if __name__ == '__main__':
    main()
