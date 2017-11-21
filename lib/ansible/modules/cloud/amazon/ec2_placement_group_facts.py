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
module: ec2_placement_group_facts
short_description: List EC2 Placement Group(s) details
description:
    - List details of EC2 Placement Group(s).
version_added: "2.4"
author: "Brad Macpherson (@iiibrad)"
options:
  names:
    description:
      - A list of names to filter on. If a listed group does not exist, there
      will be no corresponding entry in the result; no error will be raised.
    required: false
    default: []
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details or the AWS region,
# see the AWS Guide for details.

# List all placement groups.
- ec2_placement_group_facts:
  register: all_ec2_placement_groups

# List two placement groups.
- ec2_placement_group_facts:
  names:
     - my-cluster
     - my-other-cluster
  register: specific_ec2_placement_groups


'''


RETURN = '''
placement_groups:
  description: Placement group attributes
  returned: always
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
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (AnsibleAWSError, connect_to_aws,
                                      ec2_argument_spec, get_aws_connection_info,
                                      get_ec2_security_group_ids_from_names)


def get_placement_groups_details(connection, module):
    names = module.params.get("names")
    if len(names) > 0:
        groups = connection.get_all_placement_groups(
            filters={
                "group-name": names
            })
    else:
        groups = connection.get_all_placement_groups()

    results = []
    for placement_group in groups:
        results.append({
            "name": placement_group.name,
            "state": placement_group.state,
            "strategy": placement_group.strategy,
        })
    return results


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            names=dict(type='list', default=[])
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

    placement_groups = get_placement_groups_details(connection, module)
    module.exit_json(changed=False, placement_groups=placement_groups)


if __name__ == '__main__':
    main()
