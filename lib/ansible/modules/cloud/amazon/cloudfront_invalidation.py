#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---

module: cloudfront_invalidation

short_description: create invalidations for aws cloudfront distributions
description:
    - Allows for invalidation of a batch of paths for a CloudFront distribution.

requirements:
  - boto3 >= 1.0.0
  - python >= 2.6

version_added: "2.5"

author: Willem van Ketwich (@wilvk)

extends_documentation_fragment:
  - aws
  - ec2

options:
    distribution_id:
      description:
        - The id of the cloudfront distribution to invalidate paths for. Can be specified insted of the alias.
      required: false
    alias:
      description:
        - The alias of the cloudfront distribution to invalidate paths for. Can be specified instead of distribution_id.
      required: false
    caller_reference:
      description:
        - A unique reference identifier for the invalidation paths.
      required: false
      default: current datetime stamp
    target_paths:
      description:
        - A list of paths on the distribution to invalidate. Each path should begin with '/'. Wildcards are allowed. eg. '/foo/bar/*'
      required: true

notes:
  - does not support check mode

'''

EXAMPLES = '''

- name: create a batch of invalidations using a distribution_id for a reference
  cloudfront_invalidation:
    distribution_id: E15BU8SDCGSG57
    caller_reference: testing 123
    target_paths:
      - /testpathone/test1.css
      - /testpathtwo/test2.js
      - /testpaththree/test3.ss

- name: create a batch of invalidations using an alias as a reference and one path using a wildcard match
  cloudfront_invalidation:
    alias: alias.test.com
    caller_reference: testing 123
    target_paths:
      - /testpathone/test4.css
      - /testpathtwo/test5.js
      - /testpaththree/*

'''

RETURN = '''

'''

from ansible.module_utils.ec2 import get_aws_connection_info
from ansible.module_utils.ec2 import ec2_argument_spec, boto3_conn, HAS_BOTO3
from ansible.module_utils.ec2 import snake_dict_to_camel_dict
from ansible.module_utils.ec2 import camel_dict_to_snake_dict
from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.aws.cloudfront_facts import CloudFrontFactsServiceManager
import datetime
from functools import partial
import traceback

try:
    import botocore
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # caught by imported AnsibleAWSModule


class CloudFrontInvalidationServiceManager(object):
    """
    Handles CloudFront service calls to AWS for invalidations
    """

    def __init__(self, module):
        self.module = module
        self.create_client('cloudfront')

    def create_client(self, resource):
        try:
            region, ec2_url, aws_connect_kwargs = get_aws_connection_info(
                self.module, boto3=True)
            self.client = boto3_conn(self.module, conn_type='client', resource=resource, region=region, endpoint=ec2_url, **aws_connect_kwargs)
        except (ClientError, BotoCoreError) as e:
                self.module.fail_json_aws(e, msg="Unable to establish connection.")

    def create_invalidation(self, distribution_id, invalidation_batch):
        try:
            response = self.client.create_invalidation(DistributionId=distribution_id, InvalidationBatch=invalidation_batch)
            response.pop('ResponseMetadata', None)
            return response
        except (ClientError, BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error creating CloudFront invalidations.")


class CloudFrontInvalidationValidationManager(object):
    """
    Manages Cloudfront validations for invalidation batches
    """

    def __init__(self, module):
        self.module = module
        self.__cloudfront_facts_mgr = CloudFrontFactsServiceManager(module)

    def validate_distribution_id(self, distribution_id, alias):
        try:
            if distribution_id is None and alias is None:
                self.module.fail_json(msg="distribution_id or alias must be specified")
            if distribution_id is None:
                distribution_id = self.__cloudfront_facts_mgr.get_distribution_id_from_domain_name(alias)
            return distribution_id
        except (ClientError, BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error validating parameters.")

    def create_aws_list(self, invalidation_batch):
        aws_list = {}
        aws_list["Quantity"] = len(invalidation_batch)
        aws_list["Items"] = invalidation_batch
        return aws_list

    def validate_invalidation_batch(self, invalidation_batch, caller_reference):
        try:
            if caller_reference is not None:
                valid_caller_reference = caller_reference
            else:
                valid_caller_reference = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
            valid_invalidation_batch = {
                'paths': self.create_aws_list(invalidation_batch),
                'caller_reference': valid_caller_reference
            }
            return valid_invalidation_batch
        except (ClientError, BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error validating invalidation batch.")


def main():
    argument_spec = ec2_argument_spec()

    argument_spec.update(dict(
        caller_reference=dict(),
        distribution_id=dict(),
        alias=dict(),
        target_paths=dict(required=True, default=None, type='list')
    ))

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=False, mutually_exclusive=[['distribution_id', 'alias']])

    validation_mgr = CloudFrontInvalidationValidationManager(module)
    service_mgr = CloudFrontInvalidationServiceManager(module)

    caller_reference = module.params.get('caller_reference')
    distribution_id = module.params.get('distribution_id')
    alias = module.params.get('alias')
    target_paths = module.params.get('target_paths')

    result = {}

    distribution_id = validation_mgr.validate_distribution_id(distribution_id, alias)
    valid_target_paths = validation_mgr.validate_invalidation_batch(target_paths, caller_reference)
    valid_pascal_target_paths = snake_dict_to_camel_dict(valid_target_paths, True)
    result = service_mgr.create_invalidation(distribution_id, valid_pascal_target_paths)

    module.exit_json(changed=True, **camel_dict_to_snake_dict(result))


if __name__ == '__main__':
    main()
