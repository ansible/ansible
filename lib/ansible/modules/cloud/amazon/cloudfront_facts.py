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
module: cloudfront_facts
short_description: Obtain facts about an AWS CloudFront distribution
description:
  - Gets information about an AWS CloudFront distribution
requirements:
  - boto3 >= 1.0.0
  - python >= 2.6
version_added: "2.3"
author: Willem van Ketwich (@wilvk)
options:
    distribution_id:
        description:
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
          - The id of the CloudFront distribution. Used with I(distribution), I(distribution_config),
            I(invalidation), I(streaming_distribution), I(streaming_distribution_config), I(list_invalidations).
        required: false
    invalidation_id:
        description:
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< 309a37de862dd73acdd0d85102299031ee40537d
=======
>>>>>>> a1c87a1c06... fixed shippable build error
=======
<<<<<<< 309a37de862dd73acdd0d85102299031ee40537d
>>>>>>> 8b17f86304... initial commit of cloudfront_facts.py
=======
>>>>>>> c495682bac... fixed shippable build error
          - The id of the invalidation to get information about. Used with invalidation.
=======
          - The id of the invalidation to get information about. Used with I(invalidation).
>>>>>>> ebfc7bac94... cloudfront_facts module improvements
=======
            - The id of the CloudFront distribution. Used with distribution, distribution_config, invalidation, streaming_distribution, streaming_distribution_config, list_invalidations.
        required: false
    invalidation_id:
        description:
            - The id of the invalidation to get information about. Used with invalidation.
>>>>>>> 04a3aa6110... added summary documentation
=======
            - The id of the CloudFront distribution. Used with distribution, distribution_config, invalidation, streaming_distribution, streaming_distribution_config, list_invalidations.
        required: false
    invalidation_id:
        description:
            - The id of the invalidation to get information about. Used with invalidation.
>>>>>>> 00065502e7... added summary documentation
=======
          - The id of the CloudFront distribution. Used with distribution, distribution_config, invalidation, streaming_distribution, streaming_distribution_config, list_invalidations.
        required: false
    invalidation_id:
        description:
          - The id of the invalidation to get information about. Used with invalidation.
>>>>>>> c586abb069... reverted spacing in YAML as advised by @ryansb
        required: false
    origin_access_identity_id:
        description:
          - The id of the cloudfront origin access identity to get information about.
        required: false
    web_acl_id:
        description:
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
          - Used with I(list_distributions_by_web_acl_id).
        required: false
    domain_name_alias:
        description:
          - Can be used instead of I(distribution_id) - uses the aliased CNAME for the cloudfront
            distribution to get the distribution id where required.
=======
=======
>>>>>>> 00065502e7... added summary documentation
            - Used with list_distributions_by_web_acl_id.
        required: false
    domain_name_alias:
        description:
            - Can be used instead of distribution_id - uses the aliased CNAME for the cloudfront distribution to get the distribution id where required.
<<<<<<< HEAD
>>>>>>> 04a3aa6110... added summary documentation
=======
>>>>>>> 00065502e7... added summary documentation
=======
          - Used with list_distributions_by_web_acl_id.
        required: false
    domain_name_alias:
        description:
          - Can be used instead of distribution_id - uses the aliased CNAME for the cloudfront distribution to get the distribution id where required.
>>>>>>> c586abb069... reverted spacing in YAML as advised by @ryansb
        required: false
    all_lists:
        description:
          - Get all cloudfront lists that do not require parameters.
        required: false
        default: false
    origin_access_identity:
        description:
          - Get information about an origin access identity. Requires I(origin_access_identity_id)
            to be specified.
        required: false
        default: false
    origin_access_identity_config:
        description:
<<<<<<< HEAD
            - Get the configuration information about an origin access identity. Requires origin_access_identity_id to be specified.
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> 8b17f86304... initial commit of cloudfront_facts.py
=======
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
>>>>>>> initial commit of cloudfront_facts.py
<<<<<<< HEAD
=======
          - Get the configuration information about an origin access identity. Requires
            I(origin_access_identity_id) to be specified.
>>>>>>> ebfc7bac94... cloudfront_facts module improvements
=======
>>>>>>> a1c87a1c06... fixed shippable build error
=======
>>>>>>> 8b17f86304... initial commit of cloudfront_facts.py
=======
>>>>>>> c495682bac... fixed shippable build error
        required: false
        default: false
    distribution:
        description:
<<<<<<< HEAD
            - Get information about a distribution. Requires distribution_id or domain_name_alias to be specified.
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< 309a37de862dd73acdd0d85102299031ee40537d
=======
          - Get information about a distribution. Requires I(distribution_id) or I(domain_name_alias)
            to be specified.
>>>>>>> ebfc7bac94... cloudfront_facts module improvements
=======
>>>>>>> a1c87a1c06... fixed shippable build error
=======
<<<<<<< 309a37de862dd73acdd0d85102299031ee40537d
>>>>>>> 8b17f86304... initial commit of cloudfront_facts.py
=======
>>>>>>> c495682bac... fixed shippable build error
        required: false
        default: false
    distribution_config:
        description:
          - Get the configuration information about a distribution. Requires I(distribution_id)
            or I(domain_name_alias) to be specified.
        required: false
        default: false
    invalidation:
        description:
            - Get information about an invalidation. Requires I(invalidation_id) to be specified.
        required: false
        default: false
    streaming_distribution:
        description:
            - Get information about a specified RTMP distribution. Requires I(distribution_id) or
              I(domain_name_alias) to be specified.
        required: false
        default: false
    streaming_distribution_configuration:
        description:
            - Get the configuration information about a specified RTMP distribution.
              Requires I(distribution_id) or I(domain_name_alias) to be specified.
        required: false
        default: false
    list_origin_access_identities:
        description:
<<<<<<< HEAD
            - Get a list of cloudfront origin access identities. Requires origin_access_identity_id to be set.
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> 8b17f86304... initial commit of cloudfront_facts.py
=======
    list_cloud_front_origin_access_identities:
        description:
            - Get a list of cloudfront origin access identities. Requires cloud_front_origin_access_identity_id to be set.
>>>>>>> initial commit of cloudfront_facts.py
<<<<<<< HEAD
=======
            - Get a list of cloudfront origin access identities. Requires I(origin_access_identity_id) to be set.
>>>>>>> ebfc7bac94... cloudfront_facts module improvements
=======
>>>>>>> a1c87a1c06... fixed shippable build error
=======
>>>>>>> 8b17f86304... initial commit of cloudfront_facts.py
=======
>>>>>>> c495682bac... fixed shippable build error
        required: false
        default: false
    list_distributions:
        description:
            - Get a list of cloudfront distributions.
        required: false
        default: false
    list_distributions_by_web_acl_id:
        description:
            - Get a list of distributions using web acl id as a filter. Requires I(web_acl_id) to be set.
        required: false
        default: false
    list_invalidations:
        description:
            - Get a list of invalidations. Requires I(distribution_id) or I(domain_name_alias) to be specified.
        required: false
        default: false
    list_streaming_distributions:
        description:
            - Get a list of streaming distributions.
        required: false
        default: false
    summary:
        description:
<<<<<<< HEAD
<<<<<<< HEAD
            - Returns a summary of all distributions, streaming distributions and origin_access_identities.
              This is the default behaviour if no option is selected.
=======
            - Returns a summary of all distributions, streaming distributions and origin_access_identities. This is the default behaviour if no option is selected.
>>>>>>> 04a3aa6110... added summary documentation
=======
            - Returns a summary of all distributions, streaming distributions and origin_access_identities. This is the default behaviour if no option is selected.
>>>>>>> 00065502e7... added summary documentation
        required: false
        default: false

extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Get a summary of distributions
- cloudfront_facts:
    summary: true

# Get information about a distribution
- cloudfront_facts:
    distribution: true
    distribution_id: my-cloudfront-distribution-id

# Get information about a distribution using the CNAME of the cloudfront distribution.
- cloudfront_facts:
    distribution: true
    domain_name_alias: www.my-website.com

# Facts are published in ansible_facts['cloudfront'][<distribution_name>]
- debug:
    msg: "{{ ansible_facts['cloudfront']['my-cloudfront-distribution-id'] }}"

- debug:
    msg: "{{ ansible_facts['cloudfront']['www.my-website.com'] }}"

# Get all information about an invalidation for a distribution.
- cloudfront_facts:
    invalidation: true
    distribution_id: my-cloudfront-distribution-id
    invalidation_id: my-cloudfront-invalidation-id

# Get all information about a cloudfront origin access identity.
- cloudfront_facts:
    origin_access_identity: true
    origin_access_identity_id: my-cloudfront-origin-access-identity-id

# Get all information about lists not requiring parameters (ie. list_origin_access_identities, list_distributions, list_streaming_distributions)
- cloudfront_facts:
    origin_access_identity: true
    origin_access_identity_id: my-cloudfront-origin-access-identity-id

# Get all information about lists not requiring parameters (ie. list_origin_access_identities, list_distributions, list_streaming_distributions)
- cloudfront_facts:
    origin_access_identity: true
    origin_access_identity_id: my-cloudfront-origin-access-identity-id

# Get all information about lists not requiring parameters (ie. list_origin_access_identities, list_distributions, list_streaming_distributions)
- cloudfront_facts:
    origin_access_identity: true
    origin_access_identity_id: my-cloudfront-origin-access-identity-id

# Get all information about lists not requiring parameters (ie. list_origin_access_identities, list_distributions, list_streaming_distributions)
- cloudfront_facts:
    all_lists: true
'''

RETURN = '''
origin_access_identity:
    description: Describes the origin access identity information. Requires I(origin_access_identity_id) to be set.
    returned: only if I(origin_access_identity) is true
    type: dict
origin_access_identity_configuration:
    description: Describes the origin access identity information configuration information. Requires I(origin_access_identity_id) to be set.
    returned: only if I(origin_access_identity_configuration) is true
    type: dict
distribution:
<<<<<<< HEAD
    description: Facts about a cloudfront distribution. Requires distribution_id or domain_name_alias to be specified. Requires origin_access_identity_id to be set.
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> 8b17f86304... initial commit of cloudfront_facts.py
=======
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
>>>>>>> initial commit of cloudfront_facts.py
<<<<<<< HEAD
=======
    description: >
      Facts about a cloudfront distribution. Requires I(distribution_id) or I(domain_name_alias)
      to be specified. Requires I(origin_access_identity_id) to be set.
>>>>>>> ebfc7bac94... cloudfront_facts module improvements
=======
>>>>>>> a1c87a1c06... fixed shippable build error
=======
>>>>>>> 8b17f86304... initial commit of cloudfront_facts.py
=======
>>>>>>> c495682bac... fixed shippable build error
    returned: only if distribution is true
    type: dict
distribution_config:
    description: >
      Facts about a cloudfront distribution's config. Requires I(distribution_id) or I(domain_name_alias)
      to be specified.
    returned: only if I(distribution_config) is true
    type: dict
invalidation:
    description: >
      Describes the invalidation information for the distribution. Requires
      I(invalidation_id) to be specified and either I(distribution_id) or I(domain_name_alias.)
    returned: only if invalidation is true
    type: dict
streaming_distribution:
    description: >
      Describes the streaming information for the distribution. Requires
      I(distribution_id) or I(domain_name_alias) to be specified.
    returned: only if I(streaming_distribution) is true
    type: dict
streaming_distribution_configuration:
    description: >
      Describes the streaming configuration information for the distribution.
      Requires I(distribution_id) or I(domain_name_alias) to be specified.
    returned: only if I(streaming_distribution_configuration) is true
    type: dict
summary:
    description: Gives a summary of distributions, streaming distributions and origin access identities.
    returned: as default or if summary is true
    type: dict
summary:
    description: Gives a summary of distributions, streaming distributions and origin access identities.
    returned: as default or if summary is true
    type: dict
summary:
    description: Gives a summary of distributions, streaming distributions and origin access identities.
    returned: as default or if summary is true
    type: dict
'''

from ansible.module_utils.ec2 import get_aws_connection_info, ec2_argument_spec, boto3_conn, HAS_BOTO3
from ansible.module_utils.ec2 import boto3_tag_list_to_ansible_dict, camel_dict_to_snake_dict
from ansible.module_utils.basic import AnsibleModule
from functools import partial
import traceback

try:
    import botocore
except ImportError:
    pass  # will be caught by imported HAS_BOTO3

<<<<<<< HEAD
from ansible.module_utils.ec2 import get_aws_connection_info
from ansible.module_utils.ec2 import ec2_argument_spec
from ansible.module_utils.ec2 import boto3_conn
from ansible.module_utils.basic import AnsibleModule
from functools import partial
import json
import traceback
=======
>>>>>>> bd4003e3f2... Add tags to cloudfront distribution facts

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
<<<<<<< HEAD
            self.module.fail_json(msg="Region must be specified as a parameter, in AWS_DEFAULT_REGION "
                                  "environment variable or in boto configuration file")
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Can't establish connection - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))
=======
            self.module.fail_json(msg="Region must be specified as a parameter, in AWS_DEFAULT_REGION environment variable or in boto configuration file")
        except Exception as e:
            self.module.fail_json(msg="Can't establish connection - " + str(e),
                                  exception=traceback.format_exc(e))
>>>>>>> 6f7c9ebd1e... modified exceptions to multi line as advised by @willthames

    def get_distribution(self, distribution_id):
        try:
            func = partial(self.client.get_distribution,Id=distribution_id)
            return self.paginated_response(func)
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
            return self.paginated_response(func, 'Distribution')
>>>>>>> initial commit of cloudfront_facts.py
=======
>>>>>>> a1c87a1c06... fixed shippable build error
=======
=======
            return self.paginated_response(func, 'Distribution')
>>>>>>> initial commit of cloudfront_facts.py
>>>>>>> 8b17f86304... initial commit of cloudfront_facts.py
=======
>>>>>>> c495682bac... fixed shippable build error
        except Exception as e:
<<<<<<< HEAD
=======
        except botocore.exceptions.ClientError as e:
>>>>>>> ebfc7bac94... cloudfront_facts module improvements
            self.module.fail_json(msg="Error describing distribution - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))
=======
            self.module.fail_json(msg="Error describing distribution - " + str(e),
                                  exception=traceback.format_exc(e))
>>>>>>> 6f7c9ebd1e... modified exceptions to multi line as advised by @willthames

    def get_distribution_config(self, distribution_id):
        try:
            func = partial(self.client.get_distribution_config,Id=distribution_id)
            return self.paginated_response(func)
<<<<<<< HEAD
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error describing distribution configuration - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))
=======
        except Exception as e:
            self.module.fail_json(msg="Error describing distribution configuration - " + str(e),
                                  exception=traceback.format_exec(e))
>>>>>>> 6f7c9ebd1e... modified exceptions to multi line as advised by @willthames

    def get_origin_access_identity(self, origin_access_identity_id):
        try:
            func = partial(self.client.get_cloud_front_origin_access_identity,Id=origin_access_identity_id)
            return self.paginated_response(func)
<<<<<<< HEAD
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error describing origin access identity - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))
=======
        except Exception as e:
            self.module.fail_json(msg="Error describing origin access identity - " + str(e),
                                  exception=traceback.format_exc(e))
>>>>>>> 6f7c9ebd1e... modified exceptions to multi line as advised by @willthames

    def get_origin_access_identity_config(self, origin_access_identity_id):
        try:
            func = partial(self.client.get_cloud_front_origin_access_identity_config,Id=origin_access_identity_id)
            return self.paginated_response(func)
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> 8b17f86304... initial commit of cloudfront_facts.py
=======
            return self.paginated_response(func, 'DistributionConfig')
        except Exception as e:
<<<<<<< HEAD
            self.module.fail_json(msg="Error describing distribution configuration - " + str(e), exception=traceback.format_exec(e))

    def get_cloud_front_origin_access_identity(self, origin_access_identity_id):
        try:
            func = partial(self.client.get_cloud_front_origin_access_identity,Id=origin_access_identity_id)
            return self.paginated_response(func, 'CloudFrontOriginAccessIdentity')
<<<<<<< HEAD
=======
        except Exception as e:
            self.module.fail_json(msg="Error describing origin access identity - " + str(e), exception=traceback.format_exc(e))

    def get_cloud_front_origin_access_identity_config(self, origin_access_identity_id):
        try:
            func = partial(self.client.get_cloud_front_origin_access_identity_config,Id=origin_access_identity_id)
            return self.paginated_response(func, 'CloudFrontOriginAccessIdentityConfig')
>>>>>>> initial commit of cloudfront_facts.py
>>>>>>> 8b17f86304... initial commit of cloudfront_facts.py
        except Exception as e:
            self.module.fail_json(msg="Error describing origin access identity - " + str(e), exception=traceback.format_exc(e))

    def get_cloud_front_origin_access_identity_config(self, origin_access_identity_id):
        try:
            func = partial(self.client.get_cloud_front_origin_access_identity_config,Id=origin_access_identity_id)
            return self.paginated_response(func, 'CloudFrontOriginAccessIdentityConfig')
>>>>>>> initial commit of cloudfront_facts.py
=======
>>>>>>> a1c87a1c06... fixed shippable build error
=======
>>>>>>> c495682bac... fixed shippable build error
        except Exception as e:
=======
        except botocore.exceptions.ClientError as e:
>>>>>>> ebfc7bac94... cloudfront_facts module improvements
            self.module.fail_json(msg="Error describing origin access identity configuration - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))
=======
            self.module.fail_json(msg="Error describing origin access identity configuration - " + str(e),
                                  exception=traceback.format_exc(e))
>>>>>>> 6f7c9ebd1e... modified exceptions to multi line as advised by @willthames

    def get_invalidation(self, distribution_id, invalidation_id):
        try:
            func = partial(self.client.get_invalidation,DistributionId=distribution_id,Id=invalidation_id)
            return self.paginated_response(func)
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
            return self.paginated_response(func, 'Invalidation')
>>>>>>> initial commit of cloudfront_facts.py
=======
>>>>>>> a1c87a1c06... fixed shippable build error
=======
=======
            return self.paginated_response(func, 'Invalidation')
>>>>>>> initial commit of cloudfront_facts.py
>>>>>>> 8b17f86304... initial commit of cloudfront_facts.py
=======
>>>>>>> c495682bac... fixed shippable build error
        except Exception as e:
<<<<<<< HEAD
=======
        except botocore.exceptions.ClientError as e:
>>>>>>> ebfc7bac94... cloudfront_facts module improvements
            self.module.fail_json(msg="Error describing invalidation - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))
=======
            self.module.fail_json(msg="Error describing invalidation - " + str(e),
                                  exception=traceback.format_exc(e))
>>>>>>> 6f7c9ebd1e... modified exceptions to multi line as advised by @willthames

    def get_streaming_distribution(self, distribution_id):
        try:
            func = partial(self.client.get_streaming_distribution,Id=distribution_id)
            return self.paginated_response(func)
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
            return self.paginated_response(func, 'StreamingDistribution')
>>>>>>> initial commit of cloudfront_facts.py
=======
>>>>>>> a1c87a1c06... fixed shippable build error
=======
=======
            return self.paginated_response(func, 'StreamingDistribution')
>>>>>>> initial commit of cloudfront_facts.py
>>>>>>> 8b17f86304... initial commit of cloudfront_facts.py
=======
>>>>>>> c495682bac... fixed shippable build error
        except Exception as e:
<<<<<<< HEAD
=======
        except botocore.exceptions.ClientError as e:
>>>>>>> ebfc7bac94... cloudfront_facts module improvements
            self.module.fail_json(msg="Error describing streaming distribution - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))
=======
            self.module.fail_json(msg="Error describing streaming distribution - " + str(e),
                                  exception=traceback.format_exc(e))
>>>>>>> 6f7c9ebd1e... modified exceptions to multi line as advised by @willthames

    def get_streaming_distribution_config(self, distribution_id):
        try:
            func = partial(self.client.get_streaming_distribution_config,Id=distribution_id)
            return self.paginated_response(func)
<<<<<<< HEAD
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error describing streaming distribution - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))
=======
        except Exception as e:
            self.module.fail_json(msg="Error describing streaming distribution - " + str(e),
                                  exception=traceback.format_exc(e))
>>>>>>> 6f7c9ebd1e... modified exceptions to multi line as advised by @willthames

    def list_origin_access_identities(self):
        try:
            func = partial(self.client.list_cloud_front_origin_access_identities)
            origin_access_identity_list = self.paginated_response(func, 'CloudFrontOriginAccessIdentityList')
            if origin_access_identity_list['Quantity'] > 0:
<<<<<<< HEAD
<<<<<<< HEAD
                return origin_access_identity_list['Items']
            return {}
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error listing cloud front origin access identities - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))
=======
=======
>>>>>>> a9d15200cb... checks for empty list returned from boto, standardised list naming
              return origin_access_identity_list['Items']
            return {}
        except Exception as e:
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
            self.module.fail_json(msg="Error listing cloud front origin access identities = " + str(e), exception=traceback.format_exc(e))
>>>>>>> e52f2a22d6... checks for empty list returned from boto, standardised list naming
=======
            self.module.fail_json(msg="Error listing cloud front origin access identities - " + str(e), exception=traceback.format_exc(e))
>>>>>>> f9db9c39bc... more cleaning, allowed streaming distributions to be found by domain name alias
=======
            self.module.fail_json(msg="Error listing cloud front origin access identities - " + str(e), exception=traceback.format_exc(e))
>>>>>>> f0c712d884... more cleaning, allowed streaming distributions to be found by domain name alias
=======
            self.module.fail_json(msg="Error listing cloud front origin access identities - " + str(e),
                                  exception=traceback.format_exc(e))
>>>>>>> 6f7c9ebd1e... modified exceptions to multi line as advised by @willthames

    def list_distributions(self, keyed=True):
        try:
            func = partial(self.client.list_distributions)
            distribution_list = self.paginated_response(func, 'DistributionList')
            if distribution_list['Quantity'] == 0:
                return {}
            else:
                distribution_list = distribution_list['Items']
            if not keyed:
                return distribution_list
            return self.keyed_list_helper(distribution_list)
<<<<<<< HEAD
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error listing distributions - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))
=======
        except Exception as e:
<<<<<<< HEAD
            self.module.fail_json(msg="Error listing distributions - " + str(e), exception=traceback.format_exc(e))
<<<<<<< HEAD
>>>>>>> f9db9c39bc... more cleaning, allowed streaming distributions to be found by domain name alias
=======
>>>>>>> f0c712d884... more cleaning, allowed streaming distributions to be found by domain name alias
=======
            self.module.fail_json(msg="Error listing distributions - " + str(e),
                                  exception=traceback.format_exc(e))
>>>>>>> 6f7c9ebd1e... modified exceptions to multi line as advised by @willthames

    def list_distributions_by_web_acl_id(self, web_acl_id):
        try:
            func = partial(self.client.list_distributions_by_web_acl_id, WebAclId=web_acl_id)
            distribution_list = self.paginated_response(func, 'DistributionList')
            if distribution_list['Quantity'] == 0:
                return {}
            else:
                distribution_list = distribution_list['Items']
            return self.keyed_list_helper(distribution_list)
<<<<<<< HEAD
<<<<<<< HEAD
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error listing distributions by web acl id - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))
=======
=======
>>>>>>> a9d15200cb... checks for empty list returned from boto, standardised list naming
        except Exception as e:
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
            self.module.fail_json(msg="Error listing distributions by web acl id = " + str(e), exception=traceback.format_exc(e))
>>>>>>> e52f2a22d6... checks for empty list returned from boto, standardised list naming
=======
            self.module.fail_json(msg="Error listing distributions by web acl id - " + str(e), exception=traceback.format_exc(e))
>>>>>>> f9db9c39bc... more cleaning, allowed streaming distributions to be found by domain name alias
=======
            self.module.fail_json(msg="Error listing distributions by web acl id - " + str(e), exception=traceback.format_exc(e))
>>>>>>> f0c712d884... more cleaning, allowed streaming distributions to be found by domain name alias
=======
            self.module.fail_json(msg="Error listing distributions by web acl id - " + str(e),
                                  exception=traceback.format_exc(e))
>>>>>>> 6f7c9ebd1e... modified exceptions to multi line as advised by @willthames

    def list_invalidations(self, distribution_id):
        try:
            func = partial(self.client.list_invalidations, DistributionId=distribution_id)
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
            return self.paginated_response(func, 'InvalidationList')['Items']
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
            return self.paginated_response(func, 'StreamingDistributionConfig')
=======
=======
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
=======
            invalidations = self.paginated_response(func, 'InvalidationList')
            if invalidations['Quantity'] > 0:
                return invalidations['Items']
            return {}
>>>>>>> 6b9bb00cfc... initial commit of cloudfront_facts summary
        except Exception as e:
            self.module.fail_json(msg="Error listing distributions by web acl id = " + str(e), exception=traceback.format_exc(e))

    def list_invalidations(self):
        try:
            func = partial(self.client.list_invalidations)
            return self.paginated_response(func, 'InvalidationList')
>>>>>>> initial commit of cloudfront_facts.py
>>>>>>> 8b17f86304... initial commit of cloudfront_facts.py
        except Exception as e:
            self.module.fail_json(msg="Error describing streaming distribution - " + str(e), exception=traceback.format_exc(e))

    def list_cloud_front_origin_access_identities(self):
        try:
            func = partial(self.client.list_cloud_front_origin_access_identities)
            return self.paginated_response(func, 'CloudFrontOriginAccessIdentityList')
=======
            invalidations = self.paginated_response(func, 'InvalidationList')
            if invalidations['Quantity'] > 0:
                return invalidations['Items']
=======
            invalidation_list = self.paginated_response(func, 'InvalidationList')
            if invalidation_list['Quantity'] > 0:
                return invalidation_list['Items']
>>>>>>> e52f2a22d6... checks for empty list returned from boto, standardised list naming
            return {}
>>>>>>> d9c3f95f48... initial commit of cloudfront_facts summary
        except Exception as e:
<<<<<<< HEAD
            self.module.fail_json(msg="Error listing cloud front origin access identities = " + str(e), exception=traceback.format_exc(e))

    def list_distributions(self):
        try:
            func = partial(self.client.list_distributions)
            return self.paginated_response(func, 'DistributionList')
        except Exception as e:
            self.module.fail_json(msg="Error listing distributions = " + str(e), exception=traceback.format_exc(e))

<<<<<<< HEAD
    def list_distributions_by_web_acl(self, web_acl_id):
        try:
            func = partial(self.client.list_distributions, web_acl_id)
            return self.paginated_response(func, 'DistributionList')
=======
>>>>>>> c495682bac... fixed shippable build error
        except Exception as e:
            self.module.fail_json(msg="Error listing distributions by web acl id = " + str(e), exception=traceback.format_exc(e))

    def list_invalidations(self):
        try:
            func = partial(self.client.list_invalidations)
            return self.paginated_response(func, 'InvalidationList')
>>>>>>> initial commit of cloudfront_facts.py
=======
=======
>>>>>>> a9d15200cb... checks for empty list returned from boto, standardised list naming
            invalidation_list = self.paginated_response(func, 'InvalidationList')
            if invalidation_list['Quantity'] > 0:
                return invalidation_list['Items']
            return {}
<<<<<<< HEAD
>>>>>>> 93a689958e... [cloud] add summary feature and refactor AWS cloudfront_facts module (#20791)
=======
>>>>>>> a1c87a1c06... fixed shippable build error
        except Exception as e:
<<<<<<< HEAD
<<<<<<< HEAD
=======
        except botocore.exceptions.ClientError as e:
>>>>>>> ebfc7bac94... cloudfront_facts module improvements
            self.module.fail_json(msg="Error listing invalidations - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))
=======
            self.module.fail_json(msg="Error listing invalidations - " + str(e), exception=traceback.format_exc(e))
>>>>>>> f9db9c39bc... more cleaning, allowed streaming distributions to be found by domain name alias
=======
            self.module.fail_json(msg="Error listing invalidations - " + str(e), exception=traceback.format_exc(e))
>>>>>>> f0c712d884... more cleaning, allowed streaming distributions to be found by domain name alias
=======
            self.module.fail_json(msg="Error listing invalidations - " + str(e),
                                  exception=traceback.format_exc(e))
>>>>>>> 6f7c9ebd1e... modified exceptions to multi line as advised by @willthames

    def list_streaming_distributions(self, keyed=True):
        try:
            func = partial(self.client.list_streaming_distributions)
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< 309a37de862dd73acdd0d85102299031ee40537d
            streaming_distributions = self.paginated_response(func, 'StreamingDistributionList')['Items']
            return self.keyed_list_helper(streaming_distributions)
=======
            return self.paginated_response(func, 'StreamingDistributionList')
>>>>>>> initial commit of cloudfront_facts.py
=======
=======
>>>>>>> a9d15200cb... checks for empty list returned from boto, standardised list naming
            streaming_distribution_list = self.paginated_response(func, 'StreamingDistributionList')
            if streaming_distribution_list['Quantity'] == 0:
                return {}
            else:
                streaming_distribution_list = streaming_distribution_list['Items']
<<<<<<< HEAD
            if not keyed:
                return streaming_distribution_list
            return self.keyed_list_helper(streaming_distribution_list)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error listing streaming distributions - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

    def summary(self):
        summary_dict = {}
        summary_dict.update(self.summary_get_distribution_list(False))
        summary_dict.update(self.summary_get_distribution_list(True))
        summary_dict.update(self.summary_get_origin_access_identity_list())
        return summary_dict

    def summary_get_origin_access_identity_list(self):
        try:
            origin_access_identity_list = { 'origin_access_identities': [] }
            origin_access_identities = self.list_origin_access_identities()
            for origin_access_identity in origin_access_identities:
                oai_id = origin_access_identity['Id']
                oai_full_response = self.get_origin_access_identity(oai_id)
                oai_summary = { 'Id': oai_id, 'ETag': oai_full_response['ETag'] }
                origin_access_identity_list['origin_access_identities'].append( oai_summary )
            return origin_access_identity_list
<<<<<<< HEAD
>>>>>>> 93a689958e... [cloud] add summary feature and refactor AWS cloudfront_facts module (#20791)
=======
            streaming_distributions = self.paginated_response(func, 'StreamingDistributionList')['Items']
            return self.keyed_list_helper(streaming_distributions)
>>>>>>> a1c87a1c06... fixed shippable build error
=======
    def list_streaming_distributions(self, keyed=True):
        try:
            func = partial(self.client.list_streaming_distributions)
<<<<<<< HEAD
            streaming_distribution_list = self.paginated_response(func, 'StreamingDistributionList')
            if streaming_distribution_list['Quantity'] == 0:
                return {}
            else:
                streaming_distribution_list = streaming_distribution_list['Items']
            if not keyed:
                return streaming_distribution_list
            return self.keyed_list_helper(streaming_distribution_list)
>>>>>>> d9c3f95f48... initial commit of cloudfront_facts summary
        except Exception as e:
=======
        except botocore.exceptions.ClientError as e:
>>>>>>> ebfc7bac94... cloudfront_facts module improvements
            self.module.fail_json(msg="Error generating summary of origin access identities - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

    def summary_get_distribution_list(self, streaming=False):
        try:
            list_name = 'streaming_distributions' if streaming else 'distributions'
            key_list = ['Id', 'ARN', 'Status', 'LastModifiedTime', 'DomainName', 'Comment', 'PriceClass', 'Enabled' ]
            distribution_list = { list_name: [] }
            distributions = self.list_streaming_distributions(False) if streaming else self.list_distributions(False)
            for dist in distributions:
                temp_distribution = {}
                for key_name in key_list:
                    temp_distribution[key_name] = dist[key_name]
                temp_distribution['Aliases'] = [alias for alias in dist['Aliases'].get('Items', [])]
                temp_distribution['ETag'] = self.get_etag_from_distribution_id(dist['Id'], streaming)
                if not streaming:
                    temp_distribution['WebACLId'] = dist['WebACLId']
                    invalidation_ids = self.get_list_of_invalidation_ids_from_distribution_id(dist['Id'])
                    if invalidation_ids:
                        temp_distribution['Invalidations'] = invalidation_ids
                resource_tags = self.client.list_tags_for_resource(Resource=dist['ARN'])
                temp_distribution['Tags'] = boto3_tag_list_to_ansible_dict(resource_tags['Tags'].get('Items', []))
                distribution_list[list_name].append(temp_distribution)
            return distribution_list
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error generating summary of distributions - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))
        except Exception as e:
<<<<<<< HEAD
            self.module.fail_json(msg="Error generating summary of distributions - " + str(e),
                                  exception=traceback.format_exc())

    def get_etag_from_distribution_id(self, distribution_id, streaming):
        distribution = {}
        if not streaming:
            distribution = self.get_distribution(distribution_id)
        else:
            distribution = self.get_streaming_distribution(distribution_id)
        return distribution['ETag']

    def get_list_of_invalidation_ids_from_distribution_id(self, distribution_id):
        try:
            invalidation_ids = []
            invalidations = self.list_invalidations(distribution_id)
            for invalidation in invalidations:
                invalidation_ids.append(invalidation['Id'])
            return invalidation_ids
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error getting list of invalidation ids - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))
=======
            self.module.fail_json(msg="Error listing streaming distributions - " + str(e), exception=traceback.format_exc(e))
>>>>>>> f9db9c39bc... more cleaning, allowed streaming distributions to be found by domain name alias

    def summary(self):
        summary_dict = {}
        summary_dict.update(self.summary_get_distribution_list(False))
        summary_dict.update(self.summary_get_distribution_list(True))
        summary_dict.update(self.summary_get_origin_access_identity_list())
        return summary_dict

    def summary_get_origin_access_identity_list(self):
        try:
            origin_access_identity_list = { 'origin_access_identities': [] }
            origin_access_identities = self.list_origin_access_identities()
            for origin_access_identity in origin_access_identities:
                oai_id = origin_access_identity['Id']
                oai_full_response = self.get_origin_access_identity(oai_id)
                oai_summary = { 'Id': oai_id, 'ETag': oai_full_response['ETag'] }
                origin_access_identity_list['origin_access_identities'].append( oai_summary )
            return origin_access_identity_list
=======
            streaming_distribution_list = self.paginated_response(func, 'StreamingDistributionList')['Items']
=======
>>>>>>> a9d15200cb... checks for empty list returned from boto, standardised list naming
            if not keyed:
                return streaming_distribution_list
            return self.keyed_list_helper(streaming_distribution_list)
>>>>>>> 6b9bb00cfc... initial commit of cloudfront_facts summary
        except Exception as e:
            self.module.fail_json(msg="Error generating summary of origin access identities - " + str(e), exception=traceback.format_exc(e))

    def summary_get_distribution_list(self, streaming=False):
        try:
            list_name = 'streaming_distributions' if streaming else 'distributions'
            key_list = ['Id', 'ARN', 'Status', 'LastModifiedTime', 'DomainName', 'Comment', 'PriceClass', 'Enabled' ]
            distribution_list = { list_name: [] }
            distributions = self.list_streaming_distributions(False) if streaming else self.list_distributions(False)
            for dist in distributions:
                temp_distribution = {}
                for key_name in key_list:
                    temp_distribution.update( { key_name: dist[key_name] } )
                temp_distribution.update( { 'Aliases': [] } )
                temp_distribution.update( { 'ETag': self.get_etag_from_distribution_id(dist['Id'], streaming) } )
                if 'Items' in dist['Aliases']:
                    for alias in dist['Aliases']['Items']:
                        temp_distribution['Aliases'].append(alias)
                if not streaming:
                    temp_distribution.update( { 'WebACLId': dist['WebACLId'] } )
                    invalidation_ids = self.get_list_of_invalidation_ids_from_distribution_id(dist['Id'])
                    if invalidation_ids:
                        temp_distribution.update( { 'Invalidations': invalidation_ids } )
                distribution_list[list_name].append(temp_distribution)
            return distribution_list
=======
<<<<<<< 309a37de862dd73acdd0d85102299031ee40537d
            streaming_distributions = self.paginated_response(func, 'StreamingDistributionList')['Items']
            return self.keyed_list_helper(streaming_distributions)
=======
            return self.paginated_response(func, 'StreamingDistributionList')
>>>>>>> initial commit of cloudfront_facts.py
>>>>>>> 8b17f86304... initial commit of cloudfront_facts.py
        except Exception as e:
<<<<<<< HEAD
            self.module.fail_json(msg="Error generating summary of distributions - " + str(e), exception=traceback.format_exc(e))

    def get_etag_from_distribution_id(self, distribution_id, streaming):
        distribution = {}
        if not streaming:
            distribution = self.get_distribution(distribution_id)
        else:
            distribution = self.get_streaming_distribution(distribution_id)
        return distribution['ETag']

    def get_list_of_invalidation_ids_from_distribution_id(self, distribution_id):
        try:
            invalidation_ids = []
            invalidations = self.list_invalidations(distribution_id)
            for invalidation in invalidations:
                invalidation_ids.append(invalidation['Id'])
            return invalidation_ids
=======
            streaming_distributions = self.paginated_response(func, 'StreamingDistributionList')['Items']
            return self.keyed_list_helper(streaming_distributions)
>>>>>>> c495682bac... fixed shippable build error
        except Exception as e:
<<<<<<< HEAD
            self.module.fail_json(msg="Error getting list of invalidation ids - " + str(e), exception=traceback.format_exc(e))
=======
            self.module.fail_json(msg="Error listing streaming distributions - " + str(e), exception=traceback.format_exc(e))
>>>>>>> f0c712d884... more cleaning, allowed streaming distributions to be found by domain name alias
=======
            self.module.fail_json(msg="Error listing streaming distributions - " + str(e),
                                  exception=traceback.format_exc(e))
>>>>>>> 6f7c9ebd1e... modified exceptions to multi line as advised by @willthames

    def summary(self):
        summary_dict = {}
        summary_dict.update(self.summary_get_distribution_list(False))
        summary_dict.update(self.summary_get_distribution_list(True))
        summary_dict.update(self.summary_get_origin_access_identity_list())
        return summary_dict

    def summary_get_origin_access_identity_list(self):
        try:
            origin_access_identity_list = { 'origin_access_identities': [] }
            origin_access_identities = self.list_origin_access_identities()
            for origin_access_identity in origin_access_identities:
                oai_id = origin_access_identity['Id']
                oai_full_response = self.get_origin_access_identity(oai_id)
                oai_summary = { 'Id': oai_id, 'ETag': oai_full_response['ETag'] }
                origin_access_identity_list['origin_access_identities'].append( oai_summary )
            return origin_access_identity_list
        except Exception as e:
            self.module.fail_json(msg="Error generating summary of origin access identities - " + str(e),
                                  exception=traceback.format_exc(e))

    def summary_get_distribution_list(self, streaming=False):
        try:
            list_name = 'streaming_distributions' if streaming else 'distributions'
            key_list = ['Id', 'ARN', 'Status', 'LastModifiedTime', 'DomainName', 'Comment', 'PriceClass', 'Enabled' ]
            distribution_list = { list_name: [] }
            distributions = self.list_streaming_distributions(False) if streaming else self.list_distributions(False)
            for dist in distributions:
                temp_distribution = {}
                for key_name in key_list:
                    temp_distribution.update( { key_name: dist[key_name] } )
                temp_distribution.update( { 'Aliases': [] } )
                temp_distribution.update( { 'ETag': self.get_etag_from_distribution_id(dist['Id'], streaming) } )
                if 'Items' in dist['Aliases']:
                    for alias in dist['Aliases']['Items']:
                        temp_distribution['Aliases'].append(alias)
                if not streaming:
                    temp_distribution.update( { 'WebACLId': dist['WebACLId'] } )
                    invalidation_ids = self.get_list_of_invalidation_ids_from_distribution_id(dist['Id'])
                    if invalidation_ids:
                        temp_distribution.update( { 'Invalidations': invalidation_ids } )
                distribution_list[list_name].append(temp_distribution)
            return distribution_list
        except Exception as e:
            self.module.fail_json(msg="Error generating summary of distributions - " + str(e),
                                  exception=traceback.format_exc(e))

    def get_etag_from_distribution_id(self, distribution_id, streaming):
        distribution = {}
        if not streaming:
            distribution = self.get_distribution(distribution_id)
        else:
            distribution = self.get_streaming_distribution(distribution_id)
        return distribution['ETag']

    def get_list_of_invalidation_ids_from_distribution_id(self, distribution_id):
        try:
            invalidation_ids = []
            invalidations = self.list_invalidations(distribution_id)
            for invalidation in invalidations:
                invalidation_ids.append(invalidation['Id'])
            return invalidation_ids
        except Exception as e:
            self.module.fail_json(msg="Error getting list of invalidation ids - " + str(e),
                                  exception=traceback.format_exc(e))

    def get_distribution_id_from_domain_name(self, domain_name):
        try:
            distribution_id = ""
            distributions = self.list_distributions(False)
            distributions += self.list_streaming_distributions(False)
            for dist in distributions:
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> 8b17f86304... initial commit of cloudfront_facts.py
=======
            distributions = self.list_distributions()
            for dist in distributions['Items']:
>>>>>>> initial commit of cloudfront_facts.py
<<<<<<< HEAD
=======
>>>>>>> a1c87a1c06... fixed shippable build error
=======
>>>>>>> 8b17f86304... initial commit of cloudfront_facts.py
=======
>>>>>>> c495682bac... fixed shippable build error
                for alias in dist['Aliases']['Items']:
                    if str(alias).lower() == domain_name.lower():
                        distribution_id = str(dist['Id'])
                        break
=======
                if 'Items' in dist['Aliases']:
=======
		if 'Items' in dist['Aliases']:
>>>>>>> 4014b7b168... refactoring, neatening code, fix for if cname not present, added try-catch blocks
=======
                if 'Items' in dist['Aliases']:
>>>>>>> 8bab5e0f71... fixed tabs
=======
		if 'Items' in dist['Aliases']:
>>>>>>> 640e8b9baf... refactoring, neatening code, fix for if cname not present, added try-catch blocks
=======
                if 'Items' in dist['Aliases']:
>>>>>>> 4c2125ee0e... fixed tabs
                    for alias in dist['Aliases']['Items']:
                        if str(alias).lower() == domain_name.lower():
                            distribution_id = dist['Id']
                            break
<<<<<<< HEAD
<<<<<<< HEAD
>>>>>>> 93a689958e... [cloud] add summary feature and refactor AWS cloudfront_facts module (#20791)
=======
>>>>>>> 4014b7b168... refactoring, neatening code, fix for if cname not present, added try-catch blocks
=======
>>>>>>> 640e8b9baf... refactoring, neatening code, fix for if cname not present, added try-catch blocks
            return distribution_id
<<<<<<< HEAD
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error getting distribution id from domain name - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))
=======
        except Exception as e:
<<<<<<< HEAD
            self.module.fail_json(msg="Error getting distribution id from domain name - " + str(e), exception=traceback.format_exc(e))
<<<<<<< HEAD
>>>>>>> f9db9c39bc... more cleaning, allowed streaming distributions to be found by domain name alias
=======
>>>>>>> f0c712d884... more cleaning, allowed streaming distributions to be found by domain name alias
=======
            self.module.fail_json(msg="Error getting distribution id from domain name - " + str(e),
                                  exception=traceback.format_exc(e))
>>>>>>> 6f7c9ebd1e... modified exceptions to multi line as advised by @willthames

    def get_aliases_from_distribution_id(self, distribution_id):
        aliases = []
        try:
            distributions = self.list_distributions(False)
            for dist in distributions:
                if dist['Id'] == distribution_id and 'Items' in dist['Aliases']:
                    for alias in dist['Aliases']['Items']:
                        aliases.append(alias)
                    break
            return aliases
<<<<<<< HEAD
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error getting list of aliases from distribution_id - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))
=======
        except Exception as e:
<<<<<<< HEAD
            self.module.fail_json(msg="Error getting list of aliases from distribution_id - " + str(e), exception=traceback.format_exc(e))
<<<<<<< HEAD
>>>>>>> f9db9c39bc... more cleaning, allowed streaming distributions to be found by domain name alias
=======
>>>>>>> f0c712d884... more cleaning, allowed streaming distributions to be found by domain name alias
=======
            self.module.fail_json(msg="Error getting list of aliases from distribution_id - " + str(e),
                                  exception=traceback.format_exc(e))
>>>>>>> 6f7c9ebd1e... modified exceptions to multi line as advised by @willthames

    def paginated_response(self, func, result_key=""):
        '''
        Returns expanded response for paginated operations.
        The 'result_key' is used to define the concatenated results that are combined from each paginated response.
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

    def keyed_list_helper(self, list_to_key):
        keyed_list = dict()
        for item in list_to_key:
            distribution_id = item['Id']
            if 'Items' in item['Aliases']:
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
                aliases = item['Aliases']['Items']
                for alias in aliases:
                    keyed_list.update( { alias: item } )
            keyed_list.update( { distribution_id: item } )
=======
	        aliases = item['Aliases']['Items']
=======
            aliases = item['Aliases']['Items']
>>>>>>> 8bab5e0f71... fixed tabs
=======
                aliases = item['Aliases']['Items']
>>>>>>> 98e644b9cb... fixed indentation
                for alias in aliases:
<<<<<<< HEAD
                    keyed_list.update({alias: item})
            keyed_list.update({distribution_id: item})
>>>>>>> 4014b7b168... refactoring, neatening code, fix for if cname not present, added try-catch blocks
=======
                    keyed_list.update( { alias: item } )
            keyed_list.update( { distribution_id: item } )
>>>>>>> 7b965630c1... more refactoring, cleaning
=======
	        aliases = item['Aliases']['Items']
=======
            aliases = item['Aliases']['Items']
>>>>>>> 4c2125ee0e... fixed tabs
=======
                aliases = item['Aliases']['Items']
>>>>>>> 94f5b460af... fixed indentation
                for alias in aliases:
<<<<<<< HEAD
                    keyed_list.update({alias: item})
            keyed_list.update({distribution_id: item})
>>>>>>> 640e8b9baf... refactoring, neatening code, fix for if cname not present, added try-catch blocks
=======
                    keyed_list.update( { alias: item } )
            keyed_list.update( { distribution_id: item } )
>>>>>>> a3cc8146bf... more refactoring, cleaning
        return keyed_list

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> baa6e023db... refactoring of functions for modularity
=======
>>>>>>> 0701a78b23... refactoring of functions for modularity
def set_facts_for_distribution_id_and_alias(details, facts, distribution_id, aliases):
    facts[distribution_id].update(details)
    for alias in aliases:
        facts[alias].update(details)
    return facts

<<<<<<< HEAD
<<<<<<< HEAD
=======
=======
>>>>>>> modification as per review from @georgepsarakis
>>>>>>> 545a18c726... modification as per review from @georgepsarakis
=======
>>>>>>> a1c87a1c06... fixed shippable build error
=======
>>>>>>> baa6e023db... refactoring of functions for modularity
=======
=======
>>>>>>> modification as per review from @georgepsarakis
>>>>>>> 6b0189db44... modification as per review from @georgepsarakis
=======
>>>>>>> c495682bac... fixed shippable build error
=======
>>>>>>> 0701a78b23... refactoring of functions for modularity
def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> 0bbf1f681a... neatened up parameters
        distribution_id                   = dict(required=False, type='str'),
        invalidation_id                   = dict(required=False, type='str'),
        origin_access_identity_id         = dict(required=False, type='str'),
        domain_name_alias                 = dict(required=False, type='str'),
        all_lists                         = dict(required=False, default=False, type='bool'),
        distribution                      = dict(required=False, default=False, type='bool'),
        distribution_config               = dict(required=False, default=False, type='bool'),
        origin_access_identity            = dict(required=False, default=False, type='bool'),
        origin_access_identity_config     = dict(required=False, default=False, type='bool'),
        invalidation                      = dict(required=False, default=False, type='bool'),
        streaming_distribution            = dict(required=False, default=False, type='bool'),
        streaming_distribution_config     = dict(required=False, default=False, type='bool'),
        list_origin_access_identities     = dict(required=False, default=False, type='bool'),
        list_distributions                = dict(required=False, default=False, type='bool'),
        list_distributions_by_web_acl_id  = dict(required=False, default=False, type='bool'),
        list_invalidations                = dict(required=False, default=False, type='bool'),
        list_streaming_distributions      = dict(required=False, default=False, type='bool'),
        summary                           = dict(required=False, default=False, type='bool')
<<<<<<< HEAD
=======
=======
>>>>>>> e79da7dbe6... removed spaces between parameters as advised by @ryansb
        distribution_id=dict(required=False, type='str'),
        invalidation_id=dict(required=False, type='str'),
        origin_access_identity_id=dict(required=False, type='str'),
        domain_name_alias=dict(required=False, type='str'),
        all_lists=dict(required=False, default=False, type='bool'),
        distribution=dict(required=False, default=False, type='bool'),
        distribution_config=dict(required=False, default=False, type='bool'),
        origin_access_identity=dict(required=False, default=False, type='bool'),
        origin_access_identity_config=dict(required=False, default=False, type='bool'),
        invalidation=dict(required=False, default=False, type='bool'),
        streaming_distribution=dict(required=False, default=False, type='bool'),
        streaming_distribution_config=dict(required=False, default=False, type='bool'),
        list_origin_access_identities=dict(required=False, default=False, type='bool'),
        list_distributions=dict(required=False, default=False, type='bool'),
        list_distributions_by_web_acl_id=dict(required=False, default=False, type='bool'),
        list_invalidations=dict(required=False, default=False, type='bool'),
<<<<<<< HEAD
<<<<<<< HEAD
        list_streaming_distributions=dict(required=False, default=False, type='bool')
>>>>>>> 8b17f86304... initial commit of cloudfront_facts.py
=======
        list_streaming_distributions=dict(required=False, default=False, type='bool'),
        summary=dict(required=False, default=False, type='bool')
>>>>>>> 6b9bb00cfc... initial commit of cloudfront_facts summary
=======
>>>>>>> 0bbf1f681a... neatened up parameters
=======
        distribution_id = dict(required=False, type='str'),
        invalidation_id = dict(required=False, type='str'),
        origin_access_identity_id = dict(required=False, type='str'),
        domain_name_alias = dict(required=False, type='str'),
        all_lists = dict(required=False, default=False, type='bool'),
        distribution = dict(required=False, default=False, type='bool'),
        distribution_config = dict(required=False, default=False, type='bool'),
        origin_access_identity = dict(required=False, default=False, type='bool'),
        origin_access_identity_config = dict(required=False, default=False, type='bool'),
        invalidation = dict(required=False, default=False, type='bool'),
        streaming_distribution = dict(required=False, default=False, type='bool'),
        streaming_distribution_config = dict(required=False, default=False, type='bool'),
        list_origin_access_identities = dict(required=False, default=False, type='bool'),
        list_distributions = dict(required=False, default=False, type='bool'),
        list_distributions_by_web_acl_id = dict(required=False, default=False, type='bool'),
        list_invalidations = dict(required=False, default=False, type='bool'),
        list_streaming_distributions = dict(required=False, default=False, type='bool'),
        summary = dict(required=False, default=False, type='bool')
>>>>>>> 79d686df26... reverted variable spacing to be more pythonic'
=======
        list_streaming_distributions=dict(required=False, default=False, type='bool'),
        summary=dict(required=False, default=False, type='bool')
>>>>>>> e79da7dbe6... removed spaces between parameters as advised by @ryansb
    ))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required.')

    service_mgr = CloudFrontServiceManager(module)

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> 79d686df26... reverted variable spacing to be more pythonic'
    distribution_id = module.params.get('distribution_id')
    invalidation_id = module.params.get('invalidation_id')
    origin_access_identity_id = module.params.get('origin_access_identity_id')
    web_acl_id = module.params.get('web_acl_id')
    domain_name_alias = module.params.get('domain_name_alias')
    all_lists = module.params.get('all_lists')
    distribution = module.params.get('distribution')
    distribution_config = module.params.get('distribution_config')
    origin_access_identity = module.params.get('origin_access_identity')
    origin_access_identity_config = module.params.get('origin_access_identity_config')
    invalidation = module.params.get('invalidation')
    streaming_distribution = module.params.get('streaming_distribution')
    streaming_distribution_config = module.params.get('streaming_distribution_config')
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< 309a37de862dd73acdd0d85102299031ee40537d
=======
>>>>>>> 93a689958e... [cloud] add summary feature and refactor AWS cloudfront_facts module (#20791)
=======
>>>>>>> a1c87a1c06... fixed shippable build error
=======
<<<<<<< 309a37de862dd73acdd0d85102299031ee40537d
>>>>>>> 8b17f86304... initial commit of cloudfront_facts.py
=======
>>>>>>> c495682bac... fixed shippable build error
=======
>>>>>>> 79d686df26... reverted variable spacing to be more pythonic'
=======
    
>>>>>>> 6deb8e2f32... reverted line spacing for parameters for correct blame attribution as advised by @ryansb
=======
 
>>>>>>> aa4c5c6b6e... removed white space
=======

>>>>>>> d0d5b9ef58... more white space
=======
>>>>>>> ca5f335e4e... reverted line spacings for parameters as advised by @ryansb
=======
    
>>>>>>> 00b624a880... reverted line spacing for parameters for correct blame attribution as advised by @ryansb
=======
 
>>>>>>> 9cd825b760... removed white space
=======

>>>>>>> 6241f74202... more white space
=======
>>>>>>> 652b4d220a... reverted line spacings for parameters as advised by @ryansb
    list_origin_access_identities = module.params.get('list_origin_access_identities')
    list_distributions = module.params.get('list_distributions')
    list_distributions_by_web_acl_id = module.params.get('list_distributions_by_web_acl_id')
    list_invalidations = module.params.get('list_invalidations')
    list_streaming_distributions = module.params.get('list_streaming_distributions')
    summary = module.params.get('summary')
<<<<<<< HEAD

<<<<<<< HEAD
    summary = module.params.get('summary')
=======
=======
>>>>>>> 0bbf1f681a... neatened up parameters
    distribution_id                   = module.params.get('distribution_id')
    invalidation_id                   = module.params.get('invalidation_id')
    origin_access_identity_id         = module.params.get('origin_access_identity_id')
    web_acl_id                        = module.params.get('web_acl_id')
    domain_name_alias                 = module.params.get('domain_name_alias')
    all_lists                         = module.params.get('all_lists')
    distribution                      = module.params.get('distribution')
    distribution_config               = module.params.get('distribution_config')
    origin_access_identity            = module.params.get('origin_access_identity')
    origin_access_identity_config     = module.params.get('origin_access_identity_config')
    invalidation                      = module.params.get('invalidation')
    streaming_distribution            = module.params.get('streaming_distribution')
    streaming_distribution_config     = module.params.get('streaming_distribution_config')
    list_origin_access_identities     = module.params.get('list_origin_access_identities')
    list_distributions                = module.params.get('list_distributions')
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
    list_distributions_by_web_acl_id  = module.params.get('list_distributions_by_web_acl_id')
    list_invalidations                = module.params.get('list_invalidations')
    list_streaming_distributions      = module.params.get('list_streaming_distributions')
    summary                           = module.params.get('summary')
>>>>>>> a929e027ca... neatened up parameters

<<<<<<< HEAD
<<<<<<< HEAD
    result = { 'cloudfront': {} }
    facts = {}
=======
    summary = module.params.get('summary')
=======
=======

>>>>>>> f0c712d884... more cleaning, allowed streaming distributions to be found by domain name alias
=======
>>>>>>> c5444d90e9... removed unnecessary line
    list_distributions_by_web_acl_id  = module.params.get('list_distributions_by_web_acl_id');
=======
    list_distributions_by_web_acl_id  = module.params.get('list_distributions_by_web_acl_id')
>>>>>>> d1e595e84e... removed trailing whitespace
    list_invalidations                = module.params.get('list_invalidations')
    list_streaming_distributions      = module.params.get('list_streaming_distributions')
    summary                           = module.params.get('summary')
>>>>>>> 0bbf1f681a... neatened up parameters
=======
>>>>>>> 79d686df26... reverted variable spacing to be more pythonic'

<<<<<<< HEAD
>>>>>>> 6b9bb00cfc... initial commit of cloudfront_facts summary
    aliases = []
<<<<<<< HEAD
<<<<<<< HEAD
    result = { 'cloudfront': {} }
    facts = {}

    require_distribution_id = (distribution or distribution_config or invalidation or streaming_distribution or
        streaming_distribution_config or list_invalidations)
=======
    
<<<<<<< HEAD
=======
    result = { 'cloudfront': {} } 
=======
=======
    aliases = []
>>>>>>> 6deb8e2f32... reverted line spacing for parameters for correct blame attribution as advised by @ryansb
    result = { 'cloudfront': {} }
>>>>>>> a9fe9f4fdf... removed more whitespace
    facts = {}
<<<<<<< HEAD
    aliases = []
<<<<<<< HEAD
    
<<<<<<< HEAD
>>>>>>> 640e8b9baf... refactoring, neatening code, fix for if cname not present, added try-catch blocks
    require_distribution_id = (distribution or distribution_config or invalidation or
            streaming_distribution or streaming_distribution_config or list_invalidations)
>>>>>>> 4014b7b168... refactoring, neatening code, fix for if cname not present, added try-catch blocks

    # set default to summary if no option specified
<<<<<<< HEAD
<<<<<<< HEAD
    summary = summary or not (distribution or distribution_config or origin_access_identity or
        origin_access_identity_config or invalidation or streaming_distribution or streaming_distribution_config or
        list_origin_access_identities or list_distributions_by_web_acl_id or list_invalidations or
        list_streaming_distributions or list_distributions)
=======
=======
>>>>>>> 6b9bb00cfc... initial commit of cloudfront_facts summary
    summary = summary or not (distribution or distribution_config or
            origin_access_identity or origin_access_identity_config or invalidation or
            streaming_distribution or streaming_distribution_config or list_origin_access_identities or
            list_distributions_by_web_acl_id or list_invalidations or list_streaming_distributions or
            list_distributions)
<<<<<<< HEAD
>>>>>>> d9c3f95f48... initial commit of cloudfront_facts summary
=======
    require_distribution_id = (distribution or distribution_config or invalidation or streaming_distribution or 
=======
=======
>>>>>>> 6deb8e2f32... reverted line spacing for parameters for correct blame attribution as advised by @ryansb

    require_distribution_id = (distribution or distribution_config or invalidation or streaming_distribution or
>>>>>>> ff340bb756... removed trailing whitespace
        streaming_distribution_config or list_invalidations)

    # set default to summary if no option specified
    summary = summary or not (distribution or distribution_config or origin_access_identity or
        origin_access_identity_config or invalidation or streaming_distribution or streaming_distribution_config or
        list_origin_access_identities or list_distributions_by_web_acl_id or list_invalidations or
        list_streaming_distributions or list_distributions)
>>>>>>> 7b965630c1... more refactoring, cleaning
=======
>>>>>>> 6b9bb00cfc... initial commit of cloudfront_facts summary
=======
    require_distribution_id = (distribution or distribution_config or invalidation or streaming_distribution or 
=======

    require_distribution_id = (distribution or distribution_config or invalidation or streaming_distribution or
>>>>>>> d1e595e84e... removed trailing whitespace
        streaming_distribution_config or list_invalidations)

    # set default to summary if no option specified
    summary = summary or not (distribution or distribution_config or origin_access_identity or
        origin_access_identity_config or invalidation or streaming_distribution or streaming_distribution_config or
        list_origin_access_identities or list_distributions_by_web_acl_id or list_invalidations or
        list_streaming_distributions or list_distributions)
>>>>>>> a3cc8146bf... more refactoring, cleaning

    # validations
    if require_distribution_id and distribution_id is None and domain_name_alias is None:
        module.fail_json(msg='Error distribution_id or domain_name_alias have not been specified.')
    if (invalidation and invalidation_id is None):
        module.fail_json(msg='Error invalidation_id has not been specified.')
    if (origin_access_identity or origin_access_identity_config) and origin_access_identity_id is None:
        module.fail_json(msg='Error origin_access_identity_id has not been specified.')
    if list_distributions_by_web_acl_id and web_acl_id is None:
        module.fail_json(msg='Error web_acl_id has not been specified.')

    # get distribution id from domain name alias
    if require_distribution_id and distribution_id is None:
        distribution_id = service_mgr.get_distribution_id_from_domain_name(domain_name_alias)
        if not distribution_id:
            module.fail_json(msg='Error unable to source a distribution id from domain_name_alias')

    # set appropriate cloudfront id
    if distribution_id and not list_invalidations:
        facts = { distribution_id: {} }
        aliases = service_mgr.get_aliases_from_distribution_id(distribution_id)
        for alias in aliases:
            facts.update( { alias: {} } )
        if invalidation_id:
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
            facts.update( { invalidation_id: {} } )
    elif distribution_id and list_invalidations:
        facts = { distribution_id: {} }
=======
            result['cloudfront'].update( { invalidation_id: {} } )
        facts = result['cloudfront']
    elif distribution_id and list_invalidations:
        result = { 'cloudfront': { 'invalidations': {} } }
        facts = result['cloudfront']['invalidations']
>>>>>>> d9c3f95f48... initial commit of cloudfront_facts summary
        aliases = service_mgr.get_aliases_from_distribution_id(distribution_id)
        for alias in aliases:
<<<<<<< HEAD
            facts.update( { alias: {} } )
=======
            result['cloudfront']['invalidations'].update( { alias: {} } )
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
        facts = result['cloudfront']
>>>>>>> f0a5ddec55... show facts based on alias and distribution id for easy referencing as advised by @ryansb. have done for both distribution and distribution_config
=======
>>>>>>> c02981a697... removed unnecessary boto fields. made list_distributions and list_streaming_distributions dictionaries with id/alias as key. fixed list_invalidations.
=======
            facts.update( { invalidation_id: {} } )
    elif distribution_id and list_invalidations:
        facts = { distribution_id: {} }
        aliases = service_mgr.get_aliases_from_distribution_id(distribution_id)
        for alias in aliases:
<<<<<<< HEAD
            facts['invalidations'].update( { alias: {} } )
>>>>>>> 4014b7b168... refactoring, neatening code, fix for if cname not present, added try-catch blocks
=======
            facts.update( { alias: {} } )
>>>>>>> 170e495a4c... more refactoring, modified where invalidations dict is set
=======
        facts = result['cloudfront']
>>>>>>> c58f154126... show facts based on alias and distribution id for easy referencing as advised by @ryansb. have done for both distribution and distribution_config
=======
>>>>>>> 77fa4ffe0a... removed unnecessary boto fields. made list_distributions and list_streaming_distributions dictionaries with id/alias as key. fixed list_invalidations.
=======
            facts.update( { invalidation_id: {} } )
    elif distribution_id and list_invalidations:
        facts = { distribution_id: {} }
        aliases = service_mgr.get_aliases_from_distribution_id(distribution_id)
        for alias in aliases:
<<<<<<< HEAD
            facts['invalidations'].update( { alias: {} } )
>>>>>>> 640e8b9baf... refactoring, neatening code, fix for if cname not present, added try-catch blocks
=======
            facts.update( { alias: {} } )
>>>>>>> 308a539ca3... more refactoring, modified where invalidations dict is set
    elif origin_access_identity_id:
        facts = { origin_access_identity_id: {} }
    elif web_acl_id:
        facts = { web_acl_id: {} }
<<<<<<< HEAD
<<<<<<< HEAD
=======

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
>>>>>>> 4014b7b168... refactoring, neatening code, fix for if cname not present, added try-catch blocks
=======

>>>>>>> 640e8b9baf... refactoring, neatening code, fix for if cname not present, added try-catch blocks

<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> 7b965630c1... more refactoring, cleaning
# get details based on options
=======
    # get details based on options
>>>>>>> f9db9c39bc... more cleaning, allowed streaming distributions to be found by domain name alias
=======
=======
>>>>>>> a3cc8146bf... more refactoring, cleaning
# get details based on options
>>>>>>> 0701a78b23... refactoring of functions for modularity
=======
    # get details based on options
>>>>>>> f0c712d884... more cleaning, allowed streaming distributions to be found by domain name alias
    if distribution:
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
        facts_to_set = service_mgr.get_distribution(distribution_id)
    if distribution_config:
        facts_to_set = service_mgr.get_distribution_config(distribution_id)
=======
        distribution_details = service_mgr.get_distribution(distribution_id)
        facts = set_facts_for_distribution_id_and_alias(distribution_details, facts, distribution_id, aliases)
    if distribution_config:
        distribution_config_details = service_mgr.get_distribution_config(distribution_id)
        facts = set_facts_for_distribution_id_and_alias(distribution_config_details, facts, distribution_id, aliases)
<<<<<<< HEAD
>>>>>>> baa6e023db... refactoring of functions for modularity
=======
        facts_to_set = service_mgr.get_distribution(distribution_id)
    if distribution_config:
        facts_to_set = service_mgr.get_distribution_config(distribution_id)
>>>>>>> 170e495a4c... more refactoring, modified where invalidations dict is set
=======
>>>>>>> 0701a78b23... refactoring of functions for modularity
=======
        facts_to_set = service_mgr.get_distribution(distribution_id)
    if distribution_config:
        facts_to_set = service_mgr.get_distribution_config(distribution_id)
>>>>>>> 308a539ca3... more refactoring, modified where invalidations dict is set
    if origin_access_identity:
        facts[origin_access_identity_id].update(service_mgr.get_origin_access_identity(origin_access_identity_id))
    if origin_access_identity_config:
        facts[origin_access_identity_id].update(service_mgr.get_origin_access_identity_config(origin_access_identity_id))
    if invalidation:
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
        facts_to_set = service_mgr.get_invalidation(distribution_id, invalidation_id)
        facts[invalidation_id].update(facts_to_set)
    if streaming_distribution:
        facts_to_set = service_mgr.get_streaming_distribution(distribution_id)
    if streaming_distribution_config:
        facts_to_set = service_mgr.get_streaming_distribution_config(distribution_id)
=======
        invalidation = service_mgr.get_invalidation(distribution_id, invalidation_id)
        facts[invalidation_id].update(invalidation)
        facts = set_facts_for_distribution_id_and_alias(invalidation, facts, distribution_id, aliases)
<<<<<<< HEAD
=======
        facts_to_set = service_mgr.get_invalidation(distribution_id, invalidation_id)
        facts[invalidation_id].update(facts_to_set)
>>>>>>> 170e495a4c... more refactoring, modified where invalidations dict is set
    if streaming_distribution:
        facts_to_set = service_mgr.get_streaming_distribution(distribution_id)
=======
    if streaming_distribution:
        streaming_distribution_details = service_mgr.get_streaming_distribution(distribution_id)
        facts = set_facts_for_distribution_id_and_alias(streaming_distribution_details, facts, distribution_id, aliases)
>>>>>>> 0701a78b23... refactoring of functions for modularity
    if streaming_distribution_config:
<<<<<<< HEAD
        streaming_distribution_config_details = service_mgr.get_streaming_distribution_config(distribution_id)
        facts = set_facts_for_distribution_id_and_alias(streaming_distribution_config_details, facts, distribution_id, aliases)
<<<<<<< HEAD
>>>>>>> baa6e023db... refactoring of functions for modularity
=======
>>>>>>> 0701a78b23... refactoring of functions for modularity
    if list_invalidations:
<<<<<<< HEAD
        facts_to_set = {'invalidations': service_mgr.list_invalidations(distribution_id) }
    if 'facts_to_set' in vars():
        facts = set_facts_for_distribution_id_and_alias(facts_to_set, facts, distribution_id, aliases)
=======
        invalidations = service_mgr.list_invalidations(distribution_id)
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
        facts.update({distribution_id:invalidations})
        for alias in aliases:
            facts.update({alias: invalidations})
>>>>>>> d9c3f95f48... initial commit of cloudfront_facts summary

=======
        facts = set_facts_for_distribution_id_and_alias(invalidations, facts, distribution_id, aliases)
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
>>>>>>> baa6e023db... refactoring of functions for modularity
=======
    
>>>>>>> f9db9c39bc... more cleaning, allowed streaming distributions to be found by domain name alias
=======
 
>>>>>>> ff340bb756... removed trailing whitespace
=======
=======
        facts_to_set = service_mgr.get_streaming_distribution_config(distribution_id)
    if list_invalidations:
        facts_to_set = {'invalidations': service_mgr.list_invalidations(distribution_id) }
    if 'facts_to_set' in vars():
        facts = set_facts_for_distribution_id_and_alias(facts_to_set, facts, distribution_id, aliases)
>>>>>>> 170e495a4c... more refactoring, modified where invalidations dict is set
=======
        facts.update({distribution_id:invalidations})
        for alias in aliases:
            facts.update({alias: invalidations})
>>>>>>> 6b9bb00cfc... initial commit of cloudfront_facts summary

>>>>>>> 9bbe1a9cfb... removed more whitespace
=======
        facts = set_facts_for_distribution_id_and_alias(invalidations, facts, distribution_id, aliases)
>>>>>>> 0701a78b23... refactoring of functions for modularity
=======
    
>>>>>>> f0c712d884... more cleaning, allowed streaming distributions to be found by domain name alias
=======
 
>>>>>>> d1e595e84e... removed trailing whitespace
=======
=======
        facts_to_set = service_mgr.get_invalidation(distribution_id, invalidation_id)
        facts[invalidation_id].update(facts_to_set)
    if streaming_distribution:
        facts_to_set = service_mgr.get_streaming_distribution(distribution_id)
    if streaming_distribution_config:
        facts_to_set = service_mgr.get_streaming_distribution_config(distribution_id)
    if list_invalidations:
        facts_to_set = {'invalidations': service_mgr.list_invalidations(distribution_id) }
    if 'facts_to_set' in vars():
        facts = set_facts_for_distribution_id_and_alias(facts_to_set, facts, distribution_id, aliases)
>>>>>>> 308a539ca3... more refactoring, modified where invalidations dict is set

>>>>>>> a9fe9f4fdf... removed more whitespace
    # get list based on options
    if all_lists or list_origin_access_identities:
        facts['origin_access_identities'] = service_mgr.list_origin_access_identities()
    if all_lists or list_distributions:
        facts['distributions'] = service_mgr.list_distributions()
    if all_lists or list_streaming_distributions:
        facts['streaming_distributions'] = service_mgr.list_streaming_distributions()
    if list_distributions_by_web_acl_id:
        facts['distributions_by_web_acl_id'] = service_mgr.list_distributions_by_web_acl_id(web_acl_id)
    if list_invalidations:
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
        facts['invalidations'] = service_mgr.list_invalidations(distribution_id)

    # default summary option
    if summary:
        facts['summary'] = service_mgr.summary()
=======
        facts['list_invalidations'] = service_mgr.list_invalidations(distribution_id)
>>>>>>> fc6b1d64c4... fixed incorrect logic for default list_distributions, fixed list_distributions_by_web_acl - wasn't passing web_acl_id, fixed list_invalidations keyword args missing DistributionId
=======
        facts['invalidations'] = service_mgr.list_invalidations(distribution_id)
>>>>>>> 72920b1476... removed list_ prefix from list keys

    # default summary option
    if summary:
        facts['summary'] = service_mgr.summary()
=======
        facts['list_invalidations'] = service_mgr.list_invalidations(distribution_id)
>>>>>>> 1437a2eac9... fixed incorrect logic for default list_distributions, fixed list_distributions_by_web_acl - wasn't passing web_acl_id, fixed list_invalidations keyword args missing DistributionId
=======
        facts['invalidations'] = service_mgr.list_invalidations(distribution_id)
>>>>>>> 9b00e0a9af... removed list_ prefix from list keys

    # default summary option
    if summary:
        facts['summary'] = service_mgr.summary()

    result['changed'] = False
    result['cloudfront'].update(facts)
    module.exit_json(msg="Retrieved cloudfront facts.", ansible_facts=result)

if __name__ == '__main__':
    main()
