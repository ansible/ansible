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
module: cloudfront_origin_access_identity
short_description: create, update and delete origin access identities for a
                   cloudfront distribution.
description:
    - Allows for easy creation, updating and deletion of origin access
      identities.
requirements:
  - boto3 >= 1.0.0
  - python >= 2.6
version_added: "2.4"
author: Willem van Ketwich (@wilvk)
options:
    state:
      description:
        - The state of the resource. Valid states are
            present
            absent
      required: false
      default: present
    origin_access_identity_id:
      description:
        - The origin_access_identity_id of the cloudfront distribution.
      required: false
    comment:
      description:
        - A comment to describe the cloudfront origin access identity.
      required: false
    caller_reference:
      description:
        - A unique identifier to reference the origin access identity by.
      required: false

'''

EXAMPLES = '''

# create an origin access identity

- cloudfront_origin_access_identity:
    state: present
    caller_reference: this is an example reference
    comment: this is an example comment

# update an existing origin access identity
# using caller_reference as an identifier

- cloudfront_origin_access_identity:
     state: present
     origin_access_identity_id: E17DRN9XUOAHZX
     caller_reference: this is an example reference
     comment: this is a new comment

# delete an existing origin access identity
# using caller_reference as an identifier

- cloudfront_origin_access_identity:
     state: absent
     caller_reference: this is an example reference
     comment: this is a new comment

'''

RETURN = '''

location:
    description: describes a url specifying the origin access identity.
    returned: always
    type: str

'''

from ansible.module_utils.ec2 import get_aws_connection_info, ec2_argument_spec
from ansible.module_utils.ec2 import boto3_conn, HAS_BOTO3
from ansible.modules.cloud.amazon.cloudfront_facts import (
    CloudFrontFactsServiceManager)
import ansible.module_utils.cloudfront as helpers
from ansible.module_utils.ec2 import camel_dict_to_snake_dict
from ansible.module_utils.basic import AnsibleModule
from botocore.signers import CloudFrontSigner
import datetime
from functools import partial
import json
import traceback

try:
    import botocore
except ImportError:
    pass


class CloudFrontOriginAccessIdentityServiceManager(object):
    """
    Handles cloudfront origin access identity service calls to aws
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

    def create_origin_access_identity(self, caller_reference, comment):
        try:
            return self.client.create_cloud_front_origin_access_identity(
                CloudFrontOriginAccessIdentityConfig={
                    'CallerReference': caller_reference,
                    'Comment': comment
                })
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(
                msg="error creating cloud front origin access identity - " +
                str(e) + "\n" + traceback.format_exc())

    def delete_origin_access_identity(self, origin_access_identity_id, e_tag):
        try:
            return self.client.delete_cloud_front_origin_access_identity(
                Id=origin_access_identity_id, IfMatch=e_tag)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(
                msg="error deleting cloud front origin access identity - " +
                str(e) + "\n" + traceback.format_exc())

    def update_origin_access_identity(self, caller_reference, comment,
                                      origin_access_identity_id, e_tag):
        try:
            return self.client.update_cloud_front_origin_access_identity(
                CloudFrontOriginAccessIdentityConfig={
                    'CallerReference': caller_reference,
                    'Comment': comment
                },
                Id=origin_access_identity_id, IfMatch=e_tag)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(
                msg="error updating cloud front origin access identity - " +
                str(e) + "\n" + traceback.format_exc())


class CloudFrontOriginAccessIdentityValidationManager(object):
    """
    Manages Cloudfront Origin Access Identities
    """

    def __init__(self, module):
        self.module = module
        self.__cloudfront_facts_mgr = CloudFrontFactsServiceManager(module)

    def validate_etag_from_origin_access_identity_id(self,
                                                     origin_access_identity_id):
        try:
            if origin_access_identity_id is None:
                return
            oai = self.__cloudfront_facts_mgr.get_origin_access_identity(
                origin_access_identity_id)
            if oai is not None:
                return oai.get('ETag')
        except Exception as e:
            self.module.fail_json(
                msg="error getting etag from origin_access_identity_id - " +
                str(e) + "\n" + traceback.format_exc())

    def validate_origin_access_identity_id_from_caller_reference(
            self, caller_reference):
        try:
            origin_access_identities = (
                self.__cloudfront_facts_mgr.list_origin_access_identities())
            origin_origin_access_identity_ids = [oai.get('Id') for oai in
                                                 origin_access_identities]
            for origin_access_identity_id in origin_origin_access_identity_ids:
                oai_config = (
                    self.__cloudfront_facts_mgr.get_origin_access_identity_config(
                        origin_access_identity_id))
                temp_caller_reference = oai_config.get(
                    'CloudFrontOriginAccessIdentityConfig').get(
                    'CallerReference')
                if temp_caller_reference == caller_reference:
                    return origin_access_identity_id
        except Exception as e:
            self.module.fail_json(
                msg="error getting origin access identity from " +
                "caller_reference - " + str(e) + "\n" + traceback.format_exc())

    def validate_comment(self, comment):
        if comment is None:
            comment = (
                "origin access identity created by Ansible with datetime " +
                datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f'))
        return comment


def main():
    argument_spec = ec2_argument_spec()

    argument_spec.update(dict(
        state=dict(choices=['present', 'absent'], default='present'),
        origin_access_identity_id=dict(required=False, default=None,
                                       type='str'),
        caller_reference=dict(required=False, default=None, type='str'),
        comment=dict(required=False, default=None, type='str')
    ))

    result = {}
    e_tag = None
    changed = False

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False)
    service_mgr = CloudFrontOriginAccessIdentityServiceManager(module)
    validation_mgr = CloudFrontOriginAccessIdentityValidationManager(module)

    state = module.params.get('state')
    caller_reference = module.params.get('caller_reference')
    comment = module.params.get('comment')
    origin_access_identity_id = module.params.get('origin_access_identity_id')

    if origin_access_identity_id is None and caller_reference is not None:
        origin_access_identity_id = (
            validation_mgr.validate_origin_access_identity_id_from_caller_reference(
                caller_reference))

    if origin_access_identity_id is not None and state == 'present':
        state = 'updated'

    if state != 'present':
        e_tag = validation_mgr.validate_etag_from_origin_access_identity_id(
            origin_access_identity_id)

    if state == 'present':
        comment = validation_mgr.validate_comment(comment)
        result = service_mgr.create_origin_access_identity(
            caller_reference, comment)
        changed = True
    elif(state == 'absent' and origin_access_identity_id is not None and
         e_tag is not None):
        result = service_mgr.delete_origin_access_identity(
            origin_access_identity_id, e_tag)
        changed = True
    elif state == 'updated':
        result = service_mgr.update_origin_access_identity(
            caller_reference, comment, origin_access_identity_id, e_tag)
        changed = True

    if result:
        results = result
        results.pop('ResponseMetadata', None)
        result.update(results)

    module.exit_json(changed=changed, **helpers.pascal_dict_to_snake_dict(result))


if __name__ == '__main__':
    main()
