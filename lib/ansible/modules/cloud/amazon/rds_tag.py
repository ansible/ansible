#!/usr/bin/python
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: rds_tag
short_description: create and remove tag(s) to rds instance.
description: >
  Creates, removes and lists tags from any rds instance.
  The instance is referenced by its instance name.
  It is designed to be used with complex args (tags), see the examples.
  This module has a dependency on python-boto3.
version_added: "2.7"
options:
  instance_name:
    description:
      - The RDS instance name.
  state:
    description: >
      Whether the tags should be present or absent on the resource.
      Use list to interrogate the tags of an instance.
    default: present
    choices: ['present', 'absent']
  tags:
    description: >-
      a hash/dictionary of tags to add to the resource;
      '{"key":"value"}' and '{"key":"value","key":"value"}'
    required: true
extends_documentation_fragment:
    - aws
    - ec2

author: "Nao Morikawa (@cahlchang)"
'''

EXAMPLES = '''
# Note: None of these examples set aws_access_key, aws_secret_key, or region.
# It is assumed that their matching environment variables are set.

- name: add tags to instance
  rds_tag:
    region: eu-west-1
    instance_name: name-database
    state: present
    tags:
      Name: environment
      env: sandbox

- name: remove tags to instance
  rds_tag:
    region: eu-west-1
    instance_name: name-database
    state: absent
    tags:
      Name: environment
      env: sandbox
'''

RETURN = '''
---
changed:
  description: Whether there was any change.
  returned: always
  type: bool
  sample: true
message:
  description: Summary of module execution results.
  returned: always
  type: string
  sample: Add tag to arn:aws:rds:eu-west-1:xxxxxxxxxxxx:db:db_name instance
response_metadata:
  description: Value returned by boto3.
  returned: When not in dry run mode.
  type: dict
  sample:
    http_headers:
      content-length: xxx
      content-type: text/xml
      date: Mon, 02 Apr 2018 03:53:23 GMT
      x-amzn-requestid: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    http_status_code: 200
    request_id: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    retry_attempts: 0
'''

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import (
    ec2_argument_spec, camel_dict_to_snake_dict, compare_aws_tags,
    ansible_dict_to_boto3_tag_list, boto3_tag_list_to_ansible_dict)

try:
    import botocore
except ImportError:
    pass  # handled by AnsibleAWSModule


def add_rds_tags(module, client, tags_configured, tags_operate):
    lst_compare = compare_aws_tags(tags_configured['tags'],
                                   tags_operate,
                                   False)
    if 0 == len(lst_compare[0]):
        module.exit_json(message='tags already exists.', changed=False)

    if module.check_mode:
        module.exit_json(message='check mode.', changed=True)

    tags_add = lst_compare[0]
    try:
        response = client.add_tags_to_resource(
            ResourceName=tags_configured['arn'],
            Tags=ansible_dict_to_boto3_tag_list(tags_add))
    except (botocore.exceptions.ClientError,
            botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't add tag to %s"
                             % tags_configured['arn'])

    response['message'] = 'Add %s tag to %s instance' % (
        tags_add,
        tags_configured['arn'])

    return response


def remove_rds_tags(module, client, tags_configured, tags_operate):
    tags_inter = set(tags_operate.keys()) & set(tags_configured['tags'].keys())
    if 0 == len(tags_inter):
        module.exit_json(message='nothing to tags.', changed=False)

    if module.check_mode:
        module.exit_json(message='check mode.', changed=True)

    try:
        response = client.remove_tags_from_resource(
            ResourceName=tags_configured['arn'],
            TagKeys=list(tags_inter))
    except (botocore.exceptions.ClientError,
            botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e,
                             msg="Couldn't remove tag to %s instance"
                             % tags_configured['arn'])

    response['message'] = 'Remove %s tag to %s instance' % (
        list(tags_inter), tags_configured['arn'])

    return response


def get_rds_arn(module, client, instance_name):
    try:
        response_instances = client.describe_db_instances(
            DBInstanceIdentifier=instance_name)
    except (botocore.exceptions.ClientError,
            botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't find %s instance"
                             % instance_name)

    return {'arn': response_instances['DBInstances'][0]['DBInstanceArn'],
            'identifier':
            response_instances['DBInstances'][0]['DBInstanceIdentifier']}


def get_rds_tags(module, client, instance_name, map_rds_arn):
    try:
        response_tags = client.list_tags_for_resource(
            ResourceName=map_rds_arn['arn'])
    except (botocore.exceptions.ClientError,
            botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't get %s instance's tag"
                             % instance_name)

    tags = boto3_tag_list_to_ansible_dict(response_tags['TagList'])

    return {'identifier': map_rds_arn['identifier'],
            'tags': tags,
            'arn': map_rds_arn['arn']}


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            instance_name=dict(required=True),
            tags=dict(type='dict', required=True),
            state=dict(default='present',
                       type='str',
                       choices=['present', 'absent'])
        )
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True)

    client = module.client('rds')

    instance_name = module.params.get('instance_name')
    tags_operate = module.params.get('tags')
    state = module.params.get('state')

    map_rds_arn = get_rds_arn(module, client, instance_name)
    tags_configured = get_rds_tags(module,
                                   client,
                                   instance_name,
                                   map_rds_arn)

    if state == 'present':
        response = add_rds_tags(module, client, tags_configured, tags_operate)
        module.exit_json(changed=True,
                         **camel_dict_to_snake_dict(response))

    response = remove_rds_tags(module, client, tags_configured, tags_operate)
    module.exit_json(changed=True,
                     **camel_dict_to_snake_dict(response))

if __name__ == '__main__':
    main()
