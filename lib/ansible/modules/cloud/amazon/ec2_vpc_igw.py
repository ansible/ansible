#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''
---
module: ec2_vpc_igw
short_description: Manage an AWS VPC Internet gateway
description:
    - Create/Delete an AWS VPC Internet gateway
    - Add/Update tags of Internet Gateway
version_added: "2.0"
author:
  - Robert Estelle (@erydo)
  - Madhura Naniwadekar (@mnaniwadekar)
options:
  vpc_id:
    description:
      - The VPC ID for the VPC in which to manage the Internet Gateway.
    required: false
  tags:
    description:
      - A dict of tags to apply to the internet gateway.
        This is independent of the name value, note if you pass a 'Name' key it would override the Name of IGW if it's different.
    aliases: [ 'resource_tags' ]
    required: false
  state:
    description:
      - Create or terminate the IGW.
    default: present
    choices: [ 'present', 'absent' ]
  name:
    description:
      - The name to be given to IGW.
    required: false
    version_added: "2.6"
requirements:
    - boto3
    - botocore
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# The Internet Gateway ID is can be accessed via {{igw.gateway_id}} for use in setting up NATs etc.

- name: Create internet gateway with name, tags and attach to VPC
  ec2_vpc_igw:
    name: test-igw
    vpc_id: vpc-1234df
    state: present
    tags:
      module: ec2-vpc-igw
      this: works
  register: igw

- name: Delete IGW
  ec2_vpc_igw:
    state: absent
    vpc_id: vpc-1234df
'''

RETURN = '''
internet_gateway:
  description: Information about current internet gateway being created/updated.
  type: dict
  returned: I(state=present)
  sample:
    "internet_gateway": {
        "attachments": [
            {
                "state": "available",
                "vpc_id": "vpc-1234df"
            }
        ],
        "internet_gateway_id": "igw-e5ba908c",
        "tags": {
            "Name": "test-igw",
            "module": "ec2-vpc-igw",
            "this": "works"
        }
    }
'''


try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import (AWSRetry, boto3_conn, get_aws_connection_info, ec2_argument_spec, camel_dict_to_snake_dict,
                                      ansible_dict_to_boto3_tag_list, boto3_tag_list_to_ansible_dict)
from ansible.module_utils.six import string_types


@AWSRetry.exponential_backoff()
def igw_check(connection, module, vpc_id):

    try:
        matching_igws = connection.describe_internet_gateways(Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}])['InternetGateways']
        if len(matching_igws) > 1:
            module.fail_json(msg="EC2 returned more than one Internet Gateway for VPC %s, aborting:" % (vpc_id))
        return matching_igws[0]['InternetGatewayId'] if matching_igws else None
    except (ClientError, BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to describe internet gateways")


@AWSRetry.exponential_backoff()
def get_igw(connection, module, igw_id):
    try:
        igw = connection.describe_internet_gateways(InternetGatewayIds=[igw_id])['InternetGateways'][0]
        return igw
    except (ClientError, BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to describe internet gateways")


def update_igw_tags(connection, module, igw_id, name, tags):

    if tags is None:
        tags = dict()

    tags = tags.update({'Name': name}) if name else tags
    try:
        current_tags = dict((t['Key'], t['Value']) for t in connection.describe_tags(Filters=[{'Name': 'resource-id', 'Values': [igw_id]}])['Tags'])
        if tags != current_tags:
            if not module.check_mode:
                tags = ansible_dict_to_boto3_tag_list(tags)
                connection.create_tags(Resources=[igw_id], Tags=tags)
            return True
        else:
            return False
    except (ClientError, BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to update tags")


@AWSRetry.exponential_backoff()
def ensure_igw_present(connection, module, vpc_id, name, tags):

    changed = False
    igw_id = igw_check(connection, module, vpc_id)
    if igw_id is None:
        try:
            igw = connection.create_internet_gateway()['InternetGateway']
            igw_id = igw['InternetGatewayId']
            connection.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
            changed = True
        except (ClientError, BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to create internet gateway")

    if tags is not None or name is not None:
        try:
            changed = update_igw_tags(connection, module, igw_id, name, tags)
        except (ClientError, BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to update tags of internet gateway")

    igw = camel_dict_to_snake_dict(get_igw(connection, module, igw_id))
    igw['tags'] = boto3_tag_list_to_ansible_dict(igw.get('tags', []))

    return igw, changed


@AWSRetry.exponential_backoff()
def ensure_igw_absent(connection, module, vpc_id):

    changed = False
    igw_id = igw_check(connection, module, vpc_id)

    if igw_id is None:
        return changed

    try:
        connection.detach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
        connection.delete_internet_gateway(InternetGatewayId=igw_id)
        changed = True
    except (ClientError, BotoCoreError) as e:
        module.fail_json_aws(e, "Failed to delete internet gateway")

    return changed


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        vpc_id=dict(required=True),
        state=dict(default='present', choices=['present', 'absent']),
        tags=dict(default=dict(), required=False, type='dict', aliases=['resource_tags']),
        name=dict()
    )
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)
    connection = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_params)

    vpc_id = module.params.get('vpc_id')
    name = module.params.get('name')
    tags = module.params.get('tags')
    state = module.params.get('state')

    changed = False

    if state == 'present':
        if not module.check_mode:
            igw, changed = ensure_igw_present(connection, module, vpc_id, name, tags)
            module.exit_json(changed=changed, internet_gateway=igw)
        module.exit_json(changed=True, msg="Should have created internet gateway if check_mode was false")
    elif state == 'absent':
        if not module.check_mode:
            changed = ensure_igw_absent(connection, module, vpc_id)
            module.exit_json(changed=changed)
        module.exit_json(changed=True, msg="Should have created internet gateway if check_mode was false")

if __name__ == '__main__':
    main()
