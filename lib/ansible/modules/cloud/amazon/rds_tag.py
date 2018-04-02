#!/usr/bin/python
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (HAS_BOTO3, boto3_conn, ec2_argument_spec, get_aws_connection_info)

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: rds_tag
short_description: create and remove tag(s) to rds instance.
description:
    - Creates, removes and lists tags from any rds instance. The instance is referenced by its instance name.
      It is designed to be used with complex args (tags), see the examples.  This module has a dependency on python-boto3.
options:
  instance_name:
    description:
      - The RDS instance name.
  state:
    description:
      - Whether the tags should be present or absent on the resource. Use list to interrogate the tags of an instance.
    default: present
    choices: ['present', 'absent', 'list']
  tags:
    description:
      - a hash/dictionary of tags to add to the resource; '{"key":"value"}' and '{"key":"value","key":"value"}'
    required: true
'''

EXAMPLES = '''
- name: Ensure tags are present on a resource
  rds_tag:
    region: eu-west-1
    instance_name: name-database
    state: present
    tags:
      Name: environment
      env: sandbox
'''

try:
    import boto3
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False


def list_rds_arn(client, instance_name):
    if instance_name is None:
        response_instances = client.describe_db_instances()
    else:
        response_instances = client.describe_db_instances(
            DBInstanceIdentifier=instance_name)

    list_arn = [{'arn': instance['DBInstanceArn'],
                 'identifier': instance['DBInstanceIdentifier']}
                for instance in response_instances['DBInstances']]

    return list_arn


def list_rds_tags(client, list_arn):
    list_tags = []
    for map_arn in list_arn:
        response_tags = client.list_tags_for_resource(
            ResourceName=map_arn['arn'])
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

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True)

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

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

    if state == 'present':
        configured_tags = list_tags[0]

        if set(tags.items()) <= set(configured_tags['tags'].items()):
            module.exit_json(message='tags already exists.', changed=False)

        if module.check_mode:
            module.exit_json(message='check mode.', changed=True)

        add_tags = [{'Key': datum[0], 'Value': datum[1]}
                    for datum in tags.items()]
        response = client.add_tags_to_resource(
            ResourceName=configured_tags['arn'],
            Tags=add_tags)
        module.exit_json(msg="tags %s created for resource %s." %
                         (add_tags, instance_name), changed=True)

    if state == 'absent':
        configured_tags = list_tags[0]

        if not set(tags.keys()) <= set(configured_tags['tags'].keys()):
            module.exit_json(message='nothing to tags.', changed=False)

        if module.check_mode:
            module.exit_json(message='check mode.', changed=True)

        response = client.remove_tags_from_resource(
            ResourceName=configured_tags['arn'],
            TagKeys=tags.keys())

        module.exit_json(msg="tags %s remove for resource %s." %
                         (tags.keys(), instance_name), changed=True)

if __name__ == '__main__':
    main()
