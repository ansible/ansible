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
version_added: "2.5"
options:
  instance_name:
    description:
      - The RDS instance name.
  state:
    description: >
      Whether the tags should be present or absent on the resource.
      Use list to interrogate the tags of an instance.
    default: present
    choices: ['present', 'absent', 'list']
  tags:
    description: >-
      a hash/dictionary of tags to add to the resource;
      '{"key":"value"}' and '{"key":"value","key":"value"}'
    required: true
extends_documentation_fragment:
    - aws
    - ec2

author: "Akane Morikawa (@cahlchang)"
'''

EXAMPLES = '''
# Note: None of these examples set aws_access_key, aws_secret_key, or region.
# It is assumed that their matching environment variables are set.
- name: Ensure tags are present on a instance
  rds_tag:
    region: eu-west-1
    instance_name: name-database
    state: list

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
invocation:
  description: Parameters used during invocation.
  returned: always
  type: dict
  sample:
    module_args:
      aws_access_key: null
      aws_secret_key: null
      ec2_url: null
      instance_name: xxx-instance
      profile: your profile
      region: eu-west-1
      security_token: null
      state: present
      tags:
        your_setting_key_a: your_setting_value_a
        your_setting_key_b: your_setting_value_b
      validate_certs: true
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
    HAS_BOTO3, ec2_argument_spec, boto3_conn, get_aws_connection_info)
from ansible.module_utils.ec2 import (
    camel_dict_to_snake_dict, snake_dict_to_camel_dict)

try:
    import botocore
except ImportError:
    pass  # handled by AnsibleAWSModule


def add_rds_tags(module, client, configured_tags, tags):
    if set(tags.items()) <= set(configured_tags['tags'].items()):
        module.exit_json(message='tags already exists.', changed=False)

    if module.check_mode:
        module.exit_json(message='check mode.', changed=True)

    add_tags = [{'Key': datum[0], 'Value': datum[1]}
                for datum in tags.items()]
    try:
        response = client.add_tags_to_resource(
            ResourceName=configured_tags['arn'],
            Tags=add_tags)
    except (botocore.exceptions.ClientError,
            botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't add tag to %s"
                             % configured_tags['arn'])
    return response


def remove_rds_tags(module, client, configured_tags, tags):
    if not set(tags.keys()) <= set(configured_tags['tags'].keys()):
        module.exit_json(message='nothing to tags.', changed=False)

    if module.check_mode:
        module.exit_json(message='check mode.', changed=True)

    try:
        response = client.remove_tags_from_resource(
            ResourceName=configured_tags['arn'],
            TagKeys=list(tags.keys()))
    except (botocore.exceptions.ClientError,
            botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e,
                             msg="Couldn't remove tag to %s instance"
                             % configured_tags['arn'])
    return response


def list_rds_arn(client, instance_name):
    if instance_name is None:
        try:
            response_instances = client.describe_db_instances()
        except (botocore.exceptions.ClientError,
                botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't find RDS instance")
    else:
        try:
            response_instances = client.describe_db_instances(
                DBInstanceIdentifier=instance_name)
        except (botocore.exceptions.ClientError,
                botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't find %s instance"
                                 % instance_name)

    list_arn = [{'arn': instance['DBInstanceArn'],
                 'identifier': instance['DBInstanceIdentifier']}
                for instance in response_instances['DBInstances']]

    return list_arn


def list_rds_tags(client, list_arn):
    list_tags = []
    for map_arn in list_arn:
        try:
            response_tags = client.list_tags_for_resource(
                ResourceName=map_arn['arn'])
        except (botocore.exceptions.ClientError,
                botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't get %s instance's tag"
                                 % instance_name)
        tags = {}
        for datum in response_tags['TagList']:
            tags[datum['Key']] = datum['Value']

        list_tags.append({'identifier': map_arn['identifier'],
                          'tags': tags,
                          'arn': map_arn['arn']})
    return list_tags


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            instance_name=dict(type='str'),
            tags=dict(type='dict'),
            state=dict(type='str',
                       choices=['present', 'absent', 'list'],
                       required=True)
        )
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True)

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module,
                                                                  boto3=True)

    client = boto3_conn(module, conn_type='client', resource='rds',
                        region=region, **aws_connect_kwargs)

    instance_name = module.params.get('instance_name')
    tags = module.params.get('tags')
    state = module.params.get('state')

    list_arn = list_rds_arn(client, instance_name)
    list_tags = list_rds_tags(client, list_arn)

    if state == 'list':
        module.exit_json(tags=list_tags, changed=False)

    if not instance_name:
        module.fail_json(
            msg="instance_name argument is required when state is %s." % state)

    if not tags:
        module.fail_json(
            msg="tags argument is required when state is %s." % state)

    configured_tags = list_tags[0]
    if state == 'present':
        response = add_rds_tags(module, client, configured_tags, tags)
        module.exit_json(changed=True,
                         **camel_dict_to_snake_dict(response))

    if state == 'absent':
        response = remove_rds_tags(module, client, configured_tags, tags)
        module.exit_json(changed=True,
                         **camel_dict_to_snake_dict(response))

if __name__ == '__main__':
    main()
