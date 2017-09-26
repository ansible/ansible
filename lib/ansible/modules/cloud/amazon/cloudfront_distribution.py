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

module: cloudfront_distribution

short_description: create, update and delete aws cloudfront distributions.

description:
    - Allows for easy creation, updating and deletion of CloudFront distributions.

requirements:
  - boto3 >= 1.0.0
  - python >= 2.6

version_added: "2.4"

author: Willem van Ketwich (@wilvk)

options:

    state:
      description:
        - The desired state of the distribution or streaming distribution.
          present - creates a new distribution or updates an existing distribution.
          absent - deletes an existing distribution.
      choices: ['present', 'absent']

    distribution_id:
      description:
        - The id of the cloudfront distribution. This parameter can be exchanged with I(alias) or I(caller_reference) and is used in conjunction with I(e_tag).
          Used with I(streaming_distribution=no)

    streaming_distribution_id:
      description:
        - The id of the CloudFront streaming distribution. This parameter can be exchanged with I(alias) and is used in conjunction with I(e_tag).
          Used with I(streaming_distribution=yes).

    e_tag:
      description:
        - A unique identifier of a modified or existing distribution. Used in conjunction with I(distribution_id) or I(streaming_distribution_id).
          Is determined automatically if not specified.

    generate_presigned_url:
      description:
        - Generates a presigned url for a distribution from a private C(.pem) file key.
      default: 'no'
      choices: ['yes', 'no']

    caller_reference:
      description:
        - A unique identifier for creating and updating cloudfront distributions. Each caller reference must be unique across all distributions. e.g. a caller
          reference used in a web distribution cannot be reused in a streaming distribution. This parameter can be used instead of I(distribution_id) or
          I(streaming_distribution_id) to reference an existing distribution. If not specified, this defaults to a datetime stamp of the format
          'YYYY-MM-DDTHH:MM:SS.ffffff'.

    pem_key_path:
      description:
        - The path on the host to the C(.pem) private key file. This key is used to sign the url.

    pem_key_password:
      description:
        - The optional password for the pem private key file.

    cloudfront_url_to_sign:
      description:
        - The cloudfront url to sign with the pem private key.

    presigned_url_expire_date:
      description:
        - The expiry date of the presigned url. Date format is 'YYYY-MM-DD'.

    config:
      description:
        - This is the main variable used for creating and updating distributions and streaming distributions. When used, it will be a complex data type as a
          dictionary that represents the config of the distribution. When used for creating a distribution, it must contain at least one origin in I(origins)
          or the parameter I(default_domain_name_origin) as a minimum.
          When used for creating a streaming distribution, it must contain either I(s3_origin) or I(default_s3_origin_domain_name) as a minimum.
          Components of I(config) can be specified entirely in I(config) or as separate elements outside of the config.
          This parameter applies to both distributions and streaming distributions.
          Elements of a distribution are
            I(caller_reference)
            I(aliases[])
            I(default_root_object)
            I(origins[])
            I(default_cache_behavior)
            I(cache_behaviors[])
            I(custom_error_responses[])
            I(comment)
            I(logging)
            I(price_class)
            I(enabled)
            I(viewer_certificate)
            I(restrictions)
            I(web_acl_id)
            I(http_version)
            I(ipv6_enabled)
          Elements of a streaming distribution are
            I(caller_reference)
            I(s3_origin)
            I(aliases[])
            I(comment)
            I(logging)
            I(trusted_signers)
            I(http_version)
            I(ipv6_enabled)
          Most of these elements have sub-elements that can be seen in their
          entirety in the boto3 documentation at
            U(http://boto3.readthedocs.io/en/latest/reference/services/cloudfront.html#CloudFront.Client.create_distribution)
          and
            U(http://boto3.readthedocs.io/en/latest/reference/services/cloudfront.html#CloudFront.Client.create_streaming_distribution).
          When element parameters are specified as well as the I(config) parameter, the elements specified will have precendence and overwrite any relevant
          data for that element in the I(config) variable.

    tags:
      description:
        - Used for distributions and streaming distributions. Should be input as a dict() of key-value pairs.
          Note that numeric keys or values must be wrapped in quotes. e.g. "Priority:" '1'

    purge_tags:
      description:
        - Specifies whether existing tags will be removed before adding new tags. When I(purge_tags=yes), existing tags are removed and I(tags) are added, if
          specified. If no tags are specified, it removes all existing tags for the distribution. When I(purge_tags=no), existing tags are kept and I(tags)
          are added, if specified.
      default: 'no'
      choices: ['yes', 'no']

    alias:
      description:
        - The name of an alias (CNAME) that is used in a distribution. This is used to effectively reference a distribution by its alias as an alias can only
          be used by one distribution per AWS account. This variable avoids having to provide the I(distribution_id) or I(streaming_distribution_id) as well as
          the I(e_tag), or I(caller_reference) of an existing distribution. This variable is used for both distributions and streaming distributions.

    aliases:
      description:
        - A I(list[]) of domain name aliases (CNAMEs) as strings to be used for the distribution. Each alias must be unique across all distribution for the AWS
          account. Applies to both distributions and streaming distributions.

    default_root_object:
      description:
        - A config element that specifies the path to request when the user requests the origin. e.g. if specified as 'index.html', this maps to
          www.example.com/index.html when www.example.com is called by the user. This prevents the entire distribution origin from being exposed at the root.
          Used with I(streaming_distribution=no).

    default_origin_domain_name:
      description:
        - The domain name to use for an origin if no I(origins) have been specified. Should only be used on a first run of generating a distribution and not on
          subsequent runs. Should not be used in conjunction with I(distribution_id), I(caller_reference) or I(alias). Used with I(streaming_distribution=no).

    default_origin_path:
      description:
        - The default origin path to specify for an origin if no I(origins) have been specified. Defaults to empty if not specified. Used with
          I(streaming_distribution=no).

    default_s3_origin_access_identity:
      description:
        - The origin access identity to use for a distribution that references an s3 bucket if not specified in I(origins[].s3_origin_config). If the s3 bucket
          is public, can be omitted. This parameter is only valid for distributions. Used with I(streaming_distribution=no).

    default_streaming_s3_origin_access_identity:
      description:
        - The default origin access identity to use for an s3 bucket used for a streaming distribution. If the s3 bucket is public, can be omitted. This
          parameter is only valid for streaming distributions. Used with I(streaming_distribution=yes).

    default_s3_origin_domain_name:
      description:
        - The domain name of an s3 bucket to use for a streaming distribution. Required as a minimum if no other parameters are specified. Can be used in place
          of specifying I(s3_origin). This parameter should only be used on a first run of generating a distribution and not on subsequent runs. Should not be
          used in conjunction with I(distribution_id), I(caller_reference) or I(alias). Used with I(streaming_distribution=yes).

    origins:
      description:
        - A config element that is a I(list[]) of complex origin objects to be specified for the distribution. Used for creating and updating distributions.
          Only valid for I(streaming_distribution=no).
          Each origin item comprises the attributes
            I(id)
            I(domain_name) (defaults to default_origin_domain_name if not specified)
            I(origin_path) (defaults to default_origin_path if not specified)
            I(custom_headers[])
              I(header_name)
              I(header_value)
            I(s3_origin_config)
              I(origin_access_identity)
            I(custom_origin_config)
              I(http_port)
              I(https_port)
              I(origin_protocol_policy)
              I(origin_ssl_protocols[])
              I(origin_read_timeout)
              I(origin_keepalive_timeout)

    default_cache_behavior:
      description:
        - A config element that is a complex object specifying the default cache behavior of the distribution. If not specified, the I(target_origin_id) is
          defined as the I(target_origin_id) of the first valid I(cache_behavior) in I(cache_behaviors) with defaults.
          The default cache behavior comprises the attributes
            I(target_origin_id)
            I(forwarded_values)
              I(query_string)
              I(cookies)
                I(forward)
                I(whitelisted_names)
              I(headers[])
              I(query_string_cache_keys[])
              I(trusted_signers)
                I(enabled)
                I(items[])
              I(viewer_protocol_policy)
              I(min_ttl)
              I(allowed_methods)
                I(items[])
                I(cached_methods[])
              I(smooth_streaming)
              I(default_ttl)
              I(max_ttl)
              I(compress)
              I(lambda_function_associations[])
                I(lambda_function_arn)
                I(event_type)
          Only valid for I(streaming_distribution=no).

    cache_behaviors:
      description:
        - A config element that is a I(list[]) of complex cache behavior objects to be specified for the distribution.
          Each cache behavior comprises the attributes
            I(path_pattern)
            I(target_origin_id)
            I(forwarded_values)
              I(query_string)
              I(cookies)
              I(forward)
              I(whitelisted_names)
              I(headers[])
              I(query_string_cache_keys[])
            I(trusted_signers)
              I(enabled)
              I(items[])
            I(viewer_protocol_policy)
            I(min_ttl)
            I(allowed_methods)
              I(items[])
              I(cached_methods[])
            I(smooth_streaming)
            I(default_ttl)
            I(max_ttl)
            I(compress)
            I(lambda_function_associations[])
          Only valid for I(streaming_distribution=no).

    custom_error_responses:
      description:
        - A config element that is a I(list[]) of complex custom error responses to be specified for the distribution. This attribute configures custom http
          error messages returned to the user.
          Each custom error response object comprises the attributes
            I(error_code)
            I(reponse_page_path)
            I(response_code error_caching_min_ttl)
          Only valid for I(streaming_distribution=no).

    comment:
      description:
        - A comment that describes the cloudfront distribution. Applies to both distributions and streaming distributions. If not specified, it defaults to a
          generic message that it has been created with Ansible, and a datetime stamp.

    logging:
      description:
        - A config element that is a complex object that defines logging for the distribution. Applies to both distributions and streaming distributions.
          The logging object comprises the attributes
            I(enabled)
            I(include_cookies)
            I(bucket)
            I(prefix)

    price_class:
      description:
        - A string that specifies the pricing class of the distribution. Applies to both distributions and streaming distributions. As per
          U(https://aws.amazon.com/cloudfront/pricing/)
            I(price_class=PriceClass_100) consists of the areas
              United States
              Canada
              Europe
            I(price_class=PriceClass_200) consists of the areas
              United States
              Canada
              Europe
              Hong Kong, Philippines, S. Korea, Singapore & Taiwan
              Japan
              India
            I(price_class=PriceClass_All) consists of the areas
              United States
              Canada
              Europe
              Hong Kong, Philippines, S. Korea, Singapore & Taiwan
              Japan
              India
              South America
              Australia
      choices: ['PriceClass_100', 'PriceClass_200', 'PriceClass_All']
      default: aws defaults this to 'PriceClass_All'

    enabled:
      description:
        - A boolean value that specifies whether the distribution is enabled or disabled. Applies to both distributions and streaming distributions.
      default: 'yes'
      choices: ['yes', 'no']

    viewer_certificate:
      description:
        - A config element that is a complex object that specifies the encryption details of the distribution. Only valid for I(streaming_distribution=no).
          Comprises the following attributes
            I(cloudfront_default_certificate)
            I(iam_certificate_id)
            I(acm_certificate_arn)
            I(ssl_support_method)
            I(minimum_protocol_version)
            I(certificate certificate_source)

    restrictions:
      description:
        - A config element that is a complex object that describes how a distribution should restrict it's content. Only valid for
          I(streaming_distribution=no).
          The restriction object comprises the following attributes
            I(geo_restriction)
              I(restriction_type)
              I(items[])

    s3_origin:
      description:
        - A config element that is used to describe the origin of a streaming distribution. The s3 origin object comprises the attributes
            I(domain_name) (defaults to I(default_s3_origin_domain_name) if not specified)
            I(origin_access_identity) (defaults to I(default_streaming_s3_origin_access_identity) if not specified)

    web_acl_id:
      description:
        - The id of a Web Application Firewall (WAF) Access Control List (ACL).
          Only valid for I(streaming_distribution=no).

    http_version:
      description:
        - The version of the http protocol to use for the distribution. Valid for both distributions and streaming distributions.
      choices: [ 'http1.1', 'http2' ]
      default: aws defaults this to 'http2'

    ipv6_enabled:
      description:
        - Determines whether IPv6 support is enabled or not. Valid for both distributions and streaming distributions.
      choices: ['yes', 'no']
      default: 'no'

    wait:
      description:
        - Specifies whether the module waits until the distribution has completed processing the creation or update.
      choices: ['yes', 'no']
      default: 'no'

    wait_timeout:
      description:
        - Specifies the duration in seconds to wait for a timeout of a cloudfront create or update. Defaults to 1800 seconds (30 minutes).
      default: 1800

'''

EXAMPLES = '''

# create a basic distribution with defaults and tags

- cloudfront_distribution:
    state: present
    default_origin_domain_name: www.my-cloudfront-origin.com
    tags:
      Name: example distribution
      Project: example project
      Priority: '1'

# update a distribution comment by distribution_id

- cloudfront_distribution:
    state: present
    distribution_id: E1RP5A2MJ8073O
    comment: modified by ansible cloudfront.py

# update a distribution comment by caller_reference

- cloudfront_distribution:
    state: present
    caller_reference: my cloudfront distribution 001
    comment: modified by ansible cloudfront.py

# update a distribution's aliases and comment using the distribution_id as a reference

- cloudfront_distribution:
    state: present
    distribution_id: E1RP5A2MJ8073O
    comment: modified by cloudfront.py again
    aliases: [ 'www.my-distribution-source.com', 'zzz.aaa.io' ]

# update a distribution's aliases and comment using an alias as a reference

- cloudfront_distribution:
    state: present
    caller_reference: my test distribution
    comment: modified by cloudfront.py again
    aliases:
      - www.my-distribution-source.com
      - zzz.aaa.io

# update a distribution's comment and aliases and tags and remove existing tags

- cloudfront_distribution:
    state: present
    distribution_id: E15BU8SDCGSG57
    comment: modified by cloudfront.py again
    aliases:
      - tested.com
    tags:
      Project: distribution 1.2
    purge_tags: yes

# create a distribution with an origin, logging and default cache behavior

- cloudfront_distribution:
    state: present
    caller_reference: unique test distribution id
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
      allowed_methods:
        items:
          - GET
          - HEAD
        cached_methods:
          - GET
          - HEAD
    logging:
      enabled: true
      include_cookies: false
      bucket: mylogbucket.s3.amazonaws.com
      prefix: myprefix/
    enabled: false
    comment: this is a cloudfront distribution with logging

# delete a distribution

- cloudfront_distribution:
    state: absent
    caller_reference: replaceable distribution

# create a presigned url for a distribution based on a distribution_id and from a local pem file

- cloudfront_distribution:
    generate_presigned_url: yes
    distribution_id: E1RP5A2MJ8073O
    pem_key_path: /home/user/ansible/pk-APKAJMTT6OPAZSFTNSCZ.pem
    cloudfront_url_to_sign: 'http://d3vodljfucvmwf.cloudfront.net/example.txt'
    presigned_url_expire_date: '2017-04-20'

# create a streaming distribution

- cloudfront_distribution:
     streaming_distribution: yes
     state: present
     default_s3_origin_domain_name: my-example-bucket.s3.amazonaws.com
     comment: example streaming distribution

# create a streaming distribution with tags

- cloudfront_distribution:
     streaming_distribution: yes
     default_s3_origin_domain_name: example-bucket.s3.amazonaws.com
     caller_reference: test streaming
     comment: example streaming distribution
     tags:
       Name: example distribution
       Project: example project
       Priority: '1'

# update a streaming distribution

- cloudfront_distribution:
    streaming_distribution: yes
    state: present
    streaming_distribution_id: E2RTIUCAA9RINU
    comment: modified streaming distribution

'''

RETURN = '''

location:
    description: describes a url specifying the output of the action just run.
    returned: applies to I(streaming_distribution=no) with I(state=present).
    type: str

presigned_url:
    description: specifies a url that has been presigned for the cloudfront distribution.
    returned: applies to when specifying I(generate_presigned_url=yes).
    type: str

'''

from ansible.module_utils.ec2 import get_aws_connection_info
from ansible.module_utils.ec2 import ec2_argument_spec, boto3_conn, HAS_BOTO3
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, ansible_dict_to_boto3_tag_list
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.aws.cloudfront_facts import CloudFrontFactsServiceManager
import ansible.module_utils.aws.cloudfront as helpers
from botocore.signers import CloudFrontSigner
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
import datetime
import time
from functools import partial
import json
import traceback
import timeit

try:
    import botocore
except ImportError:
    pass


class CloudFrontServiceManager(object):
    """
    Handles CloudFront service calls to AWS
    """

    def __init__(self, module):
        self.module = module
        self.create_client('cloudfront')

    def create_client(self, resource):
        try:
            region, ec2_url, aws_connect_kwargs = get_aws_connection_info(self.module, boto3=True)
            self.client = boto3_conn(self.module, conn_type='client', resource=resource, region=region, endpoint=ec2_url, **aws_connect_kwargs)
        except botocore.exceptions.NoRegionError:
            self.module.fail_json(msg=("Region must be specified as a parameter in AWS_DEFAULT_REGION environment variable or in boto configuration file."))
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Unable to establish connection - " + str(e), exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    def generate_presigned_url(self, distribution_id, private_key_path, private_key_password, url, expire_date):
        try:
            self.pem_key_path = private_key_path
            self.pem_private_key_password = private_key_password
            cloudfront_signer = CloudFrontSigner(distribution_id, self.presigned_url_rsa_signer)
            presigned_url = cloudfront_signer.generate_presigned_url(url, date_less_than=expire_date)
            return {'presigned_url': presigned_url}
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error generating signed url from pem private key - " + str(e), exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))
        finally:
            self.pem_key_path = None
            self.pem_private_key_password = None

    def presigned_url_rsa_signer(self, message):
        with open(self.pem_key_path, 'rb') as key_file:
            private_key = serialization.load_pem_private_key(key_file.read(), password=self.pem_private_key_password, backend=default_backend())
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
                    'Tags': {
                        'Items': tags
                    }
                }
                func = partial(self.client.create_distribution_with_tags, DistributionConfigWithTags=distribution_config_with_tags)
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error creating distribution - " + str(e), exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    def delete_distribution(self, distribution_id, e_tag):
        try:
            func = partial(self.client.delete_distribution, Id=distribution_id, IfMatch=e_tag)
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error deleting distribution - " + str(e), exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    def update_distribution(self, config, distribution_id, e_tag):
        try:
            func = partial(self.client.update_distribution, DistributionConfig=config, Id=distribution_id, IfMatch=e_tag)
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error updating distribution - " + str(e), exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    def create_streaming_distribution(self, config, tags):
        try:
            if tags is None:
                func = partial(self.client.create_streaming_distribution, StreamingDistributionConfig=config)
            else:
                streaming_distribution_config_with_tags = {
                    'StreamingDistributionConfig': config,
                    'Tags': {
                        'Items': tags
                    }
                }
                func = partial(self.client.create_streaming_distribution_with_tags,
                               StreamingDistributionConfigWithTags=streaming_distribution_config_with_tags)
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error creating streaming distribution - " + str(e), exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

    def delete_streaming_distribution(self, streaming_distribution_id, e_tag):
        try:
            func = partial(self.client.delete_streaming_distribution, Id=streaming_distribution_id, IfMatch=e_tag)
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error deleting streaming distribution - " + str(e), exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

    def update_streaming_distribution(self, config, streaming_distribution_id, e_tag):
        try:
            func = partial(self.client.update_streaming_distribution, StreamingDistributionConfig=config, Id=streaming_distribution_id, IfMatch=e_tag)
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error updating streaming distribution - " + str(e), exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

    def tag_resource(self, arn, tags):
        try:
            func = partial(self.client.tag_resource, Resource=arn, Tags=tags)
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error tagging resource - " + str(e), exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    def untag_resource(self, arn, tag_keys):
        try:
            func = partial(self.client.untag_resource, Resource=arn, TagKeys={'Items': tag_keys})
            return self.paginated_response(func)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error untagging resource - " + str(e), exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    def remove_all_tags_from_resource(self, arn):
        tags = self.list_tags_for_resource(arn)
        key_list = []
        for tag in tags:
            key_list.append(tag.get('Key'))
        self.untag_resource(arn, key_list)

    def list_tags_for_resource(self, arn):
        try:
            func = partial(self.client.list_tags_for_resource, Resource=arn)
            response = self.paginated_response(func)
            return response.get('Tags').get('Items')
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg="Error removing all tags from resource - " + str(e), exception=traceback.format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

    def update_tags(self, valid_tags, purge_tags, arn, alias, distribution_id, streaming_distribution_id):
        try:
            changed = False
            if purge_tags:
                self.remove_all_tags_from_resource(arn)
                changed = True
            if valid_tags is not None:
                valid_aws_tags = helpers.python_list_to_aws_list(valid_tags, False)
                valid_pascal_aws_tags = helpers.snake_dict_to_pascal_dict(valid_aws_tags)
                self.tag_resource(arn, valid_pascal_aws_tags)
                changed = True
            return changed
        except Exception as e:
            self.module.fail_json(msg="Error validating and updating tags - " + str(e) + "\n" + traceback.format_exc())

    def paginated_response(self, func, result_key=''):
        '''
        Returns expanded response for paginated operations. The 'result_key' is used to define the concatenated results that are combined from each paginated
        response.
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


class CloudFrontValidationManager(object):
    """
    Manages Cloudfront validations
    """

    def __init__(self, module):
        self.__cloudfront_facts_mgr = CloudFrontFactsServiceManager(module)
        self.module = module
        self.__default_distribution_enabled = True
        self.__default_http_port = 80
        self.__default_https_port = 443
        self.__default_ipv6_enabled = False
        self.__default_origin_ssl_protocols = [
            'TLSv1',
            'TLSv1.1',
            'TLSv1.2'
        ]
        self.__default_custom_origin_protocol_policy = 'match-viewer'
        self.__default_custom_origin_read_timeout = 30
        self.__default_custom_origin_keepalive_timeout = 5
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
        self.__default_trusted_signers_enabled = False
        self.__default_presigned_url_expire_date_format = '%Y-%m-%d'
        self.__valid_price_classes = [
            'PriceClass_100',
            'PriceClass_200',
            'PriceClass_All'
        ]
        self.__valid_origin_protocol_policies = [
            'http-only',
            'match-viewer',
            'https-only'
        ]
        self.__valid_origin_ssl_protocols = [
            'SSLv3',
            'TLSv1',
            'TLSv1.1',
            'TLSv1.2'
        ]
        self.__valid_cookie_forwarding = [
            'none',
            'whitelist',
            'all'
        ]
        self.__valid_viewer_protocol_policies = [
            'allow-all',
            'https-only',
            'redirect-to-https'
        ]
        self.__valid_methods = [
            'GET',
            'HEAD',
            'POST',
            'PUT',
            'PATCH',
            'OPTIONS',
            'DELETE'
        ]
        self.__valid_methods_cached_methods = [
            [
                'GET',
                'HEAD'
            ],
            [
                'GET',
                'HEAD',
                'OPTIONS'
            ]
        ]
        self.__valid_methods_allowed_methods = [
            self.__valid_methods_cached_methods[0],
            self.__valid_methods_cached_methods[1],
            self.__valid_methods
        ]
        self.__valid_lambda_function_association_event_types = [
            'viewer-request',
            'viewer-response',
            'origin-request',
            'origin-response'
        ]
        self.__valid_viewer_certificate_ssl_support_methods = [
            'sni-only',
            'vip'
        ]
        self.__valid_viewer_certificate_minimum_protocol_versions = [
            'SSLv3',
            'TLSv1'
        ]
        self.__valid_viewer_certificate_certificate_sources = [
            'cloudfront',
            'iam',
            'acm'
        ]
        self.__valid_http_versions = [
            'http1.1',
            'http2'
        ]
        self.__s3_bucket_domain_identifier = '.s3.amazonaws.com'

    def add_missing_key(self, dict_object, key_to_set, value_to_set):
        if key_to_set not in dict_object:
            dict_object[key_to_set] = value_to_set
        return dict_object

    def add_key_else_change_dict_key(self, dict_object, old_key, new_key, value_to_set):
        if old_key not in dict_object:
            dict_object[new_key] = value_to_set
        else:
            dict_object = helpers.change_dict_key_name(dict_object, old_key, new_key)
        return dict_object

    def add_key_else_validate(self, dict_object, key_name, attribute_name, value_to_set, valid_values, to_aws_list=False):
        if key_name in dict_object:
            self.validate_attribute_with_allowed_values(value_to_set, attribute_name, valid_values)
        else:
            if to_aws_list:
                dict_object[key_name] = helpers.python_list_to_aws_list(value_to_set)
            else:
                dict_object[key_name] = value_to_set
        return dict_object

    def validate_logging(self, logging, streaming):
        try:
            if logging is None:
                return None
            valid_logging = {}
            if not streaming:
                if logging and not set(['enabled', 'include_cookies', 'bucket', 'prefix']).issubset(logging):
                    self.module.fail_json(msg="The logging parameters enabled, include_cookies, bucket and prefix must be specified.")
                valid_logging['include_cookies'] = logging.get('include_cookies')
            else:
                if logging and not set(['enabled', 'bucket', 'prefix']).issubset(logging):
                    self.module.fail_json(msg="The logging parameters enabled, bucket and prefix must be specified.")
            valid_logging['enabled'] = logging.get('enabled')
            valid_logging['bucket'] = logging.get('bucket')
            valid_logging['prefix'] = logging.get('prefix')
            return valid_logging
        except Exception as e:
            self.module.fail_json(msg="Error validating distribution logging - " + str(e) + "\n" + traceback.format_exc())

    def validate_is_list(self, list_to_validate, list_name):
        if not isinstance(list_to_validate, list):
            self.module.fail_json(msg='{0} is of type {1}. Must be a list.'.format(list_name, type(list_to_validate).__name__))

    def validate_required_key(self, key_name, full_key_name, dict_object):
        if key_name not in dict_object:
            self.module.fail_json(full_key_name + " must be specified.")

    def validate_origins(self, origins, default_origin_domain_name, default_s3_origin_access_identity, default_origin_path, streaming, create_distribution):
        try:
            valid_origins = {}
            if origins is None:
                if default_origin_domain_name is None and not create_distribution:
                    return None
                if default_origin_domain_name is not None:
                    origins = [{
                        'domain_name': default_origin_domain_name,
                        'origin_path': default_origin_path or ''
                    }]
                else:
                    origins = []
            self.validate_is_list(origins, 'origins')
            if not origins and default_origin_domain_name is None and create_distribution:
                self.module.fail_json(msg="Both origins[] and default_origin_domain_name have not been specified. Please specify at least one.")
            for origin in origins:
                origin = self.validate_origin(origin, default_origin_path, default_s3_origin_access_identity, streaming)
            return helpers.python_list_to_aws_list(origins)
        except Exception as e:
            self.module.fail_json(msg="Error validating distribution origins - " + str(e) + "\n" + traceback.format_exc())

    def validate_origin(self, origin, default_origin_path, default_s3_origin_access_identity, streaming):
        try:
            origin = self.add_missing_key(origin, 'origin_path', (default_origin_path or ''))
            self.validate_required_key('origin_path', 'origins[].domain_name', origin)
            origin = self.add_missing_key(origin, 'id', self.__default_datetime_string)
            if 'custom_headers' in origin and streaming:
                self.module.fail_json(msg="custom_headers has been specified for a streaming distribution. Custom headers are for web distributions only.")
            if 'custom_headers' in origin and len(origin.get('custom_headers')) > 0:
                for custom_header in origin.get('custom_headers'):
                    if 'header_name' not in custom_header or 'header_value' not in custom_header:
                        self.module.fail_json(msg="Both origins[].custom_headers.header_name and origins[].custom_headers.header_value must be specified.")
                origin['custom_headers'] = helpers.python_list_to_aws_list(origin.get('custom_headers'))
            else:
                origin['custom_headers'] = helpers.python_list_to_aws_list()
            if self.__s3_bucket_domain_identifier in origin.get('domain_name').lower():
                if 's3_origin_config' not in origin or 'origin_access_identity' not in origin.get('s3_origin_config'):
                    origin["s3_origin_config"] = {'origin_access_identity': default_s3_origin_access_identity or ''}
            else:
                origin = self.add_missing_key(origin, 'custom_origin_config', {})
                custom_origin_config = origin.get('custom_origin_config')
                custom_origin_config = self.add_key_else_validate(custom_origin_config, 'origin_protocol_policy',
                                                                  'origins[].custom_origin_config.origin_protocol_policy',
                                                                  self.__default_custom_origin_protocol_policy, self.__valid_origin_protocol_policies)
                custom_origin_config = self.add_missing_key(custom_origin_config, 'origin_read_timeout', self.__default_custom_origin_read_timeout)
                custom_origin_config = self.add_missing_key(custom_origin_config, 'origin_keepalive_timeout', self.__default_custom_origin_keepalive_timeout)
                custom_origin_config = self.add_key_else_change_dict_key(custom_origin_config, 'http_port', 'h_t_t_p_port', self.__default_http_port)
                custom_origin_config = self.add_key_else_change_dict_key(custom_origin_config, 'https_port', 'h_t_t_p_s_port', self.__default_https_port)
                custom_origin_config = self.add_key_else_validate(custom_origin_config, 'origin_ssl_protocols', 'origins[].origin_ssl_protocols',
                                                                  self.__default_origin_ssl_protocols, self.__valid_origin_ssl_protocols, True)
            return origin
        except Exception as e:
            self.module.fail_json(msg="Error validating distribution origin - " + str(e) + "\n" + traceback.format_exc())

    def validate_cache_behaviors(self, cache_behaviors, valid_origins):
        try:
            if cache_behaviors is None and valid_origins is not None:
                return None
            for cache_behavior in cache_behaviors:
                self.validate_cache_behavior(cache_behavior, valid_origins)
            return helpers.python_list_to_aws_list(cache_behaviors)
        except Exception as e:
            self.module.fail_json(msg="Error validating distribution cache behaviors - " + str(e) + "\n" + traceback.format_exc())

    def validate_cache_behavior(self, cache_behavior, valid_origins, is_default_cache=False):
        if is_default_cache and cache_behavior is None:
            cache_behavior = {}
        if cache_behavior is None and valid_origins is not None:
            return None
        cache_behavior = self.validate_cache_behavior_first_level_keys(cache_behavior, valid_origins, is_default_cache)
        cache_behavior = self.validate_forwarded_values(cache_behavior.get('forwarded_values'), cache_behavior)
        cache_behavior = self.validate_allowed_methods(cache_behavior.get('allowed_methods'), cache_behavior)
        cache_behavior = self.validate_lambda_function_associations(cache_behavior.get('lambda_function_associations'), cache_behavior)
        cache_behavior = self.validate_trusted_signers(cache_behavior.get('trusted_signers'), cache_behavior)
        return cache_behavior

    def validate_cache_behavior_first_level_keys(self, cache_behavior, valid_origins, is_default_cache):
        try:
            cache_behavior = self.add_key_else_change_dict_key(cache_behavior, 'min_ttl', 'min_t_t_l', self.__default_cache_behavior_min_ttl)
            cache_behavior = self.add_key_else_change_dict_key(cache_behavior, 'max_ttl', 'max_t_t_l', self.__default_cache_behavior_max_ttl)
            cache_behavior = self.add_key_else_change_dict_key(cache_behavior, 'default_ttl', 'default_t_t_l', self.__default_cache_behavior_default_ttl)
            cache_behavior = self.add_missing_key(cache_behavior, 'compress', self.__default_cache_behavior_compress)
            cache_behavior = self.add_missing_key(cache_behavior, 'target_origin_id', self.get_first_origin_id_for_default_cache_behavior(valid_origins))
            cache_behavior = self.add_key_else_validate(cache_behavior, 'viewer_protocol_policy', 'cache_behavior.viewer_protocol_policy',
                                                        self.__default_cache_behavior_viewer_protocol_policy, self.__valid_viewer_protocol_policies)
            cache_behavior = self.add_missing_key(cache_behavior, 'smooth_streaming', self.__default_cache_behavior_smooth_streaming)
            return cache_behavior
        except Exception as e:
            self.module.fail_json(msg="Error validating distribution cache behavior first level keys - " + str(e) + "\n" + traceback.format_exc())

    def validate_forwarded_values(self, forwarded_values, cache_behavior):
        try:
            if forwarded_values is None:
                forwarded_values = {}
            forwarded_values['headers'] = helpers.python_list_to_aws_list(forwarded_values.get('headers'))
            if 'cookies' not in forwarded_values:
                forwarded_values['cookies'] = {'forward': self.__default_cache_behavior_forwarded_values_forward_cookies}
            else:
                forwarded_values['cookies']['whitelisted_names'] = helpers.python_list_to_aws_list(forwarded_values.get('cookies').get('whitelisted_names'))
                cookie_forwarding = forwarded_values.get('cookies').get('forward')
                self.validate_attribute_with_allowed_values(cookie_forwarding, 'cache_behavior.forwarded_values.cookies.forward',
                                                            self.__valid_cookie_forwarding)
            forwarded_values['query_string_cache_keys'] = helpers.python_list_to_aws_list(forwarded_values.get('query_string_cache_keys'))
            forwarded_values = self.add_missing_key(forwarded_values, 'query_string', self.__default_cache_behavior_forwarded_values_query_string)
            cache_behavior['forwarded_values'] = forwarded_values
            return cache_behavior
        except Exception as e:
            self.module.fail_json(msg="Error validating forwarded values - " + str(e) + "\n" + traceback.format_exc())

    def validate_lambda_function_associations(self, lambda_function_associations, cache_behavior):
        try:
            if lambda_function_associations is not None:
                self.validate_is_list(lambda_function_associations, 'lambda_function_associations')
                for association in lambda_function_associations:
                    association = helpers.change_dict_key_name(association, 'lambda_function_arn', 'lambda_function_a_r_n')
                    self.validate_attribute_with_allowed_values(association.get('event_type'), 'cache_behaviors[].lambda_function_associations.event_type',
                                                                self.__valid_lambda_function_association_event_types)
            cache_behavior['lambda_function_associations'] = helpers.python_list_to_aws_list(lambda_function_associations)
            return cache_behavior
        except Exception as e:
            self.module.fail_json(msg="Error validating lambda function associations - " + str(e) + "\n" + traceback.format_exc())

    def validate_allowed_methods(self, allowed_methods, cache_behavior):
        try:
            if allowed_methods is not None:
                self.validate_required_key('items', 'cache_behavior.allowed_methods.items[]', allowed_methods)
                temp_allowed_items = allowed_methods.get('items')
                self.validate_is_list(temp_allowed_items, 'cache_behavior.allowed_methods.items')
                self.validate_attribute_list_with_allowed_list(temp_allowed_items, 'cache_behavior.allowed_items.allowed_methods[]',
                                                               self.__valid_methods_allowed_methods)
                cached_items = allowed_methods.get('cached_methods')
                if 'cached_methods' in allowed_methods:
                    self.validate_is_list(cached_items, 'cache_behavior.allowed_methods.cached_methods')
                    self.validate_attribute_list_with_allowed_list(cached_items, 'cache_behavior.allowed_items.cached_methods[]',
                                                                   self.__valid_methods_cached_methods)
                cache_behavior['allowed_methods'] = helpers.python_list_to_aws_list(temp_allowed_items)
                cache_behavior['allowed_methods']['cached_methods'] = helpers.python_list_to_aws_list(cached_items)
            return cache_behavior
        except Exception as e:
            self.module.fail_json(msg="Error validating allowed methods - " + str(e) + "\n" + traceback.format_exc())

    def validate_trusted_signers(self, trusted_signers, cache_behavior):
        try:
            if trusted_signers is None:
                trusted_signers = {}
            trusted_signers = self.add_missing_key(trusted_signers, 'enabled', self.__default_trusted_signers_enabled)
            trusted_signers = self.add_missing_key(trusted_signers, 'items', [])
            valid_trusted_signers = helpers.python_list_to_aws_list(trusted_signers.get('items'))
            valid_trusted_signers['enabled'] = trusted_signers.get('enabled')
            cache_behavior['trusted_signers'] = valid_trusted_signers
            return cache_behavior
        except Exception as e:
            self.module.fail_json(msg="Error validating trusted signers - " + str(e) + "\n" + traceback.format_exc())

    def validate_s3_origin(self, s3_origin, default_s3_origin_domain_name, default_streaming_s3_origin_access_identity):
        try:
            if s3_origin is not None:
                self.validate_required_key('domain_name', 's3_origin.domain_name', s3_origin)
                self.validate_required_key('origin_access_identity', 's3_origin.origin_access_identity', s3_origin)
                return s3_origin
            s3_origin = {}
            if default_s3_origin_domain_name is not None:
                s3_origin['domain_name'] = default_s3_origin_domain_name
            else:
                self.module.fail_json(msg="s3_origin and default_s3_origin_domain_name not specified. Please specify one.")
            s3_origin = self.add_missing_key(s3_origin, 'origin_access_identity', (default_streaming_s3_origin_access_identity or ''))
            return s3_origin
        except Exception as e:
            self.module.fail_json(msg="Error validating s3 origin - " + str(e) + "\n" + traceback.format_exc())

    def validate_viewer_certificate(self, viewer_certificate):
        try:
            if viewer_certificate is None:
                return None
            if viewer_certificate.get('cloudfront_default_certificate') and viewer_certificate.get('ssl_support_method') is not None:
                self.module.fail_json(msg="viewer_certificate.ssl_support_method should not be specified with viewer_certificate_cloudfront_default" +
                                      "_certificate set to true.")
            self.validate_attribute_with_allowed_values(viewer_certificate.get('ssl_support_method'), 'viewer_certificate.ssl_support_method',
                                                        self.__valid_viewer_certificate_ssl_support_methods)
            self.validate_attribute_with_allowed_values(viewer_certificate.get('minimum_protocol_version'), 'viewer_certificate.minimum_protocol_version',
                                                        self.__valid_viewer_certificate_minimum_protocol_versions)
            self.validate_attribute_with_allowed_values(viewer_certificate.get('certificate_source'), 'viewer_certificate.certificate_source',
                                                        self.__valid_viewer_certificate_certificate_sources)
            viewer_certificate = helpers.change_dict_key_name(viewer_certificate, 'ssl_support_method', 's_s_l_support_method')
            viewer_certificate = helpers.change_dict_key_name(viewer_certificate, 'iam_certificate_id', 'i_a_m_certificate_id')
            viewer_certificate = helpers.change_dict_key_name(viewer_certificate, 'acm_certificate_arn', 'a_c_m_certificate_arn')
            return viewer_certificate
        except Exception as e:
            self.module.fail_json(msg="Error validating viewer certificate - " + str(e) + "\n" + traceback.format_exc())

    def validate_custom_error_responses(self, custom_error_responses):
        try:
            if custom_error_responses is None:
                return None
            self.validate_is_list(custom_error_responses, 'custom_error_responses')
            for custom_error_response in custom_error_responses:
                self.validate_required_key('error_code', 'custom_error_responses[].error_code', custom_error_response)
                custom_error_response = helpers.change_dict_key_name(custom_error_responses, 'error_caching_min_ttl', 'error_caching_min_t_t_l')
            return helpers.python_list_to_aws_list(custom_error_responses)
        except Exception as e:
            self.module.fail_json(msg="Error validating custom error responses - " + str(e) + "\n" + traceback.format_exc())

    def validate_restrictions(self, restrictions):
        try:
            if restrictions is None:
                return None
            self.validate_required_key('geo_restriction', 'restrictions.geo_restriction', restrictions)
            geo_restriction = restrictions.get('geo_restriction')
            self.validate_required_key('restriction_type', 'restrictions.geo_restriction.restriction_type', geo_restriction)
            valid_restrictions = helpers.python_list_to_aws_list(geo_restriction.get('items'))
            valid_restrictions['restriction_type'] = geo_restriction.get('restriction_type')
            return valid_restrictions
        except Exception as e:
            self.module.fail_json(msg="Error validating restrictions - " + str(e) + "\n" + traceback.format_exc())

    def validate_distribution_id_etag(self, alias, distribution_id, config, e_tag):
        try:
            if distribution_id is None and alias is None:
                self.module.fail_json(msg="distribution_id, alias or caller_reference must be specified for updating or deleting a distribution.")
            if distribution_id is None:
                distribution_id = self.__cloudfront_facts_mgr.get_distribution_id_from_domain_name(alias)
            if config is None:
                config = self.__cloudfront_facts_mgr.get_distribution_config(distribution_id).get('DistributionConfig')
            if e_tag is None:
                e_tag = self.__cloudfront_facts_mgr.get_etag_from_distribution_id(distribution_id, False)
            return distribution_id, config, e_tag
        except Exception as e:
            self.module.fail_json(msg="Error validating parameters for distribution update and delete - " + str(e) + "\n" + traceback.format_exc())

    def validate_streaming_distribution_id_etag(self, alias, streaming_distribution_id, config, e_tag):
        try:
            if streaming_distribution_id is None and alias is None:
                self.module.fail_json(msg="streaming_distribution_id or alias must be specified for updating or deleting a streaming distribution.")
            if streaming_distribution_id is None:
                streaming_distribution_id = self.__cloudfront_facts_mgr.get_distribution_id_from_domain_name(alias)
            if config is None:
                config = self.__cloudfront_facts_mgr.get_streaming_distribution_config(streaming_distribution_id).get('StreamingDistributionConfig')
            if e_tag is None:
                e_tag = self.__cloudfront_facts_mgr.get_etag_from_distribution_id(streaming_distribution_id, True)
            return streaming_distribution_id, config, e_tag
        except Exception as e:
            self.module.fail_json(msg="Error validating parameters for streaming distribution update and delete - " + str(e))

    def validate_tagging_arn(self, alias, distribution_id, streaming_distribution_id):
        try:
            distribution_response = None
            streaming_distribution_response = None
            if alias is not None:
                distribution_id = self.__cloudfront_facts_mgr.get_distribution_id_from_domain_name(alias)
            if distribution_id is not None:
                distribution_response = self.__cloudfront_facts_mgr.get_distribution(distribution_id)
            if distribution_response is not None:
                distribution = distribution_response.get('Distribution')
                if distribution is not None:
                    return distribution.get('ARN')
            streaming_distribution_response = self.__cloudfront_facts_mgr.get_streaming_distribution(streaming_distribution_id)
            if streaming_distribution_response is not None:
                streaming_distribution = streaming_distribution_response.get('StreamingDistribution')
                if streaming_distribution is not None:
                    return streaming_distribution.get('ARN')
            self.module.fail_json(msg="Unable to find a matching distribution with given parameters.")
        except Exception as e:
            self.module.fail_json(msg="Error validating tagging parameters - " + str(e) + "\n" + traceback.format_exc())

    def validate_distribution_config_parameters(self, config, default_root_object, ipv6_enabled, http_version, web_acl_id):
        try:
            config['default_root_object'] = default_root_object or ''
            config['is_i_p_v_6_enabled'] = ipv6_enabled or self.__default_ipv6_enabled
            if http_version is not None:
                self.validate_attribute_with_allowed_values(http_version, 'http_version', self.__valid_http_versions)
                config['http_version'] = http_version
            if web_acl_id is not None:
                config['web_a_c_l_id'] = web_acl_id
            return config
        except Exception as e:
            self.module.fail_json(msg="Error validating distribution config parameters - " + str(e) + "\n" + traceback.format_exc())

    def validate_streaming_distribution_config_parameters(self, config, comment, trusted_signers, s3_origin, default_s3_origin_domain_name,
                                                          default_streaming_s3_origin_access_identity):
        try:
            if s3_origin is None:
                s3_origin = config.get('s3_origin')
            config['s3_origin'] = self.validate_s3_origin(s3_origin, default_s3_origin_domain_name, default_streaming_s3_origin_access_identity)
            config['trusted_signers'] = self.validate_trusted_signers(trusted_signers)
            return config
        except Exception as e:
            self.module.fail_json(msg="Error validating streaming distribution config parameters - " + str(e) + "\n" + traceback.format_exc())

    def validate_common_distribution_parameters(self, config, enabled, aliases, logging, price_class, comment, is_streaming_distribution):
        try:
            if config is None:
                config = {}
            if aliases is not None:
                config['aliases'] = helpers.python_list_to_aws_list(aliases)
            if logging is not None:
                config['logging'] = self.validate_logging(logging, is_streaming_distribution)
            config['enabled'] = enabled or self.__default_distribution_enabled
            if price_class is not None:
                self.validate_attribute_with_allowed_values(price_class, 'price_class', self.__valid_price_classes)
                config['price_class'] = price_class
            config['comment'] = comment or "Distribution created by Ansible with datetime stamp " + self.__default_datetime_string
            return config
        except Exception as e:
            self.module.fail_json(msg="Error validating common distribution parameters - " + str(e) + "\n" + traceback.format_exc())

    def validate_caller_reference_for_distribution(self, config, caller_reference):
        config['caller_reference'] = caller_reference or self.__default_datetime_string
        return config

    def get_first_origin_id_for_default_cache_behavior(self, valid_origins):
        try:
            if valid_origins is not None:
                valid_origins_list = valid_origins.get('items')
                if valid_origins_list is not None and isinstance(valid_origins_list, list) and len(valid_origins_list) > 0:
                    return str(valid_origins_list[0].get('id'))
            self.module.fail_json(msg="There are no valid origins from which to specify a target_origin_id for the default_cache_behavior configuration.")
        except Exception as e:
            self.module.fail_json(msg="Error getting first origin_id for default cache behavior - " + str(e) + "\n" + traceback.format_exc())

    def validate_attribute_list_with_allowed_list(self, attribute_list, attribute_list_name, allowed_list):
        try:
            self.validate_is_list(attribute_list, attribute_list_name)
            matched_one = False
            for allowed_sub_list in allowed_list:
                matched_one |= set(attribute_list) == set(allowed_sub_list)
            if not matched_one:
                self.module.fail_json(msg='The attribute list {0} must be one of [{1}]'.format(attribute_list_name, ' '.join(str(a) for a in allowed_list)))
        except Exception as e:
            self.module.fail_json(msg="Error validating attribute list with allowed value list - " + str(e) + "\n" + traceback.format_exc())

    def validate_attribute_with_allowed_values(self, attribute, attribute_name, allowed_list):
        if attribute is not None and attribute not in allowed_list:
            self.module.fail_json(msg='The attribute {0} must be one of [{1}]'.format(attribute_name, ' '.join(str(a) for a in allowed_list)))

    def validate_presigned_url_expire_date(self, datetime_string):
        try:
            return datetime.datetime.strptime(datetime_string, self.__default_presigned_url_expire_date_format)
        except Exception as e:
            self.module.fail_json(msg="presigned_url_expire_date must be in the format '{0}'".format(self.__default_presigned_url_expire_date_format))

    def validate_distribution_id_from_caller_reference(self, caller_reference, streaming=False):
        try:
            if streaming:
                distributions = self.__cloudfront_facts_mgr.list_streaming_distributions(False)
                distribution_name = 'StreamingDistribution'
                distribution_config_name = 'StreamingDistributionConfig'
            else:
                distributions = self.__cloudfront_facts_mgr.list_distributions(False)
                distribution_name = 'Distribution'
                distribution_config_name = 'DistributionConfig'
            distribution_ids = [dist.get('Id') for dist in distributions]
            for distribution_id in distribution_ids:
                if streaming:
                    config = self.__cloudfront_facts_mgr.get_streaming_distribution(distribution_id)
                else:
                    config = self.__cloudfront_facts_mgr.get_distribution(distribution_id)
                distribution = config.get(distribution_name)
                if distribution is not None:
                    distribution_config = distribution.get(distribution_config_name)
                    if distribution_config is not None and distribution_config.get('CallerReference') == caller_reference:
                        return distribution_id

        except Exception as e:
            self.module.fail_json(msg="Error validating (streaming)distribution_id from caller reference - " + str(e) + "\n" + traceback.format_exc())

    def validate_distribution_requires_update(self, proposed_config, distribution_id, streaming=False):
        try:
            if not streaming:
                config_name = "DistributionConfig"
                distribution = self.__cloudfront_facts_mgr.get_distribution_config(distribution_id)
            else:
                config_name = "StreamingDistributionConfig"
                distribution = self.__cloudfront_facts_mgr.get_streaming_distribution_config(distribution_id)
            existing_config = distribution.get(config_name)
            return sorted(existing_config.items()) == sorted(proposed_config.items())
        except Exception as e:
            self.module.fail_json(msg="Error validating distribution requires update - " + str(e) + "\n" + traceback.format_exc())

    def validate_id_from_alias_aliases_caller_reference(self, distribution_id, streaming_distribution_id, alias, aliases, caller_reference,
                                                        streaming_distribution):
        try:
            if caller_reference is not None:
                if streaming_distribution:
                    streaming_distribution_id = self.validate_distribution_id_from_caller_reference(caller_reference, True)
                else:
                    distribution_id = self.validate_distribution_id_from_caller_reference(caller_reference, False)
            if streaming_distribution_id is None and distribution_id is None:
                if alias is not None or aliases is not None:
                    if not streaming_distribution:
                        distribution_id = self.validate_distribution_id_from_alias(alias, aliases)
                    if streaming_distribution:
                        streaming_distribution_id = self.validate_distribution_id_from_alias(alias, aliases)
            return distribution_id, streaming_distribution_id
        except Exception as e:
            self.module.fail_json(msg="Error validating distribution_id from alias, aliases and caller reference - " + str(e) + "\n" + traceback.format_exc())

    def validate_distribution_exists(self, distribution_id, streaming_distribution_id, streaming_distribution):
        if not streaming_distribution:
            distributions = self.__cloudfront_facts_mgr.list_distributions(False)
        else:
            distributions = self.__cloudfront_facts_mgr.list_streaming_distributions(False)
        distribution_ids = [dist.get('Id') for dist in distributions]
        if not streaming_distribution:
            return distribution_id in distribution_ids
        else:
            return streaming_distribution_id in distribution_ids

    def wait_until_processed(self, wait_timeout, streaming_distribution, distribution_id, streaming_distribution_id, caller_reference):
        try:
            start_time = timeit.default_timer()
            generic_id = streaming_distribution_id if streaming_distribution else distribution_id

            if generic_id is None:
                generic_id = self.validate_distribution_id_from_caller_reference(caller_reference=caller_reference, streaming=streaming_distribution)

            while True:
                distribution = self.__cloudfront_facts_mgr.get_distribution(generic_id)
                if distribution.get('Distribution').get('Status') == "Deployed":
                    return
                elapsed = timeit.default_timer() - start_time
                if elapsed >= wait_timeout:
                    self.module.fail_json(msg="Timeout waiting for cloudfront action. Waited for " + str(wait_timeout) + " seconds before timeout.")
                time.sleep(10)
        except Exception as e:
            return


def main():
    argument_spec = ec2_argument_spec()

    argument_spec.update(dict(
        state=dict(choices=['present', 'absent']),
        streaming_distribution=dict(default=False, type='bool'),
        generate_presigned_url=dict(type='bool'),
        caller_reference=dict(),
        comment=dict(),
        distribution_id=dict(),
        streaming_distribution_id=dict(),
        e_tag=dict(),
        pem_key_path=dict(),
        pem_key_password=dict(no_log=True),
        cloudfront_url_to_sign=dict(),
        presigned_url_expire_date=dict(),
        config=dict(type='json'),
        tags=dict(type='dict'),
        purge_tags=dict(type='bool'),
        alias=dict(),
        aliases=dict(type='list'),
        default_root_object=dict(),
        origins=dict(type='list'),
        default_cache_behavior=dict(type='dict'),
        cache_behaviors=dict(type='list'),
        custom_error_responses=dict(type='list'),
        logging=dict(type='dict'),
        price_class=dict(),
        enabled=dict(type='bool'),
        viewer_certificate=dict(type='dict'),
        restrictions=dict(type='json'),
        web_acl_id=dict(),
        http_version=dict(),
        ipv6_enabled=dict(type='bool'),
        s3_origin=dict(type='json'),
        trusted_signers=dict(type='list'),
        default_origin_domain_name=dict(),
        default_origin_path=dict(),
        default_s3_origin_access_identity=dict(),
        default_s3_origin_domain_name=dict(),
        default_streaming_s3_origin_access_identity=dict(),
        wait=dict(default=False, type='bool'),
        wait_timeout=dict(default=1800, type='int')
    ))

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required.')

    result = {}
    changed = True
    valid_tags = None

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
        mutually_exclusive=[
            ['state', 'cloudfront_url_to_sign'],
            ['state', 'pem_key_path'],
            ['state', 'pem_key_password'],
            ['state', 'presigned_url_expire_date'],
            ['s3_origin', 'default_cache_behavior'],
            ['s3_origin', 'origins'],
            ['s3_origin', 'cache_behaviors'],
            ['s3_origin', 'custom_error_responses'],
            ['s3_origin', 'restrictions'],
            ['s3_origin', 'custom_error_responses'],
            ['s3_origin', 'viewer_certificate'],
            ['s3_origin', 'web_acl_id'],
            ['s3_origin', 'trusted_signers'],
            ['default_s3_origin_domain_name', 'default_cache_behavior'],
            ['default_s3_origin_domain_name', 'origins'],
            ['default_s3_origin_domain_name', 'cache_behaviors'],
            ['default_s3_origin_domain_name', 'custom_error_responses'],
            ['default_s3_origin_domain_name', 'restrictions'],
            ['default_s3_origin_domain_name', 'custom_error_responses'],
            ['default_s3_origin_domain_name', 'viewer_certificate'],
            ['default_s3_origin_domain_name', 'web_acl_id'],
            ['default_s3_origin_domain_name', 'trusted_signers'],
            ['distribution_id', 'streaming_distribution_id'],
            ['distribution_id', 'alias'],
            ['streaming_distribution_id', 'alias'],
            ['default_origin_domain_name', 'distribution_id'],
            ['default_origin_domain_name', 'alias'],
            ['default_s3_origin_domain_name', 'streaming_distribution_id'],
            ['default_s3_origin_domain_name', 'alias']
        ]
    )

    service_mgr = CloudFrontServiceManager(module)
    validation_mgr = CloudFrontValidationManager(module)

    state = module.params.get('state')
    streaming_distribution = module.params.get('streaming_distribution')
    generate_presigned_url = module.params.get('generate_presigned_url')
    caller_reference = module.params.get('caller_reference')
    comment = module.params.get('comment')
    e_tag = module.params.get('e_tag')
    pem_key_path = module.params.get('pem_key_path')
    pem_key_password = module.params.get('pem_key_password')
    cloudfront_url_to_sign = module.params.get('cloudfront_url_to_sign')
    presigned_url_expire_date = module.params.get('presigned_url_expire_date')
    config = module.params.get('config')
    tags = module.params.get('tags')
    purge_tags = module.params.get('purge_tags')
    distribution_id = module.params.get('distribution_id')
    streaming_distribution_id = module.params.get('streaming_distribution_id')
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
    ipv6_enabled = module.params.get('ipv6_enabled')
    s3_origin = module.params.get('s3_origin')
    trusted_signers = module.params.get('trusted_signers')
    default_origin_domain_name = module.params.get('default_origin_domain_name')
    default_origin_path = module.params.get('default_origin_path')
    default_s3_origin_access_identity = module.params.get('default_s3_origin_access_identity')
    default_s3_origin_domain_name = module.params.get('default_s3_origin_domain_name')
    default_streaming_s3_origin_access_identity = module.params.get('default_streaming_s3_origin_access_identity')
    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')

    distribution_id, streaming_distribution_id = validation_mgr.validate_id_from_alias_aliases_caller_reference(
        distribution_id, streaming_distribution_id, alias, aliases, caller_reference, streaming_distribution)

    create_distribution = state == 'present' and not streaming_distribution and distribution_id is None
    update_distribution = state == 'present' and not streaming_distribution and distribution_id is not None
    delete_distribution = state == 'absent' and not streaming_distribution
    create_streaming_distribution = state == 'present' and streaming_distribution and streaming_distribution_id is None
    update_streaming_distribution = state == 'present' and streaming_distribution and streaming_distribution_id is not None
    delete_streaming_distribution = state == 'absent' and streaming_distribution

    create_update_distribution = create_distribution or update_distribution
    create_update_streaming_distribution = create_streaming_distribution or update_streaming_distribution
    update_delete_distribution = update_distribution or delete_distribution
    update_delete_streaming_distribution = update_streaming_distribution or delete_streaming_distribution
    create = create_distribution or create_streaming_distribution
    update = update_distribution or update_streaming_distribution
    delete = delete_distribution or delete_streaming_distribution

    if update:
        default_origin_domain_name = None
        default_origin_path = None
        default_s3_origin_domain_name = None
        default_s3_origin_access_identity = None
        default_streaming_s3_origin_access_identity = None

    if state is None and not generate_presigned_url:
        module.fail_json(msg="Please select either a state or generate_presigned_url=yes.")

    if create and config is None:
        config = {}

    distribution_exists = validation_mgr.validate_distribution_exists(distribution_id, streaming_distribution_id, streaming_distribution)

    if update and not distribution_exists:
        module.fail_json(msg="No matching distribution exists.")

    if update_delete_distribution and distribution_exists:
        distribution_id, config, e_tag = validation_mgr.validate_distribution_id_etag(alias, distribution_id, config, e_tag)

    if update_delete_streaming_distribution and distribution_exists:
        streaming_distribution_id, config, e_tag = validation_mgr.validate_streaming_distribution_id_etag(alias, streaming_distribution_id, config, e_tag)

    if (create or update) and tags is not None:
        valid_tags = ansible_dict_to_boto3_tag_list(tags)

    if create or update or delete and config is not None:
        config = helpers.pascal_dict_to_snake_dict(config, True)

    if create or update:
        config = validation_mgr.validate_common_distribution_parameters(config, enabled, aliases, logging, price_class, comment,
                                                                        create_update_streaming_distribution)

    if create_update_distribution:
        valid_origins = validation_mgr.validate_origins(origins, default_origin_domain_name, default_s3_origin_access_identity, default_origin_path,
                                                        create_update_streaming_distribution, create_distribution)
        config = helpers.merge_validation_into_config(config, valid_origins, 'origins')
        config_origins = config.get('origins')
        valid_cache_behaviors = validation_mgr.validate_cache_behaviors(cache_behaviors, config_origins)
        config = helpers.merge_validation_into_config(config, valid_cache_behaviors, 'cache_behaviors')
        valid_default_cache_behavior = validation_mgr.validate_cache_behavior(default_cache_behavior, config_origins, True)
        config = helpers.merge_validation_into_config(config, valid_default_cache_behavior, 'default_cache_behavior')
        valid_custom_error_responses = validation_mgr.validate_custom_error_responses(custom_error_responses)
        config = helpers.merge_validation_into_config(config, valid_custom_error_responses, 'custom_error_responses')
        valid_restrictions = validation_mgr.validate_restrictions(restrictions)
        config = helpers.merge_validation_into_config(config, valid_restrictions, 'restrictions')
        config = validation_mgr.validate_distribution_config_parameters(config, default_root_object, ipv6_enabled, http_version, web_acl_id)
        valid_viewer_certificate = validation_mgr.validate_viewer_certificate(viewer_certificate)
        config = helpers.merge_validation_into_config(config, valid_viewer_certificate, 'viewer_certificate')

    if create_update_streaming_distribution:
        config = validation_mgr.validate_streaming_distribution_config_parameters(
            config, comment, trusted_signers, s3_origin, default_s3_origin_domain_name, default_streaming_s3_origin_access_identity)

    if create:
        config = validation_mgr.validate_caller_reference_for_distribution(config, caller_reference)

    if create or update or delete:
        config = helpers.snake_dict_to_pascal_dict(config)

    if generate_presigned_url:
        validated_pem_expire_date = validation_mgr.validate_presigned_url_expire_date(presigned_url_expire_date)
        result = service_mgr.generate_presigned_url(distribution_id, pem_key_path, pem_key_password, cloudfront_url_to_sign, validated_pem_expire_date)

    if create_distribution:
        result = service_mgr.create_distribution(config, valid_tags)

    if delete_distribution:
        if distribution_exists:
            result = service_mgr.delete_distribution(distribution_id, e_tag)
        else:
            changed = False

    if update_distribution:
        identical = validation_mgr.validate_distribution_requires_update(config, distribution_id)
        changed = not identical
        if not identical:
            result = service_mgr.update_distribution(config, distribution_id, e_tag)

    if create_streaming_distribution:
        result = service_mgr.create_streaming_distribution(config, valid_tags)

    if delete_streaming_distribution:
        if distribution_exists:
            result = service_mgr.delete_streaming_distribution(streaming_distribution_id, e_tag)
        else:
            changed = False

    if update_streaming_distribution:
        identical = validation_mgr.validate_distribution_requires_update(config, streaming_distribution_id, True)
        changed = not identical
        if not identical:
            result = service_mgr.update_streaming_distribution(config, streaming_distribution_id, e_tag)

    if update:
        arn = validation_mgr.validate_tagging_arn(alias, distribution_id, streaming_distribution_id)
        changed |= service_mgr.update_tags(valid_tags, purge_tags, arn, alias, distribution_id, streaming_distribution_id)

    if wait and (create or update):
        validation_mgr.wait_until_processed(wait_timeout, streaming_distribution, distribution_id, streaming_distribution_id, config.get('CallerReference'))

    module.exit_json(changed=changed, **helpers.pascal_dict_to_snake_dict(result))


if __name__ == '__main__':
    main()
