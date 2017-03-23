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
                    CloudFrontOriginAccessIdentityConfig = {
                        "CallerReference": caller_reference,
                        "Comment": comment
                        },
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

    def generate_signed_url_from_pem_private_key(self, distribution_id, private_key_string, url, expire_date):
        try:
            cloudfront_signer = CloudFrontSigner(key_id, rsa_signer)
            signed_url = cloudfront_signer.generate_presigned_url(url, date_less_than=expire_date)
            return {"presigned_url": signed_url }
        except Exception as e:
            self.module.fail_json(msg="Error generating signed url from pem private key - " + str(e),
                    exception=traceback.format_exc())

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

    def delete_distribution(self, distribution_id, e_tag):
        try:
            func = partial(self.client.delete_distribution, Id = distribution_id,
                    IfMatch=e_tag)
            return self.paginated_response(func)
        except Exception as e:
            self.module.fail_json(msg="Error deleting distribution - " + str(e),
                    exception=traceback.format_exc())

    def update_distribution(self, config, distribution_id, e_tag):
        try:
            func = partial(self.client.update_distribution, DistributionConfig=config,
                    Id = distribution_id, IfMatch=e_tag)
            return self.paginated_response(func)
        except Exception as e:
            self.module.fail_json(msg="Error updating distribution - " + str(e),
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

    def delete_streaming_distribution(self, streaming_distribution_id, e_tag):
        try:
            func = partial(self.client.delete_streaming_distribution, Id = streaming_distribution_id,
                    IfMatch=e_tag)
            return self.paginated_response(func)
        except Exception as e:
            self.module.fail_json(msg="Error deleting streaming distribution - " + str(e),
                    exception=traceback.format_exc())
    
    def update_streaming_distribution(self, config, streaming_distribution_id, e_tag):
        try:
            func = partial(self.client.update_streaming_distribution, StreamingDistributionConfig=config,
                    Id = streaming_distribution_id, IfMatch=e_tag)
            return self.paginated_response(func)
        except Exception as e:
            self.module.fail_json(msg="Error updating streaming distribution - " + str(e),
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

    def validate_aliases(self, aliases, alias):
        if sum(map(bool, [aliases, alias])) > 1:
            self.module.fail_json(msg="Error: both aliases and alias are defined. Please specify only one.")
        if alias:
            aliases = [ alias ]
        if aliases:
            return {
                    "Quantity": len(alias_list),
                    "Items": alias_list
                    }
        return None

    def validate_logging(self, logging, streaming):
        if logging is None:
            return None
        if logging and not streaming and (logging["enabled"] is None or logging["include_cookies"] is None or logging["bucket"] is None or logging["prefix"]):
            self.module.fail_json(msg="the logging a parameters enabled, include_cookies, bucket and prefix must be specified")
        if logging and streaming and (logging["enabled"] is None logging["bucket"] is None or logging["prefix"]):
            self.module.fail_json(msg="the logging a parameters enabled, bucket and prefix must be specified")
        valid_logging = {
            "Enabled": logging["enabled"],
            "Bucket": logging["bucket"],
            "Prefix": logging["prefix"]
            }
        if not streaming:
            valid_logging["IncludeCookies"] = logging["include_cookies"]
        return valid_logging

    def validate_origins(self, origins):
        quantity = len(origins)
        if quantity > 0:
            for origin in origins:
                if origin["domain_name"] is None:
                    self.module.fail_msg(msg="domain_name must be specified for an origin as a minimum")
                if origin["id"] is None:
                    origin["id"] = self.generate_datetime_string()
                if origin["custom_headers"] and streaming:
                    self.module.fail_json(msg="custom headers have been specified for a streaming distribution. " +
                            "custom headers are for web distributions only")
                if origin["custom_headers"]:
                    custom_headers_quantity = len(origin["custom_headers"])
                    if custom_headers_quantity > 0:
                        for custom_header in custom_headers:
                            if custom_header["header_name"] is None or custom_header["header_value"] is None:
                                self.module.fail_json(msg="both header name and header value must be specified")
                if ".s3.awsamazon.com" in origin["domain_name"]:
                    if origin["s3_origin_config"] is None or origin["s3_origin_config"]["origin_access_identity"] is None:
                        origin["s3_origin_config"]["origin_access_identity"] = ""
                if origin["custom_origin_config"]:
                    if origin["http_port"] is None or origin["https_port"] is None or origin["origin_protocol_policy"] is None:
                        self.module.fail_json(msg="http_port, https_port and origin_protocol_policy must be defined")
                    if origin["origin_ssl_protocols"] is not None and origin["origin_ssl_protocols"]["items"] is None:
                        self.module.fail_json(msg="list of origin_ssl_protocols must be defined")
            return origins
        return None:

    def validate_trusted_signers(self, trusted_signers):
        if trusted_signers:
            if 'enabled' not in trusted_signers:
                trusted_signers["enabled"] = true
            if 'items' not in trusted_signers:
                trusted_signers["items"] = []
            return {
                "Enabled": trusted_signers["enabled"],
                "Quantity": len(trusted_signers["items"]),
                "Items": trusted_signers["items"]
                }
        return None

    def validate_s3_origin(self, s3_origin):
        if s3_origin:
            if 'domain_name' not in s3_origin:
                self.module.fail_json("domain_name must be specified for s3_origin")
            if 'origin_access_identity' not in s3_origin:
                self.module.fail_json("origin_access_identity must be specified for s3_origin")
            return {
                "DomainName": s3_origin["domain_name"],
                "OriginAccessIdentity": s3_origin["origin_access_identity"]
                }
        return None

    def validate_viewer_certificate(self, viewer_certificate):
        #TODO:
        return None

    def validate_update_or_delete_distribution_parameters(self, alias, distribution_id, config, e_tag):
        if distribution_id is None and alias is None:
            self.module.fail_json(msg="Error: distribution_id or alias must be specified for updating or deleting a distribution.")
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

    def generate_datetime_string():
        return datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")

# TODO: validate delete parameters
#       more validation of update parameters - CallerReference and S3Origin and Origins
#       validate required create parameters  


def main():
    argument_spec = ec2_argument_spec()

    argument_spec.update(dict(
        create_origin_access_identity=dict(required=False, default=False, type='bool'),
        caller_reference=dict(required=False, default=None, type='str'),
        comment=dict(required=False, default=None, type='str'),
        create_distribution=dict(required=False, default=False, type='bool'),
        delete_distribution=dict(required=False, default=False, type='bool'),
        update_distribution=dict(required=False, default=False, type='bool'),
        create_invalidation=dict(required=False, default=False, type='bool'),
        distribution_id=dict(required=False, default=None, type='str'),
        streaming_distribution_id=dict(required=False, default=None, type='str'),
        invalidation_batch=dict(required=False, default=None, type='str'),
        create_streaming_distribution=dict(required=False, default=False, type='bool'),
        delete_streaming_distribution=dict(required=False, default=False, type='bool'),
        update_streaming_distribution=dict(required=False, default=False, type='bool'),
        delete_origin_access_identity=dict(required=False, default=False, type='bool'),
        origin_access_identity_id=dict(required=False, default=None, type='str'),
        e_tag=dict(required=False, default=None, type='str'),
        generate_presigned_url=dict(required=False, default=False, type='bool'),
        generate_s3_presigned_url=dict(required=False, default=False, type='bool'),
        client_method=dict(required=False, default=None, type='str'),
        s3_bucket_name=dict(required=False, default=None, type='str'),
        s3_key_name=dict(required=False, default=None, type='str'),
        expires_in=dict(required=False, default=3600, type='int'),
        http_method=dict(required=False, default=None, type='str'),
        tag_resource=dict(required=False, default=False, type='bool'),
        untag_resource=dict(required=False, default=False, type='bool'),
        update_origin_access_identity=dict(required=False, default=False, type='bool'),
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
        generate_signed_url_from_pem_private_key=dict(required=False, default=False, type='bool'),
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
    logging_enabled = module.params.get('logging_enabled')
    logging_include_cookies = module.params.get('logging_include_cookies')
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

    valid_aliases = service_mgr.validate_aliases(aliases, alias)
    valid_logging = service_mgr.validate_logging(logging)
    valid_origins = service_mgr.validate_origins(origins)
    valid_trusted_signers = service_mgr.validate_trusted_signers(trusted_signers)
    valid_s3_origin = service_mgr.validate_s3_origin(s3_origin)
    valid_viewer_certificate = service_mgr.validate_viewer_certificate(viewer_certificate)

    if update_distribution or delete_distribution:
        distribution_id, config, e_tag = service_mgr.validate_update_or_delete_distribution_parameters(alias,
                distribution_id, config, e_tag)

    if update_streaming_distribution or delete_streaming_distribution:
        streaming_distribution_id, config, e_tag = service_mgr.validate_update_or_delete_streaming_distribution_parameters(alias,
                streaming_distribution_id, config, e_tag)

    default_datetime_string = service_mgr.generate_datetime_string()

    if create_distribution:
        if config is None:
            config = {}
        if valid_origins is None:
            if ".s3.amazonaws.com" not in default_origin_domain_name:
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
        if default_cache_behavior is None:
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
        config["DefaultRootObject"] = default_root_object
        config["IsIPV6Enabled"] = is_ipv6_enabled
        if http_version:
            config["HttpVersion"] = http_version
        if comment is None:
            config["Comment"] = "distribution created by ansible with datetime " + default_datetime_string
    elif create_streaming_distribution:
        if config is None:
            config = {}
        if comment is None:
            config["Comment"] = "streaming distribution created by ansible with datetime " + default_datetime_string
        if valid_trusted_signers is None:
            config["TrustedSigners"] = {
                    "Enabled": False,
                    "Quantity": 0
                }
        else:
            config["TrustedSigners"] = valid_trusted_signers
        if create_streaming_distribution:
            if valid_s3_origin:
                config["S3Origin"] = valid_s3_origin
            else:
                config["S3Origin"] = {
                    "DomainName": s3_origin_domain_name,
                    "OriginAccessIdentity": s3_origin_origin_access_identity
                }
    if distribution or streaming_distribution:
        config["Enabled"] = enabled
        if valid_aliases:
            config["Aliases"] = valid_aliases
        if valid_logging:
            config["Logging"] = valid_logging
        if price_class:
            config["PriceClass"] = price_class
        if comment:
            config["Comment"] = comment
    if create_distribution or create_streaming_distribution:
        if caller_reference:
            config["CallerReference"] = caller_reference
        else:
            config["CallerReference"] = default_datetime_string

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
