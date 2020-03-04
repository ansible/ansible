#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ec2_placement_group_info
short_description: List EC2 Placement Group(s) details
description:
    - List details of EC2 Placement Group(s).
    - This module was called C(ec2_placement_group_facts) before Ansible 2.9. The usage did not change.
version_added: "2.5"
author: "Brad Macpherson (@iiibrad)"
options:
  names:
    description:
      - A list of names to filter on. If a listed group does not exist, there
        will be no corresponding entry in the result; no error will be raised.
    type: list
    elements: str
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
- ec2_placement_group_info:
  register: all_ec2_placement_groups

# List two placement groups.
- ec2_placement_group_info:
    names:
     - my-cluster
     - my-other-cluster
  register: specific_ec2_placement_groups

- debug: msg="{{ specific_ec2_placement_groups | json_query(\"[?name=='my-cluster']\") }}"

'''


RETURN = '''
placement_groups:
  description: Placement group attributes
  returned: always
  type: complex
  contains:
    name:
      description: PG name
      type: str
      sample: my-cluster
    state:
      description: PG state
      type: str
      sample: "available"
    strategy:
      description: PG strategy
      type: str
      sample: "cluster"

'''

from ansible.module_utils.aws.core import AnsibleAWSModule
try:
    from botocore.exceptions import (BotoCoreError, ClientError)
except ImportError:
    pass  # caught by AnsibleAWSModule


def get_placement_groups_details(connection, module):
    names = module.params.get("names")
    try:
        if len(names) > 0:
            response = connection.describe_placement_groups(
                Filters=[{
                    "Name": "group-name",
                    "Values": names
                }])
        else:
            response = connection.describe_placement_groups()
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(
            e,
            msg="Couldn't find placement groups named [%s]" % names)

    results = []
    for placement_group in response['PlacementGroups']:
        results.append({
            "name": placement_group['GroupName'],
            "state": placement_group['State'],
            "strategy": placement_group['Strategy'],
        })
    return results


def main():
    argument_spec = dict(
        names=dict(type='list', default=[])
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )
    if module._module._name == 'ec2_placement_group_facts':
        module._module.deprecate("The 'ec2_placement_group_facts' module has been renamed to 'ec2_placement_group_info'", version='2.13')

    connection = module.client('ec2')

    placement_groups = get_placement_groups_details(connection, module)
    module.exit_json(changed=False, placement_groups=placement_groups)


if __name__ == '__main__':
    main()
