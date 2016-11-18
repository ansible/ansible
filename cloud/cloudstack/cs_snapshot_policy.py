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
module: cs_snapshot_policy
short_description: Manages volume snapshot policies on Apache CloudStack based clouds.
description:
    - Create, update and delete volume snapshot policies.
version_added: '2.2'
author: "René Moser (@resmo)"
options:
  volume:
    description:
      - Name of the volume.
      - Either C(volume) or C(vm) is required.
    required: false
    default: null
  volume_type:
    description:
      - Type of the volume.
    required: false
    default: null
    choices:
      - DATADISK
      - ROOT
    version_added: "2.3"
  vm:
    description:
      - Name of the instance to select the volume from.
      - Use C(volume_type) if VM has a DATADISK and ROOT volume.
      - In case of C(volume_type=DATADISK), additionally use C(device_id) if VM has more than one DATADISK volume.
      - Either C(volume) or C(vm) is required.
    required: false
    default: null
    version_added: "2.3"
  device_id:
    description:
      - ID of the device on a VM the volume is attached to.
      - This will only be considered if VM has multiple DATADISK volumes.
    required: false
    default: null
    version_added: "2.3"
  vpc:
    description:
      - Name of the vpc the instance is deployed in.
    required: false
    default: null
    version_added: "2.3"
  interval_type:
    description:
      - Interval of the snapshot.
    required: false
    default: 'daily'
    choices: [ 'hourly', 'daily', 'weekly', 'monthly' ]
    aliases: [ 'interval' ]
  max_snaps:
    description:
      - Max number of snapshots.
    required: false
    default: 8
    aliases: [ 'max' ]
  schedule:
    description:
      - Time the snapshot is scheduled. Required if C(state=present).
      - 'Format for C(interval_type=HOURLY): C(MM)'
      - 'Format for C(interval_type=DAILY): C(MM:HH)'
      - 'Format for C(interval_type=WEEKLY): C(MM:HH:DD (1-7))'
      - 'Format for C(interval_type=MONTHLY): C(MM:HH:DD (1-28))'
    required: false
    default: null
  time_zone:
    description:
      - Specifies a timezone for this command.
    required: false
    default: 'UTC'
    aliases: [ 'timezone' ]
  state:
    description:
      - State of the snapshot policy.
    required: false
    default: 'present'
    choices: [ 'present', 'absent' ]
  domain:
    description:
      - Domain the volume is related to.
    required: false
    default: null
  account:
    description:
      - Account the volume is related to.
    required: false
    default: null
  project:
    description:
      - Name of the project the volume is related to.
    required: false
    default: null
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# Ensure a snapshot policy daily at 1h00 UTC
- local_action:
    module: cs_snapshot_policy
    volume: ROOT-478
    schedule: '00:1'
    max_snaps: 3

# Ensure a snapshot policy daily at 1h00 UTC on the second DATADISK of VM web-01
- local_action:
    module: cs_snapshot_policy
    vm: web-01
    volume_type: DATADISK
    device_id: 2
    schedule: '00:1'
    max_snaps: 3

# Ensure a snapshot policy hourly at minute 5 UTC
- local_action:
    module: cs_snapshot_policy
    volume: ROOT-478
    schedule: '5'
    interval_type: hourly
    max_snaps: 1

# Ensure a snapshot policy weekly on Sunday at 05h00, TZ Europe/Zurich
- local_action:
    module: cs_snapshot_policy
    volume: ROOT-478
    schedule: '00:5:1'
    interval_type: weekly
    max_snaps: 1
    time_zone: 'Europe/Zurich'

# Ensure a snapshot policy is absent
- local_action:
    module: cs_snapshot_policy
    volume: ROOT-478
    interval_type: hourly
    state: absent
'''

RETURN = '''
---
id:
  description: UUID of the snapshot policy.
  returned: success
  type: string
  sample: a6f7a5fc-43f8-11e5-a151-feff819cdc9f
interval_type:
  description: interval type of the snapshot policy.
  returned: success
  type: string
  sample: daily
schedule:
  description: schedule of the snapshot policy.
  returned: success
  type: string
  sample:
max_snaps:
  description: maximum number of snapshots retained.
  returned: success
  type: int
  sample: 10
time_zone:
  description: the time zone of the snapshot policy.
  returned: success
  type: string
  sample: Etc/UTC
volume:
  description: the volume of the snapshot policy.
  returned: success
  type: string
  sample: Etc/UTC
zone:
  description: Name of zone the volume is related to.
  returned: success
  type: string
  sample: ch-gva-2
project:
  description: Name of project the volume is related to.
  returned: success
  type: string
  sample: Production
account:
  description: Account the volume is related to.
  returned: success
  type: string
  sample: example account
domain:
  description: Domain the volume is related to.
  returned: success
  type: string
  sample: example domain
'''

# import cloudstack common
from ansible.module_utils.cloudstack import *


class AnsibleCloudStackSnapshotPolicy(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackSnapshotPolicy, self).__init__(module)
        self.returns = {
            'schedule': 'schedule',
            'timezone': 'time_zone',
            'maxsnaps': 'max_snaps',
        }
        self.interval_types = {
            'hourly':   0,
            'daily':    1,
            'weekly':   2,
            'monthly':  3,
        }
        self.volume = None

    def get_interval_type(self):
        interval_type = self.module.params.get('interval_type')
        return self.interval_types[interval_type]

    def get_volume(self, key=None):
        if self.volume:
            return self._get_by_key(key, self.volume)

        args = {
            'name': self.module.params.get('volume'),
            'account': self.get_account(key='name'),
            'domainid': self.get_domain(key='id'),
            'projectid': self.get_project(key='id'),
            'virtualmachineid': self.get_vm(key='id'),
            'type': self.module.params.get('volume_type'),
        }
        volumes = self.cs.listVolumes(**args)
        if volumes:
            if volumes['count'] > 1:
                device_id = self.module.params.get('device_id')
                if not device_id:
                    self.module.fail_json(msg="Found more then 1 volume: combine params 'vm', 'volume_type', 'device_id' and/or 'volume' to select the volume")
                else:
                    for v in volumes['volume']:
                        if v.get('deviceid') == device_id:
                            self.volume = v
                            return self._get_by_key(key, self.volume)
                    self.module.fail_json(msg="No volume found with device id %s" % device_id)
            self.volume = volumes['volume'][0]
            return self._get_by_key(key, self.volume)
        return None

    def get_snapshot_policy(self):
        args = {
            'volumeid': self.get_volume(key='id')
        }
        policies = self.cs.listSnapshotPolicies(**args)
        if policies:
            for policy in policies['snapshotpolicy']:
                if policy['intervaltype'] == self.get_interval_type():
                    return policy
            return None

    def present_snapshot_policy(self):
        required_params = [
            'schedule',
        ]
        self.module.fail_on_missing_params(required_params=required_params)

        policy = self.get_snapshot_policy()
        args = {
            'id': policy.get('id') if policy else None,
            'intervaltype': self.module.params.get('interval_type'),
            'schedule': self.module.params.get('schedule'),
            'maxsnaps': self.module.params.get('max_snaps'),
            'timezone': self.module.params.get('time_zone'),
            'volumeid': self.get_volume(key='id')
        }
        if not policy or (policy and self.has_changed(policy, args, only_keys=['schedule', 'maxsnaps', 'timezone'])):
            self.result['changed'] = True
            if not self.module.check_mode:
                res = self.cs.createSnapshotPolicy(**args)
                policy = res['snapshotpolicy']
                if 'errortext' in policy:
                    self.module.fail_json(msg="Failed: '%s'" % policy['errortext'])
        return policy

    def absent_snapshot_policy(self):
        policy = self.get_snapshot_policy()
        if policy:
            self.result['changed'] = True
            args = {
                'id': policy['id']
            }
            if not self.module.check_mode:
                res = self.cs.deleteSnapshotPolicies(**args)
                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % policy['errortext'])
        return policy

    def get_result(self, policy):
        super(AnsibleCloudStackSnapshotPolicy, self).get_result(policy)
        if policy and 'intervaltype' in policy:
            for key, value in self.interval_types.items():
                if value == policy['intervaltype']:
                    self.result['interval_type'] = key
                    break
        volume = self.get_volume()
        if volume:
            volume_results = {
                'volume':   volume.get('name'),
                'zone':     volume.get('zonename'),
                'project':  volume.get('project'),
                'account':  volume.get('account'),
                'domain':   volume.get('domain'),
            }
            self.result.update(volume_results)
        return self.result


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        volume=dict(default=None),
        volume_type=dict(choices=['DATADISK', 'ROOT'], default=None),
        vm=dict(default=None),
        device_id=dict(type='int', default=None),
        vpc=dict(default=None),
        interval_type=dict(default='daily', choices=['hourly', 'daily', 'weekly', 'monthly'], aliases=['interval']),
        schedule=dict(default=None),
        time_zone=dict(default='UTC', aliases=['timezone']),
        max_snaps=dict(type='int', default=8, aliases=['max']),
        state=dict(choices=['present', 'absent'], default='present'),
        domain=dict(default=None),
        account=dict(default=None),
        project=dict(default=None),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        required_one_of = (
            ['vm', 'volume'],
        ),
        supports_check_mode=True
    )

    try:
        acs_snapshot_policy = AnsibleCloudStackSnapshotPolicy(module)

        state = module.params.get('state')
        if state in ['absent']:
            policy = acs_snapshot_policy.absent_snapshot_policy()
        else:
            policy = acs_snapshot_policy.present_snapshot_policy()

        result = acs_snapshot_policy.get_result(policy)

    except CloudStackException as e:
        module.fail_json(msg='CloudStackException: %s' % str(e))

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
