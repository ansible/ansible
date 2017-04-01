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
from ansible.modules.cloud.amazon.cloudfront_facts import CloudFrontFactsServiceManager 
from functools import partial
import json
import traceback
import datetime
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from botocore.signers import CloudFrontSigner

class CloudFrontServiceManager:
    """Handles CloudFront Services"""

    def __init__(self, module, cloudfront_facts_mgr):
        self.module = module
        self.cloudfront_facts_mgr = cloudfront_facts_mgr
        self.__default_http_port = 80
        self.__default_https_port = 443
        self.__default_origin_ssl_protocols = [ "TLSv1", "TLSv1.1", "TLSv1.2" ]
        self.__default_datetime_string = self.generate_datetime_string()
        self.__default_cache_behavior_min_ttl = 0
        self.__default_cache_behavior_max_ttl = 31536000
        self.__default_cache_behavior_trusted_signers_enabled = False
        self.__default_cache_behavior_compress = False
        self.__default_cache_behavior_viewer_protocol_policy = "allow-all"
        self.__default_cache_behavior_smooth_streaming = False
        self.__default_cache_behavior_forwarded_values_cookies = 'none'
        self.__default_cache_behavior_forwarded_values_query_string = True
        self.create_client('cloudfront')

    @property
    def default_datetime_string(self):
        return self.__default_datetime_string

    def create_client(self, resource):
        try:
            region, ec2_url, aws_connect_kwargs = get_aws_connection_info(self.module, boto3=True)
            self.client = boto3_conn(self.module, conn_type='client', resource=resource,
                    region=region, endpoint=ec2_url, **aws_connect_kwargs)
        except botocore.exceptions.NoRegionError:
            self.module.fail_json(msg = ("Region must be specified as a parameter, in "
                                         "AWS_DEFAULT_REGION environment variable or in "
                                         "boto configuration file") )
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Can't establish connection - " + str(e),
                    exception=traceback.format_exc(),
                    **camel_dict_to_snake_dict(e.response))

    def create_origin_access_identity(self, caller_reference, comment):
        try:
            func = partial(self.client.create_cloud_front_origin_access_identity, 
                    CloudFrontOriginAccessIdentityConfig =
                    { 'CallerReference': caller_reference, 'Comment': comment })
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error creating cloud front origin access identity - " + str(e), 
                    exception=traceback.format_exc(),
                    **camel_dict_to_snake_dict(e.response))

    def delete_origin_access_identity(self, origin_access_identity_id, e_tag):
        try:
            func = partial(self.client.delete_cloud_front_origin_access_identity,
                    Id=origin_access_identity_id, IfMatch=e_tag)
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error deleting cloud front origin access identity - " + str(e),
                    exception=traceback.format_exc(),
                    **camel_dict_to_snake_dict(e.response))

    def update_origin_access_identity(self, caller_reference, comment, origin_access_identity_id, e_tag):
        try:
            func = partial(self.client.update_cloud_front_origin_access_identity,
                    CloudFrontOriginAccessIdentityConfig = {
                        "CallerReference": caller_reference,
                        "Comment": comment
                        },
                    Id=origin_access_identity_id, IfMatch=e_tag)
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error updating cloud front origin access identity - " + str(e),
                    exception=traceback.format_exc(),
                    **camel_dict_to_snake_dict(e.response))
    
    def create_invalidation(self, distribution_id, invalidation_batch):
        try:
            func = partial(self.client.create_invalidation, DistributionId = distribution_id, 
                    InvalidationBatch=invalidation_batch)
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error creating invalidation(s) - " + str(e),
                    exception=traceback.format_exc(),
                    **camel_dict_to_snake_dict(e.response))

    def generate_presigned_url(self, client_method, params, expires_in, http_method):
        try:
            func = partial(self.client.generate_presigned_url, ClientMethod = client_method,
                    Params=params, ExpiresIn=expires_in, HttpMethod=http_method)
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error generating presigned url - " + str(e),
                    exception=traceback.format_exc(),
                    **camel_dict_to_snake_dict(e.response))

    def generate_signed_url_from_pem_private_key(self, distribution_id, private_key_string, url, expire_date):
        try:
            cloudfront_signer = CloudFrontSigner(key_id, rsa_signer)
            signed_url = cloudfront_signer.generate_presigned_url(url, date_less_than=expire_date)
            return {"presigned_url": signed_url }
        except Exception as e:
            self.module.fail_json(msg="Error generating signed url from pem private key - " + str(e),
                    exception=traceback.format_exc(),
                    **camel_dict_to_snake_dict(e.response))

    def rsa_signer(message, private_key_string):
        private_key = serialization.load_pem_private_key(
            private_key_string,
            password=None,
            backend=default_backend()
        )
        signer = private_key.signer(padding.PKCS1v15(), hashes.SHA1())
        signer.update(message)
        return signer.finalize()

    def generate_s3_presigned_url(self, client_method, s3_bucket_name, s3_key_name, expires_in, http_method):
        try:
            self.create_client('s3')
            params = { "Bucket": s3_bucket_name, "Key": s3_key_name }
            response = self.client.generate_presigned_url(client_method, Params=params,
                    ExpiresIn=expires_in, HttpMethod=http_method)
            return { "presigned_url": response }
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error generating s3 presigned url - " + str(e),
                    exception=traceback.format_exc(),
                    **camel_dict_to_snake_dict(e.response))

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
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error creating distribution - " + str(e),
                    exception=traceback.format_exc(),
                    **camel_dict_to_snake_dict(e.response))

    def delete_distribution(self, distribution_id, e_tag):
        try:
            func = partial(self.client.delete_distribution, Id = distribution_id,
                    IfMatch=e_tag)
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error deleting distribution - " + str(e),
                    exception=traceback.format_exc(),
                    **camel_dict_to_snake_dict(e.response))

    def update_distribution(self, config, distribution_id, e_tag):
        try:
            func = partial(self.client.update_distribution, DistributionConfig=config,
                    Id = distribution_id, IfMatch=e_tag)
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error updating distribution - " + str(e),
                    exception=traceback.format_exc(),
                    **camel_dict_to_snake_dict(e.response))

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
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error creating streaming distribution - " + str(e),
                    exception=traceback.format_exc(),
                    **camel_dict_to_snake_dict(e.response))

    def delete_streaming_distribution(self, streaming_distribution_id, e_tag):
        try:
            func = partial(self.client.delete_streaming_distribution, Id = streaming_distribution_id,
                    IfMatch=e_tag)
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error deleting streaming distribution - " + str(e),
                    exception=traceback.format_exc(),
                    **camel_dict_to_snake_dict(e.response))
    
    def update_streaming_distribution(self, config, streaming_distribution_id, e_tag):
        try:
            func = partial(self.client.update_streaming_distribution, StreamingDistributionConfig=config,
                    Id = streaming_distribution_id, IfMatch=e_tag)
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error updating streaming distribution - " + str(e),
                    exception=traceback.format_exc(),
                    **camel_dict_to_snake_dict(e.response))

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

    def validate_aliases(self, aliases, alias):
        if sum(map(bool, [aliases, alias])) > 1:
            self.module.fail_json(msg="both aliases and alias are defined. please specify only one.")
        if alias:
            aliases = [ alias ]
        if aliases:
            return self.python_list_to_aws_list(aliases)
        return None

    def python_list_to_aws_list(self, list_items=None):
        if list_items is None:
            list_items = []
        if not isinstance(list_items, list):
            self.module.fail_json(msg="expecting a list []. got a " + type(list_items).__name__ ) 
        result = {}
        result["quantity"] = len(list_items)
        result["items"] = list_items
        return result

    def validate_logging(self, logging, streaming):
        if logging is None:
            return None
        if logging and not streaming and (logging["enabled"] is None or logging["include_cookies"] is None or logging["bucket"] is None or logging["prefix"]):
            self.module.fail_json(msg="the logging parameters enabled, include_cookies, bucket and prefix must be specified")
        if logging and streaming and (logging["enabled"] is None or logging["bucket"] is None or logging["prefix"]):
            self.module.fail_json(msg="the logging parameters enabled, bucket and prefix must be specified")
        valid_logging["enabled"] = logging["enabled"]
        valid_logging["bucket"] = logging["bucket"]
        valid_logging["prefix"] = logging["prefix"]
        if not streaming:
            valid_logging["include_cookies"] = logging["include_cookies"]
        return valid_logging

    def validate_origins(self, origins, default_origin_domain_name, default_origin_access_identity, default_origin_path, streaming, create_distribution):
        valid_origins = {}
        if origins is None:
            origins = []
        quantity = len(origins)
        if quantity == 0 and default_origin_domain_name is None and create_distribution:
            self.module.fail_json(msg="origins and default_origin_domain_name have not been specified. please specify at least one.")
        if quantity > 0:
            for origin in origins:
                if origin.get("origin_path") is None:
                    origin["origin_path"] = default_origin_path
                if origin.get("domain_name") is None:
                    self.module.fail_json(msg="origins[].domain_name must be specified for an origin as a minimum")
                if origin.get("id") is None:
                    origin["id"] = self.generate_datetime_string()
                else:
                    origin["id"] = str(origin["id"])
                if origin.get("custom_headers") and streaming:
                    self.module.fail_json(msg="custom_headers has been specified for a streaming distribution. " +
                            "custom headers are for web distributions only")
                if origin.get("custom_headers"):
                    custom_headers_quantity = len(origin.get("custom_headers"))
                    if custom_headers_quantity > 0:
                        for custom_header in origin["custom_headers"]:
                            if custom_header.get("header_name") is None or custom_header.get("header_value") is None:
                                self.module.fail_json(msg="both origins[].custom_headers.header_name and origins[].custom_headers.header_value must be specified")
                        temp_custom_headers = origin.get("custom_headers")
                        origin["custom_headers"] = { "items": temp_custom_headers, "quantity": custom_headers_quantity }
                else:
                    origin["custom_headers"] = { "quantity": 0 }
                if ".s3.awsamazon.com" in origin.get("domain_name"):
                    if origin.get("s3_origin_config") is None or origin.get("s3_origin_config").get("origin_access_identity") is None:
                        origin["s3_origin_config"] = {}
                        origin["s3_origin_config"]["origin_access_identity"] = default_origin_access_identity
                else:
                    if origin.get("custom_origin_config") is None:
		        origin["custom_origin_config"] = {}
                    custom_origin_config = origin["custom_origin_config"]
		    if custom_origin_config.get("origin_protocol_policy") is None:
		        custom_origin_config["origin_protocol_policy"] = "match-viewer"
        		if custom_origin_config.get("http_port") is None:
        		    custom_origin_config["h_t_t_p_port"] = self.__default_http_port
                    else: 
		        custom_origin_config["h_t_t_p_port"] = origin["custom_origin_config"]["http_port"]
		        custom_origin_config.pop("http_port", None)
		    if custom_origin_config.get("https_port") is None:
		        custom_origin_config["h_t_t_p_s_port"] = self.__default_https_port
                    else:
		        custom_origin_config["h_t_t_p_s_port"] = custom_origin_config["https_port"]
		        custom_origin_config.pop("https_port", None)
                    if custom_origin_config.get("origin_ssl_protocols") is None:
		        temp_origin_ssl_protocols = self.__default_origin_ssl_protocols
                    temp_origin_ssl_protocols = custom_origin_config["origin_ssl_protocols"]
                    origin_ssl_protocols_quantity = len(temp_origin_ssl_protocols)
                    custom_origin_config["origin_ssl_protocols"] = { "items": temp_origin_ssl_protocols, "quantity": origin_ssl_protocols_quantity }
            return self.python_list_to_aws_list(origins)
        return None

    def validate_cache_behaviors(self, cache_behaviors, valid_origins):
        if cache_behaviors is None:
            cache_behaviors = []
        for cache_behavior in cache_behaviors:
            self.validate_cache_behavior(cache_behavior, valid_origins)
        return self.python_list_to_aws_list(cache_behaviors)

    def validate_cache_behavior(self, cache_behavior, valid_origins):
        if cache_behavior is None:
            cache_behavior = {}
        if 'min_ttl' not in cache_behavior:
            cache_behavior["min_t_t_l"] = self.__default_cache_behavior_min_ttl
        if 'max_ttl' not in cache_behavior:
            cache_behavior["max_t_t_l"] = self.__default_cache_behavior_max_ttl
        if 'compress' not in cache_behavior:
            cache_behavior["compress"] = self.__default_cache_behavior_compress
        trusted_signers = cache_behavior.get("trusted_signers")
        if trusted_signers is None:
            cache_behavior["trusted_signers"] = { "enabled": self.__default_cache_behavior_trusted_signers_enabled, "quantity": 0 }
        else:
            if 'enabled' in cache_behavior["trusted_signers"]:
                temp_enabled = cache_behavior["trusted_signers"]["enabled"]
            else:
                temp_enabled = self.__default_cache_behavior_trusted_signers_enabled
            cache_behavior["trusted_signers"] = self.python_list_to_aws_list(trusted_signers)
            cache_behavior["enabled"] = temp_enabled
        if 'target_origin_id' not in cache_behavior:
            cache_behavior["target_origin_id"] = self.get_first_origin_id_for_default_cache_behavior(valid_origins)
        if 'forwarded_values' not in cache_behavior:
            cache_behavior["forwarded_values"] = {}
        forwarded_values = cache_behavior["forwarded_values"]
        if 'headers' not in forwarded_values:
            forwarded_values["headers"] = self.python_list_to_aws_list()
        if 'cookies' not in forwarded_values:
            forwarded_values["cookies"] = { "forward": self.__default_cache_behavior_forwarded_values_cookies }
        if 'query_string_cache_keys' not in forwarded_values:
            forwarded_values["query_string_cache_keys"] = self.python_list_to_aws_list()
        if 'query_string' not in forwarded_values:
            forwarded_values["query_string"] = self.__default_cache_behavior_forwarded_values_query_string
        if 'allowed_methods' in cache_behavior:
            if 'items' not in cache_behavior["allowed_methods"]:
                self.module.fail_json(msg="a list of items must be specified for allowed_methods")
            if 'cached_methods' in cache_behavior and not isinstance(cache_behavior.get("cached_methods"), list):
                self.module.fail_json(msg="allowed_methods.cached_methods must be a list")
        if 'lambda_function_associations' in cache_behavior:
            if not isinstance(cache_behavior["lambda_function_associations"], list):
                self.module.fail_json(msg="lambda_function_associations must be a list")
        else:
            cache_behavior["lambda_function_associations"] = self.python_list_to_aws_list()
        if 'viewer_protocol_policy' not in cache_behavior:
            cache_behavior["viewer_protocol_policy"] = self.__default_cache_behavior_viewer_protocol_policy
        if 'smooth_streaming' not in cache_behavior:
            cache_behavior["smooth_streaming"] = self.__default_cache_behavior_smooth_streaming

    def validate_custom_origin_configs(self, custom_origin_configs):
        if origin.get("custom_origin_config"):
            if(origin["custom_origin_config"].get("http_port") is None or origin["custom_origin_config"].get("https_port") is None 
                     or origin["custom_origin_config"].get("origin_protocol_policy") is None):
                self.module.fail_json(msg="http_port, https_port and origin_protocol_policy must all be specified")

    def validate_trusted_signers(self, trusted_signers):
        if trusted_signers:
            if 'enabled' not in trusted_signers:
                trusted_signers["enabled"] = True
            if 'items' not in trusted_signers:
                trusted_signers["items"] = []
            valid_trusted_signers = self.python_list_to_aws_list(trusted_signers["items"])
            valid_trusted_signers["enabled"] = trusted_signers["enabled"]
            return valid_trusted_signers
        return None

    def validate_s3_origin(self, s3_origin):
        if s3_origin:
            if 'domain_name' not in s3_origin:
                self.module.fail_json("domain_name must be specified for s3_origin")
            if 'origin_access_identity' not in s3_origin:
                self.module.fail_json("origin_access_identity must be specified for s3_origin")
            return {
                "domain_name": s3_origin["domain_name"],
                "origin_access_identity": s3_origin["origin_access_identity"]
                }
        return None

    def validate_viewer_certificate(self, viewer_certificate):
        #TODO:
        return None

    def validate_update_or_delete_distribution_parameters(self, alias, distribution_id, config, e_tag):
        if distribution_id is None and alias is None:
            self.module.fail_json(msg="distribution_id or alias must be specified for updating or deleting a distribution.")
        if distribution_id is None:
            distribution_id = self.cloudfront_facts_mgr.get_distribution_id_from_domain_name(alias)
        if config is None:
            config = self.cloudfront_facts_mgr.get_distribution_config(distribution_id)["DistributionConfig"]
        if e_tag is None:
            e_tag = self.cloudfront_facts_mgr.get_etag_from_distribution_id(distribution_id, False)
        return distribution_id, config, e_tag
 
    def validate_update_or_delete_streaming_distribution_parameters(self, alias, streaming_distribution_id, config, e_tag):
        if streaming_distribution_id is None and alias is None:
            self.module.fail_json(msg="streaming_distribution_id or alias must be specified for updating or deleting a streaming distribution.")
        if streaming_distribution_id is None:
            streaming_distribution_id = self.cloudfront_facts_mgr.get_distribution_id_from_domain_name(alias)
        if config is None:
            config = self.cloudfront_facts_mgr.get_streaming_distribution_config(streaming_distribution_id)["StreamingDistributionConfig"]
        if e_tag is None:
            e_tag = self.cloudfront_facts_mgr.get_etag_from_distribution_id(streaming_distribution_id, True)
        return streaming_distribution_id, config, e_tag

    def generate_datetime_string(self):
        return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")

    def get_first_origin_id_for_default_cache_behavior(self, valid_origins):
        if valid_origins is None:
            return self.__default_datetime_string
        param_id = valid_origins["Items"][0].get("Id")
        if param_id is None:
            return self.__default_datetime_string
        return param_id

def snake_dict_to_pascal_dict(snake_dict):

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

def pascal_dict_to_snake_dict(pascal_dict, split_caps=False):

    def pascal_to_snake(name):
        import re
        first_cap_re = re.compile('(.)([A-Z][a-z]+)')
        all_cap_re = re.compile('([a-z0-9])([A-Z]+)')
        split_cap_re = re.compile('([A-Z])')
        s1 = first_cap_re.sub(r'\1\2', name)
        if split_caps:
            s2 = split_cap_re.sub(r'_\1', s1).lower().replace('_', '', 1)
        else:
            s2 = all_cap_re.sub(r'\1_\2', s1).lower()
        return s2

    def value_is_list(pascal_list):
        checked_list = []
        for item in pascal_list:
            if isinstance(item, dict):
                checked_list.append(pascal_dict_to_snake_dict(item, split_caps))
            elif isinstance(item, list):
                checked_list.append(value_is_list(item))
            else:
                checked_list.append(item)
        return checked_list

    snake_dict = {}

    for k, v in pascal_dict.items():
        if isinstance(v, dict):
            snake_dict[pascal_to_snake(k)] = pascal_dict_to_snake_dict(v, split_caps)
        elif isinstance(v, list):
            snake_dict[pascal_to_snake(k)] = value_is_list(v)
        else:
            snake_dict[pascal_to_snake(k)] = v

    return snake_dict

def main():
    argument_spec = ec2_argument_spec()

    argument_spec.update(dict(
        create_origin_access_identity=dict(required=False, default=False, type='bool'),
        update_origin_access_identity=dict(required=False, default=False, type='bool'),
        create_distribution=dict(required=False, default=False, type='bool'),
        delete_distribution=dict(required=False, default=False, type='bool'),
        update_distribution=dict(required=False, default=False, type='bool'),
        create_invalidation=dict(required=False, default=False, type='bool'),
        create_streaming_distribution=dict(required=False, default=False, type='bool'),
        delete_streaming_distribution=dict(required=False, default=False, type='bool'),
        update_streaming_distribution=dict(required=False, default=False, type='bool'),
        delete_origin_access_identity=dict(required=False, default=False, type='bool'),
        generate_presigned_url=dict(required=False, default=False, type='bool'),
        generate_s3_presigned_url=dict(required=False, default=False, type='bool'),
        generate_signed_url_from_pem_private_key=dict(required=False, default=False, type='bool'),
        origin_access_identity_id=dict(required=False, default=None, type='str'),
        caller_reference=dict(required=False, default=None, type='str'),
        comment=dict(required=False, default=None, type='str'),
        distribution_id=dict(required=False, default=None, type='str'),
        streaming_distribution_id=dict(required=False, default=None, type='str'),
        invalidation_batch=dict(required=False, default=None, type='str'),
        e_tag=dict(required=False, default=None, type='str'),
        client_method=dict(required=False, default=None, type='str'),
        s3_bucket_name=dict(required=False, default=None, type='str'),
        s3_key_name=dict(required=False, default=None, type='str'),
        expires_in=dict(required=False, default=3600, type='int'),
        http_method=dict(required=False, default=None, type='str'),
        tag_resource=dict(required=False, default=False, type='bool'),
        untag_resource=dict(required=False, default=False, type='bool'),
        config=dict(required=False, default=None, type='json'),
        tags=dict(required=False, default=None, type='str'),
        alias=dict(required=False, default=None, type='str'),
        aliases=dict(required=False, default=None, type='list'),
        default_root_object=dict(required=False, default='', type='str'),
        origins=dict(required=False, default=None, type='list'),
        default_cache_behavior=dict(required=False, default=None, type='dict'),
        cache_behaviors=dict(required=False, default=None, type='list'),
        custom_error_responses=dict(required=False, default=None, type='list'),
        logging=dict(required=False, default=None, type='dict'),
        price_class=dict(required=False, default=None, type='str'),
        enabled=dict(required=False, default=False, type='bool'),
        viewer_certificate=dict(required=False, default=None, type='dict'),
        restrictions=dict(required=False, default=None, type='json'),
        restrictions_restriction_type=dict(required=False, default=None, type='str'),
        restrictions_items=dict(required=False, default=None, type='list'),
        web_acl=dict(required=False, default=None, type='str'),
        http_version=dict(required=False, default=None, type='str'),
        is_ipv6_enabled=dict(required=False, default=False, type='bool'),
        s3_origin=dict(required=False, default=None, type='json'),
        trusted_signers=dict(required=False, default=None, type='list'),
        default_origin_domain_name=dict(required=False, default=None, type='str'),
        default_origin_path=dict(required=False, default='', type='str'),
        default_origin_access_identity=dict(required=False, default='', type='str'),
        signed_url_pem_private_key_string=dict(required=False, default=None, type='str'),
        signed_url_url=dict(required=False, default=None, type='str'),
        signed_url_expire_date=dict(required=False, default=None, type='str')
    ))

    result = {}

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required')

    cloudfront_facts_mgr = CloudFrontFactsServiceManager(module)
    service_mgr = CloudFrontServiceManager(module, cloudfront_facts_mgr)
    
    create_origin_access_identity = module.params.get('create_origin_access_identity')
    caller_reference = module.params.get('caller_reference')
    comment = module.params.get('comment')
    delete_origin_access_identity = module.params.get('delete_origin_access_identity')
    origin_access_identity_id = module.params.get('origin_access_identity_id')
    e_tag = module.params.get('e_tag')
    update_origin_access_identity = module.params.get('update_origin_access_identity')
    origin_access_identity_id = module.params.get('origin_access_identity_id')
    generate_presigned_url = module.params.get('generate_presigned_url')
    generate_s3_presigned_url = module.params.get('generate_s3_presigned_url')
    generate_signed_url_from_pem_private_key = module.params.get('generate_signed_url_from_pem_private_key')
    client_method = module.params.get('client_method')
    s3_bucket_name = module.params.get('s3_bucket_name')
    s3_key_name = module.params.get('s3_key_name')
    expires_in = module.params.get('expires_in')
    http_method = module.params.get('http_method')
    create_distribution = module.params.get('create_distribution')
    delete_distribution = module.params.get('delete_distribution')
    update_distribution = module.params.get('update_distribution')
    create_streaming_distribution = module.params.get('create_streaming_distribution')
    delete_streaming_distribution = module.params.get('delete_streaming_distribution')
    update_streaming_distribution = module.params.get('update_streaming_distribution')
    config = module.params.get('config')
    tags = module.params.get('tags')
    create_invalidation = module.params.get('create_invalidation')
    distribution_id = module.params.get('distribution_id')
    streaming_distribution_id = module.params.get('streaming_distribution_id')
    invalidation_batch = module.params.get('invalidation_batch')
    alias = module.params.get('alias')
    aliases = module.params.get('aliases')
    alias_list = module.params.get('alias_list')
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
    web_acl = module.params.get('web_acl')
    http_version = module.params.get('http_version')
    is_ipv6_enabled = module.params.get('is_ipv6_enabled')
    s3_origin = module.params.get('s3_origin')
    trusted_signers = module.params.get('trusted_signers')
    default_origin_domain_name = module.params.get('default_origin_domain_name')
    default_origin_path = module.params.get('default_origin_path')
    default_origin_access_identity = module.params.get('default_origin_access_identity')
    signed_url_pem_private_key_string = module.params.get('signed_url_pem_private_key_string')
    signed_url_url = module.params.get('signed_url_url')
    signed_url_expire_date = module.params.get('signed_url_expire_date')

    distribution = create_distribution or update_distribution
    streaming_distribution = create_streaming_distribution or update_streaming_distribution

    if sum(map(bool, [create_origin_access_identity, delete_origin_access_identity, update_origin_access_identity,
            generate_presigned_url, generate_s3_presigned_url, create_distribution, delete_distribution,
            update_distribution, create_streaming_distribution, delete_streaming_distribution,
            update_streaming_distribution, generate_signed_url_from_pem_private_key])) > 1:
        module.fail_json(msg="more than one cloudfront action has been specified. please select only one action.")

    if update_distribution or delete_distribution:
        distribution_id, config, e_tag = service_mgr.validate_update_or_delete_distribution_parameters(alias,
                distribution_id, config, e_tag)

    if update_streaming_distribution or delete_streaming_distribution:
        streaming_distribution_id, config, e_tag = service_mgr.validate_update_or_delete_streaming_distribution_parameters(alias,
                streaming_distribution_id, config, e_tag)

    valid_aliases = service_mgr.validate_aliases(aliases, alias)
    valid_logging = service_mgr.validate_logging(logging, streaming_distribution)

    valid_origins = service_mgr.validate_origins(origins, default_origin_domain_name, default_origin_access_identity,
            default_origin_path, streaming_distribution, create_distribution)

    valid_cache_behaviors = service_mgr.validate_cache_behaviors(cache_behaviors, valid_origins)
    valid_default_cache_behavior = service_mgr.validate_cache_behavior(default_cache_behavior, valid_origins)

    # DefaultCacheBehavior
    # CacheBehaviors
    # CustomErrorResponses
    # Restrictions
    # ViewerCertificate
    # duplicate_distribution
    # duplicate streaming_distribution
    # check all required attributes
    # url signing
    # doc

    valid_trusted_signers = service_mgr.validate_trusted_signers(trusted_signers)
    valid_s3_origin = service_mgr.validate_s3_origin(s3_origin)
    valid_viewer_certificate = service_mgr.validate_viewer_certificate(viewer_certificate)

    if create_distribution:
        if config is None:
            config = {}
        config["default_root_object"] = default_root_object
        config["is_i_p_v_6_enabled"] = is_ipv6_enabled
        if http_version:
            config["http_version"] = http_version
        if comment is None:
            config["comment"] = "distribution created by ansible with datetime " + service_mgr.default_datetime_string
    elif create_streaming_distribution:
        if config is None:
            config = {}
        if comment is None:
            config["comment"] = "streaming distribution created by ansible with datetime " + service_mgr.default_datetime_string
        if valid_trusted_signers is None:
            config["trusted_signers"] = {
                    "enabled": False,
                    "quantity": 0
                }
        else:
            config["trusted_signers"] = valid_trusted_signers
        if create_streaming_distribution:
            if valid_s3_origin:
                config["s3_origin"] = valid_s3_origin
            else:
                config["s3_origin"] = {
                    "domain_name": s3_origin_domain_name,
                    "origin_access_identity": s3_origin_origin_access_identity
                }
    if distribution or streaming_distribution:
        config["enabled"] = enabled
        if valid_origins:
            config["origins"] = valid_origins
        if valid_aliases:
            config["aliases"] = valid_aliases
        if valid_logging:
            config["logging"] = valid_logging
        if price_class:
            config["price_class"] = price_class
        if comment:
            config["comment"] = comment
    if create_distribution or create_streaming_distribution:
        if caller_reference:
            config["caller_reference"] = caller_reference
        else:
            config["caller_reference"] = service_mgr.default_datetime_string

    config = snake_dict_to_pascal_dict(pascal_dict_to_snake_dict(config, True))

    if create_origin_access_identity:
        result=service_mgr.create_origin_access_identity(caller_reference, comment)
    elif delete_origin_access_identity:
        result=service_mgr.delete_origin_access_identity(origin_access_identity_id, e_tag)
    elif update_origin_access_identity:
        result=service_mgr.update_origin_access_identity(caller_reference, comment, origin_access_identity_id, e_tag)
    elif create_invalidation:
        result=service_mgr.create_invalidation(distribution_id, invalidation_batch)
    elif generate_s3_presigned_url:
        result=service_mgr.generate_s3_presigned_url(client_method, s3_bucket_name, s3_key_name, expires_in, http_method)
    elif generate_presigned_url:
        result=service_mgr.generate_presigned_url(client_method, s3_bucket_name, s3_key_name, expires_in, http_method)
    elif generate_signed_url_from_pem_private_key:
        result=service_mgr.generate_signed_url_from_pem_private_key(distribution_id, signed_url_pem_private_key_string,
                signed_url_url, signed_url_expire_date)
    elif create_distribution:
        result=service_mgr.create_distribution(config, tags)
    elif delete_distribution:
        result=service_mgr.delete_distribution(distribution_id, e_tag)
    elif update_distribution:
        result=service_mgr.update_distribution(config, distribution_id, e_tag)
    elif create_streaming_distribution:
        result=service_mgr.create_streaming_distribution(config, tags)
    elif delete_streaming_distribution:
        result=service_mgr.delete_streaming_distribution(streaming_distribution_id, e_tag)
    elif update_streaming_distribution:
        result=service_mgr.update_streaming_distribution(config, streaming_distribution_id, e_tag)

    module.exit_json(changed=True, **camel_dict_to_snake_dict(result))

if __name__ == '__main__':
    main()
