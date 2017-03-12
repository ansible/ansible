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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: cloudfront
short_description: Create, update and delete AWS CloudFront distributions
description:
  - Allows for easy creation, updating and deletion of CloudFront distributions
requirements:
  - boto3 >= 1.0.0
  - python >= 2.6
version_added: "2.3"
author: Willem van Ketwich (@wilvk)
  
options:
  distribution_id:
      description:
        - The id of the CloudFront distribution. Used with distribution, distribution_config, invalidation, streaming_distribution, streaming_distribution_config, list_invalidations.
      required: false

extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create a config for an Origin Access Identity
- cloudfront:
    create_origin_access_identity_config: yes
    callerreference: callerreferencevalue
    comment: creating an origin access identity
    register: "{{ oai_config_details }}"

# Create an Origin Access Identity
  - cloudfront:
    create_cloudfront_origin_access_identity: yes
    origin_access_identity_config: "{{ oai_config_details }}"

# Create a Distribution Configuration
  - cloudfront:
    create_distribution_config: true
 ...
register: "{{ distribution_config_details }}"

# Create a Distribution
  - cloudfront:
    create_distribution: true
    distribution_config: '{{ distribution_config }}'

'''

RETURN = '''
'''

try:
    import boto3
    import botocore
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ansible.module_utils.ec2 import get_aws_connection_info
from ansible.module_utils.ec2 import ec2_argument_spec
from ansible.module_utils.ec2 import boto3_conn
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import camel_dict_to_snake_dict
from functools import partial
import json
import traceback

class CloudFrontServiceManager:
    """Handles CloudFront Services"""

    def __init__(self, module):
        self.module = module

        try:
            region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
            self.client = boto3_conn(module, conn_type='client', resource='cloudfront', 
                                     region=region, endpoint=ec2_url, **aws_connect_kwargs)
        except botocore.exceptions.NoRegionError:
            self.module.fail_json(msg = ("Region must be specified as a parameter, in "
                                         "AWS_DEFAULT_REGION environment variable or in "
                                         "boto configuration file") )
        except Exception as e:
            self.module.fail_json(msg="Can't establish connection - " + str(e),
                                  exception=traceback.format_exc())

    def create_origin_access_identity(self, caller_reference, comment):
        try:
            func = partial(self.client.create_cloud_front_origin_access_identity, 
                           CloudFrontOriginAccessIdentityConfig = 
                           { 'CallerReference': caller_reference, 'Comment': comment })
            return self.paginated_response(func)
        except Exception as e:
            self.module.fail_json(msg="Error creating cloud front origin access identity - " + str(e), 
                                  exception=traceback.format_exc())

    def delete_origin_access_identity(self, origin_access_identity_id, e_tag):
        try:
            func = partial(self.client.delete_cloud_front_origin_access_identity,
                           Id=origin_access_identity_id, IfMatch=e_tag)
            return self.paginated_response(func)
        except Exception as e:
            self.module.fail_json(msg="Error deleting cloud front origin access identity - " + str(e),
                                  exception=traceback.format_exc())

    def update_origin_access_identity(self, caller_reference, comment, origin_access_identity_id, e_tag):
        try:
            func = partial(self.client.update_cloud_front_origin_access_identity,
                           CloudFrontOriginAccessIdentityConfig = 
                           { 'CallerReference': caller_reference, 'Comment': comment },
                           Id=origin_access_identity_id, IfMatch=e_tag)
            return self.paginated_response(func)
        except Exception as e:
            self.module.fail_json(msg="Error updating cloud front origin access identity - " + str(e),
                                  exception=traceback.format_exc())
    
    def create_invalidation(self, distribution_id, invalidation_batch):
        try:
            func = partial(self.client.create_invalidation, DistributionId = distribution_id, 
                           InvalidationBatch=invalidation_batch)
            return self.paginated_response(func)
        except Exception as e:
            self.module.fail_json(msg="Error creating invalidation(s) - " + str(e),
                                  exception=traceback.format_exec())

    def paginated_response(self, func, result_key=""):
        '''
        Returns expanded response for paginated operations.
        The 'result_key' is used to define the concatenated results that are combined 
        from each paginated response.
        '''
        args = dict()
        results = dict()
        loop = True
        while loop:
            response = func(**args)
            if result_key == "":
                result = response
                result.pop('ResponseMetadata', None)
            else:
                result = response.get(result_key)
            results.update(result)
            args['NextToken'] = response.get('NextToken')
            loop = args['NextToken'] is not None
        return results

def main():
    argument_spec = ec2_argument_spec()

    argument_spec.update(dict(
        create_origin_access_identity=dict(required=False, default=False, type='bool'),
        caller_reference=dict(required=False, default=None, type='str'),
        comment=dict(required=False, default=None, type='str'),
        create_distribution=dict(required=False, default=False, type='bool'),
        distribution_config=dict(required=False, default=None, type='json'),
        create_distribution_with_tags=dict(required=False, default=False, type='bool'),
        distribution_with_tags_config=dict(required=False, default=None, type='json'),
        create_invalidation=dict(required=False, default=False, type='bool'),
        distribution_id=dict(required=False, default=None, type='str'),
        invalidation_batch=dict(required=False, default=None, type='str'),
        create_streaming_distribution=dict(required=False, default=False, type='bool'),
        streaming_distribution_config=dict(required=False, default=None, type='json'),
        create_streaming_distribution_with_tags=dict(required=False, default=False, type='bool'),
        streaming_distribution_with_tags_config=dict(required=False, default=None, type='json'),
        delete_origin_access_identity=dict(required=False, default=False, type='bool'),
        origin_access_identity_id=dict(required=False, default=None, type='str'),
        e_tag=dict(required=False, default=None, type='str'),
        delete_distribution=dict(required=False, default=False, type='bool'),
        delete_streaming_distribution=dict(required=False, default=False, type='bool'),
        generate_presigned_url=dict(required=False, default=False, type='bool'),
        tag_resource=dict(required=False, default=False, type='bool'),
        untag_resource=dict(required=False, default=False, type='bool'),
        update_origin_access_identity=dict(required=False, default=False, type='bool'),
        update_distribution=dict(required=False, default=False, type='bool'),
        update_streaming_distribution=dict(required=False, default=False, type='bool'),
        content=dict(required=False, default=None, type='str')
    ))

    result = {}
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)
    
    if not HAS_BOTO3:
        module.fail_json(msg='Error boto3 is required.')
    
    service_mgr = CloudFrontServiceManager(module)
    
    create_origin_access_identity = module.params.get('create_origin_access_identity')
    caller_reference = module.params.get('caller_reference')
    comment = module.params.get('comment')

    delete_origin_access_identity = module.params.get('delete_origin_access_identity')
    origin_access_identity_id = module.params.get('origin_access_identity_id')
    e_tag = module.params.get('e_tag')

    update_origin_access_identity = module.params.get('update_origin_access_identity')
    origin_access_identity_id = module.params.get('origin_access_identity_id')

    create_distribution = module.params.get('create_distribution')
    distribution_config = module.params.get('distribution_config')

    create_distribution_with_tags = module.params.get('create_distribution_with_tags')
    distribution_with_tags_config = module.params.get('distribution_with_tags_config')

    create_invalidation = module.params.get('create_invalidation')
    distribution_id = module.params.get('distribution_id')
    invalidation_batch = module.params.get('invalidation_batch')

    create_streaming_distribution_with_tags = module.params.get('create_streaming_distribution_with_tags')
    streaming_distribution_with_tags_config = module.params.get('streaming_distribution_with_tags_config')

    if(create_origin_access_identity):
        result=service_mgr.create_origin_access_identity(caller_reference, comment)
    elif(delete_origin_access_identity):
        result=service_mgr.delete_origin_access_identity(origin_access_identity_id, e_tag)
    elif(update_origin_access_identity):
        result=service_mgr.update_origin_access_identity(caller_reference, comment, origin_access_identity_id, e_tag)
    elif(create_invalidation):
        result=service_mgr.create_invalidation(distribution_id, invalidation_batch)

    module.exit_json(changed=True, **camel_dict_to_snake_dict(result))

if __name__ == '__main__':
    main()
