#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2016, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_snapshot_policy
short_description: Manages volume snapshot policies on Apache CloudStack based clouds.
description:
    - Create, update and delete volume snapshot policies.
version_added: '2.2'
author: René Moser (@resmo)
options:
  volume:
    description:
      - Name of the volume.
      - Either I(volume) or I(vm) is required.
    type: str
  volume_type:
    description:
      - Type of the volume.
    type: str
    choices:
      - DATADISK
      - ROOT
    version_added: '2.3'
  vm:
    description:
      - Name of the instance to select the volume from.
      - Use I(volume_type) if VM has a DATADISK and ROOT volume.
      - In case of I(volume_type=DATADISK), additionally use I(device_id) if VM has more than one DATADISK volume.
      - Either I(volume) or I(vm) is required.
    type: str
    version_added: '2.3'
  device_id:
    description:
      - ID of the device on a VM the volume is attached to.
      - This will only be considered if VM has multiple DATADISK volumes.
    type: int
    version_added: '2.3'
  vpc:
    description:
      - Name of the vpc the instance is deployed in.
    type: str
    version_added: '2.3'
  interval_type:
    description:
      - Interval of the snapshot.
    type: str
    default: daily
    choices: [ hourly, daily, weekly, monthly ]
    aliases: [ interval ]
  max_snaps:
    description:
      - Max number of snapshots.
    type: int
    default: 8
    aliases: [ max ]
  schedule:
    description:
      - Time the snapshot is scheduled. Required if I(state=present).
      - 'Format for I(interval_type=HOURLY): C(MM)'
      - 'Format for I(interval_type=DAILY): C(MM:HH)'
      - 'Format for I(interval_type=WEEKLY): C(MM:HH:DD (1-7))'
      - 'Format for I(interval_type=MONTHLY): C(MM:HH:DD (1-28))'
    type: str
  time_zone:
    description:
      - Specifies a timezone for this command.
    type: str
    default: UTC
    aliases: [ timezone ]
  state:
    description:
      - State of the snapshot policy.
    type: str
    default: present
    choices: [ present, absent ]
  domain:
    description:
      - Domain the volume is related to.
    type: str
  account:
    description:
      - Account the volume is related to.
    type: str
  project:
    description:
      - Name of the project the volume is related to.
    type: str
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: ensure a snapshot policy daily at 1h00 UTC
  cs_snapshot_policy:
    volume: ROOT-478
    schedule: '00:1'
    max_snaps: 3
  delegate_to: localhost

- name: ensure a snapshot policy daily at 1h00 UTC on the second DATADISK of VM web-01
  cs_snapshot_policy:
    vm: web-01
    volume_type: DATADISK
    device_id: 2
    schedule: '00:1'
    max_snaps: 3
  delegate_to: localhost

- name: ensure a snapshot policy hourly at minute 5 UTC
  cs_snapshot_policy:
    volume: ROOT-478
    schedule: '5'
    interval_type: hourly
    max_snaps: 1
  delegate_to: localhost

- name: ensure a snapshot policy weekly on Sunday at 05h00, TZ Europe/Zurich
  cs_snapshot_policy:
    volume: ROOT-478
    schedule: '00:5:1'
    interval_type: weekly
    max_snaps: 1
    time_zone: 'Europe/Zurich'
  delegate_to: localhost

- name: ensure a snapshot policy is absent
  cs_snapshot_policy:
    volume: ROOT-478
    interval_type: hourly
    state: absent
  delegate_to: localhost
'''

RETURN = '''
---
id:
  description: UUID of the snapshot policy.
  returned: success
  type: str
  sample: a6f7a5fc-43f8-11e5-a151-feff819cdc9f
interval_type:
  description: interval type of the snapshot policy.
  returned: success
  type: str
  sample: daily
schedule:
  description: schedule of the snapshot policy.
  returned: success
  type: str
  sample:
max_snaps:
  description: maximum number of snapshots retained.
  returned: success
  type: int
  sample: 10
time_zone:
  description: the time zone of the snapshot policy.
  returned: success
  type: str
  sample: Etc/UTC
volume:
  description: the volume of the snapshot policy.
  returned: success
  type: str
  sample: Etc/UTC
zone:
  description: Name of zone the volume is related to.
  returned: success
  type: str
  sample: ch-gva-2
project:
  description: Name of project the volume is related to.
  returned: success
  type: str
  sample: Production
account:
  description: Account the volume is related to.
  returned: success
  type: str
  sample: example account
domain:
  description: Domain the volume is related to.
  returned: success
  type: str
  sample: example domain
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together
)


class AnsibleCloudStackSnapshotPolicy(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackSnapshotPolicy, self).__init__(module)
        self.returns = {
            'schedule': 'schedule',
            'timezone': 'time_zone',
            'maxsnaps': 'max_snaps',
        }
        self.interval_types = {
            'hourly': 0,
            'daily': 1,
            'weekly': 2,
            'monthly': 3,
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
            'virtualmachineid': self.get_vm(key='id', filter_zone=False),
            'type': self.module.params.get('volume_type'),
        }
        volumes = self.query_api('listVolumes', **args)
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
        policies = self.query_api('listSnapshotPolicies', **args)
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
                res = self.query_api('createSnapshotPolicy', **args)
                policy = res['snapshotpolicy']
        return policy

    def absent_snapshot_policy(self):
        policy = self.get_snapshot_policy()
        if policy:
            self.result['changed'] = True
            args = {
                'id': policy['id']
            }
            if not self.module.check_mode:
                self.query_api('deleteSnapshotPolicies', **args)
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
                'volume': volume.get('name'),
                'zone': volume.get('zonename'),
                'project': volume.get('project'),
                'account': volume.get('account'),
                'domain': volume.get('domain'),
            }
            self.result.update(volume_results)
        return self.result


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        volume=dict(),
        volume_type=dict(choices=['DATADISK', 'ROOT']),
        vm=dict(),
        device_id=dict(type='int'),
        vpc=dict(),
        interval_type=dict(default='daily', choices=['hourly', 'daily', 'weekly', 'monthly'], aliases=['interval']),
        schedule=dict(),
        time_zone=dict(default='UTC', aliases=['timezone']),
        max_snaps=dict(type='int', default=8, aliases=['max']),
        state=dict(choices=['present', 'absent'], default='present'),
        domain=dict(),
        account=dict(),
        project=dict(),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        required_one_of=(
            ['vm', 'volume'],
        ),
        supports_check_mode=True
    )

    acs_snapshot_policy = AnsibleCloudStackSnapshotPolicy(module)

    state = module.params.get('state')
    if state in ['absent']:
        policy = acs_snapshot_policy.absent_snapshot_policy()
    else:
        policy = acs_snapshot_policy.present_snapshot_policy()

    result = acs_snapshot_policy.get_result(policy)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
