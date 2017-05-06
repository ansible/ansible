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
module: cloudfront
short_description: create, update, delete, duplicate and validate AWS CloudFront distributions
description:
    - Allows for easy creation, updating, deletion, duplication and validation
      of CloudFront distributions.
requirements:
  - boto3 >= 1.0.0
  - python >= 2.6
version_added: "2.3"
author: Willem van Ketwich (@wilvk)
options:
  distribution_id:
    description:
      - The id of the cloudfront distribution.
        Used with
          I(create_distribution),
          I(update_distribution),
          I(delete_distribution),
          I(duplicate_distribution),
          I(create_invalidation),
          I(generate_presigned_url_from_pem_private_key).
        This parameter can be exchanged with I(alias) and in conjunction with e_tag.
    required: false
  streaming_distribution_id:
    description:
      - The id of the CloudFront streaming distribution.
        Used with
          I(create_streaming_distribution),
          I(update_streaming_distribution),
          I(delete_streaming_distribution),
          I(duplicate_streaming_distribution).
        This parameter can be exchanged with I(alias) and in conjunction with e_tag.
    required: false
  origin_access_identity_id:
    description:
      - The id of the Origin Access Identity.
        Used with
          I(create_origin_access_identity),
          I(update_origin_access_identity),
          I(delete_origin_access_identity).
    required: false
  e_tag:
    description:
      - A unique identifier of a modified or newly created distribution.
        Used in conjunction with I(distribution_id) or I(streaming_distribution_id).
        Is determined automatically if not specified.
    required: false
  create_origin_access_identity:
    description:
      - If C(yes), creates an origin access identity.
    default: 'no'
    choices: ['yes', 'no']
    required: false
  update_origin_access_identity:
    description:
      - If C(yes), updates an origin access identity.
    default: 'no'
    choices: ['yes', 'no']
    required: false
  delete_origin_access_identity:
    description:
      - If C(yes), delete an origin access identity.
    default: 'no'
    choices: ['yes', 'no']
    required: false
  create_distribution:
    description:
      - If C(yes), creates a distribution.
        As a minimum, either I(default_origin_domain_name) or at least one origin
        in I(origins) must be specified.
    default: 'no'
    choices: ['yes', 'no']
    required: false
  create_invalidation:
    description:
      - If C(yes), creates one or more invalidations.
    default: 'no'
    choices: ['yes', 'no']
    required: false
  update_distribution:
    description:
      - If C(yes), updates a distribution.
        This can be used with just an C(alias) to specify the distribution and
        either C(config) or one of it's attributes.
    default: 'no'
    choices: ['yes', 'no']
    required: false
  delete_distribution:
    description:
      - If C(yes), deletes a distribution.
    default: 'no'
    choices: ['yes', 'no']
    required: false
  duplicate_distribution:
    description:
      - If C(yes), duplicates a distribution.
        This can be used with just an C(alias) to specify the
        distribution and either C(config) or one of it's attributes.
    default: 'no'
    choices: ['yes', 'no']
    required: false
  validate_distribution:
    description:
      - If C(yes), validates a distribution.
    default: 'no'
    choices: ['yes', 'no']
    required: false
  create_streaming_distribution:
    description:
      - If C(yes), creates a streaming distribution.
    default: 'no'
    choices: ['yes', 'no']
    required: false
  update_streaming_distribution:
    description:
      - If C(yes), updates a streaming distribution. This can be used
        with just an C(alias) to specify the distribution and either
        C(config) or one of it's attributes.
    default: 'no'
    choices: ['yes', 'no']
    required: false
  delete_streaming_distribution:
    description:
      - If C(yes), deletes a streaming distribution.
    default: 'no'
    choices: ['yes', 'no']
    required: false
  duplicate_streaming_distribution:
    description:
      - If C(yes), duplicates a streaming distribution. This can be used with
        just an C(alias) to specify the distribution and either C(config) or
        one of it's attributes.
    default: 'no'
    choices: ['yes', 'no']
    required: false
  validate_streaming_distribution:
    description:
      - If C(yes), validates a streaming distribution.
    default: 'no'
    choices: ['yes', 'no']
    required: false
  generate_presigned_url_from_pem_private_key:
    description:
      - If C(yes), generates a presigned url for a distribution from a private
        .pem key.
    default: 'no'
    choices: ['yes', 'no']
    required: false
  caller_reference:
    description:
      - A unique identifier for creating and duplicating cloudfront distributions.
    required: false
  invalidation_batch:
    description:
      - An array of path strings to be invalidated.
    required: false
  presigned_url_pem_private_key_path:
    description:
      - The path on the host to the pem private key.
        This key is used to sign the url.
    required: false
  presigned_url_pem_private_key_password:
    description:
      - The password for the pem private key if a password exists.
    required: false
  presigned_url_pem_url:
    description:
      - The cloudfront url to sign with the pem private key.
    required: false
  presigned_url_pem_expire_date:
    description:
      - The expiry date of the presigned url. Date format is I(YYYY-MM-DD)
    required: false
  config:
    description:
      - This is the main variable used for creating and updating distributions
        and streaming distributions. When used, it will be a complex data type as
        a dictionary that represents the config of the distribution.
        When used for creating a distribution, it must contain at least one
        origin in I(origins) or the variable default_domain_name_origin should be
        used instead. Components of C(config) can be specified entirely in
        C(config) or as separate elements outside of the config.
        This parameter applies to both distributions and streaming distributions.
        Elements of a distribution are
          caller_reference
          aliases
          default_root_object
          origins
          default_cache_behavior
          cache_behaviors
          custom_error_responses
          comment
          logging
          price_class
          enabled
          viewer_certificate
          restrictions
          web_acl_id
          http_version
          is_ipv6_enabled
        Elements of a streaming distribution are
          caller_reference
          s3_origin
          aliases
          comment
          logging
          trusted_signers
        Most of these elements have sub-elements that can be seen in their entirety
        in the boto3 documentation at
          U(http://boto3.readthedocs.io/en/latest/reference/services/cloudfront.html#CloudFront.Client.create_distribution)
        and
          U(http://boto3.readthedocs.io/en/latest/reference/services/cloudfront.html#CloudFront.Client.create_streaming_distribution).
        When element variables are specified as well as the config variable, the
        elements specified will have precendence and overwrite any relevant data
        for that element in the config variable.
    config_required: false
  tags:
    description:
      - Used for distributions and streaming distributions in conjunction with
        C(config). Should be input as a list of I(Key) I(Value) pairs.
    required: false
  alias:
    description:
      - The name of an alias that is used in a distribution. This is used to
        effectively reference a distribution by it's alias as an alias can only
        be used by one distribution. This variable avoids haing to provide the
        distribution_id or streaming_distribution_id as well as the e_tag to
        reference a distribution. This variable is used for the actions
          C(update_distribution=yes),
          C(update_streaming_distribution=yes),
          C(duplicate_distribution=yes),
          C(duplicate_streaming_distribution=yes)
    required: no
  aliases:
    description:
    - A list of domain name aliases as strings to be used for the distribution.
      Each alias must be unique across all distributions.
      Applies to both distributions and streaming distributions.
    required: no
  default_root_object:
    description:
      - Specifies the path to request when the user requests the origin.
        eg. if specified as 'index.html', this maps to www.example.com/index.html
        when www.example.com is called by the user. This prevents the entire
        distribution origin from being exposed at the root.
  origins:
    description:
      - A list of complex origin objects to be specified for the distribution.
        Used for C(create_distribution), C(update_distribution) and
        C(duplicate_distribution). Only valid for distributions. Each origin
        attribute comprises the attributes
          id
          default_origin_domain_name
          origin_path custom_headers[]
          s3_origin_config origin_access_identity
          custom_origin_config
  default_cache_behavior:
    description:
      - A complex object specifying the default cache behavior of the
        distribution. If not specified, the target_origin_id is defined as the
        target_origin_id of the first valid cache_behavior in cache_behaviors[]
        with defaults. Only valid for distributions.
    required: false
  cache_behaviors:
    description:
      - A list of complex cache behavior objects to be specified for the
        distribution. Only valid for distributions.
        Each cache behavior comprises the attributes of
          path_pattern target_origin_id
          forwarded_values trusted_signers
          viewer_protocol_policy
          min_ttl
          allowed_methods
          smooth_streaming
          default_ttl
          max_ttl
          compress
          lambda_function_associations[]
    required: false
  custom_error_responses:
    description:
      - A list of complex custom error responses to be specified for the
        distribution. This attribute configures custom http error messages
        returned to the user. Only valid for distributions.
        Each custom error response comprises the attributes
          error_code
          reponse_page_path
          response_code error_caching_min_ttl
    required: false
  comment:
    description:
      - A unique comment to describe the cloudfront distribution. Applies to both
        distributions and streaming distributions. If not specified, it defaults
        to a generic message that it has been created with Ansible, and a
        datetime stamp.
    required: false
  logging:
    description:
      - A complex object that defines logging for the distribution. Applies to
        both distributions and streaming distributions. The logging object
        comprises the attributes
          enabled
          include_cookies
          bucket
          prefix
    required: false
  price_class:
    description:
      - A string that specifies the pricing class of the distribution. Applies to
        both distributions and streaming distributions.
    choices: ['PriceClass_100', 'PriceClass_200', 'PriceClass_All']
    required: false
  enabled:
    description:
      - A boolean value that specifies whether the distribution is enabled or
        disabled. Applies to both distributions and streaming distributions.
    default: false
    required: false
  viewer_certificate:
    description:
      - A complex object that specifies the encryption details of the
        distribution. Only valid for distributions. Comprises of the following
        attributes
          cloudfront_default_certificate
          iam_certificate_id
          acm_certificate_arn
          ssl_support_method
          minimum_protocol_version
          certificate certificate_source
    required: false
  restrictions:
    description:
      - A complex object that describes how a distribution should restrict it's
        content. Only valid for distributions. The restriction object comprises the
        following attributes
          geo_restriction
  web_acl_id:
    description:
      - The id of a waf web_acl. Only valid for distributions.
    required: false
  http_version:
    description:
      - The version of http to use for the distribution.
        Only valid for distributions.
    choices: [ 'http1.1', 'http2' ]
    required: false


'''

EXAMPLES = '''
# create a basic distribution with defaults and tags
- cloudfront:
    create_distribution: yes
    default_origin_domain_name: www.my-cloudfront-origin.com
    tags:
      - Name: example distribution
      - Project: example project
      - Priority: 1

# update a distribution comment by distribution_id
- cloudfront:
    update_distribution: yes
    distribution_id: E1RP5A2MJ8073O
    comment: modified by ansible cloudfront.py

# update a distribution's aliases and comment using the distribution_id as a reference
- cloudfront:
    update_distribution: yes
    distribution_id: E1RP5A2MJ8073O
    comment: modified by cloudfront.py again
    aliases: [ 'www.my-distribution-source.com', 'zzz.aaa.io' ]

# update a distribution's aliases and comment using an alias as a reference
- cloudfront:
    update_distribution: yes
    distribution_id: zzz.aaa.io
    comment: modified by cloudfront.py again
    aliases:
      - www.my-distribution-source.com
      - zzz.aaa.io

# add tags to a distribution referenced by alias
- cloudfront:
    tag_resource: yes
    alias: zzz.aaa.io
    tags:
      - Name: aaa
      - Project: aaa project

# remove a tag from a distribution referenced by alias
- cloudfront:
    untag_resource: yes
    alias: zzz.aaa.io
    tag_keys:
    - Project

# validate a distribution with an origin, logging and default cache behavior
- cloudfront:
    validate_distribution: yes
    origins:
        - id: 'my test origin-000111'
          domain_name: www.example.com
          origin_path: /production
          custom_headers:
            - header_name: MyCustomHeaderName
              header_value: MyCustomHeaderValue
    default_cache_behavior:
      target_origin_id: 'my test origin-000111'
      forwarded_values:
        query_string: true
        cookies:
          forward: all
        headers:
         - '*'
      viewer_protocol_policy: allow-all
      smooth_streaming: true
      compress: true
    logging:
      enabled: true
      include_cookies: false
      bucket: myawslogbucket.s3.amazonaws.com
      prefix: myprefix/
    enabled: false
    comment: this is a cloudfront distribution with logging

# create a distribution with an origin, logging and default cache behavior
    - cloudfront:
        create_distribution: yes
        origins:
            - id: 'my test origin-000111'
              domain_name: www.example.com
              origin_path: /production
              custom_headers:
                - header_name: MyCustomHeaderName
                  header_value: MyCustomHeaderValue
        default_cache_behavior:
          target_origin_id: 'my test origin-000111'
          forwarded_values:
            query_string: true
            cookies:
              forward: all
            headers:
             - '*'
          viewer_protocol_policy: allow-all
          smooth_streaming: true
          compress: true
        logging:
          enabled: true
          include_cookies: false
          bucket: mylogbucket.s3.amazonaws.com
          prefix: myprefix/
        enabled: false
        comment: this is a cloudfront distribution with logging

# delete a distribution
- cloudfront:
    delete_distribution: yes
    distribution_id: E1ZNUV0U7KWO4P

# duplicate a distribution by distribution_id and modify the comment field
- cloudfront:
    duplicate_distribution: yes
    distribution_id: E1RP5A2MJ8073O
    comment: duplicated distribution

# duplicate a distribution based on distribution_id and set comment and aliases on new distribution
- cloudfront:
    duplicate_distribution: yes
    distribution_id: E1RP5A2MJ8073O
    comment: duplicated distribution with different aliases
    aliases: [ 'test.one', 'test.two', 'another.domain.not.in.original.com' ]

# create a presigned url for a distribution based on a distribution_id and from a local pem file
- cloudfront:
    generate_presigned_url_from_pem_private_key: yes
    distribution_id: E1RP5A2MJ8073O
    presigned_url_pem_private_key_path: /home/user/ansible/pk-APKAJMTT6OPAZSFTNSCZ.pem
    presigned_url_pem_url: 'http://d3vodljfucvmwf.cloudfront.net/example.txt'
    presigned_url_pem_expire_date: '2017-04-20'

# create a streaming distribution
- cloudfront:
     create_streaming_distribution: yes
     default_s3_origin_domain_name: example-bucket.s3.amazonaws.com
     comment: example streaming distribution

# create a streaming distribution with tags
- cloudfront:
     create_streaming_distribution: yes
     default_s3_origin_domain_name: example-bucket.s3.amazonaws.com
     comment: example streaming distribution
     tags:
       - Name: example distribution
       - Project: example project
       - Priority: 1

# duplicate a streaming distribution
- cloudfront:
    duplicate_streaming_distribution: yes
    streaming_distribution_id: E2RTIUCAA9RINU

# update a streaming distribution
- cloudfront:
    update_streaming_distribution: yes
    streaming_distribution_id: E2RTIUCAA9RINU
    comment: modified streaming distribution

# create an origin access identity
- cloudfront:
    create_origin_access_identity: yes
    caller_reference: this is an example reference
    comment: this is an example comment

# update an origin access identity
- cloudfront:
     update_origin_access_identity: yes
     origin_access_identity_id: E17DRN9XUOAHZX
     caller_reference: this is an example reference
     e_tag: E2SOGFWHPXECAI
     comment: this is a new comment

# delete an origin access identity
- cloudfront:
    delete_origin_access_identity: yes
    origin_access_identity_id: EBXCCWOVSAYYD
    e_tag: E19J3JLL3TEPVY

# create a batch of invalidations
- cloudfront:
    create_invalidation: yes
    distribution_id: E15BU8SDCGSG57
    invalidation_batch:
      - /testpathone/test1.txt
      - /testpathtwo/test2.log
      - /testpaththree/test3.log


'''

RETURN = '''
location:
    description: describes a url specifying the output of the action just run.
    returned: applies to create_distribution, update_distribution,
    duplicate_distribution, create_streaming_distribution,
    update_streaming_distribution, duplicate_streaming_distribution,
    create_invalidation, create_origin_access_identity,
    update_origin_access_identity, delete_origin_access_identity
    type: str
validation_result:
    description: either returns 'OK' or fails with a description of why the
    validation failed.
    returned: applies to validate_distribution and validate_streaming_distribution
    type: str
'''

from ansible.module_utils.ec2 import get_aws_connection_info, ec2_argument_spec, boto3_conn, HAS_BOTO3
from ansible.module_utils.ec2 import camel_dict_to_snake_dict
from ansible.module_utils.basic import AnsibleModule
from ansible.modules.cloud.amazon.cloudfront_facts import CloudFrontFactsServiceManager
from botocore.signers import CloudFrontSigner
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
import datetime
from functools import partial
import json
import traceback

try:
    import botocore
except ImportError:
    pass


class CloudFrontServiceManager:
    """
    Handles CloudFront service calls to AWS
    """

    def __init__(self, module):
        self.module = module
        self.create_client('cloudfront')

    def create_client(self, resource):
        try:
            region, ec2_url, aws_connect_kwargs = get_aws_connection_info(self.module, boto3=True)
            self.client = boto3_conn(self.module, conn_type='client', resource=resource,
                                     region=region, endpoint=ec2_url, **aws_connect_kwargs)
        except botocore.exceptions.NoRegionError:
            self.module.fail_json(msg=("region must be specified as a parameter in "
                                       "AWS_DEFAULT_REGION environment variable or in "
                                       "boto configuration file"))
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="unable to establish connection - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

    def create_origin_access_identity(self, caller_reference, comment):
        try:
            func = partial(self.client.create_cloud_front_origin_access_identity,
                           CloudFrontOriginAccessIdentityConfig={
                               'CallerReference': caller_reference,
                               'Comment': comment
                           })
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="error creating cloud front origin access identity - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

    def delete_origin_access_identity(self, origin_access_identity_id, e_tag):
        try:
            func = partial(self.client.delete_cloud_front_origin_access_identity,
                           Id=origin_access_identity_id, IfMatch=e_tag)
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="error deleting cloud front origin access identity - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

    def update_origin_access_identity(self, caller_reference, comment, origin_access_identity_id, e_tag):
        try:
            func = partial(self.client.update_cloud_front_origin_access_identity,
                           CloudFrontOriginAccessIdentityConfig={
                               'CallerReference': caller_reference,
                               'Comment': comment
                           },
                           Id=origin_access_identity_id, IfMatch=e_tag)
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="error updating cloud front origin access identity - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

    def create_invalidation(self, distribution_id, invalidation_batch):
        try:
            func = partial(self.client.create_invalidation, DistributionId=distribution_id,
                           InvalidationBatch=invalidation_batch)
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="error creating invalidation(s) - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

    def generate_presigned_url_from_pem_private_key(self, distribution_id, private_key_path, private_key_password, url, expire_date):
        try:
            self.pem_private_key_path = private_key_path
            self.pem_private_key_password = private_key_password
            cloudfront_signer = CloudFrontSigner(distribution_id, self.presigned_url_rsa_signer)
            presigned_url = cloudfront_signer.generate_presigned_url(
                url, date_less_than=expire_date)
            return {'presigned_url': presigned_url}
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="error generating signed url from pem private key - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))
        finally:
            self.pem_private_key_path = None
            self.pem_private_key_password = None

    def presigned_url_rsa_signer(self, message):
        with open(self.pem_private_key_path, 'rb') as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=self.pem_private_key_password,
                backend=default_backend()
            )
        signer = private_key.signer(padding.PKCS1v15(), hashes.SHA1())
        signer.update(message)
        return signer.finalize()

    def create_distribution(self, config, tags):
        try:
            if tags is None:
                func = partial(self.client.create_distribution, DistributionConfig=config)
            else:
                distribution_config_with_tags = {
                    'DistributionConfig': config,
                    'Tags': tags
                }
                func = partial(self.client.create_distribution_with_tags,
                               DistributionConfigWithTags=distribution_config_with_tags)
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="error creating distribution - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

    def delete_distribution(self, distribution_id, e_tag):
        try:
            func = partial(self.client.delete_distribution, Id=distribution_id,
                           IfMatch=e_tag)
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="error deleting distribution - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

    def update_distribution(self, config, distribution_id, e_tag):
        try:
            func = partial(self.client.update_distribution, DistributionConfig=config,
                           Id=distribution_id, IfMatch=e_tag)
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="error updating distribution - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

    def create_streaming_distribution(self, config, tags):
        try:
            if tags is None:
                func = partial(self.client.create_streaming_distribution,
                               StreamingDistributionConfig=config)
            else:
                streaming_distribution_config_with_tags = {
                    'StreamingDistributionConfig': config,
                    'Tags': tags
                }
                func = partial(self.client.create_streaming_distribution_with_tags,
                               StreamingDistributionConfigWithTags=streaming_distribution_config_with_tags)
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="error creating streaming distribution - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

    def delete_streaming_distribution(self, streaming_distribution_id, e_tag):
        try:
            func = partial(self.client.delete_streaming_distribution, Id=streaming_distribution_id,
                           IfMatch=e_tag)
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="error deleting streaming distribution - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

    def update_streaming_distribution(self, config, streaming_distribution_id, e_tag):
        try:
            func = partial(self.client.update_streaming_distribution, StreamingDistributionConfig=config,
                           Id=streaming_distribution_id, IfMatch=e_tag)
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="error updating streaming distribution - " + str(e),
                                  exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

    def tag_resource(self, arn, tags):
        try:
            func = partial(self.client.tag_resource, Resource=arn,
                           Tags=tags)
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="error tagging resource - " + str(e), exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

    def untag_resource(self, arn, tag_keys):
        try:
            func = partial(self.client.untag_resource, Resource=arn,
                           TagKeys=tag_keys)
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="error untagging resource - " + str(e), exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

    def paginated_response(self, func, result_key=''):
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
            if result_key == '':
                result = response
                result.pop('ResponseMetadata', None)
            else:
                result = response.get(result_key)
            results.update(result)
            args['NextToken'] = response.get('NextToken')
            loop = args['NextToken'] is not None
        return results


class CloudFrontValidationManager:
    """
    Manages Cloudfront validations
    """

    def __init__(self, module):
        self.__cloudfront_facts_mgr = CloudFrontFactsServiceManager(module)
        self.module = module
        self.__helpers = CloudFrontHelpers()
        self.__default_distribution_enabled = False
        self.__default_http_port = 80
        self.__default_https_port = 443
        self.__default_is_ipv6_enabled = False
        self.__default_origin_ssl_protocols = ['TLSv1', 'TLSv1.1', 'TLSv1.2']
        self.__default_custom_origin_protocol_policy = 'match-viewer'
        self.__default_datetime_string = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
        self.__default_cache_behavior_min_ttl = 0
        self.__default_cache_behavior_max_ttl = 31536000
        self.__default_cache_behavior_default_ttl = 86400
        self.__default_cache_behavior_trusted_signers_enabled = False
        self.__default_cache_behavior_compress = False
        self.__default_cache_behavior_viewer_protocol_policy = 'allow-all'
        self.__default_cache_behavior_smooth_streaming = False
        self.__default_cache_behavior_forwarded_values_forward_cookies = 'none'
        self.__default_cache_behavior_forwarded_values_query_string = True
        self.__default_trusted_signers_enabled = True
        self.__default_presigned_url_pem_expire_date_format = '%Y-%m-%d'
        self.__valid_price_classes = ['PriceClass_100', 'PriceClass_200', 'PriceClass_All']
        self.__valid_custom_origin_protocol_policies = ['http-only', 'match-viewer', 'https-only']
        self.__valid_origin_ssl_protocols = ['SSLv3', 'TLSv1', 'TLSv1.1', 'TLSv1.2']
        self.__valid_cookie_forwarding = ['none', 'whitelist', 'all']
        self.__valid_viewer_protocol_policies = ['allow-all', 'https-only', 'redirect-to-https']
        self.__valid_methods = ['GET', 'HEAD', 'POST', 'PUT', 'PATCH', 'OPTIONS', 'DELETE']
        self.__valid_lambda_function_association_event_types = ['viewer-request', 'viewer-response',
                                                                'origin-request', 'origin-response']
        self.__valid_viewer_certificate_ssl_support_methods = ['sni-only', 'vip']
        self.__valid_viewer_certificate_minimum_protocol_versions = ['SSLv3', 'TLSv1']
        self.__valid_viewer_certificate_certificate_sources = ['cloudfront', 'iam', 'acm']
        self.__valid_http_versions = ['http1.1', 'http2']
        self.__s3_bucket_domain_identifier = '.s3.amazonaws.com'

    def validate_logging(self, logging, streaming):
        try:
            if logging is None:
                return None
            valid_logging = {}
            if not streaming:
                if(logging and ('enabled' not in logging or 'include_cookies' not in logging or
                                'bucket' not in logging or 'prefix' not in logging)):
                    self.module.fail_json(msg="the logging parameters enabled, include_cookies, bucket and " +
                                          "prefix must be specified")
                valid_logging['include_cookies'] = logging.get('include_cookies')
            else:
                if logging and ('enabled' not in logging or 'bucket' not in logging or 'prefix' not in logging):
                    self.module.fail_json(
                        msg="the logging parameters enabled, bucket and prefix must be specified")
            valid_logging['enabled'] = logging.get('enabled')
            valid_logging['bucket'] = logging.get('bucket')
            valid_logging['prefix'] = logging.get('prefix')
            return valid_logging
        except Exception as e:
            self.module.fail_json(msg="error validating distribution logging - " + str(e))

    def validate_is_list(self, list_to_validate, list_name):
        if not isinstance(list_to_validate, list):
            self.module.fail_json(msg='{0} must be a list'.format(list_name))

    def validate_origins(self, origins, default_origin_domain_name, default_origin_access_identity,
                         default_origin_path, streaming, create_distribution):
        try:
            valid_origins = {}
            if origins is None:
                if default_origin_domain_name is None and not create_distribution:
                    return None
                if default_origin_domain_name is not None:
                    origins = [{
                        'domain_name': default_origin_domain_name,
                        'origin_path': '' if default_origin_path is None else str(default_origin_path)
                    }]
            self.validate_is_list(origins, 'origins')
            quantity = len(origins)
            if quantity == 0 and default_origin_domain_name is None and create_distribution:
                self.module.fail_json(msg="both origins[] and default_origin_domain_name have not been " +
                                      "specified. please specify at least one.")
            for origin in origins:
                origin = self.validate_origin(
                    origin, default_origin_path, default_origin_access_identity, streaming)
            return self.__helpers.python_list_to_aws_list(origins)
        except Exception as e:
            self.module.fail_json(msg="error validating distribution origins - " + str(e))

    def validate_origin(self, origin, default_origin_path, default_origin_access_identity, streaming):
        try:
            if 'origin_path' not in origin:
                if default_origin_path is not None:
                    origin['origin_path'] = default_origin_path
                else:
                    origin['origin_path'] = ''
            if 'domain_name' not in origin:
                self.module.fail_json(msg="origins[].domain_name must be specified for an origin")
            if 'id' not in origin:
                origin['id'] = self.__default_datetime_string
            if 'custom_headers' in origin and streaming:
                self.module.fail_json(msg="custom_headers has been specified for a streaming " +
                                      "distribution. custom headers are for web distributions only")
            if 'custom_headers' in origin and len(origin.get('custom_headers')) > 0:
                for custom_header in origin.get('custom_headers'):
                    if 'header_name' not in custom_header or 'header_value' not in custom_header:
                        self.module.fail_json(msg="both origins[].custom_headers.header_name and " +
                                              "origins[].custom_headers.header_value must be specified")
                origin['custom_headers'] = self.__helpers.python_list_to_aws_list(
                    origin.get('custom_headers'))
            else:
                origin['custom_headers'] = self.__helpers.python_list_to_aws_list()
            if self.__s3_bucket_domain_identifier in origin.get('domain_name'):
                if 's3_origin_config' not in origin or 'origin_access_identity' not in origin.get('s3_origin_config'):
                    origin["s3_origin_config"] = {}
                    if default_origin_access_identity is not None:
                        origin['s3_origin_config']['origin_access_identity'] = default_origin_access_identity
                    else:
                        origin['s3_origin_config']['origin_access_identity'] = ''
            else:
                if 'custom_origin_config' not in origin:
                    origin['custom_origin_config'] = {}
                custom_origin_config = origin.get('custom_origin_config')
                if 'origin_protocol_policy' not in custom_origin_config:
                    custom_origin_config['origin_protocol_policy'] = self.__default_custom_origin_protocol_policy
                else:
                    self.validate_attribute_with_allowed_values(custom_origin_config.get('origin_protocol_policy'),
                                                                'origins[].custom_origin_config.origin_protocol_policy', self.__valid_origin_protocol_policies)
                if 'http_port' not in custom_origin_config:
                    custom_origin_config['h_t_t_p_port'] = self.__default_http_port
                else:
                    custom_origin_config = self.__helpers.change_dict_key_name(custom_origin_config, 'http_port',
                                                                               'h_t_t_p_port')
                if 'https_port' not in custom_origin_config:
                    custom_origin_config['h_t_t_p_s_port'] = self.__default_https_port
                else:
                    custom_origin_config = self.__helpers.change_dict_key_name(custom_origin_config, 'https_port',
                                                                               'h_t_t_p_s_port')
                if 'origin_ssl_protocols' not in custom_origin_config:
                    temp_origin_ssl_protocols = self.__default_origin_ssl_protocols
                else:
                    self.validate_attribute_with_allowed_values(custom_origin_config.get('origin_ssl_protocols'),
                                                                'origins[].origin_ssl_protocols', self.__valid_origin_ssl_protocols)
                custom_origin_config['origin_ssl_protocols'] = self.__helpers.python_list_to_aws_list(
                    temp_origin_ssl_protocols)
            return origin
        except Exception as e:
            self.module.fail_json(msg="error validating distribution origin - " + str(e))

    def validate_cache_behaviors(self, cache_behaviors, valid_origins):
        try:
            if cache_behaviors is None and valid_origins is not None:
                return None
            for cache_behavior in cache_behaviors:
                self.validate_cache_behavior(cache_behavior, valid_origins)
            return self.__helpers.python_list_to_aws_list(cache_behaviors)
        except Exception as e:
            self.module.fail_json(msg="error validating distribution cache behaviors - " + str(e))

    def validate_cache_behavior(self, cache_behavior, valid_origins, is_default_cache=False):
        try:
            if is_default_cache and cache_behavior is None:
                cache_behavior = {}
            if cache_behavior is None and valid_origins is not None:
                return None
            if 'min_ttl' not in cache_behavior:
                cache_behavior['min_t_t_l'] = self.__default_cache_behavior_min_ttl
            else:
                cache_behavior = self.__helpers.change_dict_key_name(
                    cache_behavior, 'min_ttl', 'min_t_t_l')
            if 'max_ttl' not in cache_behavior:
                cache_behavior['max_t_t_l'] = self.__default_cache_behavior_max_ttl
            else:
                cache_behavior = self.__helpers.change_dict_key_name(
                    cache_behavior, 'max_ttl', 'max_t_t_l')
            if 'default_ttl' not in cache_behavior:
                cache_behavior['default_t_t_l'] = self.__default_cache_behavior_default_ttl
            else:
                cache_behavior = self.__helpers.change_dict_key_name(
                    cache_behavior, 'default_ttl', 'default_t_t_l')
            if 'compress' not in cache_behavior:
                cache_behavior['compress'] = self.__default_cache_behavior_compress
            if is_default_cache:
                if 'target_origin_id' not in cache_behavior:
                    cache_behavior['target_origin_id'] = self.get_first_origin_id_for_default_cache_behavior(
                        valid_origins)
                else:
                    cache_behavior['target_origin_id'] = str(cache_behavior.get('target_origin_id'))
            if 'forwarded_values' not in cache_behavior:
                cache_behavior['forwarded_values'] = {}
            forwarded_values = cache_behavior.get('forwarded_values')
            forwarded_values['headers'] = self.__helpers.python_list_to_aws_list(
                forwarded_values.get('headers'))
            if 'cookies' not in forwarded_values:
                forwarded_values['cookies'] = {}
                forwarded_values['cookies']['forward'] = self.__default_cache_behavior_forwarded_values_forward_cookies
            else:
                forwarded_values['cookies']['whitelisted_names'] = self.__helpers.python_list_to_aws_list(
                    forwarded_values['cookies'].get('whitelisted_names'))
                cookie_forwarding = forwarded_values['cookies'].get('forward')
                self.validate_attribute_with_allowed_values(cookie_forwarding,
                                                            'cache_behavior.forwarded_values.cookies.forward', self.__valid_cookie_forwarding)
            forwarded_values['query_string_cache_keys'] = self.__helpers.python_list_to_aws_list(
                forwarded_values.get('query_string_cache_keys'))
            if 'query_string' not in forwarded_values:
                forwarded_values['query_string'] = self.__default_cache_behavior_forwarded_values_query_string
            allowed_methods = cache_behavior.get('allowed_methods')
            if allowed_methods is not None:
                if 'items' not in allowed_methods:
                    self.module.fail_json(
                        msg="cache_behavior.allowed_methods.items[] must be specified")
                self.validate_attribute_with_allowed_values(cache_behavior.get('cached_methods'),
                                                            'cache_behavior.allowed_items.cached_methods[]', self.__valid_methods)
                self.validate_is_list(allowed_methods.get('items'),
                                      'cache_behavior.allowed_methods.items')
                if 'cached_methods' in allowed_methods:
                    self.validate_is_list(allowed_methods.get('cached_methods'),
                                          'cache_behavior.allowed_methods.cached_methods')
                    self.validate_attribute_with_allowed_values(allowed_methods.get('cached_methods'),
                                                                'cache_behavior.allowed_items.cached_methods[]', self.__valid_methods)
            lambda_function_associations = cache_behavior.get('lambda_function_associations')
            if lambda_function_associations is not None:
                self.validate_is_list(lambda_function_associations, 'lambda_function_associations')
                for association in lambda_function_associations:
                    if 'lambda_function_arn' in association:
                        association = self.__helpers.change_dict_key_name(association, 'lambda_function_arn',
                                                                          'lambda_function_a_r_n')
                    if 'event_type' in association:
                        self.validate_attribute_with_allowed_values(association.get('event_type'),
                                                                    'cache_behaviors[].lambda_function_associations.event_type',
                                                                    self.__valid_lambda_function_association_event_types)
            cache_behavior['lambda_function_associations'] = self.__helpers.python_list_to_aws_list(
                lambda_function_associations)
            if 'viewer_protocol_policy' not in cache_behavior:
                cache_behavior['viewer_protocol_policy'] = self.__default_cache_behavior_viewer_protocol_policy
            else:
                self.validate_attribute_with_allowed_values(cache_behavior.get('viewer_protocol_policy'),
                                                            'cache_behavior.viewer_protocol_policy', self.__valid_viewer_protocol_policies)
            if 'smooth_streaming' not in cache_behavior:
                cache_behavior['smooth_streaming'] = self.__default_cache_behavior_smooth_streaming
            cache_behavior['trusted_signers'] = self.validate_trusted_signers(
                cache_behavior.get('trusted_signers'))
            return cache_behavior
        except Exception as e:
            self.module.fail_json(msg="error validating distribution cache behavior - " + str(e))

    def validate_trusted_signers(self, trusted_signers):
        try:
            if trusted_signers is None:
                trusted_signers = {}
            if 'enabled' not in trusted_signers:
                trusted_signers['enabled'] = self.__default_trusted_signers_enabled
            if 'items' not in trusted_signers:
                trusted_signers['items'] = []
            valid_trusted_signers = self.__helpers.python_list_to_aws_list(
                trusted_signers.get('items'))
            valid_trusted_signers['enabled'] = trusted_signers.get('enabled')
            return valid_trusted_signers
        except Exception as e:
            self.module.fail_json(msg="error validating trusted signers - " + str(e))

    def validate_s3_origin(self, s3_origin, default_s3_origin_domain_name, default_s3_origin_origin_access_identity):
        try:
            if s3_origin is not None:
                if 'domain_name' not in s3_origin:
                    self.module.fail_json("s3_origin.domain_name must be specified for s3_origin")
                if 'origin_access_identity' not in s3_origin:
                    self.module.fail_json(
                        "s3_origin.origin_origin_access_identity must be specified for s3_origin")
                return s3_origin
            s3_origin = {}
            if default_s3_origin_domain_name is not None:
                s3_origin['domain_name'] = default_s3_origin_domain_name
            else:
                self.module.fail_json(msg="s3_origin and default_s3_origin_domain_name not specified. " +
                                      "please specify one.")
            if default_s3_origin_origin_access_identity is not None:
                s3_origin['origin_access_identity'] = default_s3_origin_origin_access_identity
            else:
                s3_origin['origin_access_identity'] = ''
            return s3_origin
        except Exception as e:
            self.module.fail_json(msg="error validating s3 origin - " + str(e))

    def validate_viewer_certificate(self, viewer_certificate):
        try:
            if viewer_certificate is None:
                return None
            if(viewer_certificate.get('cloudfront_default_certificate') and
                    viewer_certificate.get('ssl_support_method') is not None):
                self.module.fail_json(msg="viewer_certificate.ssl_support_method should not be specified with" +
                                      "viewer_certificate_cloudfront_default_certificate set to true")
            if 'ssl_support_method' in viewer_certificate:
                self.validate_attribute_with_allowed_values(viewer_certificate.get('ssl_support_method'),
                                                            'viewer_certificate.ssl_support_method',
                                                            self.__valid_viewer_certificate_ssl_support_methods)
            if 'minimum_protocol_version' in viewer_certificate:
                self.validate_attribute_with_allowed_values(viewer_certificate.get('minimum_protocol_version'),
                                                            'viewer_certificate.minimum_protocol_version',
                                                            self.__valid_viewer_certificate_minimum_protocol_versions)
            if 'certificate_source' in viewer_certificate:
                self.validate_attribute_with_allowed_values(viewer_certificate.get('certificate_source'),
                                                            'viewer_certificate.certificate_source',
                                                            self.__valid_viewer_certificate_certificate_sources)
            if 'ssl_support_method' in viewer_certificate:
                viewer_certificate = self.__helpers.change_dict_key_name(viewer_certificate, 'ssl_support_method',
                                                                         's_s_l_support_method')
            if 'iam_certificate' in viewer_certificate:
                viewer_certificate = self.__helpers.change_dict_key_name(viewer_certificate, 'iam_certificate_id',
                                                                         'i_a_m_certificate_id')
            if 'acm_certificate' in viewer_certificate:
                viewer_certificate = self.__helpers.change_dict_key_name(viewer_certificate, 'acm_certificate_arn',
                                                                         'a_c_m_certificate_arn')
            return viewer_certificate
        except Exception as e:
            self.module.fail_json(msg="error validating viewer certificate - " + str(e))

    def validate_custom_error_responses(self, custom_error_responses):
        try:
            if custom_error_responses is None:
                return None
            self.validate_is_list(custom_error_responses, 'custom_error_responses')
            for custom_error_response in custom_error_responses:
                if custom_error_response.get('error_code') is None:
                    self.module.json_fail(
                        msg="custom_error_responses[].error_code must be specified")
                custom_error_response = self.__helpers.change_dict_key_name(custom_error_responses, 'error_caching_min_ttl',
                                                                            'error_caching_min_t_t_l')
            return self.__helpers.python_list_to_aws_list(custom_error_responses)
        except Exception as e:
            self.module.fail_json(msg="error validating custom error responses - " + str(e))

    def validate_restrictions(self, restrictions):
        try:
            if restrictions is None:
                return None
            geo_restriction = restrictions.get('geo_restriction')
            if geo_restriction is None:
                self.module.fail_json(msg="restrictions.geo_restriction must be specified")
            restriction_type = geo_restriction.get('restriction_type')
            if restriction_type is None:
                self.module.fail_json(
                    msg="restrictions.geo_restriction.restriction_type must be specified")
            items = geo_restriction.get('items')
            valid_restrictions = python_list_to_aws_list(items)
            valid_restrictions['restriction_type'] = restriction_type
            return valid_restrictions
        except Exception as e:
            self.module.fail_json(msg="error validating restrictions - " + str(e))

    def validate_update_delete_distribution_parameters(self, alias, distribution_id, config, e_tag):
        try:
            if distribution_id is None and alias is None:
                self.module.fail_json(msg="distribution_id or alias must be specified for updating or "
                                      "deleting a distribution.")
            if distribution_id is None:
                distribution_id = self.__cloudfront_facts_mgr.get_distribution_id_from_domain_name(
                    alias)
            if config is None:
                config = self.__cloudfront_facts_mgr.get_distribution_config(
                    distribution_id).get('DistributionConfig')
            if e_tag is None:
                e_tag = self.__cloudfront_facts_mgr.get_etag_from_distribution_id(
                    distribution_id, False)
            return distribution_id, config, e_tag
        except Exception as e:
            self.module.fail_json(
                msg="error validating parameters for distribution update and delete - " + str(e))

    def validate_update_delete_streaming_distribution_parameters(self, alias, streaming_distribution_id,
                                                                 config, e_tag):
        try:
            if streaming_distribution_id is None and alias is None:
                self.module.fail_json(msg="streaming_distribution_id or alias must be specified for updating " +
                                      "or deleting a streaming distribution.")
            if streaming_distribution_id is None:
                streaming_distribution_id = self.__cloudfront_facts_mgr.get_distribution_id_from_domain_name(
                    alias)
            if config is None:
                config = self.__cloudfront_facts_mgr.get_streaming_distribution_config(
                    streaming_distribution_id).get('StreamingDistributionConfig')
            if e_tag is None:
                e_tag = self.__cloudfront_facts_mgr.get_etag_from_distribution_id(
                    streaming_distribution_id, True)
            return streaming_distribution_id, config, e_tag
        except Exception as e:
            self.module.fail_json(
                msg="error validating parameters for streaming distribution update and delete - " + str(e))

    def validate_tagging_arn(self, arn, alias, distribution_id, streaming_distribution_id):
        try:
            if arn is not None:
                return arn
            if alias is not None and (distribution_id is not None or streaming_distribution_id is not None):
                self.module.fail_json(msg="both alias and a distribution id have been specified for tagging a resource. " +
                                      "please only specify one.")
            if distribution_id is not None and streaming_distribution_id is not None:
                self.module.fail_json(msg="both distribution_id and streaming_distribution_id have been specified. " +
                                      "please only specify one.")
            if alias is not None:
                distribution_id = self.__cloudfront_facts_mgr.get_distribution_id_from_domain_name(
                    alias)
            if distribution_id is not None:
                distribution_response = self.__cloudfront_facts_mgr.get_distribution(
                    distribution_id)
            if distribution_response is not None:
                distribution = distribution_response.get('Distribution')
                if distribution is not None:
                    return distribution.get('ARN')
            streaming_distribution_response = self.__cloudfront_facts_mgr.get_streaming_distribution(
                streaming_distribution_id)
            if streaming_distribution_response is not None:
                streaming_distribution = streaming_distribution_response.get(
                    'StreamingDistribution')
                if streaming_distribution is not None:
                    return streaming_distribution.get('ARN')
            self.module.fail_json(
                msg="unable to find a matching distribution with given parameters")
        except Exception as e:
            self.module.fail_json(msg="error validating tagging parameters - " + str(e))

    def create_aws_list_without_quantity(self, list_items):
        try:
            if list_items is None:
                return None
            aws_list_items = self.__helpers.python_list_to_aws_list(list_items)
            aws_list_items.pop('quantity', None)
            pascal_aws_list_items = self.__helpers.snake_dict_to_pascal_dict(aws_list_items)
            return pascal_aws_list_items
        except Exception as e:
            self.module.fail_json(msg="error creating aws list without items - " + str(e))

    def validate_tags(self, tags):
        try:
            if tags is None:
                return None
            list_items = []
            for item in tags:
                key, value = item.iteritems().next()
                list_items.append({'Key': key, 'Value': value})
            return self.create_aws_list_without_quantity(list_items)
        except Exception as e:
            self.module.fail_json(msg="error validating tags - " + str(e))

    def validate_distribution_config_parameters(self, config, default_root_object, is_ipv6_enabled,
                                                http_version, web_acl_id):
        try:
            if default_root_object is not None:
                config['default_root_object'] = default_root_object
            else:
                config['default_root_object'] = ''
            if is_ipv6_enabled is not None:
                config['is_i_p_v_6_enabled'] = is_ipv6_enabled
            else:
                config['is_i_p_v_6_enabled'] = self.__default_is_ipv6_enabled
            if http_version is not None:
                self.valiate_attribute_with_allowed_values(
                    http_version, 'http_version', self.__valid_http_versions)
                config['http_version'] = http_version
            if web_acl_id is not None:
                config['web_a_c_l_id'] = web_acl_id
            return config
        except Exception as e:
            self.module.fail_json(msg="error validating distribution config parameters - " + str(e))

    def validate_streaming_distribution_config_parameters(self, config, comment, trusted_signers, s3_origin,
                                                          default_s3_origin_domain_name, default_s3_origin_origin_access_identity):
        try:
            if s3_origin is None:
                s3_origin = config.get('s3_origin')
            config['s3_origin'] = self.validate_s3_origin(s3_origin, default_s3_origin_domain_name,
                                                          default_s3_origin_origin_access_identity)
            config['trusted_signers'] = self.validate_trusted_signers(trusted_signers)
            return config
        except Exception as e:
            self.module.fail_json(
                msg="error validating streaming distribution config parameters - " + str(e))

    def validate_invalidation_batch(self, invalidation_batch, caller_reference):
        try:
            if caller_reference is not None:
                valid_caller_reference = caller_reference
            else:
                valid_caller_reference = self.__default_datetime_string
            valid_invalidation_batch = {
                'paths': self.__helpers.python_list_to_aws_list(invalidation_batch),
                'caller_reference': valid_caller_reference
            }
            return valid_invalidation_batch
        except Exception as e:
            self.module.fail_json(msg="error validating invalidation batch - " + str(e))

    def validate_common_distribution_parameters(self, config, enabled, aliases, logging,
                                                price_class, comment, is_streaming_distribution):
        try:
            if config is None:
                config = {}
            if aliases is not None:
                config['aliases'] = self.__helpers.python_list_to_aws_list(aliases)
            if logging is not None:
                config['logging'] = self.validate_logging(logging, is_streaming_distribution)
            if enabled is not None:
                config['enabled'] = enabled
            else:
                config['enabled'] = self.__default_distribution_enabled
            if price_class is not None:
                self.validate_attribute_with_allowed_values(
                    price_class, 'price_class', self.__valid_price_classes)
                config['price_class'] = price_class
            if comment is not None:
                config['comment'] = comment
            else:
                config['comment'] = "distribution created by ansible with datetime " + \
                    self.__default_datetime_string
            return config
        except Exception as e:
            self.module.fail_json(msg="error validating common distribution parameters - " + str(e))

    def validate_caller_reference_for_distribution(self, config, caller_reference):
        try:
            if caller_reference is not None:
                config['caller_reference'] = caller_reference
            else:
                config['caller_reference'] = self.__default_datetime_string
            return config
        except Exception as e:
            self.module.fail_json(msg="error validating caller reference - " + str(e))

    def get_first_origin_id_for_default_cache_behavior(self, valid_origins):
        try:
            if valid_origins is not None:
                valid_origins_list = valid_origins.get('items')
                if valid_origins_list is not None and isinstance(valid_origins_list, list) and len(valid_origins_list) > 0:
                    return str(valid_origins.get('items')[0].get('id'))
            self.module.fail_json(msg="there are no valid origins from which to specify a target_origin_id " +
                                  "for the default_cache_behavior configuration")
        except Exception as e:
            self.module.fail_json(
                msg="error getting first origin_id for default cache behavior- " + str(e))

    def validate_attribute_with_allowed_values(self, attribute, attribute_name, allowed_list):
        try:
            if attribute is not None and attribute not in allowed_list:
                self.module.fail_json(msg='the attribute {0} must be one of {1}'.format(attribute_name,
                                                                                        ' '.join(str(e) for e in allowed_list)))
        except Exception as e:
            self.module.fail_json(msg="error validating attribute with allowed values - " + str(e))

    def validate_presigned_url_pem_expire_date(self, datetime_string):
        try:
            return datetime.datetime.strptime(datetime_string, self.__default_presigned_url_pem_expire_date_format)
        except Exception as e:
            self.module.fail_json(msg="presigned_url_pem_expire_date must be in the format '{0}'".format(
                self.__default_presigned_url_pem_expire_date_format))


class CloudFrontHelpers:
    """
    Miscellaneous helpers for processing cloudfront data
    """

    def change_dict_key_name(self, dictionary, old_key, new_key):
        if old_key in dictionary:
            dictionary[new_key] = dictionary.get(old_key)
            dictionary.pop(old_key, None)
        return dictionary

    def snake_dict_to_pascal_dict(self, snake_dict):
        def pascalize(complex_type):
            if complex_type is None:
                return
            new_type = type(complex_type)()
            if isinstance(complex_type, dict):
                for key in complex_type:
                    new_type[pascal(key)] = pascalize(complex_type[key])
            elif isinstance(complex_type, list):
                for i in range(len(complex_type)):
                    new_type.append(pascalize(complex_type[i]))
            else:
                return complex_type
            return new_type

        def pascal(words):
            return words.capitalize().split('_')[0] + ''.join(x.capitalize() or '_' for x in words.split('_')[1:])
        return pascalize(snake_dict)

    def pascal_dict_to_snake_dict(self, pascal_dict, split_caps=False):
        def pascal_to_snake(name):
            import re
            first_cap_re = re.compile('(.)([A-Z][a-z]+)')
            all_cap_re = re.compile('([a-z0-9])([A-Z]+)')
            split_cap_re = re.compile('([A-Z])')
            s1 = first_cap_re.sub(r'\1\2', name)
            if split_caps:
                s2 = split_cap_re.sub(r'_\1', s1).lower()
                s2 = s2[1:] if s2[0] == '_' else s2
            else:
                s2 = all_cap_re.sub(r'\1_\2', s1).lower()
            return s2

        def value_is_list(pascal_list):
            checked_list = []
            for item in pascal_list:
                if isinstance(item, dict):
                    checked_list.append(self.pascal_dict_to_snake_dict(item, split_caps))
                elif isinstance(item, list):
                    checked_list.append(value_is_list(item))
                else:
                    checked_list.append(item)
            return checked_list
        snake_dict = {}
        for k, v in pascal_dict.items():
            if isinstance(v, dict):
                snake_dict[pascal_to_snake(k)] = self.pascal_dict_to_snake_dict(v, split_caps)
            elif isinstance(v, list):
                snake_dict[pascal_to_snake(k)] = value_is_list(v)
            else:
                snake_dict[pascal_to_snake(k)] = v
        return snake_dict

    def merge_validation_into_config(self, config, validated_node, node_name):
        if validated_node is not None:
            if isinstance(validated_node, dict):
                config_node = config.get(node_name)
                if config_node is not None:
                    config_node_items = config_node.items()
                else:
                    config_node_items = []
                config[node_name] = dict(config_node_items + validated_node.items())
            if isinstance(validated_node, list):
                config[node_name] = list(set(config.get(node_name) + validated_node))
        return config

    def python_list_to_aws_list(self, list_items=None):
        if list_items is None:
            list_items = []
        if not isinstance(list_items, list):
            self.module.fail_json(msg='expected a python list, got a python {0} with value {1}'.format(
                type(list_items).__name__, str(list_items)))
        result = {}
        result['quantity'] = len(list_items)
        result['items'] = list_items
        return result


def main():
    argument_spec = ec2_argument_spec()

    argument_spec.update(dict(
        create_origin_access_identity=dict(required=False, default=False, type='bool'),
        update_origin_access_identity=dict(required=False, default=False, type='bool'),
        delete_origin_access_identity=dict(required=False, default=False, type='bool'),
        create_distribution=dict(required=False, default=False, type='bool'),
        update_distribution=dict(required=False, default=False, type='bool'),
        delete_distribution=dict(required=False, default=False, type='bool'),
        create_invalidation=dict(required=False, default=False, type='bool'),
        create_streaming_distribution=dict(required=False, default=False, type='bool'),
        update_streaming_distribution=dict(required=False, default=False, type='bool'),
        delete_streaming_distribution=dict(required=False, default=False, type='bool'),
        generate_presigned_url_from_pem_private_key=dict(
            required=False, default=False, type='bool'),
        duplicate_distribution=dict(required=False, default=False, type='bool'),
        duplicate_streaming_distribution=dict(required=False, default=False, type='bool'),
        validate_distribution=dict(required=False, default=False, type='bool'),
        validate_streaming_distribution=dict(required=False, default=False, type='bool'),
        origin_access_identity_id=dict(required=False, default=None, type='str'),
        caller_reference=dict(required=False, default=None, type='str'),
        comment=dict(required=False, default=None, type='str'),
        distribution_id=dict(required=False, default=None, type='str'),
        streaming_distribution_id=dict(required=False, default=None, type='str'),
        invalidation_batch=dict(required=False, default=None, type='list'),
        e_tag=dict(required=False, default=None, type='str'),
        presigned_url_pem_private_key_path=dict(required=False, default=None, type='str'),
        presigned_url_pem_private_key_password=dict(
            required=False, default=None, type='str', no_log=True),
        presigned_url_pem_url=dict(required=False, default=None, type='str'),
        presigned_url_pem_expire_date=dict(required=False, default=None, type='str'),
        tag_keys=dict(required=False, default=False, type='list'),
        config=dict(required=False, default=None, type='json'),
        tags=dict(required=False, default=None, type='list'),
        tag_resource=dict(required=False, default=None, type='bool'),
        untag_resource=dict(required=False, default=None, type='bool'),
        arn=dict(required=False, default=None, type='str'),
        alias=dict(required=False, default=None, type='str'),
        aliases=dict(required=False, default=None, type='list'),
        default_root_object=dict(required=False, default=None, type='str'),
        origins=dict(required=False, default=None, type='list'),
        default_cache_behavior=dict(required=False, default=None, type='dict'),
        cache_behaviors=dict(required=False, default=None, type='list'),
        custom_error_responses=dict(required=False, default=None, type='list'),
        logging=dict(required=False, default=None, type='dict'),
        price_class=dict(required=False, default=None, type='str'),
        enabled=dict(required=False, default=None, type='bool'),
        viewer_certificate=dict(required=False, default=None, type='dict'),
        restrictions=dict(required=False, default=None, type='json'),
        restrictions_restriction_type=dict(required=False, default=None, type='str'),
        restrictions_items=dict(required=False, default=None, type='list'),
        web_acl_id=dict(required=False, default=None, type='str'),
        http_version=dict(required=False, default=None, type='str'),
        is_ipv6_enabled=dict(required=False, default=None, type='bool'),
        s3_origin=dict(required=False, default=None, type='json'),
        trusted_signers=dict(required=False, default=None, type='list'),
        default_origin_domain_name=dict(required=False, default=None, type='str'),
        default_origin_path=dict(required=False, default=None, type='str'),
        default_origin_access_identity=dict(required=False, default=None, type='str'),
        default_s3_origin_domain_name=dict(required=False, default=None, type='str'),
        default_s3_origin_origin_access_identity=dict(required=False, default=None, type='str')
    ))

    result = {}

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)
    service_mgr = CloudFrontServiceManager(module)
    validation_mgr = CloudFrontValidationManager(module)
    helpers = CloudFrontHelpers()

    create_origin_access_identity = module.params.get('create_origin_access_identity')
    update_origin_access_identity = module.params.get('update_origin_access_identity')
    delete_origin_access_identity = module.params.get('delete_origin_access_identity')
    create_distribution = module.params.get('create_distribution')
    update_distribution = module.params.get('update_distribution')
    delete_distribution = module.params.get('delete_distribution')
    create_streaming_distribution = module.params.get('create_streaming_distribution')
    update_streaming_distribution = module.params.get('update_streaming_distribution')
    delete_streaming_distribution = module.params.get('delete_streaming_distribution')
    generate_presigned_url_from_pem_private_key = module.params.get(
        'generate_presigned_url_from_pem_private_key')
    duplicate_distribution = module.params.get('duplicate_distribution')
    duplicate_streaming_distribution = module.params.get('duplicate_streaming_distribution')
    validate_distribution = module.params.get('validate_distribution')
    validate_streaming_distribution = module.params.get('validate_streaming_distribution')
    caller_reference = module.params.get('caller_reference')
    comment = module.params.get('comment')
    e_tag = module.params.get('e_tag')
    origin_access_identity_id = module.params.get('origin_access_identity_id')
    presigned_url_pem_private_key_path = module.params.get('presigned_url_pem_private_key_path')
    presigned_url_pem_private_key_password = module.params.get(
        'presigned_url_pem_private_key_password')
    presigned_url_pem_url = module.params.get('presigned_url_pem_url')
    presigned_url_pem_expire_date = module.params.get('presigned_url_pem_expire_date')
    config = module.params.get('config')
    tags = module.params.get('tags')
    tag_keys = module.params.get('tag_keys')
    tag_resource = module.params.get('tag_resource')
    untag_resource = module.params.get('untag_resource')
    arn = module.params.get('arn')
    create_invalidation = module.params.get('create_invalidation')
    distribution_id = module.params.get('distribution_id')
    streaming_distribution_id = module.params.get('streaming_distribution_id')
    invalidation_batch = module.params.get('invalidation_batch')
    alias = module.params.get('alias')
    aliases = module.params.get('aliases')
    default_root_object = module.params.get('default_root_object')
    origins = module.params.get('origins')
    default_cache_behavior = module.params.get('default_cache_behavior')
    cache_behaviors = module.params.get('cache_behaviors')
    custom_error_responses = module.params.get('custom_error_responses')
    comment = module.params.get('comment')
    logging = module.params.get('logging')
    price_class = module.params.get('price_class')
    enabled = module.params.get('enabled')
    viewer_certificate = module.params.get('viewer_certificate')
    restrictions = module.params.get('restrictions')
    web_acl_id = module.params.get('web_acl_id')
    http_version = module.params.get('http_version')
    is_ipv6_enabled = module.params.get('is_ipv6_enabled')
    s3_origin = module.params.get('s3_origin')
    trusted_signers = module.params.get('trusted_signers')
    default_origin_domain_name = module.params.get('default_origin_domain_name')
    default_origin_path = module.params.get('default_origin_path')
    default_origin_access_identity = module.params.get('default_origin_access_identity')
    default_s3_origin_domain_name = module.params.get('default_s3_origin_domain_name')
    default_s3_origin_origin_access_identity = module.params.get(
        'default_s3_origin_origin_access_identity')

    create_update_distribution = create_distribution or update_distribution
    create_update_streaming_distribution = create_streaming_distribution or update_streaming_distribution
    update_delete_duplicate_distribution = update_distribution or delete_distribution or duplicate_distribution
    update_delete_duplicate_streaming_distribution = (update_streaming_distribution or delete_streaming_distribution or
                                                      duplicate_streaming_distribution)
    create = create_distribution or create_streaming_distribution
    validate = validate_distribution or validate_streaming_distribution
    duplicate = duplicate_distribution or duplicate_streaming_distribution
    delete = delete_distribution or delete_streaming_distribution or delete_origin_access_identity
    config_required = (create_distribution or update_delete_duplicate_distribution or create_streaming_distribution or
                       update_delete_duplicate_streaming_distribution or validate)
    tagging = tag_resource or untag_resource
    has_tags = not (delete or untag_resource or generate_presigned_url_from_pem_private_key)

    if sum(map(bool, [create_origin_access_identity, delete_origin_access_identity, update_origin_access_identity,
                      create_distribution, delete_distribution, update_distribution, create_streaming_distribution,
                      delete_streaming_distribution, update_streaming_distribution, generate_presigned_url_from_pem_private_key,
                      duplicate_distribution, duplicate_streaming_distribution, validate_distribution,
                      validate_streaming_distribution, create_invalidation, tag_resource, untag_resource])) > 1:
        module.fail_json(
            msg="more than one cloudfront action has been specified. please select only one action.")

    if (validate or create) and config is None:
        config = {}

    if update_delete_duplicate_distribution or config:
        distribution_id, config, e_tag = validation_mgr.validate_update_delete_distribution_parameters(
            alias, distribution_id, config, e_tag)

    if update_delete_duplicate_streaming_distribution or validate_streaming_distribution:
        streaming_distribution_id, config, e_tag = validation_mgr.validate_update_delete_streaming_distribution_parameters(alias, streaming_distribution_id,
                                                                                                                           config, e_tag)

    if tagging:
        arn = validation_mgr.validate_tagging_arn(
            arn, alias, distribution_id, streaming_distribution_id)
    if has_tags:
        valid_tags = validation_mgr.validate_tags(tags)
    if untag_resource:
        valid_tag_keys = validation_mgr.validate_list_without_quantity(tag_keys)

    if config_required:
        config = helpers.pascal_dict_to_snake_dict(config, True)

    if create_update_distribution or create_update_streaming_distribution or duplicate:
        config = validation_mgr.validate_common_distribution_parameters(config, enabled, aliases, logging,
                                                                        price_class, comment, create_update_streaming_distribution)

    if create_update_distribution or validate:
        valid_origins = validation_mgr.validate_origins(
            origins, default_origin_domain_name, default_origin_access_identity,
            default_origin_path, create_update_streaming_distribution, create_distribution)
        config = helpers.merge_validation_into_config(config, valid_origins, 'origins')
        config_origins = config.get('origins')
        valid_cache_behaviors = validation_mgr.validate_cache_behaviors(
            cache_behaviors, config_origins)
        config = helpers.merge_validation_into_config(
            config, valid_cache_behaviors, 'cache_behaviors')
        valid_default_cache_behavior = validation_mgr.validate_cache_behavior(
            default_cache_behavior, config_origins, True)
        config = helpers.merge_validation_into_config(
            config, valid_default_cache_behavior, 'default_cache_behavior')
        valid_custom_error_responses = validation_mgr.validate_custom_error_responses(
            custom_error_responses)
        config = helpers.merge_validation_into_config(
            config, valid_custom_error_responses, 'custom_error_responses')
        valid_restrictions = validation_mgr.validate_restrictions(restrictions)
        config = helpers.merge_validation_into_config(config, valid_restrictions, 'restrictions')
        config = validation_mgr.validate_distribution_config_parameters(config, default_root_object,
                                                                        is_ipv6_enabled, http_version, web_acl_id)
        valid_viewer_certificate = validation_mgr.validate_viewer_certificate(viewer_certificate)
        config = helpers.merge_validation_into_config(
            config, valid_viewer_certificate, 'viewer_certificate')
    elif create_update_streaming_distribution or validate:
        config = validation_mgr.validate_streaming_distribution_config_parameters(config, comment, trusted_signers,
                                                                                  s3_origin, default_s3_origin_domain_name,
                                                                                  default_s3_origin_origin_access_identity)
    if(create_distribution or create_streaming_distribution or duplicate_distribution or
            duplicate_streaming_distribution or validate):
        config = validation_mgr.validate_caller_reference_for_distribution(config, caller_reference)

    if config_required:
        config = helpers.snake_dict_to_pascal_dict(config)

    if create_invalidation:
        valid_invalidation_batch = validation_mgr.validate_invalidation_batch(
            invalidation_batch, caller_reference)
        valid_invalidation_batch = helpers.snake_dict_to_pascal_dict(valid_invalidation_batch)

    if create_origin_access_identity:
        result = service_mgr.create_origin_access_identity(caller_reference, comment)
    elif delete_origin_access_identity:
        result = service_mgr.delete_origin_access_identity(origin_access_identity_id, e_tag)
    elif update_origin_access_identity:
        result = service_mgr.update_origin_access_identity(
            caller_reference, comment, origin_access_identity_id, e_tag)
    elif create_invalidation:
        result = service_mgr.create_invalidation(distribution_id, valid_invalidation_batch)
    elif generate_presigned_url_from_pem_private_key:
        validated_pem_expire_date = validation_mgr.validate_presigned_url_pem_expire_date(
            presigned_url_pem_expire_date)
        result = service_mgr.generate_presigned_url_from_pem_private_key(distribution_id, presigned_url_pem_private_key_path,
                                                                         presigned_url_pem_private_key_password,
                                                                         presigned_url_pem_url, validated_pem_expire_date)
    elif create_distribution or duplicate_distribution:
        result = service_mgr.create_distribution(config, valid_tags)
    elif delete_distribution:
        result = service_mgr.delete_distribution(distribution_id, e_tag)
    elif update_distribution:
        result = service_mgr.update_distribution(config, distribution_id, e_tag)
    elif create_streaming_distribution or duplicate_streaming_distribution:
        result = service_mgr.create_streaming_distribution(config, valid_tags)
    elif delete_streaming_distribution:
        result = service_mgr.delete_streaming_distribution(streaming_distribution_id, e_tag)
    elif update_streaming_distribution:
        result = service_mgr.update_streaming_distribution(config, streaming_distribution_id, e_tag)
    elif validate:
        result = {'validation_result': 'OK'}
    elif tag_resource:
        result = service_mgr.tag_resource(arn, valid_tags)
    elif untag_resource:
        result = service_mgr.untag_resource(arn, valid_tag_keys)

    module.exit_json(changed=(not validate), **helpers.pascal_dict_to_snake_dict(result))


if __name__ == '__main__':
    main()
