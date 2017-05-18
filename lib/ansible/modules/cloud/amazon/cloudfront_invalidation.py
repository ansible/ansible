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
version_added: "2.4"
author: Willem van Ketwich (@wilvk)
options:
    distribution_id:
      description:
        - The id of the cloudfront distribution to invalidate paths for.
          Can be specified insted of the alias.
      required: false
    alias:
      description:
        - The alias of the cloudfront distribution to invalidate paths for.
          Can be specified instead of distribution_id.
      required: false
    caller_reference:
      description:
        - A unique reference identifier for the invalidation paths.
      required: false
      default: current datetime stamp
    target_paths:
      description:
        - A list of paths on the distribution to invalidate.
          Each path should begin with '/'.
          Windcards are allowed. eg. '/foo/bar/*'
      required: true
'''

EXAMPLES = '''

# create a batch of invalidations using a distribution_id for a reference

- cloudfront_invalidation:
    distribution_id: E15BU8SDCGSG57
    caller_reference: testing 123
    target_paths:
      - /testpathone/test1.css
      - /testpathtwo/test2.js
      - /testpaththree/test3.ss

# create a batch of invalidations using an alias as a reference
# and one path using a wildcard match

- cloudfront_invalidation:
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
from ansible.module_utils.ec2 import camel_dict_to_snake_dict
from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.cloudfront as helpers
from ansible.modules.cloud.amazon.cloudfront_facts import CloudFrontFactsServiceManager
import datetime
from functools import partial
import traceback

try:
    import botocore
except ImportError:
    pass


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
            self.client = boto3_conn(
                self.module, conn_type='client', resource=resource,
                region=region, endpoint=ec2_url, **aws_connect_kwargs)
        except botocore.exceptions.NoRegionError:
            self.module.fail_json(
                msg=("region must be specified as a parameter in "
                     "AWS_DEFAULT_REGION environment variable or in "
                     "boto configuration file"))
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(
                msg="unable to establish connection - " + str(e),
                exception=traceback.format_exc(),
                **camel_dict_to_snake_dict(e.response))

    def create_invalidation(self, distribution_id, invalidation_batch):
        try:
            response = self.client.create_invalidation(
                DistributionId=distribution_id,
                InvalidationBatch=invalidation_batch)
            response.pop('ResponseMetadata', None)
            return response
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(
                msg="error creating invalidation(s) - " + str(e),
                exception=traceback.format_exc(),
                **camel_dict_to_snake_dict(e.response))


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
                self.module.fail_json(
                    msg="distribution_id or alias must be specified")
            if distribution_id is None:
                distribution_id = self.__cloudfront_facts_mgr.get_distribution_id_from_domain_name(
                    alias)
            return distribution_id
        except Exception as e:
            self.module.fail_json(
                msg="error validating parameters for distribution update and delete - " +
                str(e), exception=traceback.format_exc(),
                **camel_dict_to_snake_dict(e.response))

    def validate_invalidation_batch(self, invalidation_batch, caller_reference):
        try:
            if caller_reference is not None:
                valid_caller_reference = caller_reference
            else:
                valid_caller_reference = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
            valid_invalidation_batch = {
                'paths': helpers.python_list_to_aws_list(invalidation_batch),
                'caller_reference': valid_caller_reference
            }
            return valid_invalidation_batch
        except Exception as e:
            self.module.fail_json(
                msg="error validating invalidation batch - " +
                str(e), exception=traceback.format_exc(),
                **camel_dict_to_snake_dict(e.response))


def main():
    argument_spec = ec2_argument_spec()

    argument_spec.update(dict(
        caller_reference=dict(required=False, default=None, type='str'),
        distribution_id=dict(required=False, default=None, type='str'),
        alias=dict(required=False, default=None, type='str'),
        target_paths=dict(required=True, default=None, type='list')
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
        mutually_exclusive=[
            ['distribution_id', 'alias']
        ])

    validation_mgr = CloudFrontInvalidationValidationManager(module)
    service_mgr = CloudFrontInvalidationServiceManager(module)

    caller_reference = module.params.get('caller_reference')
    distribution_id = module.params.get('distribution_id')
    alias = module.params.get('alias')
    target_paths = module.params.get('target_paths')

    result = {}

    distribution_id = validation_mgr.validate_distribution_id(
        distribution_id, alias)

    valid_target_paths = validation_mgr.validate_invalidation_batch(
        target_paths, caller_reference)
    valid_pascal_target_paths = helpers.snake_dict_to_pascal_dict(
        valid_target_paths)
    result = service_mgr.create_invalidation(
        distribution_id, valid_pascal_target_paths)

    module.exit_json(changed=True, **helpers.pascal_dict_to_snake_dict(result))


if __name__ == '__main__':
    main()
