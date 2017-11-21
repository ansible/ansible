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
version_added: "2.4"
author: "Brad Macpherson (@iiibrad)"
options:
  name:
    description:
      - The name for the placement group.
    required: true
    default: null
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

try:
    import boto.ec2
    import boto.vpc
    from boto.exception import BotoServerError
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (AnsibleAWSError, connect_to_aws,
                                      ec2_argument_spec, get_aws_connection_info,
                                      get_ec2_security_group_ids_from_names)


def get_placement_group_details(connection, module):
    name = module.params.get("name")
    groups = connection.get_all_placement_groups(
        filters={
            "group-name": [name]
        })

    if len(groups) != 1:
        return None
    else:
        placement_group = groups[0]
        return {
            "name": placement_group.name,
            "state": placement_group.state,
            "strategy": placement_group.strategy,
        }


def create_placement_group(connection, module):
    name = module.params.get("name")

    try:
        connection.create_placement_group(
            name, 'cluster', dry_run=module.check_mode)

    except BotoServerError as e:
        module.fail_json(msg=e.message)

    module.exit_json(changed=True,
                     placement_group=get_placement_group_details(
                         connection, module
                     ))


def delete_placement_group(connection, module):
    name = module.params.get("name")

    try:
        connection.delete_placement_group(name, dry_run=module.check_mode)

    except BotoServerError as e:
        module.fail_json(msg=e.message)

    module.exit_json(changed=True)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(type='str'),
            state=dict(default='present', choices=['present', 'absent'])
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)

    if region:
        try:
            connection = connect_to_aws(boto.ec2, region, **aws_connect_params)
        except (boto.exception.NoAuthHandlerFound, AnsibleAWSError) as e:
            module.fail_json(msg=str(e))
    else:
        module.fail_json(msg="region must be specified")

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
