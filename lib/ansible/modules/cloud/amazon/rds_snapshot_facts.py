#!/usr/bin/python
# Copyright (c) 2014-2017 Ansible Project
# Copyright (c) 2017, 2018 Will Thames
# Copyright (c) 2017, 2018 Michael De La Rue
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: rds_snapshot_facts
version_added: "2.6"
short_description: obtain facts about one or more RDS snapshots
description:
  - obtain facts about one or more RDS snapshots.  This does not currently include
  - Aurora snapshots but may in future change to include them.
options:
  db_snapshot_identifier:
    description:
      - Name of an RDS snapshot. Mutually exclusive with I(db_instance_identifier)
    required: false
    aliases:
      - snapshot_name
  db_instance_identifier:
    description:
      - RDS instance name for which to find snapshots. Mutually exclusive with I(db_snapshot_identifier)
    required: false
  snapshot_type:
    description:
      - Type of snapshot to find. By default both automated and manual
        snapshots will be returned.
    required: false
    choices: ['automated', 'manual', 'shared', 'public']

requirements:
    - "python >= 2.6"
    - "boto3"
author:
    - "Will Thames (@willthames)"
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Get facts about an snapshot
- rds_snapshot_facts:
    db_snapshot_identifier: snapshot_name
  register: new_database_facts

# Get all RDS snapshots for an RDS instance
- rds_snapshot_facts:
    db_instance_identifier: helloworld-rds-master
'''

RETURN = '''
snapshots:
    description: zero or more snapshots that match the (optional) parameters
    type: list
    returned: always
    sample:
       "snapshots": [
           {
               "availability_zone": "ap-southeast-2b",
               "create_time": "2017-02-23T19:36:26.303000+00:00",
               "id": "rds:helloworld-rds-master-2017-02-23-19-36",
               "instance_created": "2017-02-16T23:04:16.619000+00:00",
               "instance_id": "helloworld-rds-master",
               "snapshot_type": "automated",
               "status": "available"
           }
       ]
'''

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import AWSRetry, boto3_tag_list_to_ansible_dict
from ansible.module_utils.aws.rds import snapshot_to_facts

try:
    import botocore
except BaseException:
    pass  # caught by imported HAS_BOTO3


def snapshot_facts(module, conn):
    snapshot_name = module.params.get('db_snapshot_identifier')
    snapshot_type = module.params.get('snapshot_type')
    instance_name = module.params.get('db_instance_identifier')

    params = dict()
    if snapshot_name:
        params['DBSnapshotIdentifier'] = snapshot_name
    if instance_name:
        params['DBInstanceIdentifier'] = instance_name
    if snapshot_type:
        params['SnapshotType'] = snapshot_type
        if snapshot_type == 'public':
            params['IsPublic'] = True
        elif snapshot_type == 'shared':
            params['IsShared'] = True

    paginator = conn.get_paginator('describe_db_snapshots')
    try:
        results = paginator.paginate(**params).build_full_result()['DBSnapshots']
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'DBSnapshotNotFound':
            results = []
        else:
            module.fail_json_aws(e, "trying to get snapshot information")
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json_aws(e, "trying to get snapshot information")

    for instance in results:
        try:
            instance['Tags'] = boto3_tag_list_to_ansible_dict(conn.list_tags_for_resource(ResourceName=instance['DBSnapshotArn'],
                                                                                          aws_retry=True)['TagList'])
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, "Couldn't get tags for snapshot %s" % instance['DBSnapshotIdentifier'])

    return dict(changed=False, snapshots=[snapshot_to_facts(snapshot) for snapshot in results])


def main():
    argument_spec = dict(
        db_snapshot_identifier=dict(aliases=['snapshot_name']),
        db_instance_identifier=dict(),
        snapshot_type=dict(choices=['automated', 'manual', 'shared', 'public'])
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[['db_snapshot_identifier', 'db_instance_identifier']],
    )

    conn = module.client('rds', retry_decorator=AWSRetry.jittered_backoff(retries=10))

    module.exit_json(**snapshot_facts(module, conn))


if __name__ == '__main__':
    main()
