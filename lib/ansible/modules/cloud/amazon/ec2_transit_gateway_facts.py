#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'supported_by': 'community',
    'status': ['preview']
}

DOCUMENTATION = '''
module: ec2_transit_gateway_facts
short_description: Gather facts about ec2 transit gateways in AWS
description:
    - Gather facts about ec2 transit gateways in AWS
version_added: "2.8"
author: "Bob Boldin (@BobBoldin)"
requirements:
  - botocore
  - boto3
options:
  transit_gateway_ids:
    description:
      - A list of transit gateway IDs to gather facts for.
    version_added: "2.8"
    aliases: [transit_gateway_id]
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeTransitGateways.html) for possible filters.
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather facts about all transit gateways
- ec2_transit_gateway_facts:

# Gather facts about a particular transit gateway using transit gateway IDs
- ec2_transit_gateway_facts:
    filters:
      transit_gateway_id: tgw-02c42332e6b7da829

# Gather facts about multiple transit gateways using IDs
- ec2_transit_gateway_facts:
    filters:
      transit_gateway_ids:
        - tgw-02c42332e6b7da829
        - tgw-03c53443d5a8cb716
'''

RETURN = '''
transit_gateways:
    description: >
        Transit gateways that match the provided filters. Each element consists of a dict with all the information
        related to that transit gateway.
    returned: on success
    type: complex
    contains:
        creation_time:
            description: The creation time.
            returned: always
            type: str
            sample: "2019-02-05T16:19:58+00:00"
        description:
            description: The description of the transit gateway.
            returned: always
            type: str
            sample: "A transit gateway"
        options:
            description: A dictionary of the transit gateway options.
            returned: always
            type: complex
            contains:
                 amazon_side_asn:
                    description:
                      - A private Autonomous System Number (ASN) for  the  Amazon
                        side  of  a  BGP session. The range is 64512 to 65534 for
                        16-bit ASNs and 4200000000 to 4294967294 for 32-bit ASNs.
                    returned: always
                    type: str
                    sample: 64512
                 auto_accept_shared_attachments:
                    description:
                       - Indicates whether attachment requests  are  automatically accepted.
                    returned: always
                    type: str
                    sample: "enable"
                 default_route_table_association:
                    description:
                      - Indicates  whether resource attachments are automatically
                        associated with the default association route table.
                    returned: always
                    type: str
                    sample: "disable"
                 association_default_route_table_id:
                    description:
                      - The ID of the default association route table.
                    returned: when present
                    type: str
                    sample: "rtb-11223344"
                 default_route_table_propagation:
                    description:
                      - Indicates  whether  resource  attachments   automatically
                        propagate routes to the default propagation route table.
                    returned: always
                    type: str
                    sample: "disable"
                 dns_support:
                    description:
                      - Indicates whether DNS support is enabled.
                    returned: always
                    type: str
                    sample: "enable"
                 propagation_default_route_table_id:
                    description:
                      - The ID of the default propagation route table.
                    returned: when present
                    type: str
                    sample: "rtb-11223344"
                 vpn_ecmp_support:
                    description:
                      - Indicates  whether  Equal Cost Multipath Protocol support
                        is enabled.
                    returned: always
                    type: str
                    sample: "enable"
        owner_id:
            description: The AWS account number ID which owns the transit gateway.
            returned: always
            type: str
            sample: "1234567654323"
        state:
            description: The state of the transit gateway.
            returned: always
            type: str
            sample: "available"
        tags:
            description: A dict of tags associated with the transit gateway.
            returned: always
            type: dict
            sample:
              Name: "A sample TGW"
        transit_gateway_arn:
            description: The Amazon Resource Name (ARN) of the transit gateway.
            returned: always
            type: str
            sample: "arn:aws:ec2:us-west-2:1234567654323:transit-gateway/tgw-02c42332e6b7da829"
        transit_gateway_id:
            description: The ID of the transit gateway.
            returned: always
            type: str
            sample: "tgw-02c42332e6b7da829"
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
    pass  # will be detected by imported HAS_BOTO3


@AWSRetry.exponential_backoff()
def describe_transit_gateways_with_backoff(connection, transit_gateway_ids, filters):
    """
    Describe transit gateways with AWSRetry backoff throttling support.

    connection  : boto3 client connection object
    transit_gateway_ids  : list of transit gateway ids for which to gather facts
    filters     : additional filters to apply to request
    """
    return connection.describe_transit_gateways(TransitGatewayIds=transit_gateway_ids, Filters=filters)


def describe_transit_gateways(connection, module):
    """
    Describe transit gateways.

    module  : AnsibleModule object
    connection  : boto3 client connection object
    """
    # collect parameters
    filters = ansible_dict_to_boto3_filter_list(module.params.get('filters'))
    transit_gateway_ids = module.params.get('transit_gateway_ids')

    if transit_gateway_ids is None:
        # Set transit_gateway_ids to empty list if it is None
        transit_gateway_ids = []

    # init empty list for return vars
    transit_gateway_info = list()

    # Get the basic transit gateway info
    try:
        response = describe_transit_gateways_with_backoff(connection, transit_gateway_ids, filters)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    for transit_gateway in response['TransitGateways']:
        transit_gateway_info.append(camel_dict_to_snake_dict(transit_gateway))
        # convert tag list to ansible dict
        transit_gateway_info[-1]['tags'] = boto3_tag_list_to_ansible_dict(transit_gateway.get('Tags', []))

    module.exit_json(transit_gateways=transit_gateway_info)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        transit_gateway_ids=dict(type='list', default=[], aliases=['transit_gateway_id']),
        filters=dict(type='dict', default={})
    ))

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)

    if region:
        try:
            connection = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_params)
        except (botocore.exceptions.NoCredentialsError, botocore.exceptions.ProfileNotFound) as e:
            module.fail_json(msg=to_native(e), exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    else:
        module.fail_json(msg="Region must be specified")

    describe_transit_gateways(connection, module)


if __name__ == '__main__':
    main()
