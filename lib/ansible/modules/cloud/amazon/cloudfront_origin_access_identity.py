#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
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

version_added: "2.5"

author: Willem van Ketwich (@wilvk)

extends_documentation_fragment:
  - aws
  - ec2

options:
    state:
      description: If the named resource should exist.
      choices:
        - present
        - absent
      default: update_origin_access_identity
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

notes:
  - does not support check mode

'''

EXAMPLES = '''

- name: create an origin access identity
  cloudfront_origin_access_identity:
    state: present
    caller_reference: this is an example reference
    comment: this is an example comment

- name: update an existing origin access identity using caller_reference as an identifier
  cloudfront_origin_access_identity:
     origin_access_identity_id: E17DRN9XUOAHZX
     caller_reference: this is an example reference
     comment: this is a new comment

- name: delete an existing origin access identity using caller_reference as an identifier
  cloudfront_origin_access_identity:
     state: absent
     caller_reference: this is an example reference
     comment: this is a new comment

'''

RETURN = '''
cloud_front_origin_access_identity:
  description: The origin access identity's information.
  returned: always
  type: complex
  contains:
    cloud_front_origin_access_identity_config:
      description: describes a url specifying the origin access identity.
      returned: always
      type: complex
      contains:
        caller_reference:
          description: a caller reference for the oai
          returned: always
          type: str
        comment:
          description: a comment describing the oai
          returned: always
          type: str
    id:
      description: a unique identifier of the oai
      returned: always
      type: str
    s3_canonical_user_id:
      description: the canonical user id of the user who created the oai
      returned: always
      type: str
e_tag:
  description: The current version of the origin access identity created.
  returned: always
  type: str
location:
  description: The fully qualified URI of the new origin access identity just created.
  returned: when initially created
  type: str

'''

from ansible.module_utils.ec2 import get_aws_connection_info, ec2_argument_spec
from ansible.module_utils.ec2 import boto3_conn
from ansible.module_utils.aws.cloudfront_facts import CloudFrontFactsServiceManager
from ansible.module_utils.ec2 import camel_dict_to_snake_dict
from ansible.module_utils.aws.core import AnsibleAWSModule
import datetime
from functools import partial
import json
import traceback

try:
    import botocore
    from botocore.signers import CloudFrontSigner
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # caught by imported AnsibleAWSModule


class CloudFrontOriginAccessIdentityServiceManager(object):
    """
    Handles cloudfront origin access identity service calls to aws
    """

    def __init__(self, module):
        self.module = module
        self.create_client('cloudfront')

    def create_client(self, resource):
        try:
            region, ec2_url, aws_connect_kwargs = get_aws_connection_info(self.module, boto3=True)
            self.client = boto3_conn(self.module, conn_type='client', resource=resource, region=region, endpoint=ec2_url, **aws_connect_kwargs)
        except (ClientError, BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Unable to establish connection.")

    def create_origin_access_identity(self, caller_reference, comment):
        try:
            return self.client.create_cloud_front_origin_access_identity(
                CloudFrontOriginAccessIdentityConfig={
                    'CallerReference': caller_reference,
                    'Comment': comment
                }
            )
        except (ClientError, BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error creating cloud front origin access identity.")

    def delete_origin_access_identity(self, origin_access_identity_id, e_tag):
        try:
            return self.client.delete_cloud_front_origin_access_identity(Id=origin_access_identity_id, IfMatch=e_tag)
        except (ClientError, BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error updating Origin Access Identity.")

    def update_origin_access_identity(self, caller_reference, comment, origin_access_identity_id, e_tag):
        changed = False
        new_config = {
            'CallerReference': caller_reference,
            'Comment': comment
        }

        try:
            current_config = self.client.get_cloud_front_origin_access_identity_config(
                Id=origin_access_identity_id)['CloudFrontOriginAccessIdentityConfig']
        except (ClientError, BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error getting Origin Access Identity config.")

        if new_config != current_config:
            changed = True

        try:
            # If the CallerReference is a value already sent in a previous identity request
            # the returned value is that of the original request
            result = self.client.update_cloud_front_origin_access_identity(
                CloudFrontOriginAccessIdentityConfig=new_config,
                Id=origin_access_identity_id,
                IfMatch=e_tag,
            )
        except (ClientError, BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error updating Origin Access Identity.")

        return result, changed


class CloudFrontOriginAccessIdentityValidationManager(object):
    """
    Manages Cloudfront Origin Access Identities
    """

    def __init__(self, module):
        self.module = module
        self.__cloudfront_facts_mgr = CloudFrontFactsServiceManager(module)

    def validate_etag_from_origin_access_identity_id(self, origin_access_identity_id):
        try:
            if origin_access_identity_id is None:
                return
            oai = self.__cloudfront_facts_mgr.get_origin_access_identity(origin_access_identity_id)
            if oai is not None:
                return oai.get('ETag')
        except (ClientError, BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error getting etag from origin_access_identity.")

    def validate_origin_access_identity_id_from_caller_reference(
            self, caller_reference):
        try:
            origin_access_identities = self.__cloudfront_facts_mgr.list_origin_access_identities()
            origin_origin_access_identity_ids = [oai.get('Id') for oai in origin_access_identities]
            for origin_access_identity_id in origin_origin_access_identity_ids:
                oai_config = (self.__cloudfront_facts_mgr.get_origin_access_identity_config(origin_access_identity_id))
                temp_caller_reference = oai_config.get('CloudFrontOriginAccessIdentityConfig').get('CallerReference')
                if temp_caller_reference == caller_reference:
                    return origin_access_identity_id
        except (ClientError, BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error getting Origin Access Identity from caller_reference.")

    def validate_comment(self, comment):
        if comment is None:
            return "origin access identity created by Ansible with datetime " + datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
        return comment


def main():
    argument_spec = ec2_argument_spec()

    argument_spec.update(dict(
        state=dict(choices=['present', 'absent'], default='present'),
        origin_access_identity_id=dict(),
        caller_reference=dict(),
        comment=dict(),
    ))

    result = {}
    e_tag = None
    changed = False

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=False)
    service_mgr = CloudFrontOriginAccessIdentityServiceManager(module)
    validation_mgr = CloudFrontOriginAccessIdentityValidationManager(module)

    state = module.params.get('state')
    caller_reference = module.params.get('caller_reference')

    comment = module.params.get('comment')
    origin_access_identity_id = module.params.get('origin_access_identity_id')

    if origin_access_identity_id is None and caller_reference is not None:
        origin_access_identity_id = validation_mgr.validate_origin_access_identity_id_from_caller_reference(caller_reference)

    e_tag = validation_mgr.validate_etag_from_origin_access_identity_id(origin_access_identity_id)
    comment = validation_mgr.validate_comment(comment)

    if state == 'present':
        if origin_access_identity_id is not None and e_tag is not None:
            result, changed = service_mgr.update_origin_access_identity(caller_reference, comment, origin_access_identity_id, e_tag)
        else:
            result = service_mgr.create_origin_access_identity(caller_reference, comment)
            changed = True
    elif(state == 'absent' and origin_access_identity_id is not None and
         e_tag is not None):
        result = service_mgr.delete_origin_access_identity(origin_access_identity_id, e_tag)
        changed = True

    result.pop('ResponseMetadata', None)

    module.exit_json(changed=changed, **camel_dict_to_snake_dict(result))


if __name__ == '__main__':
    main()
