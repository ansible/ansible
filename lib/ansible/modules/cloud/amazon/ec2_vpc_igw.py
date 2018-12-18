#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ec2_vpc_igw
short_description: Manage an AWS VPC Internet gateway
description:
    - Manage an AWS VPC Internet gateway
version_added: "2.0"
author: Robert Estelle (@erydo)
options:
  vpc_id:
    description:
      - The VPC ID for the VPC in which to manage the Internet Gateway.
    required: true
  tags:
    description:
      - "A dict of tags to apply to the internet gateway. Any tags currently applied to the internet gateway and not present here will be removed."
    aliases: [ 'resource_tags' ]
    version_added: "2.4"
  state:
    description:
      - Create or terminate the IGW
    default: present
    choices: [ 'present', 'absent' ]
extends_documentation_fragment:
    - aws
    - ec2
requirements:
  - botocore
  - boto3
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Ensure that the VPC has an Internet Gateway.
# The Internet Gateway ID is can be accessed via {{igw.gateway_id}} for use in setting up NATs etc.
ec2_vpc_igw:
  vpc_id: vpc-abcdefgh
  state: present
register: igw

'''

RETURN = '''
changed:
  description: If any changes have been made to the Internet Gateway.
  type: bool
  returned: always
  sample:
    changed: false
gateway_id:
  description: The unique identifier for the Internet Gateway.
  type: str
  returned: I(state=present)
  sample:
    gateway_id: "igw-XXXXXXXX"
tags:
  description: The tags associated the Internet Gateway.
  type: dict
  returned: I(state=present)
  sample:
    tags:
      "Ansible": "Test"
vpc_id:
  description: The VPC ID associated with the Internet Gateway.
  type: str
  returned: I(state=present)
  sample:
    vpc_id: "vpc-XXXXXXXX"
'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import (
    AWSRetry,
    boto3_conn,
    ec2_argument_spec,
    get_aws_connection_info,
    camel_dict_to_snake_dict,
    boto3_tag_list_to_ansible_dict,
    ansible_dict_to_boto3_filter_list,
    ansible_dict_to_boto3_tag_list,
    compare_aws_tags
)
from ansible.module_utils.six import string_types


class AnsibleEc2Igw(object):

    def __init__(self, module, results):
        self._module = module
        self._results = results
        self._connection = self._module.client('ec2')
        self._check_mode = self._module.check_mode

    def process(self):
        vpc_id = self._module.params.get('vpc_id')
        state = self._module.params.get('state', 'present')
        tags = self._module.params.get('tags')

        if state == 'present':
            self.ensure_igw_present(vpc_id, tags)
        elif state == 'absent':
            self.ensure_igw_absent(vpc_id)

    def get_matching_igw(self, vpc_id):
        filters = ansible_dict_to_boto3_filter_list({'attachment.vpc-id': vpc_id})
        igws = []
        try:
            response = self._connection.describe_internet_gateways(Filters=filters)
            igws = response.get('InternetGateways', [])
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self._module.fail_json_aws(e)

        igw = None
        if len(igws) > 1:
            self._module.fail_json(
                msg='EC2 returned more than one Internet Gateway for VPC {0}, aborting'.format(vpc_id))
        elif igws:
            igw = camel_dict_to_snake_dict(igws[0])

        return igw

    def check_input_tags(self, tags):
        nonstring_tags = [k for k, v in tags.items() if not isinstance(v, string_types)]
        if nonstring_tags:
            self._module.fail_json(msg='One or more tags contain non-string values: {0}'.format(nonstring_tags))

    def ensure_tags(self, igw_id, tags, add_only):
        final_tags = []

        filters = ansible_dict_to_boto3_filter_list({'resource-id': igw_id, 'resource-type': 'internet-gateway'})
        cur_tags = None
        try:
            cur_tags = self._connection.describe_tags(Filters=filters)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self._module.fail_json_aws(e, msg="Couldn't describe tags")

        purge_tags = bool(not add_only)
        to_update, to_delete = compare_aws_tags(boto3_tag_list_to_ansible_dict(cur_tags.get('Tags')), tags, purge_tags)
        final_tags = boto3_tag_list_to_ansible_dict(cur_tags.get('Tags'))

        if to_update:
            try:
                if self._check_mode:
                    # update tags
                    final_tags.update(to_update)
                else:
                    AWSRetry.exponential_backoff()(self._connection.create_tags)(
                        Resources=[igw_id],
                        Tags=ansible_dict_to_boto3_tag_list(to_update)
                    )

                self._results['changed'] = True
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                self._module.fail_json_aws(e, msg="Couldn't create tags")

        if to_delete:
            try:
                if self._check_mode:
                    # update tags
                    for key in to_delete:
                        del final_tags[key]
                else:
                    tags_list = []
                    for key in to_delete:
                        tags_list.append({'Key': key})

                    AWSRetry.exponential_backoff()(self._connection.delete_tags)(Resources=[igw_id], Tags=tags_list)

                self._results['changed'] = True
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                self._module.fail_json_aws(e, msg="Couldn't delete tags")

        if not self._check_mode and (to_update or to_delete):
            try:
                response = self._connection.describe_tags(Filters=filters)
                final_tags = boto3_tag_list_to_ansible_dict(response.get('Tags'))
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                self._module.fail_json_aws(e, msg="Couldn't describe tags")

        return final_tags

    @staticmethod
    def get_igw_info(igw):
        return {
            'gateway_id': igw['internet_gateway_id'],
            'tags': igw['tags'],
            'vpc_id': igw['vpc_id']
        }

    def ensure_igw_absent(self, vpc_id):
        igw = self.get_matching_igw(vpc_id)
        if igw is None:
            return self._results

        if self._check_mode:
            self._results['changed'] = True
            return self._results

        try:
            self._results['changed'] = True
            self._connection.detach_internet_gateway(InternetGatewayId=igw['internet_gateway_id'], VpcId=vpc_id)
            self._connection.delete_internet_gateway(InternetGatewayId=igw['internet_gateway_id'])
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self._module.fail_json_aws(e, msg="Unable to delete Internet Gateway")

        return self._results

    def ensure_igw_present(self, vpc_id, tags):
        self.check_input_tags(tags)

        igw = self.get_matching_igw(vpc_id)

        if igw is None:
            if self._check_mode:
                self._results['changed'] = True
                self._results['gateway_id'] = None
                return self._results

            try:
                response = self._connection.create_internet_gateway()
                igw = camel_dict_to_snake_dict(response['InternetGateway'])
                self._connection.attach_internet_gateway(InternetGatewayId=igw['internet_gateway_id'], VpcId=vpc_id)
                self._results['changed'] = True
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                self._module.fail_json_aws(e, msg='Unable to create Internet Gateway')

        igw['vpc_id'] = vpc_id

        igw['tags'] = self.ensure_tags(igw_id=igw['internet_gateway_id'], tags=tags, add_only=False)

        igw_info = self.get_igw_info(igw)
        self._results.update(igw_info)

        return self._results


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            vpc_id=dict(required=True),
            state=dict(default='present', choices=['present', 'absent']),
            tags=dict(default=dict(), required=False, type='dict', aliases=['resource_tags'])
        )
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    results = dict(
        changed=False
    )
    igw_manager = AnsibleEc2Igw(module=module, results=results)
    igw_manager.process()

    module.exit_json(**results)


if __name__ == '__main__':
    main()
