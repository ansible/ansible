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
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: cloudfront_facts
short_description: Obtain facts about an AWS CloudFront distribution
description:
  - Gets information about an AWS CloudFront distribution
requirements:
  - boto3 >= 1.0.0
  - python >= 2.6
version_added: "2.2"
author: Willem van Ketwich (@wilvk)
options:
    distribution_id:
        description:
          - The id of the CloudFront distribution. Used with distribution, distribution_config, invalidation, streaming_distribution, streaming_distribution_config, list_invalidations.
        required: false
    invalidation_id:
        description:
          - The id of the invalidation to get information about. Used with invalidation
          required: false
    cloud_front_origin_access_identity_id:
        description:
          - The id of the cloudfront origin access identity to get information about
        required: false
    web_acl_id:
        description:
          - Used with list_distributions_by_web_acl_id
          required: false
    domain_name_alias:
        description:
          - Can be used instead of distribution_id - uses the aliased CNAME for the cloudfront distribution to get the distribution id where required
          required: false
    all_lists:
        description:
            - Get all cloudfront lists that do not require parameters
        required: false
        default: false
    cloud_front_origin_access_identity:
        description:
            - Get information about an origin access identity
        required: false
        default: false
    cloud_front_origin_access_identity_config:
        description:
            - Get the configuration information about an origin access identity
        required: false
        default: false
    distribution:
        description:
            - Get information about a distribution. Requires distribution_id or domain_name_alias to be specified.
    distribution_config:
        description:
            - Get the configuration information about a distribution. Requires distribution_id or domain_name_alias to be specified.
        required: false
        default: false
    invalidation:
        description:
            - Get information about an invalidation. Requires invalidation_id to be specified.
        required: false
        default: false
    streaming_distribution:
        description:
            - Get information about a specified RTMP distribution. Requires distribution_id or domain_name_alias to be specified.
        required: false
        default: false
    streaming_distribution_configuration:
        description:
            - Get the configuration information about a specified RTMP distribution. Requires distribution_id or domain_name_alias to be specified.
        required: false
        default: false
    list_cloud_front_origin_access_identities:
        description:
            - Get a list of cloudfront origin access identities. Requires cloud_front_origin_access_identity_id to be set.
        required: false
        default: false
    list_distributions:
        description:
            - Get a list of cloudfront distributions.
        required: false
        default: false
    list_distributions_by_web_acl:
        description:
            - Get a list of distributions using web acl id as a filter. Requires web_acl_id to be set.
        required: false
        default: false
    list_invalidations:
        description:
            - Get a list of invalidations. Requires distribution_id or domain_name_alias to be specified.
        required: false
        default: false
    list_streaming_distributions:
        description:
            - Get a list of streaming distributions
        required: false
        default: false

extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Get information about a distribution
- cloudfront_facts:
    distribution: true
    distribution_id: my-cloudfront-distribution-id

# Get information about a distribution using the CNAME of the cloudfront distribution
- cloudfront_facts:
    distribution: true
    domain_name_alias: www.my-website.com

# Facts are published in ansible_facts['cloudfront'][<distribution_name>]
- debug:
    msg: '{{ ansible_facts['cloudfront']['my-cloudfront-distribution-id'] }}'

# Get all information about an invalidation for a distribution
- cloudfront_facts:
    invalidation: true
    distribution_id: my-cloudfront-distribution-id
    invalidation_id: my-cloudfront-invalidation-id

# Get all information about a cloudfront origin access identity
- cloudfront_facts:
    cloud_front_origin_access_identity: true
    cloud_front_origin_access_identity_id: my-cloudfront-origin-access-identity-id

# Get all information about lists not requiring parameters (ie. list_cloud_front_origin_access_identities, list_distributions, list_streaming_distributions)
- cloudfront_facts:
    all_lists: true
'''

RETURN = '''
cloud_front_origin_access_identity:
    description: Describes the origin access identity information. Requires cloud_front_origin_access_identity_id to be set.
    returned: only if cloud_front_origin_access_identity is true
    type: dict
cloud_front_origin_access_identity_configuration:
    description: Describes the origin access identity information configuration information. Requires cloud_front_origin_access_identity_id to be set.
    returned: only if cloud_front_origin_access_identity_configuration is true
    type: dict
distribution:
    description: Facts about a cloudfront distribution. Requires distribution_id or domain_name_alias to be specified. Requires cloud_front_origin_access_identity_id to be set.
    returned: only if distribution is true
    type: dict
distribution_config:
    description: Facts about a cloudfront distribution's config. Requires distribution_id or domain_name_alias to be specified.
    returned: only if distribution_config is true
    type: dict
invalidation:
    description: Describes the invalidation information for the distribution. Requires invalidation_id to be specified and either distribution_id or domain_name_alias.
    returned: only if invalidation is true
    type: dict
streaming_distribution:
    description: Describes the streaming information for the distribution. Requires distribution_id or domain_name_alias to be specified.
    returned: only if streaming_distribution is true
    type: dict
streaming_distribution_configuration:
    description: Describes the streaming configuration information for the distribution. Requires distribution_id or domain_name_alias to be specified.
    returned: only if streaming_distribution_configuration is true
    type: dict
'''

try:
    import boto3
    import botocore
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ansible.module_utils.ec2 import get_aws_connection_info
from ansible.module_utils.basic import AnsibleModule
from functools import partial
import json
import traceback

class CloudFrontServiceManager:
    """Handles CloudFront Services"""

    def __init__(self, module):
        self.module = module

        try:
            region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
            self.client = boto3_conn(module, conn_type='client',
                                     resource='cloudfront', region=region,
                                     endpoint=ec2_url, **aws_connect_kwargs)
        except botocore.exceptions.NoRegionError:
            self.module.fail_json(msg="Region must be specified as a parameter, in AWS_DEFAULT_REGION environment variable or in boto configuration file")
        except Exception as e:
            self.module.fail_json(msg="Can't establish connection - " + str(e), exception=traceback.format_exc(e))

    def get_distribution(self, distribution_id):
        try:
            func = partial(self.client.get_distribution,Id=distribution_id)
            return self.paginated_response(func, 'Distribution')
        except Exception as e:
            self.module.fail_json(msg="Error describing distribution - " + str(e), exception=traceback.format_exc(e))

    def get_distribution_config(self, distribution_id):
        try:
            func = partial(self.client.get_distribution_config,Id=distribution_id)
            return self.paginated_response(func, 'DistributionConfig')
        except Exception as e:
            self.module.fail_json(msg="Error describing distribution configuration - " + str(e), exception=traceback.format_exec(e))

    def get_cloud_front_origin_access_identity(self, origin_access_identity_id):
        try:
            func = partial(self.client.get_cloud_front_origin_access_identity,Id=origin_access_identity_id)
            return self.paginated_response(func, 'CloudFrontOriginAccessIdentity')
        except Exception as e:
            self.module.fail_json(msg="Error describing origin access identity - " + str(e), exception=traceback.format_exc(e))

    def get_cloud_front_origin_access_identity_config(self, origin_access_identity_id):
        try:
            func = partial(self.client.get_cloud_front_origin_access_identity_config,Id=origin_access_identity_id)
            return self.paginated_response(func, 'CloudFrontOriginAccessIdentityConfig')
        except Exception as e:
            self.module.fail_json(msg="Error describing origin access identity configuration - " + str(e), exception=traceback.format_exc(e))

    def get_invalidation(self, distribution_id, invalidation_id):
        try:
            func = partial(self.client.get_invalidation,DistributionId=distribution_id,Id=invalidation_id)
            return self.paginated_response(func, 'Invalidation')
        except Exception as e:
            self.module.fail_json(msg="Error describing invalidation - " + str(e), exception=traceback.format_exc(e))

    def get_streaming_distribution(self, distribution_id):
        try:
            func = partial(self.client.get_streaming_distribution,Id=distribution_id)
            return self.paginated_response(func, 'StreamingDistribution')
        except Exception as e:
            self.module.fail_json(msg="Error describing streaming distribution - " + str(e), exception=traceback.format_exc(e))

    def get_streaming_distribution_config(self, distribution_id):
        try:
            func = partial(self.client.get_streaming_distribution_config,Id=distribution_id)
            return self.paginated_response(func, 'StreamingDistributionConfig')
        except Exception as e:
            self.module.fail_json(msg="Error describing streaming distribution - " + str(e), exception=traceback.format_exc(e))

    def list_cloud_front_origin_access_identities(self):
        try:
            func = partial(self.client.list_cloud_front_origin_access_identities)
            return self.paginated_response(func, 'CloudFrontOriginAccessIdentityList')
        except Exception as e:
            self.module.fail_json(msg="Error listing cloud front origin access identities = " + str(e), exception=traceback.format_exc(e))

    def list_distributions(self):
        try:
            func = partial(self.client.list_distributions)
            return self.paginated_response(func, 'DistributionList')
        except Exception as e:
            self.module.fail_json(msg="Error listing distributions = " + str(e), exception=traceback.format_exc(e))

    def list_distributions_by_web_acl(self, web_acl_id):
        try:
            func = partial(self.client.list_distributions, web_acl_id)
            return self.paginated_response(func, 'DistributionList')
        except Exception as e:
            self.module.fail_json(msg="Error listing distributions by web acl id = " + str(e), exception=traceback.format_exc(e))

    def list_invalidations(self):
        try:
            func = partial(self.client.list_invalidations)
            return self.paginated_response(func, 'InvalidationList')
        except Exception as e:
            self.module.fail_json(msg="Error listing invalidations = " + str(e), exception=traceback.format_exc(e))

    def list_streaming_distributions(self):
        try:
            func = partial(self.client.list_streaming_distributions)
            return self.paginated_response(func, 'StreamingDistributionList')
        except Exception as e:
            self.module.fail_json(msg="Error listing streaming distributions = " + str(e), exception=traceback.format_exc(e))

    def get_distribution_id_from_domain_name(self, domain_name):
        try:
            distribution_id = ""
            distributions = self.list_distributions()
            for dist in distributions['Items']:
                for alias in dist['Aliases']['Items']:
                    if str(alias).lower() == domain_name.lower():
                        distribution_id = str(dist['Id'])
                        break
            return distribution_id
        except Exception as e:
            self.module.fail_json(msg="Error getting distribution id from domain name = " + str(e), exception=traceback.format_exc(e))

    def paginated_response(self, func, result_key, next_token=None):
        '''
        Returns expanded response for paginated operations.
        The 'result_key' is used to define the concatenated results that are combined from each paginated response.
        '''
        args=dict()
        if next_token:
            args['NextToken'] = next_token
        response = func(**args)
        result = response.get(result_key)
        next_token = response.get('NextToken')
        if not next_token:
           return result
        return result + self.paginated_response(func, result_key, next_token)

def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        distribution_id=dict(required=False, type='str'),
        invalidation_id=dict(required=False, type='str'),
        cloud_front_origin_access_identity_id=dict(required=False, type='str'),
        domain_name_alias=dict(required=False, type='str'),
        all_lists=dict(required=False, default=False, type='bool'),
        distribution=dict(required=False, default=False, type='bool'),
        distribution_config=dict(required=False, default=False, type='bool'),
        cloud_front_origin_access_identity=dict(required=False, default=False, type='bool'),
        cloud_front_origin_access_identity_config=dict(required=False, default=False, type='bool'),
        invalidation=dict(required=False, default=False, type='bool'),
        streaming_distribution=dict(required=False, default=False, type='bool'),
        streaming_distribution_config=dict(required=False, default=False, type='bool'),
        list_cloud_front_origin_access_identities=dict(required=False, default=False, type='bool'),
        list_distributions=dict(required=False, default=False, type='bool'),
        list_distributions_by_web_acl=dict(required=False, default=False, type='bool'),
        list_invalidations=dict(required=False, default=False, type='bool'),
        list_streaming_distributions=dict(required=False, default=False, type='bool')
    ))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    if not HAS_BOTO3:
      module.fail_json(msg='boto3 is required.')

    service_mgr = CloudFrontServiceManager(module)

    distribution_id = module.params.get('distribution_id')
    invalidation_id = module.params.get('invalidation_id')
    cloud_front_origin_access_identity_id = module.params.get('cloud_front_origin_access_identity_id')
    web_acl_id = module.params.get('web_acl_id')
    domain_name_alias = module.params.get('domain_name_alias')

    all_lists = module.params.get('all_lists')

    distribution = module.params.get('distribution')
    distribution_config = module.params.get('distribution_config')
    cloud_front_origin_access_identity = module.params.get('cloudfront_origin_access_identity')
    cloud_front_origin_access_identity_config = module.params.get('cloudfront_origin_access_identity_config')
    invalidation = module.params.get('invalidation')
    streaming_distribution = module.params.get('streaming_distribution')
    streaming_distribution_config = module.params.get('streaming_distribution_config')

    list_cloud_front_origin_access_identities = module.params.get('list_cloud_front_origin_access_identities')
    list_distributions = module.params.get('list_distributions')
    list_distributions_by_web_acl_id = module.params.get('list_distributions_by_web_acl_id');
    list_invalidations = module.params.get('list_invalidations')
    list_streaming_distributions = module.params.get('list_streaming_distributions')

    require_distribution_id = (distribution or distribution_config or invalidation or
            streaming_distribution or streaming_distribution_config or list_invalidations)

    # validations
    if require_distribution_id and distribution_id is None and domain_name_alias is None:
        module.fail_json(msg='Error distribution_id or domain_name have not been specified.')
    if (invalidation and invalidation_id is None):
        module.fail_json(msg='Error invalidation_id has not been specified.')
    if (cloud_front_origin_access_identity or cloud_front_origin_access_identity_config) and cloud_front_origin_access_identity_id is None:
        module.fail_json(msg='Error cloud_front_origin_access_identity_id has not been specified.')
    if list_distributions_by_web_acl_id and web_acl_id is None:
        module.fail_json(msg='Error web_acl_id has not been specified.')

    # get distribution id from domain name alias
    if require_distribution_id and distribution_id is None:
        distribution_id = service_mgr.get_distribution_id_from_domain_name(domain_name_alias)
        if not distribution_id:
            module.fail_json(msg='Error unable to source a distribution id from domain_name_alias')

    # set appropriate ansible_facts id
    if distribution_id:
        result = { 'ansible_facts': { 'cloudfront': { distribution_id:{} } } }
        facts = result['ansible_facts']['cloudfront'][distribution_id]
    elif cloud_front_origin_access_identity_id:
        result = { 'ansible_facts': { 'cloudfront': { cloud_front_origin_access_identity_id:{} } } }
        facts = result['ansible_facts']['cloudfront'][cloud_front_origin_access_identity_id]
    elif web_acl_id:
        result = { 'ansible_facts': { 'cloudfront': { web_acl_id:{} } } }
        facts = result['ansible_facts']['cloudfront'][web_acl_id]
    else:
        result = { 'ansible_facts': { 'cloudfront': {} } }
        facts = result['ansible_facts']['cloudfront']

    # call details based on options
    if distribution:
        facts['distribution'] = service_mgr.get_distribution(distribution_id)
    if distribution_config:
        facts['distribution_config'] = service_mgr.get_distribution_config(distribution_id)
    if cloud_front_origin_access_identity:
        facts['cloud_front_origin_access_identity'] = service_mgr.get_cloud_front_origin_access_identity(cloud_front_origin_access_identity_id)
    if cloud_front_origin_access_identity_config:
        facts['cloud_front_origin_access_identity_config'] = service_mgr.get_cloud_front_origin_access_identity_config(cloud_front_origin_access_identity_id)
    if invalidation:
        facts['invalidation'] = service_mgr.get_invalidation(distribution_id, invalidation_id)
    if streaming_distribution:
        facts['streaming_distribution'] = service_mgr.get_streaming_distribution(distribution_id)
    if streaming_distribution_config:
        facts['streaming_distribution_config'] = service_mgr.get_streaming_distribution_config(distribution_id)

    # call list based on options
    if all_lists or list_cloud_front_origin_access_identities:
        facts['list_cloud_front_origin_access_identities'] = service_mgr.list_cloud_front_origin_access_identities()
    if all_lists or list_distributions:
        facts['list_distributions'] = service_mgr.list_distributions()
    if all_lists or list_streaming_distributions:
        facts['list_streaming_distributions'] = service_mgr.list_streaming_distributions()
    if list_distributions_by_web_acl_id:
        facts['list_distributions_by_web_acl'] = service_mgr.list_distributions_by_web_acl()
    if list_invalidations:
        facts['list_invalidations'] = service_mgr.list_invalidations(distribution_id)

    result['changed'] = False
    module.exit_json(msg="Retrieved cloudfront facts.", ansible_facts=result)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
