#!/usr/bin/python
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: ec2_snapshot
short_description: creates a snapshot from an existing volume
description:
    - creates an EC2 snapshot from an existing EBS volume
version_added: "1.5"
options:
  region:
    description:
      - The AWS region to use. If not specified then the value of the EC2_REGION environment variable, if any, is used.
    required: false
    aliases: ['aws_region', 'ec2_region']
  volume_id:
    description:
      - volume from which to take the snapshot
    required: false
  description:
    description:
      - description to be applied to the snapshot
    required: false
  instance_id:
    description:
    - instance that has the required volume to snapshot mounted
    required: false
  device_name:
    description:
    - device name of a mounted volume to be snapshotted
    required: false
  snapshot_tags:
    description:
      - a hash/dictionary of tags to add to the snapshot
    required: false
    version_added: "1.6"
  wait:
    description:
      - wait for the snapshot to be ready
    choices: ['yes', 'no']
    required: false
    default: yes
    version_added: "1.5.1"
  wait_timeout:
    description:
      - how long before wait gives up, in seconds
      - specify 0 to wait forever
    required: false
    default: 0
    version_added: "1.5.1"
  state:
    description:
      - whether to add or create a snapshot
    required: false
    default: present
    choices: ['absent', 'present']
    version_added: "1.9"
  snapshot_id:
    description:
      - snapshot id to remove
    required: false
    version_added: "1.9"

author: Will Thames
extends_documentation_fragment: aws
'''

EXAMPLES = '''
# Simple snapshot of volume using volume_id
- ec2_snapshot:
    volume_id: vol-abcdef12   
    description: snapshot of /data from DB123 taken 2013/11/28 12:18:32

# Snapshot of volume mounted on device_name attached to instance_id
- ec2_snapshot:
    instance_id: i-12345678
    device_name: /dev/sdb1
    description: snapshot of /data from DB123 taken 2013/11/28 12:18:32

# Snapshot of volume with tagging
- ec2_snapshot:
    instance_id: i-12345678
    device_name: /dev/sdb1
    snapshot_tags:
        frequency: hourly
        source: /data

# Remove a snapshot
- local_action:
    module: ec2_snapshot
    snapshot_id: snap-abcd1234
    state: absent
'''    

import sys
import time

try:
    import boto.ec2
except ImportError:
    print "failed=True msg='boto required for this module'"
    sys.exit(1)

def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            volume_id = dict(),
            description = dict(),
            instance_id = dict(),
            snapshot_id = dict(),
            device_name = dict(),
            wait = dict(type='bool', default='true'),
            wait_timeout = dict(default=0),
            snapshot_tags = dict(type='dict', default=dict()),
            state = dict(choices=['absent','present'], default='present'),
        )
    )
    module = AnsibleModule(argument_spec=argument_spec)

    volume_id = module.params.get('volume_id')
    snapshot_id = module.params.get('snapshot_id')
    description = module.params.get('description')
    instance_id = module.params.get('instance_id')
    device_name = module.params.get('device_name')
    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')
    snapshot_tags = module.params.get('snapshot_tags')
    state = module.params.get('state')

    if not volume_id and not instance_id and not snapshot_id or volume_id and instance_id and snapshot_id:
        module.fail_json('One and only one of volume_id or instance_id or snapshot_id must be specified')
    if instance_id and not device_name or device_name and not instance_id:
        module.fail_json('Instance ID and device name must both be specified')

    ec2 = ec2_connect(module)

    if instance_id:
        try:
            volumes = ec2.get_all_volumes(filters={'attachment.instance-id': instance_id, 'attachment.device': device_name})
            if not volumes:
                module.fail_json(msg="Could not find volume with name %s attached to instance %s" % (device_name, instance_id))
            volume_id = volumes[0].id
        except boto.exception.BotoServerError, e:
            module.fail_json(msg = "%s: %s" % (e.error_code, e.error_message))

    if state == 'absent':
        if not snapshot_id:
            module.fail_json(msg = 'snapshot_id must be set when state is absent')
        try:
            snapshots = ec2.get_all_snapshots([snapshot_id])
            ec2.delete_snapshot(snapshot_id)
            module.exit_json(changed=True)
        except boto.exception.BotoServerError, e:
            # exception is raised if snapshot does not exist
            if e.error_code == 'InvalidSnapshot.NotFound':
                module.exit_json(changed=False)
            else:
                module.fail_json(msg = "%s: %s" % (e.error_code, e.error_message))

    try:
        snapshot = ec2.create_snapshot(volume_id, description=description)
        time_waited = 0
        if wait:
            snapshot.update()
            while snapshot.status != 'completed':
                time.sleep(3)
                snapshot.update()
                time_waited += 3
                if wait_timeout and time_waited > wait_timeout:
                    module.fail_json('Timed out while creating snapshot.')
        for k, v in snapshot_tags.items():
            snapshot.add_tag(k, v)
    except boto.exception.BotoServerError, e:
        module.fail_json(msg = "%s: %s" % (e.error_code, e.error_message))

    module.exit_json(changed=True, snapshot_id=snapshot.id, volume_id=snapshot.volume_id,
            volume_size=snapshot.volume_size, tags=snapshot.tags.copy())

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

main()
