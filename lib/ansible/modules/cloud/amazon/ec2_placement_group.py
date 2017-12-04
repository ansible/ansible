#!/usr/bin/python
#
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This Ansible library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

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
      group is absent, do nothing.
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
from ansible.module_utils.ec2 import (boto3_conn,
                                      ec2_argument_spec,
                                      get_aws_connection_info,
                                      HAS_BOTO3)
try:
    from botocore.exceptions import (BotoCoreError, ClientError)
except ImportError:
    pass  # caught by imported HAS_BOTO3


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


def create_placement_group(connection, module):
    name = module.params.get("name")

    try:
        connection.create_placement_group(
            GroupName=name, Strategy='cluster', DryRun=module.check_mode)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(
            e,
            msg="Couldn't create placement group [%s]" % name)

    module.exit_json(changed=True,
                     placement_group=get_placement_group_details(
                         connection, module
                     ))


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
            state=dict(default='present', choices=['present', 'absent'])
        )
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 and botocore are required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(
        module, boto3=True)

    connection = boto3_conn(module,
                            resource='ec2', conn_type='client',
                            region=region, **aws_connect_params)

    state = module.params.get("state")

    if state == 'present':
        placement_group = get_placement_group_details(connection, module)
        if placement_group is None:
            create_placement_group(connection, module)
        else:
            module.exit_json(changed=False, placement_group=placement_group)

    elif state == 'absent':
        placement_group = get_placement_group_details(connection, module)
        if placement_group is None:
            module.exit_json(changed=False)
        else:
            delete_placement_group(connection, module)


if __name__ == '__main__':
    main()
