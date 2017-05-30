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

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import get_aws_connection_info, boto3_conn
from ansible.module_utils.ec2 import ec2_argument_spec, HAS_BOTO3
from ansible.module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ansible.module_utils.ec2 import ansible_dict_to_boto3_filter_list

DOCUMENTATION = '''
module: ec2_vpc_facts
short_description: Gathers facts about AWS VPCs
description:
  - Gather facts about AWS VPCs
version_added: "2.3"
author: "Mike Mochan (@mmochan)"
requires: [ boto3 ]
options:
  filters:
    description:
      - >-
           A dict of filters to apply. Each dict item consists of a filter key
           and a filter value. See
           U(http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeVpcs.html)
           for possible filters. Filter names and values are case sensitive.
    required: false
    default: {}
notes:
  - By default, the module will return all VPCs

extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
# Simple example of filtering based on vpc_id
ec2_vpc_facts:
  region: "{{ region }}"
  filters:
    vpc-id: "{{vpc_id}}"
register: ec2_vpc_facts
'''


try:
    import botocore
except ImportError:
    pass  # will be picked up by imported HAS_BOTO3


def get_vpc_info(vpc):

    return dict(vpc_id=vpc['VpcId'],
                state=vpc['State'],
                cidr_block=vpc['CidrBlock'],
                dhcp_options_id=vpc['DhcpOptionsId'],
                tags=boto3_tag_list_to_ansible_dict(vpc['Tags']),
                instance_tenancy=vpc['InstanceTenancy'],
                is_default=vpc['IsDefault'])


def list_vpcs(client, module):
    filters = ansible_dict_to_boto3_filter_list(module.params.get("filters"))

    return [get_vpc_info(vpc)
            for vpc in client.describe_vpcs(DryRun=module.check_mode,
                                            Filters=filters)['Vpcs']]


def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            filters = dict(default=dict(), type='dict'),
        )
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    # Validate Requirements
    if not HAS_BOTO3:
        module.fail_json(msg='botocore and boto3 are required.')

    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        connection = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except botocore.exceptions.NoCredentialsError as e:
        module.fail_json(msg="Can't authorize connection - " + str(e))

    # call your function here
    vpcs = list_vpcs(connection, module)

    module.exit_json(changed=False, vpc_facts=vpcs)


if __name__ == '__main__':
    main()
