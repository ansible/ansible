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
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: ec2_vpc_net_info
short_description: Gather information about ec2 VPCs in AWS
description:
    - Gather information about ec2 VPCs in AWS
    - This module was called C(ec2_vpc_net_facts) before Ansible 2.9. The usage did not change.
version_added: "2.1"
author: "Rob White (@wimnat)"
requirements:
  - boto3
  - botocore
options:
  vpc_ids:
    description:
      - A list of VPC IDs that exist in your account.
    version_added: "2.5"
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeVpcs.html) for possible filters.
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather information about all VPCs
- ec2_vpc_net_info:

# Gather information about a particular VPC using VPC ID
- ec2_vpc_net_info:
    vpc_ids: vpc-00112233

# Gather information about any VPC with a tag key Name and value Example
- ec2_vpc_net_info:
    filters:
      "tag:Name": Example

'''

RETURN = '''
vpcs:
    description: Returns an array of complex objects as described below.
    returned: success
    type: complex
    contains:
        id:
            description: The ID of the VPC (for backwards compatibility).
            returned: always
            type: str
        vpc_id:
            description: The ID of the VPC .
            returned: always
            type: str
        state:
            description: The state of the VPC.
            returned: always
            type: str
        tags:
            description: A dict of tags associated with the VPC.
            returned: always
            type: dict
        instance_tenancy:
            description: The instance tenancy setting for the VPC.
            returned: always
            type: str
        is_default:
            description: True if this is the default VPC for account.
            returned: always
            type: bool
        cidr_block:
            description: The IPv4 CIDR block assigned to the VPC.
            returned: always
            type: str
        classic_link_dns_supported:
            description: True/False depending on attribute setting for classic link DNS support.
            returned: always
            type: bool
        classic_link_enabled:
            description: True/False depending on if classic link support is enabled.
            returned: always
            type: bool
        enable_dns_hostnames:
            description: True/False depending on attribute setting for DNS hostnames support.
            returned: always
            type: bool
        enable_dns_support:
            description: True/False depending on attribute setting for DNS support.
            returned: always
            type: bool
        ipv6_cidr_block_association_set:
            description: An array of IPv6 cidr block association set information.
            returned: always
            type: complex
            contains:
                association_id:
                    description: The association ID
                    returned: always
                    type: str
                ipv6_cidr_block:
                    description: The IPv6 CIDR block that is associated with the VPC.
                    returned: always
                    type: str
                ipv6_cidr_block_state:
                    description: A hash/dict that contains a single item. The state of the cidr block association.
                    returned: always
                    type: dict
                    contains:
                        state:
                            description: The CIDR block association state.
                            returned: always
                            type: str
'''

import traceback
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (
    boto3_conn,
    ec2_argument_spec,
    get_aws_connection_info,
    AWSRetry,
    HAS_BOTO3,
    boto3_tag_list_to_ansible_dict,
    camel_dict_to_snake_dict,
    ansible_dict_to_boto3_filter_list
)

try:
    import botocore
except ImportError:
    pass  # caught by imported HAS_BOTO3


@AWSRetry.exponential_backoff()
def describe_vpc_attr_with_backoff(connection, vpc_id, vpc_attribute):
    """
    Describe VPC Attributes with AWSRetry backoff throttling support.

    connection  : boto3 client connection object
    vpc_id      : The VPC ID to pull attribute value from
    vpc_attribute     : The VPC attribute to get the value from - valid options = enableDnsSupport or enableDnsHostnames
    """

    return connection.describe_vpc_attribute(VpcId=vpc_id, Attribute=vpc_attribute)


def describe_vpcs(connection, module):
    """
    Describe VPCs.

    connection  : boto3 client connection object
    module  : AnsibleModule object
    """
    # collect parameters
    filters = ansible_dict_to_boto3_filter_list(module.params.get('filters'))
    vpc_ids = module.params.get('vpc_ids')

    # init empty list for return vars
    vpc_info = list()
    vpc_list = list()

    # Get the basic VPC info
    try:
        response = connection.describe_vpcs(VpcIds=vpc_ids, Filters=filters)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Unable to describe VPCs {0}: {1}".format(vpc_ids, to_native(e)),
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Unable to describe VPCs {0}: {1}".format(vpc_ids, to_native(e)),
                         exception=traceback.format_exc())

    # Loop through results and create a list of VPC IDs
    for vpc in response['Vpcs']:
        vpc_list.append(vpc['VpcId'])

    # We can get these results in bulk but still needs two separate calls to the API
    try:
        cl_enabled = connection.describe_vpc_classic_link(VpcIds=vpc_list)
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Message"] == "The functionality you requested is not available in this region.":
            cl_enabled = {'Vpcs': [{'VpcId': vpc_id, 'ClassicLinkEnabled': False} for vpc_id in vpc_list]}
        else:
            module.fail_json(msg="Unable to describe if ClassicLink is enabled: {0}".format(to_native(e)),
                             exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Unable to describe if ClassicLink is enabled: {0}".format(to_native(e)),
                         exception=traceback.format_exc())

    try:
        cl_dns_support = connection.describe_vpc_classic_link_dns_support(VpcIds=vpc_list)
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Message"] == "The functionality you requested is not available in this region.":
            cl_dns_support = {'Vpcs': [{'VpcId': vpc_id, 'ClassicLinkDnsSupported': False} for vpc_id in vpc_list]}
        else:
            module.fail_json(msg="Unable to describe if ClassicLinkDns is supported: {0}".format(to_native(e)),
                             exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Unable to describe if ClassicLinkDns is supported: {0}".format(to_native(e)),
                         exception=traceback.format_exc())

    # Loop through the results and add the other VPC attributes we gathered
    for vpc in response['Vpcs']:
        error_message = "Unable to describe VPC attribute {0}: {1}"
        # We have to make two separate calls per VPC to get these attributes.
        try:
            dns_support = describe_vpc_attr_with_backoff(connection, vpc['VpcId'], 'enableDnsSupport')
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg=error_message.format('enableDnsSupport', to_native(e)),
                             exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
        except botocore.exceptions.BotoCoreError as e:
            module.fail_json(msg=error_message.format('enableDnsSupport', to_native(e)),
                             exception=traceback.format_exc())
        try:
            dns_hostnames = describe_vpc_attr_with_backoff(connection, vpc['VpcId'], 'enableDnsHostnames')
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg=error_message.format('enableDnsHostnames', to_native(e)),
                             exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
        except botocore.exceptions.BotoCoreError as e:
            module.fail_json(msg=error_message.format('enableDnsHostnames', to_native(e)),
                             exception=traceback.format_exc())

        # loop through the ClassicLink Enabled results and add the value for the correct VPC
        for item in cl_enabled['Vpcs']:
            if vpc['VpcId'] == item['VpcId']:
                vpc['ClassicLinkEnabled'] = item['ClassicLinkEnabled']

        # loop through the ClassicLink DNS support results and add the value for the correct VPC
        for item in cl_dns_support['Vpcs']:
            if vpc['VpcId'] == item['VpcId']:
                vpc['ClassicLinkDnsSupported'] = item['ClassicLinkDnsSupported']

        # add the two DNS attributes
        vpc['EnableDnsSupport'] = dns_support['EnableDnsSupport'].get('Value')
        vpc['EnableDnsHostnames'] = dns_hostnames['EnableDnsHostnames'].get('Value')
        # for backwards compatibility
        vpc['id'] = vpc['VpcId']
        vpc_info.append(camel_dict_to_snake_dict(vpc))
        # convert tag list to ansible dict
        vpc_info[-1]['tags'] = boto3_tag_list_to_ansible_dict(vpc.get('Tags', []))

    module.exit_json(vpcs=vpc_info)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        vpc_ids=dict(type='list', default=[]),
        filters=dict(type='dict', default={})
    ))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    if module._name == 'ec2_vpc_net_facts':
        module.deprecate("The 'ec2_vpc_net_facts' module has been renamed to 'ec2_vpc_net_info'", version='2.13')

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 and botocore are required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)
    connection = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_params)

    describe_vpcs(connection, module)


if __name__ == '__main__':
    main()
