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
module: ec2_snapshot_facts
short_description: Gather facts about ec2 volume snapshots in AWS
description:
    - Gather facts about ec2 volume snapshots in AWS
version_added: "2.1"
author: "Rob White (@wimnat)"
options:
  snapshot_ids:
    description:
      - If you specify one or more snapshot IDs, only snapshots that have the specified IDs are returned.
    required: false
    default: []
  owner_ids:
    description:
      - If you specify one or more snapshot owners, only snapshots from the specified owners and for which you have \
      access are returned.
    required: false
    default: []
  restorable_by_user_ids:
    description:
      - If you specify a list of restorable users, only snapshots with create snapshot permissions for those users are \
      returned.
    required: false
    default: []
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value. See \
      U(http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeSnapshots.html) for possible filters. Filter \
      names and values are case sensitive.
    required: false
    default: {}
notes:
  - By default, the module will return all snapshots, including public ones. To limit results to snapshots owned by \
  the account use the filter 'owner-id'.

extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather facts about all snapshots, including public ones
- ec2_snapshot_facts:

# Gather facts about all snapshots owned by the account 0123456789
- ec2_snapshot_facts:
    filters:
      owner-id: 0123456789

# Or alternatively...
- ec2_snapshot_facts:
    owner_ids:
      - 0123456789

# Gather facts about a particular snapshot using ID
- ec2_snapshot_facts:
    filters:
      snapshot-id: snap-00112233

# Or alternatively...
- ec2_snapshot_facts:
    snapshot_ids:
      - snap-00112233

# Gather facts about any snapshot with a tag key Name and value Example
- ec2_snapshot_facts:
    filters:
      "tag:Name": Example

# Gather facts about any snapshot with an error status
- ec2_snapshot_facts:
    filters:
      status: error

'''

RETURN = '''
snapshot_id:
    description: The ID of the snapshot. Each snapshot receives a unique identifier when it is created.
    type: string
    sample: snap-01234567
volume_id:
    description: The ID of the volume that was used to create the snapshot.
    type: string
    sample: vol-01234567
state:
    description: The snapshot state (completed, pending or error).
    type: string
    sample: completed
state_message:
    description: Encrypted Amazon EBS snapshots are copied asynchronously. If a snapshot copy operation fails (for example, if the proper AWS Key Management Service (AWS KMS) permissions are not obtained) this field displays error state details to help you diagnose why the error occurred.
    type: string
    sample:
start_time:
    description: The time stamp when the snapshot was initiated.
    type: datetime
    sample: 2015-02-12T02:14:02+00:00
progress:
    description: The progress of the snapshot, as a percentage.
    type: string
    sample: 100%
owner_id:
    description: The AWS account ID of the EBS snapshot owner.
    type: string
    sample: 099720109477
description:
    description: The description for the snapshot.
    type: string
    sample: My important backup
volume_size:
    description: The size of the volume, in GiB.
    type: integer
    sample: 8
owner_alias:
    description: The AWS account alias (for example, amazon, self) or AWS account ID that owns the snapshot.
    type: string
    sample: 033440102211
tags:
    description: Any tags assigned to the snapshot.
    type: list
    sample: "{ 'my_tag_key': 'my_tag_value' }"
encrypted:
    description: Indicates whether the snapshot is encrypted.
    type: boolean
    sample: True
kms_key_id:
    description: The full ARN of the AWS Key Management Service (AWS KMS) customer master key (CMK) that was used to \
    protect the volume encryption key for the parent volume.
    type: string
    sample: 74c9742a-a1b2-45cb-b3fe-abcdef123456
data_encryption_key_id:
    description: The data encryption key identifier for the snapshot. This value is a unique identifier that \
    corresponds to the data encryption key that was used to encrypt the original volume or snapshot copy.
    type: string
    sample: "arn:aws:kms:ap-southeast-2:012345678900:key/74c9742a-a1b2-45cb-b3fe-abcdef123456"

'''

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (ansible_dict_to_boto3_filter_list,
        boto3_conn, boto3_tag_list_to_ansible_dict, camel_dict_to_snake_dict,
        ec2_argument_spec, get_aws_connection_info)


def list_ec2_snapshots(connection, module):

    snapshot_ids = module.params.get("snapshot_ids")
    owner_ids = module.params.get("owner_ids")
    restorable_by_user_ids = module.params.get("restorable_by_user_ids")
    filters = ansible_dict_to_boto3_filter_list(module.params.get("filters"))

    try:
        snapshots = connection.describe_snapshots(SnapshotIds=snapshot_ids, OwnerIds=owner_ids, RestorableByUserIds=restorable_by_user_ids, Filters=filters)
    except ClientError as e:
        module.fail_json(msg=e.message)

    # Turn the boto3 result in to ansible_friendly_snaked_names
    snaked_snapshots = []
    for snapshot in snapshots['Snapshots']:
        snaked_snapshots.append(camel_dict_to_snake_dict(snapshot))

    # Turn the boto3 result in to ansible friendly tag dictionary
    for snapshot in snaked_snapshots:
        if 'tags' in snapshot:
            snapshot['tags'] = boto3_tag_list_to_ansible_dict(snapshot['tags'])

    module.exit_json(snapshots=snaked_snapshots)


def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            snapshot_ids=dict(default=[], type='list'),
            owner_ids=dict(default=[], type='list'),
            restorable_by_user_ids=dict(default=[], type='list'),
            filters=dict(default={}, type='dict')
        )
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=[
                               ['snapshot_ids', 'owner_ids', 'restorable_by_user_ids', 'filters']
                           ]
                           )

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)

    if region:
        connection = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_params)
    else:
        module.fail_json(msg="region must be specified")

    list_ec2_snapshots(connection, module)


if __name__ == '__main__':
    main()
