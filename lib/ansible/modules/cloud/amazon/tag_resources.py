#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, yanan@epicon.com.au
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

import json
import traceback

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass    # Handled by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule

DOCUMENTATION = '''
---
module: tag_resources
version_added: "2.9"
short_description: manage AWS resources tags.
description:
     - tag or untag AWS resoruce tags.
     - Check https://docs.aws.amazon.com/ARG/latest/userguide/supported-resources.html for the supported resources
options:
  state:
    description:
      - Specify the desired state of the tag.
    choices: [ 'present', 'absent']
    type: str
  arns:
    description:
      - The resource arns .
    required: true
    aliases:
      - resource_arns
    type: list
  tags:
    description:
      - tags dict to apply to the resources. Required when the state is present
    type: dict
  tag_keys:
    description:
      - tags list to be applyed for untagging from the resources.
      - If the tag_keys is not provided , the module uses the argument tags instead.
      - Either tag_keys or tags is required when the state is absent.
    type: list
requirements:
    - "python >= 2.6"
    - "boto3"
author:
    - "yanan@epicon.com.au"
extends_documentation_fragment:
  - ec2
  - aws
'''

EXAMPLES = """
- name: Tag elasticache cluster
  tag_resources:
    arns:
      - "arn:aws:elasticache:us-east-2:0000000:cluster:test-mem"
    state: present
    tags:  {  "key_1": "value_1" ,    "key_2": "value_2"}
  delegate_to: localhost

- name: Untag elasticache cluster with argument tags
  tag_resources:
    arns:
      - "arn:aws:elasticache:us-east-2:0000000:cluster:test-mem"
    state: absent
    tags:  {  "key_1": "value_1" ,    "key_2": "value_2"}
  delegate_to: localhost

- name: Untag elasticache cluster with argument tag_keys
  tag_resources:
    arns:
      - "arn:aws:elasticache:us-east-2:0000000:cluster:test-mem"
    state: absent
    tags:
      - "key_1"
      - "key_2"
  delegate_to: localhost
"""

RETURN = """
httpstatuscode:
  description: The http status code for the request
  returned: always
  type: int
  sample: OK
requestid:
  description: The message ID of the submitted message
  returned: when success to submit
  type: str
  sample: 2f681ef0-6d76-5c94-99b2-4ae3996ce57b
success:
  description: Is the tag/untag successful.
  returned: always
  type: bool
error:
  description: The error details
  returned: if the error happens
  type: complex
  contains:
    <dynamic arn>:
      description: The resource arn
      returned: always
      type: str
      contains:
        ErrorCode:
          description: The error code
          returned: always
          type: str
        ErrorMessage:
          description: The error reason
          returned: always
          type: str
        StatusCode:
          description: The error status code
          returned: always
          type: int

"""


def tag_resources(module, tag_client, tags ,resources  ):
    try:
      if len(resources) > 20:
          module.fail_json(msg="The size of resource arns can't be exceeded than 20 ")
      if len(resources) == 0:
          module.fail_json(msg="At least one resource arn needs to be provided")
      resp = tag_client.tag_resources(
                ResourceARNList=resources,
                Tags=tags
              )
      return _handle_tag_resp(resp)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg='Failed to untag_resource')    

def untag_resources(module,tag_client, tag_keys ,resources  ):
    try:
      if len(resources) > 20:
          module.fail_json(msg="The size of arns can't be exceeded than 20 ")
      if len(resources) == 0:
          module.fail_json(msg="At least one resource arn needs to be provided")
      resp = tag_client.untag_resources(
          ResourceARNList=resources,
          TagKeys=tag_keys
          )
      return _handle_tag_resp(resp)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg='Failed to untag_resource')

def _handle_tag_resp(resp):
      result = {
                "requestid": resp["ResponseMetadata"]["RequestId"],
                "httpstatuscode": resp["ResponseMetadata"]["HTTPStatusCode"],
              }
      if resp["ResponseMetadata"]["HTTPStatusCode"] == 200:
        if resp.get("FailedResourcesMap",{})  != {} :
            result["success"] = False
            result["error"] = resp["FailedResourcesMap"]
        else:
            result["success"] = True     
      else:
            result["success"] = False
      return result


def main():
   
    exit_result = dict() 
    argument_spec = dict(
        tag_keys=dict(required=False, type='list', elements='str', aliases=['tag_keys']),
        tags=dict(required=False, type='dict'),
        arns=dict(required=True, type='list', aliases=['resource_arns']),
        state=dict(required=True, choices=['present', 'absent'])
    )
    

    module = AnsibleAWSModule(argument_spec=argument_spec)
    client = module.client('resourcegroupstaggingapi')

    arns = module.params['arns']
    tags = module.params.get('tags',None)
    tag_keys = module.params.get('tag_keys',None)

    if module.params['state'] == "present":
      if tags == None:
        module.fail_json(msg="argument tags is required for the present state")
      result = tag_resources(module,client,tags,arns)
      exit_result.update(result)
    

    if module.params['state'] == "absent":
      if tags == None and tag_keys== None:
        module.fail_json(msg="Either argument tags or tag_keys is required for the absent state")
      if tag_keys != None:
        result = untag_resources(module,client,tag_keys,arns)
        exit_result.update(result)
      else:
        result = untag_resources(module,client,tags.keys(),arns)
        exit_result.update(result)
      ## Assume the changed is true if it's no error , as it's not worth to check each resource's tag status
    if exit_result["success"]:
      exit_result["changed"] = True
    module.exit_json(**exit_result)



if __name__ == '__main__':
    main()