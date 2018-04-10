#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: s3_website
short_description: Configure an s3 bucket as a website
description:
    - Configure an s3 bucket as a website
version_added: "2.2"
requirements: [ boto3 ]
author: Rob White (@wimnat)
options:
  name:
    description:
      - "Name of the s3 bucket"
    required: true
    default: null
  error_key:
    description:
      - "The object key name to use when a 4XX class error occurs. To remove an error key, set to None."
    required: false
    default: null
  redirect_all_requests:
    description:
      - "Describes the redirect behavior for every request to this s3 bucket website endpoint"
    required: false
    default: null
  region:
    description:
     - >
       AWS region to create the bucket in. If not set then the value of the AWS_REGION and EC2_REGION environment variables are checked,
       followed by the aws_region and ec2_region settings in the Boto config file.  If none of those are set the region defaults to the
       S3 Location: US Standard.
    required: false
    default: null
  state:
    description:
      - "Add or remove s3 website configuration"
    required: false
    default: present
    choices: [ 'present', 'absent' ]
  suffix:
    description:
      - >
        Suffix that is appended to a request that is for a directory on the website endpoint (e.g. if the suffix is index.html and you make a request to
        samplebucket/images/ the data that is returned will be for the object with the key name images/index.html). The suffix must not include a slash
        character.
    required: false
    default: index.html

extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Configure an s3 bucket to redirect all requests to example.com
- s3_website:
    name: mybucket.com
    redirect_all_requests: example.com
    state: present

# Remove website configuration from an s3 bucket
- s3_website:
    name: mybucket.com
    state: absent

# Configure an s3 bucket as a website with index and error pages
- s3_website:
    name: mybucket.com
    suffix: home.htm
    error_key: errors/404.htm
    state: present

'''

RETURN = '''
index_document:
    description: index document
    type: complex
    returned: always
    contains:
        suffix:
            description: suffix that is appended to a request that is for a directory on the website endpoint
            returned: success
            type: string
            sample: index.html
error_document:
    description: error document
    type: complex
    returned: always
    contains:
        key:
            description:  object key name to use when a 4XX class error occurs
            returned: when error_document parameter set
            type: string
            sample: error.html
redirect_all_requests_to:
    description: where to redirect requests
    type: complex
    returned: always
    contains:
        host_name:
            description: name of the host where requests will be redirected.
            returned: when redirect all requests parameter set
            type: string
            sample: ansible.com
routing_rules:
    description: routing rules
    type: complex
    returned: always
    contains:
        routing_rule:
            host_name:
                description: name of the host where requests will be redirected.
                returned: when host name set as part of redirect rule
                type: string
                sample: ansible.com
        condition:
            key_prefix_equals:
            description: object key name prefix when the redirect is applied. For example, to redirect requests for ExamplePage.html, the key prefix will be
                     ExamplePage.html
            returned: when routing rule present
            type: string
            sample: docs/
        redirect:
            replace_key_prefix_with:
                description: object key prefix to use in the redirect request
                returned: when routing rule present
                type: string
                sample: documents/
'''

import time

try:
    import boto3
    from botocore.exceptions import ClientError, ParamValidationError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (HAS_BOTO3, boto3_conn, camel_dict_to_snake_dict, ec2_argument_spec,
                                      get_aws_connection_info)


def _create_redirect_dict(url):

    redirect_dict = {}
    url_split = url.split(':')

    # Did we split anything?
    if len(url_split) == 2:
        redirect_dict[u'Protocol'] = url_split[0]
        redirect_dict[u'HostName'] = url_split[1].replace('//', '')
    elif len(url_split) == 1:
        redirect_dict[u'HostName'] = url_split[0]
    else:
        raise ValueError('Redirect URL appears invalid')

    return redirect_dict


def _create_website_configuration(suffix, error_key, redirect_all_requests):

    website_configuration = {}

    if error_key is not None:
        website_configuration['ErrorDocument'] = {'Key': error_key}

    if suffix is not None:
        website_configuration['IndexDocument'] = {'Suffix': suffix}

    if redirect_all_requests is not None:
        website_configuration['RedirectAllRequestsTo'] = _create_redirect_dict(redirect_all_requests)

    return website_configuration


def enable_or_update_bucket_as_website(client_connection, resource_connection, module):

    bucket_name = module.params.get("name")
    redirect_all_requests = module.params.get("redirect_all_requests")
    # If redirect_all_requests is set then don't use the default suffix that has been set
    if redirect_all_requests is not None:
        suffix = None
    else:
        suffix = module.params.get("suffix")
    error_key = module.params.get("error_key")
    changed = False

    try:
        bucket_website = resource_connection.BucketWebsite(bucket_name)
    except ClientError as e:
        module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))

    try:
        website_config = client_connection.get_bucket_website(Bucket=bucket_name)
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchWebsiteConfiguration':
            website_config = None
        else:
            module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))

    if website_config is None:
        try:
            bucket_website.put(WebsiteConfiguration=_create_website_configuration(suffix, error_key, redirect_all_requests))
            changed = True
        except (ClientError, ParamValidationError) as e:
            module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))
        except ValueError as e:
            module.fail_json(msg=str(e))
    else:
        try:
            if (suffix is not None and website_config['IndexDocument']['Suffix'] != suffix) or \
                    (error_key is not None and website_config['ErrorDocument']['Key'] != error_key) or \
                    (redirect_all_requests is not None and website_config['RedirectAllRequestsTo'] != _create_redirect_dict(redirect_all_requests)):

                try:
                    bucket_website.put(WebsiteConfiguration=_create_website_configuration(suffix, error_key, redirect_all_requests))
                    changed = True
                except (ClientError, ParamValidationError) as e:
                    module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))
        except KeyError as e:
            try:
                bucket_website.put(WebsiteConfiguration=_create_website_configuration(suffix, error_key, redirect_all_requests))
                changed = True
            except (ClientError, ParamValidationError) as e:
                module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))
        except ValueError as e:
            module.fail_json(msg=str(e))

        # Wait 5 secs before getting the website_config again to give it time to update
        time.sleep(5)

    website_config = client_connection.get_bucket_website(Bucket=bucket_name)
    module.exit_json(changed=changed, **camel_dict_to_snake_dict(website_config))


def disable_bucket_as_website(client_connection, module):

    changed = False
    bucket_name = module.params.get("name")

    try:
        client_connection.get_bucket_website(Bucket=bucket_name)
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchWebsiteConfiguration':
            module.exit_json(changed=changed)
        else:
            module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))

    try:
        client_connection.delete_bucket_website(Bucket=bucket_name)
        changed = True
    except ClientError as e:
        module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))

    module.exit_json(changed=changed)


def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(type='str', required=True),
            state=dict(type='str', required=True, choices=['present', 'absent']),
            suffix=dict(type='str', required=False, default='index.html'),
            error_key=dict(type='str', required=False),
            redirect_all_requests=dict(type='str', required=False)
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[
            ['redirect_all_requests', 'suffix'],
            ['redirect_all_requests', 'error_key']
        ])

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)

    if region:
        client_connection = boto3_conn(module, conn_type='client', resource='s3', region=region, endpoint=ec2_url, **aws_connect_params)
        resource_connection = boto3_conn(module, conn_type='resource', resource='s3', region=region, endpoint=ec2_url, **aws_connect_params)
    else:
        module.fail_json(msg="region must be specified")

    state = module.params.get("state")

    if state == 'present':
        enable_or_update_bucket_as_website(client_connection, resource_connection, module)
    elif state == 'absent':
        disable_bucket_as_website(client_connection, module)


if __name__ == '__main__':
    main()
