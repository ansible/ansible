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
        - The id of the CloudFront distribution. Used with distribution, distribution_config,
          invalidation, streaming_distribution, streaming_distribution_config, list_invalidations.
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
import datetime

class CloudFrontServiceManager:
    """Handles CloudFront Services"""

    def __init__(self, module):
        self.module = module
        self.create_client('cloudfront')

    def create_client(self, resource):
        try:
            region, ec2_url, aws_connect_kwargs = get_aws_connection_info(self.module, boto3=True)
            self.client = boto3_conn(self.module, conn_type='client', resource=resource,
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
                    exception=traceback.format_exc())

    def generate_presigned_url(self, client_method, params, expires_in, http_method):
        try:
            func = partial(self.client.generate_presigned_url, ClientMethod = client_method,
                    Params=params, ExpiresIn=expires_in, HttpMethod=http_method)
            return self.paginated_response(func)
        except Exception as e:
            self.module.fail_json(msg="Error generating presigned url - " + str(e),
                    exception=traceback.format_exc())

    def generate_s3_presigned_url(self, client_method, s3_bucket_name, s3_key_name, expires_in, http_method):
        try:
            self.create_client('s3')
            params = { "Bucket": s3_bucket_name, "Key": s3_key_name }
            response = self.client.generate_presigned_url(client_method, Params=params,
                    ExpiresIn=expires_in, HttpMethod=http_method)
            return { "presigned_url": response }
        except Exception as e:
            self.module.fail_json(msg="Error generating s3 presigned url - " + str(e),
                    exception=traceback.format_exc())

    def create_distribution(self, config, tags):
        try:
            if tags is None:
                func = partial(self.client.create_distribution, DistributionConfig=config)
            else:
                distribution_config_with_tags = {}
                distribution_config_with_tags["DistributionConfig"] = config
                distribution_config_with_tags["Tags"] = tags
                func = partial(self.client.create_disribution_with_tags,
                        DistributionConfigWithTags=distribution_config_with_tags)
            return self.paginated_response(func)
        except Exception as e:
            self.module.fail_json(msg="Error creating distribution - " + str(e),
                    exception=traceback.format_exc())

    def create_streaming_distribution(self, config, tags):
        try:
            if tags is None:
                func = partial(self.client.create_streaming_distribution, StreamingDistributionConfig=config)
            else:
                streaming_distribution_config_with_tags["StreamingDistributionConfig"] = config
                streaming_distribution_config_with_tags["Tags"] = tags
                func = partial(self.client.create_streaming_disribution_with_tags, 
                        StreamingDistributionConfigWithTags=streaming_distribution_config_with_tags)
            return self.paginated_response(func)
        except Exception as e:
            self.module.fail_json(msg="Error creating streaming distribution - " + str(e),
                    exception=traceback.format_exc())
    
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

    def validate_aliases(self, aliases, alias_list):
        if(aliases is not None and alias_list is not None):
            self.module.fail_json(msg="Error: aliases and alias_list parameters are both defined. Please specify only one.")
        if(aliases is not None):
            return aliases
        if(alias_list is not None):
            return {
                    "Quantity": len(alias_list),
                    "Items": alias_list
                    }
        return None

    def validate_logging(self, logging, enabled, include_cookies, s3_bucket_name, s3_bucket_prefix, streaming):
        if(logging is not None and (s3_bucket_name is not None or s3_bucket_prefix is not None):
            self.module.fail_json(msg="Error: the logging and logging_* parameters are both defined. Please specify either logging or all logging_ parameters."
        if(include_cookies is not None and streaming):
            self.module.fail_json(msg="Error: logging_include_cookies has been defined for a streaming distribution"
        if(logging is not None):
            return logging
        if(s3_bucket_name is None):
            return None
        valid_logging = {
            "Enabled": enabled,
            "Bucket": s3_bucket_name,
            "Prefix": s3_bucket_prefix
            }
        if(not streaming):
            valid_logging["IncludeCookies"] = include_cookies
        return valid_logging

    def validate_origins(self, origins, origin_list):
        if(origins is not None and origin_list is not None):
            self.module.fail_json(msg="Error: the origins and origins_list parameters are both defined. Please specify only one.")
        if(origins is not None):
            return origins
        if(origin_list is not None):
            return {
                "Quantity": len(origin_list),
                "Items": origin_list
                }
        return None

def generate_datetime_string():
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")

def main():
    argument_spec = ec2_argument_spec()

    argument_spec.update(dict(
        create_origin_access_identity=dict(required=False, default=False, type='bool'),
        caller_reference=dict(required=False, default=None, type='str'),
        comment=dict(required=False, default=None, type='str'),
        create_distribution=dict(required=False, default=False, type='bool'),
        create_invalidation=dict(required=False, default=False, type='bool'),
        distribution_id=dict(required=False, default=None, type='str'),
        invalidation_batch=dict(required=False, default=None, type='str'),
        create_streaming_distribution=dict(required=False, default=False, type='bool'),
        delete_origin_access_identity=dict(required=False, default=False, type='bool'),
        origin_access_identity_id=dict(required=False, default=None, type='str'),
        e_tag=dict(required=False, default=None, type='str'),
        delete_distribution=dict(required=False, default=False, type='bool'),
        delete_streaming_distribution=dict(required=False, default=False, type='bool'),
        generate_s3_presigned_url=dict(required=False, default=False, type='bool'),
        client_method=dict(required=False, default=None, type='str'),
        s3_bucket_name=dict(required=False, default=None, type='str'),
        s3_key_name=dict(required=False, default=None, type='str'),
        expires_in=dict(required=False, default=3600, type='int'),
        http_method=dict(required=False, default=None, type='str'),
        tag_resource=dict(required=False, default=False, type='bool'),
        untag_resource=dict(required=False, default=False, type='bool'),
        update_origin_access_identity=dict(required=False, default=False, type='bool'),
        update_distribution=dict(required=False, default=False, type='bool'),
        update_streaming_distribution=dict(required=False, default=False, type='bool'),
        config=dict(required=False, default=None, type='json'),
        tags=dict(required=False, default=None, type='str'),
        aliases=dict(required=False, default=None, type='json'),
        aliases_list=dict(required=False, default=None, type='list'),
        default_root_object=dict(required=False, default=None, type='str'),
        origins=dict(required=False, default=None, type='json'),
        origin_list=dict(required=False, default=None, type='list'),
        default_cache_behavior=dict(required=False, default=None, type='json'),
        cache_behaviors=dict(required=False, default=None, type='json'),
        custom_error_responses=dict(required=False, default=None, type='json'),
        logging=dict(required=False, default=None, type='json'),
        logging_enabled=dict(required=False, default=False, type='bool'),
        logging_include_cookies=dict(required=False, default=False, type='bool'),
        logging_s3_bucket_name=dict(required=False, default=None, type='str'),
        logging_s3_bucket_prefix=dict(required=False, default=None, type='str'),
        price_class=dict(required=False, default=None, type='str'),
        enabled=dict(required=False, default=False, type='bool'),
        viewer_certificate=dict(required=False, default=None, type='json'),
        restrictions=dict(required=False, default=None, type='json'),
        web_acl=dict(required=False, default=None, type='str'),
        http_version=dict(required=False, default=None, type='str'),
        is_ipv6_enabled=dict(required=False, default=False, type='bool'),
        s3_origin=dict(required=False, default=None, type='json'),
        trusted_signers=dict(required=False, default=None, type='json'),
        default_origin_domain_name=dict(required=False, default=None, type='str'),
        default_origin_path=dict(required=False, default='', type='str'),
        default_origin_access_identity=dict(required=False, default='', type='str'),
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
    generate_presigned_url = module.params.get('generate_presigned_url')
    client_method = module.params.get('client_method')
    s3_bucket_name = module.params.get('s3_bucket_name')
    s3_key_name = module.params.get('s3_key_name')
    expires_in = module.params.get('expires_in')
    http_method = module.params.get('http_method')
    create_distribution = module.params.get('create_distribution')
    create_streaming_distribution = module.params.get('create_streaming_distribution')
    config = module.params.get('config')
    tags = module.params.get('tags')
    create_invalidation = module.params.get('create_invalidation')
    distribution_id = module.params.get('distribution_id')
    invalidation_batch = module.params.get('invalidation_batch')
    aliases = module.params.get('aliases')
    alias_list = module.params.get('alias_list')
    default_root_object = module.params.get('default_root_object')
    origins = module.params.get('origins')
    origin_list = mdule.params.get('origin_list')
    default_cache_behavior = module.params.get('default_cache_behavior')
    cache_behaviors = module.params.get('cache_behaviors')
    custom_error_responses = module.params.get('custom_error_responses')
    comment = module.params.get('comment')
    logging = module.params.get('logging')
    logging_enabled = module.params.get('logging_enabled')
    logging_include_cookies = module.params.get('logging_enabled')
    logging_s3_bucket_name = module.params.get('logging_s3_bucket_name')
    logging_s3_bucket_prefix = module.params.get('logging_s3_bucket_prefix')
    price_class = module.params.get('price_class')
    enabled = module.params.get('enabled')
    viewer_certificate = module.params.get('viewer_certificate')
    restrictions = module.params.get('restrictions')
    web_acl = module.params.get('web_acl')
    http_version = module.params.get('http_version')
    is_ipv6_enabled = module.params.get('is_ipv6_enabled')
    s3_origin = module.params.get('s3_origin')
    trusted_signers = module.params.get('trusted_signers')
    default_origin_domain_name = module.params.get('default_origin_domain_name')
    default_origin_path = module.params.get('default_origin_path')
    default_origin_access_identity = module.params.get('default_origin_access_identity')

    valid_aliases = service_mgr.validate_aliases(aliases, alias_list)
    valid_logging = service.mgr_validate_logging(logging, logging_enabled, logging_include_cookies,
            logging_s3_bucket_name, logging_s3_bucket_prefix, create_streaming_distribution)
    valid_origins = service.mgr_validate_origins(origins, origin_list)

    default_datetime_string = generate_datetime_string()

    # if no config exists, set all required defaults and add all to object
    # if config exists, add all non-None to config
    
    # miniumum requirements for a distribution are a domain name and an id
    # set defaults for all required objects
    if(create_distribution):
        if(config is None):
            config = {}
            if(caller_reference is None):
                config["CallerReference"] = default_datetime_string
            if(valid_origins is None):
                if(".s3.amazonaws.com" not in default_origin_domain_name):
                    config["Origins"] = {
                            "Quantity": 1,
                                "Items": [ {
                                    "CustomHeaders": { "Quantity": 0 },
                                    "CustomOriginConfig": {
                                        "HTTPPort": 80,
                                        "HTTPSPort": 443,
                                        "OriginProtocolPolicy": "match-viewer",
                                        "OriginSslProtocols": {
                                            "Items": [
                                                "TLSv1",
                                                "TLSv1.1",
                                                "TLSv1.2"
                                            ],
                                            "Quantity": 3
                                        }
                                    },
                                    "DomainName": default_origin_domain_name,
                                    "Id": default_datetime_string,
                                    "OriginPath": default_origin_path
                            } ]
                        }
                else:
                    config["Origins"] = {
                            "Quantity": 1,
                                "Items": [ {
                                    "DomainName": default_origin_domain_name,
                                    "Id": default_datetime_string,
                                    "OriginPath": default_origin_path,
                                    "S3OriginConfig": {
                                        "OriginAccessIdentity": default_origin_access_identity
                                    }
                                } ]
                            }
            if(default_cache_behavior is None):
                config["DefaultCacheBehavior"] = {
                        "MinTTL": 0,
                        "TrustedSigners": {
                            "Enabled": False,
                            "Quantity": 0
                        },
                        "TargetOriginId": default_datetime_string,
                        "Compress": False,
                        "ViewerProtocolPolicy": "allow-all",
                        "ForwardedValues": {
                            "Headers": { "Quantity": 0 },
                            "Cookies": { "Forward": "none" },
                            "QueryStringCacheKeys": { "Quantity": 0 },
                            "QueryString": True
                        },
                        "MaxTTL": 31536000,
                        "SmoothStreaming": False,
                        "LambdaFunctionAssociations": { "Quantity": 0 }
                    }
            if(comment is None):
                config["Comment"] = "distribution created by ansible with datetime string: " + default_datetime_string
    elif(create_streaming_distribution):
        if(config is None):
            config = {}
            if(caller_reference is None):
                caller_reference =  default_datetime_string
            if(s3_origin is None):
                s3_origin = {
                            "DomainName": default_origin_domain_name,
                            "OriginAccessIdentity": default_origin_access_identity
                        }
            if(comment is None):
                comment = "streaming distribution created by ansible with datetime string: " + generate_datetime_string()
            if(trusted_signers is None):
                trusted_signers = {
                            "Enabled": False,
                            "Quantity": 0
                        }
        if(caller_reference is not None):
            config["CallerReference"] = caller_reference
        if(s3_origin is not None):
            config["S3Origin"] = s3_origin
        if(comment is not None):
            config["Comment"] = comment

    if(create_distribution or create_streaming_distribution):
        config["Enabled"] = enabled
        if(valid_aliases is not None):
            config["Aliases"] = valid_aliases
        if(valid_logging is not None):
            config["Logging"] = valid_logging
        if(price_class is not None):
            config["PriceClass"] = price_class
    
    if(create_origin_access_identity):
        result=service_mgr.create_origin_access_identity(caller_reference, comment)
    elif(delete_origin_access_identity):
        result=service_mgr.delete_origin_access_identity(origin_access_identity_id, e_tag)
    elif(update_origin_access_identity):
        result=service_mgr.update_origin_access_identity(caller_reference, comment, origin_access_identity_id, e_tag)
    elif(create_invalidation):
        result=service_mgr.create_invalidation(distribution_id, invalidation_batch)
    elif(generate_s3_presigned_url):
        result=service_mgr.generate_s3_presigned_url(client_method, s3_bucket_name, s3_key_name, expires_in, http_method)
    elif(generate_presigned_url):
        result=service_mgr.generate_presigned_url(client_method, s3_bucket_name, s3_key_name, expires_in, http_method)
    elif(create_distribution):
        result=service_mgr.create_distribution(config, tags)
    elif(create_streaming_distribution):
        result=service_mgr.create_streaming_distribution(config, tags)

    module.exit_json(changed=True, **camel_dict_to_snake_dict(result))

if __name__ == '__main__':
    main()
