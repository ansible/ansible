#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: ec2_snapshot
short_description: creates a snapshot from an existing volume
description:
    - creates an EC2 snapshot from an existing EBS volume
version_added: "1.5"
options:
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
  last_snapshot_min_age:
    description:
      - If the volume's most recent snapshot has started less than `last_snapshot_min_age' minutes ago, a new snapshot will not be created.
    required: false
    default: 0
    version_added: "2.0"

author: "Will Thames (@willthames)"
extends_documentation_fragment:
    - aws
    - ec2
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

# Create a snapshot only if the most recent one is older than 1 hour
- local_action:
    module: ec2_snapshot
    volume_id: vol-abcdef12
    last_snapshot_min_age: 60
'''

import time
import datetime

try:
    import boto.exception
except ImportError:
    pass  # Taken care of by ec2.HAS_BOTO

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import HAS_BOTO, ec2_argument_spec, ec2_connect


# Find the most recent snapshot
def _get_snapshot_starttime(snap):
    return datetime.datetime.strptime(snap.start_time, '%Y-%m-%dT%H:%M:%S.000Z')


def _get_most_recent_snapshot(snapshots, max_snapshot_age_secs=None, now=None):
    """
    Gets the most recently created snapshot and optionally filters the result
    if the snapshot is too old
    :param snapshots: list of snapshots to search
    :param max_snapshot_age_secs: filter the result if its older than this
    :param now: simulate time -- used for unit testing
    :return:
    """
    if len(snapshots) == 0:
        return None

    if not now:
        now = datetime.datetime.utcnow()

    youngest_snapshot = max(snapshots, key=_get_snapshot_starttime)

    # See if the snapshot is younger that the given max age
    snapshot_start = datetime.datetime.strptime(youngest_snapshot.start_time, '%Y-%m-%dT%H:%M:%S.000Z')
    snapshot_age = now - snapshot_start

    if max_snapshot_age_secs is not None:
        if snapshot_age.total_seconds() > max_snapshot_age_secs:
            return None

    return youngest_snapshot


def _create_with_wait(snapshot, wait_timeout_secs, sleep_func=time.sleep):
    """
    Wait for the snapshot to be created
    :param snapshot:
    :param wait_timeout_secs: fail this step after this many seconds
    :param sleep_func:
    :return:
    """
    time_waited = 0
    snapshot.update()
    while snapshot.status != 'completed':
        sleep_func(3)
        snapshot.update()
        time_waited += 3
        if wait_timeout_secs and time_waited > wait_timeout_secs:
            return False
    return True


def create_snapshot(module, ec2, state=None, description=None, wait=None,
                    wait_timeout=None, volume_id=None, instance_id=None,
                    snapshot_id=None, device_name=None, snapshot_tags=None,
                    last_snapshot_min_age=None):
    snapshot = None
    changed = False

    required = [volume_id, snapshot_id, instance_id]
    if required.count(None) != len(required) - 1:  # only 1 must be set
        module.fail_json(msg='One and only one of volume_id or instance_id or snapshot_id must be specified')
    if instance_id and not device_name or device_name and not instance_id:
        module.fail_json(msg='Instance ID and device name must both be specified')

    if instance_id:
        try:
            volumes = ec2.get_all_volumes(filters={'attachment.instance-id': instance_id, 'attachment.device': device_name})
        except boto.exception.BotoServerError as e:
            module.fail_json(msg="%s: %s" % (e.error_code, e.error_message))

        if not volumes:
            module.fail_json(msg="Could not find volume with name %s attached to instance %s" % (device_name, instance_id))

        volume_id = volumes[0].id

    if state == 'absent':
        if not snapshot_id:
            module.fail_json(msg='snapshot_id must be set when state is absent')
        try:
            ec2.delete_snapshot(snapshot_id)
        except boto.exception.BotoServerError as e:
            # exception is raised if snapshot does not exist
            if e.error_code == 'InvalidSnapshot.NotFound':
                module.exit_json(changed=False)
            else:
                module.fail_json(msg="%s: %s" % (e.error_code, e.error_message))

        # successful delete
        module.exit_json(changed=True)

    if last_snapshot_min_age > 0:
        try:
            current_snapshots = ec2.get_all_snapshots(filters={'volume_id': volume_id})
        except boto.exception.BotoServerError as e:
            module.fail_json(msg="%s: %s" % (e.error_code, e.error_message))

        last_snapshot_min_age = last_snapshot_min_age * 60  # Convert to seconds
        snapshot = _get_most_recent_snapshot(current_snapshots,
                                             max_snapshot_age_secs=last_snapshot_min_age)
    try:
        # Create a new snapshot if we didn't find an existing one to use
        if snapshot is None:
            snapshot = ec2.create_snapshot(volume_id, description=description)
            changed = True
        if wait:
            if not _create_with_wait(snapshot, wait_timeout):
                module.fail_json(msg='Timed out while creating snapshot.')
        if snapshot_tags:
            for k, v in snapshot_tags.items():
                snapshot.add_tag(k, v)
    except boto.exception.BotoServerError as e:
        module.fail_json(msg="%s: %s" % (e.error_code, e.error_message))

    module.exit_json(changed=changed,
                     snapshot_id=snapshot.id,
                     volume_id=snapshot.volume_id,
                     volume_size=snapshot.volume_size,
                     tags=snapshot.tags.copy())


def create_snapshot_ansible_module():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            volume_id=dict(),
            description=dict(),
            instance_id=dict(),
            snapshot_id=dict(),
            device_name=dict(),
            wait=dict(type='bool', default=True),
            wait_timeout=dict(type='int', default=0),
            last_snapshot_min_age=dict(type='int', default=0),
            snapshot_tags=dict(type='dict', default=dict()),
            state=dict(choices=['absent', 'present'], default='present'),
        )
    )
    module = AnsibleModule(argument_spec=argument_spec)
    return module


def main():
    module = create_snapshot_ansible_module()

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    volume_id = module.params.get('volume_id')
    snapshot_id = module.params.get('snapshot_id')
    description = module.params.get('description')
    instance_id = module.params.get('instance_id')
    device_name = module.params.get('device_name')
    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')
    last_snapshot_min_age = module.params.get('last_snapshot_min_age')
    snapshot_tags = module.params.get('snapshot_tags')
    state = module.params.get('state')

    ec2 = ec2_connect(module)

    create_snapshot(
        module=module,
        state=state,
        description=description,
        wait=wait,
        wait_timeout=wait_timeout,
        ec2=ec2,
        volume_id=volume_id,
        instance_id=instance_id,
        snapshot_id=snapshot_id,
        device_name=device_name,
        snapshot_tags=snapshot_tags,
        last_snapshot_min_age=last_snapshot_min_age
    )


if __name__ == '__main__':
    main()
