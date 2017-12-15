#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ec2_placement_group
short_description: Create or delete an EC2 Placement Group
description:
    - Create an EC2 Placement Group; if the placement group already exists,
      nothing is done. Or, delete an existing placement group. If the placement
      group is absent, do nothing. See also
      http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/placement-groups.html
version_added: "2.5"
author: "Brad Macpherson (@iiibrad)"
options:
  name:
    description:
      - The name for the placement group.
    required: true
  state:
    description:
      - Create or delete placement group.
    required: false
    default: present
    choices: [ 'present', 'absent' ]
  strategy:
    description:
      - Placement group strategy. Cluster will cluster instances into a
        low-latency group in a single Availability Zone, while Spread spreads
        instances across underlying hardware.
    required: false
    default: cluster
    choices: [ 'cluster', 'spread' ]
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide
# for details.

# Create a placement group.
- ec2_placement_group:
    name: my-cluster
    state: present

# Create a Spread placement group.
- ec2_placement_group:
    name: my-cluster
    state: present
    strategy: spread

# Delete a placement group.
- ec2_placement_group:
    name: my-cluster
    state: absent

'''


RETURN = '''
placement_group:
  description: Placement group attributes
  returned: when state != absent
  type: complex
  contains:
    name:
      description: PG name
      type: string
      sample: my-cluster
    state:
      description: PG state
      type: string
      sample: "available"
    strategy:
      description: PG strategy
      type: string
      sample: "cluster"

'''

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import (AWSRetry,
                                      boto3_conn,
                                      ec2_argument_spec,
                                      get_aws_connection_info)
try:
    from botocore.exceptions import (BotoCoreError, ClientError)
except ImportError:
    pass  # caught by AnsibleAWSModule


@AWSRetry.exponential_backoff()
def get_placement_group_details(connection, module):
    name = module.params.get("name")
    try:
        response = connection.describe_placement_groups(
            Filters=[{
                "Name": "group-name",
                "Values": [name]
            }])
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(
            e,
            msg="Couldn't find placement group named [%s]" % name)

    if len(response['PlacementGroups']) != 1:
        return None
    else:
        placement_group = response['PlacementGroups'][0]
        return {
            "name": placement_group['GroupName'],
            "state": placement_group['State'],
            "strategy": placement_group['Strategy'],
        }


@AWSRetry.exponential_backoff()
def create_placement_group(connection, module):
    name = module.params.get("name")
    strategy = module.params.get("strategy")

    try:
        connection.create_placement_group(
            GroupName=name, Strategy=strategy, DryRun=module.check_mode)
    except (BotoCoreError, ClientError) as e:
        if e.response['Error']['Code'] == "DryRunOperation":
            module.exit_json(changed=True, placement_group={
                "name": name,
                "state": 'DryRun',
                "strategy": strategy,
            })
        module.fail_json_aws(
            e,
            msg="Couldn't create placement group [%s]" % name)

    module.exit_json(changed=True,
                     placement_group=get_placement_group_details(
                         connection, module
                     ))


@AWSRetry.exponential_backoff()
def delete_placement_group(connection, module):
    name = module.params.get("name")

    try:
        connection.delete_placement_group(
            GroupName=name, DryRun=module.check_mode)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(
            e,
            msg="Couldn't delete placement group [%s]" % name)

    module.exit_json(changed=True)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(type='str'),
            state=dict(default='present', choices=['present', 'absent']),
            strategy=dict(default='cluster', choices=['cluster', 'spread'])
        )
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    region, ec2_url, aws_connect_params = get_aws_connection_info(
        module, boto3=True)

    connection = boto3_conn(module,
                            resource='ec2', conn_type='client',
                            region=region, endpoint=ec2_url, **aws_connect_params)

    state = module.params.get("state")

    if state == 'present':
        placement_group = get_placement_group_details(connection, module)
        if placement_group is None:
            create_placement_group(connection, module)
        else:
            strategy = module.params.get("strategy")
            if placement_group['strategy'] == strategy:
                module.exit_json(
                    changed=False, placement_group=placement_group)
            else:
                name = module.params.get("name")
                module.fail_json(
                    msg=("Placement group '{}' exists, can't change strategy" +
                         " from '{}' to '{}'").format(
                             name,
                             placement_group['strategy'],
                             strategy))

    elif state == 'absent':
        placement_group = get_placement_group_details(connection, module)
        if placement_group is None:
            module.exit_json(changed=False)
        else:
            delete_placement_group(connection, module)


if __name__ == '__main__':
    main()
