#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
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
        - The id of the cloudfront distribution to invalidate paths for. Can be specified instead of the alias.
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
invalidation:
  description: The invalidation's information.
  returned: always
  type: complex
  contains:
    create_time:
      description: The date and time the invalidation request was first made.
      returned: always
      type: str
      sample: '2018-02-01T15:50:41.159000+00:00'
    id:
      description: The identifier for the invalidation request.
      returned: always
      type: str
      sample: I2G9MOWJZFV612
    invalidation_batch:
      description: The current invalidation information for the batch request.
      returned: always
      type: complex
      contains:
        caller_reference:
          description: The value used to uniquely identify an invalidation request.
          returned: always
          type: str
          sample: testing 123
        paths:
          description: A dict that contains information about the objects that you want to invalidate.
          returned: always
          type: complex
          contains:
            items:
              description: A list of the paths that you want to invalidate.
              returned: always
              type: list
              sample:
              - /testpathtwo/test2.js
              - /testpathone/test1.css
              - /testpaththree/test3.ss
            quantity:
              description: The number of objects that you want to invalidate.
              returned: always
              type: int
              sample: 3
    status:
      description: The status of the invalidation request.
      returned: always
      type: str
      sample: Completed
location:
  description: The fully qualified URI of the distribution and invalidation batch request.
  returned: always
  type: str
  sample: https://cloudfront.amazonaws.com/2017-03-25/distribution/E1ZID6KZJECZY7/invalidation/I2G9MOWJZFV622
'''

from ansible.module_utils.ec2 import get_aws_connection_info
from ansible.module_utils.ec2 import ec2_argument_spec, boto3_conn
from ansible.module_utils.ec2 import snake_dict_to_camel_dict
from ansible.module_utils.ec2 import camel_dict_to_snake_dict
from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.aws.cloudfront_facts import CloudFrontFactsServiceManager
import datetime

try:
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
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(self.module, boto3=True)
        self.client = boto3_conn(self.module, conn_type='client', resource=resource, region=region, endpoint=ec2_url, **aws_connect_kwargs)

    def create_invalidation(self, distribution_id, invalidation_batch):
        current_invalidation_response = self.get_invalidation(distribution_id, invalidation_batch['CallerReference'])
        try:
            response = self.client.create_invalidation(DistributionId=distribution_id, InvalidationBatch=invalidation_batch)
            response.pop('ResponseMetadata', None)
            if current_invalidation_response:
                return response, False
            else:
                return response, True
        except BotoCoreError as e:
            self.module.fail_json_aws(e, msg="Error creating CloudFront invalidations.")
        except ClientError as e:
            if ('Your request contains a caller reference that was used for a previous invalidation batch '
                    'for the same distribution.' in e.response['Error']['Message']):
                self.module.warn("InvalidationBatch target paths are not modifiable. "
                                 "To make a new invalidation please update caller_reference.")
                return current_invalidation_response, False
            else:
                self.module.fail_json_aws(e, msg="Error creating CloudFront invalidations.")

    def get_invalidation(self, distribution_id, caller_reference):
        current_invalidation = {}
        # find all invalidations for the distribution
        try:
            paginator = self.client.get_paginator('list_invalidations')
            invalidations = paginator.paginate(DistributionId=distribution_id).build_full_result().get('InvalidationList', {}).get('Items', [])
            invalidation_ids = [inv['Id'] for inv in invalidations]
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e, msg="Error listing CloudFront invalidations.")

        # check if there is an invalidation with the same caller reference
        for inv_id in invalidation_ids:
            try:
                invalidation = self.client.get_invalidation(DistributionId=distribution_id, Id=inv_id)['Invalidation']
                caller_ref = invalidation.get('InvalidationBatch', {}).get('CallerReference')
            except (BotoCoreError, ClientError) as e:
                self.module.fail_json_aws(e, msg="Error getting Cloudfront invalidation {0}".format(inv_id))
            if caller_ref == caller_reference:
                current_invalidation = invalidation
                break

        current_invalidation.pop('ResponseMetadata', None)
        return current_invalidation


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
                valid_caller_reference = datetime.datetime.now().isoformat()
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
        target_paths=dict(required=True, type='list')
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
    result, changed = service_mgr.create_invalidation(distribution_id, valid_pascal_target_paths)

    module.exit_json(changed=changed, **camel_dict_to_snake_dict(result))


if __name__ == '__main__':
    main()
