#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = '''
---
module: ec2_snapshot_copy
short_description: copies an EC2 snapshot and returns the new Snapshot ID.
description:
    - Copies an EC2 Snapshot from a source region to a destination region.
version_added: "2.4"
options:
  source_region:
    description:
      - The source region the Snapshot should be copied from.
    required: true
  source_snapshot_id:
    description:
      - The ID of the Snapshot in source region that should be copied.
    required: true
  description:
    description:
      - An optional human-readable string describing purpose of the new Snapshot.
  encrypted:
    description:
      - Whether or not the destination Snapshot should be encrypted.
    type: bool
    default: 'no'
  kms_key_id:
    description:
      - KMS key id used to encrypt snapshot. If not specified, defaults to EBS Customer Master Key (CMK) for that account.
  wait:
    description:
      - Wait for the copied Snapshot to be in 'Available' state before returning.
    type: bool
    default: 'no'
  wait_timeout:
    version_added: "2.6"
    description:
      - How long before wait gives up, in seconds.
    default: 600
  tags:
    description:
      - A hash/dictionary of tags to add to the new Snapshot; '{"key":"value"}' and '{"key":"value","key":"value"}'
author: "Deepak Kothandan <deepak.kdy@gmail.com>"
extends_documentation_fragment:
    - aws
    - ec2
requirements:
    - boto3
'''

EXAMPLES = '''
# Basic Snapshot Copy
- ec2_snapshot_copy:
    source_region: eu-central-1
    region: eu-west-1
    source_snapshot_id: snap-xxxxxxx

# Copy Snapshot and wait until available
- ec2_snapshot_copy:
    source_region: eu-central-1
    region: eu-west-1
    source_snapshot_id: snap-xxxxxxx
    wait: yes
    wait_timeout: 1200   # Default timeout is 600
  register: snapshot_id

# Tagged Snapshot copy
- ec2_snapshot_copy:
    source_region: eu-central-1
    region: eu-west-1
    source_snapshot_id: snap-xxxxxxx
    tags:
        Name: Snapshot-Name

# Encrypted Snapshot copy
- ec2_snapshot_copy:
    source_region: eu-central-1
    region: eu-west-1
    source_snapshot_id: snap-xxxxxxx
    encrypted: yes

# Encrypted Snapshot copy with specified key
- ec2_snapshot_copy:
    source_region: eu-central-1
    region: eu-west-1
    source_snapshot_id: snap-xxxxxxx
    encrypted: yes
    kms_key_id: arn:aws:kms:eu-central-1:XXXXXXXXXXXX:key/746de6ea-50a4-4bcb-8fbc-e3b29f2d367b
'''

RETURN = '''
snapshot_id:
    description: snapshot id of the newly created snapshot
    returned: when snapshot copy is successful
    type: string
    sample: "snap-e9095e8c"
'''

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (boto3_conn, ec2_argument_spec, get_aws_connection_info, camel_dict_to_snake_dict)
from ansible.module_utils._text import to_native

try:
    import boto3
    from botocore.exceptions import ClientError, WaiterError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def copy_snapshot(module, ec2):
    """
    Copies an EC2 Snapshot to another region

    module : AnsibleModule object
    ec2: ec2 connection object
    """

    params = {
        'SourceRegion': module.params.get('source_region'),
        'SourceSnapshotId': module.params.get('source_snapshot_id'),
        'Description': module.params.get('description')
    }

    if module.params.get('encrypted'):
        params['Encrypted'] = True

    if module.params.get('kms_key_id'):
        params['KmsKeyId'] = module.params.get('kms_key_id')

    try:
        snapshot_id = ec2.copy_snapshot(**params)['SnapshotId']
        if module.params.get('wait'):
            delay = 15
            # Add one to max_attempts as wait() increment
            # its counter before assessing it for time.sleep()
            max_attempts = (module.params.get('wait_timeout') // delay) + 1
            ec2.get_waiter('snapshot_completed').wait(
                SnapshotIds=[snapshot_id],
                WaiterConfig=dict(Delay=delay, MaxAttempts=max_attempts)
            )
        if module.params.get('tags'):
            ec2.create_tags(
                Resources=[snapshot_id],
                Tags=[{'Key': k, 'Value': v} for k, v in module.params.get('tags').items()]
            )

    except WaiterError as we:
        module.fail_json(msg='An error occurred waiting for the snapshot to become available. (%s)' % str(we), exception=traceback.format_exc())
    except ClientError as ce:
        module.fail_json(msg=str(ce), exception=traceback.format_exc(), **camel_dict_to_snake_dict(ce.response))

    module.exit_json(changed=True, snapshot_id=snapshot_id)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        source_region=dict(required=True),
        source_snapshot_id=dict(required=True),
        description=dict(default=''),
        encrypted=dict(type='bool', default=False, required=False),
        kms_key_id=dict(type='str', required=False),
        wait=dict(type='bool', default=False),
        wait_timeout=dict(type='int', default=600),
        tags=dict(type='dict')))

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO3:
        module.fail_json(msg='botocore and boto3 are required.')

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    client = boto3_conn(module, conn_type='client', resource='ec2',
                        region=region, endpoint=ec2_url, **aws_connect_kwargs)

    copy_snapshot(module, client)


if __name__ == '__main__':
    main()
