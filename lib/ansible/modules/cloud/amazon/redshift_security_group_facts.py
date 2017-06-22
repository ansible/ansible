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

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'supported_by': 'community',
    'status': ['preview']
}

DOCUMENTATION = '''
---
module: redshift_security_group_facts
short_description: Gather facts about Redshift cluster security goups in AWS
description:
  - Gather facts about Redshift cluster security goups in AWS
version_added: "2.4"
author: "Jens Carl (@j-carl)"
options:
  name:
    description:
      - The prefix of name of the Redshift cluster security group(s) you are searching for.
      - "This is a regular expression match with implicit '^'. Append '$' for a complete match."
    required: false
  tags:
    description:
      - "A dictionary/hash of tags in the format { tag1_name: 'tag1_value', tag2_name: 'tag2_value' }
        to match against the security group(s) you are searching for."
    required: false
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Find all groups
- redshift_security_group_facts:
  register: redshift_security_groups

# Find a group with matching name/prefix
- redshift_security_group_facts:
    name: public-webserver-security_group
  register: redshift_security_groups

# Find a group with matching tags
- redshift_security_group_facts:
    tags:
      project: webapp
      env: production
  register: redshift_security_groups

# Find a group with matching name/prefix and tags
- redshift_security_group_facts:
    name: myproject
    tags:
      env: production
  register: redshift_security_groups

# Fail if no groups are found
- redshift_security_group_facts:
    name: public-webserver-security_group
  register: redshift_security_groups
  failed_when: "{{ security_groups.results | length == 0 }}"

# Fail if more than 1 group is found
- redshift_security_group_facts:
    name: public-webserver-security_group
  register: redshift_security_groups
  failed_when: "{{ security_groups.results | length > 1 }}"
'''

RETURN = '''
---
cluster_security_group_name:
    description: Name of the Redshift cluster security group
    returned: success
    type: string
    sample: "default"
description:
    description: Description of the Redshift cluster security group
    returned: success
    type: string
    sample: "default"
ec2_security_groups:
    description: A list of EC2 security groups that are permitted to access the cluster.
    returned: success
    type: list
    sample: [
        {
            "ec2_security_group_name": "launch-wizard-3",
            "ec2_security_group_owner_id": "1234567890",
            "status": "authorized",
            "tags": []
        },
        {
            "ec2_security_group_name": "quicklaunch-1",
            "ec2_security_group_owner_id": "1234567890",
            "status": "authorized",
            "tags": []
        }
    ]
ip_ranges:
    description: A list of IP ranges (CIDR blocks) that are permitted to access the cluster.
    returned: success
    type: list
    sample: [
        {
            "cidrip": "1.1.1.1/32",
            "status": "authorized",
            "tags": []
        },
        {
            "cidrip": "2.2.2.2/32",
            "status": "authorized",
            "tags": []
        }
    ]
tags:
    description: List of tags for the ASG, and whether or not each tag propagates to instances at launch.
    returned: success
    type: list
    sample: [
        {
            "key": "Env",
            "value": "prd"
        },
        {
            "key": "Stack",
            "value": "db"
        }
    ]
'''

import traceback
import re
# Import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import ec2_argument_spec, boto3_conn, get_aws_connection_info
from ansible.module_utils.ec2 import HAS_BOTO3, camel_dict_to_snake_dict

try:
    from botocore.exceptions import ClientError
except ImportError:
    pass  # will be picked up from imported HAS_BOTO3


def match_csg_tags(tags_to_match, csg):
    for key, value in tags_to_match.items():
        for tag in csg['Tags']:
            if key == tag['Key'] and value == tag['Value']:
                return True

    return False


def find_csgs(conn, module, name=None, tags=None):

    try:
        csgs_paginator = conn.get_paginator('describe_cluster_security_groups')
        csgs = csgs_paginator.paginate().build_full_result()
    except ClientError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    matched_csgs = []

    if name is not None:
        name_prog = re.compile(r'^' + name)

    for csg in csgs['ClusterSecurityGroups']:

        matched_name = True
        if name:
            matched_name = name_prog.search(csg['ClusterSecurityGroupName'])

        matched_tags = True
        if tags:
            matched_tags = match_csg_tags(tags, csg)

        if matched_name and matched_tags:
            matched_csgs.append(camel_dict_to_snake_dict(csg))

    return matched_csgs


def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(type='str'),
            tags=dict(type='dict')
        )
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    csg_name = module.params.get('name')
    csg_tags = module.params.get('tags')

    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        redshift = boto3_conn(module, conn_type='client', resource='redshift', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except ClientError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    results = find_csgs(redshift, module, name=csg_name, tags=csg_tags)
    module.exit_json(results=results)


if __name__ == '__main__':
    main()
