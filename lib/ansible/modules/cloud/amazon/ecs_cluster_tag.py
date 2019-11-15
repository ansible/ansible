#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ecs_cluster_tag
short_description: create and remove tags on ecs clusters.
description:
    - Creates, removes and lists tags for an ecs_cluster.  The resource is referenced by its cluster name.
      It is designed to be used with complex args (tags), see the examples.
version_added: "2.8"
requirements: [ "boto3", "botocore" ]
options:
  cluster_name:
    description:
      - The name of the cluster who's resources we are tagging
    required: true
  resource:
    description:
      - The ecs resource name. Can be none only if resource_type is cluster.
    required: false
  resource_type:
    description:
      - The type of resource
      default: cluster
      choices: ['cluster', 'task', 'service', task_definition', 'container']
  state:
    description:
      - Whether the tags should be present or absent on the resource. Use 
        list to interrogate the tags of a ecs resource.
    default: present
    choices: ['present', 'absent', 'list']
  tags:
    description:
      - A dictionary of tags to add or remove from the resource.
      - If the value provided for a tag is null and C(state) is I(absent), the 
        tag will be removed regardless of its current value.
    required: true
  purge_tags:
    description:
      - Whether unspecified tags should be removed from the resource.
      - "Note that when combined with C(state: absent), specified tags with non-matching values are not purged."
    type: bool
    default: no
    version_added: '2.8'

author:
  - Lester Wade (@lwade)
  - Paul Arthur (@flowerysong)
  - Michael Pechner (@mpechner)
extends_documentation_fragment:
    - aws
    - ecs
'''

EXAMPLES = '''
- name: Ensure tags are present on a resource
  ecs_cluster_tag:
    region: eu-west-1
    cluster_name: mycluster
    resource_type: cluster
    state: present
    tags:
      Name: ubervol
      env: prod

- name: Retrieve all tags on a cluster
  ecs_cluster_tag:
    region: eu-west-1
    cluster_name: mycluster
    resource: http_task
    resource_type: task 
    state: list
  register: ecs_cluster_tags

- name: Remove the Env tag
  ecs_cluster_tag:
    region: eu-west-1
    cluster_name: mycluster
    resource_type: cluster
    tags:
      Env:
    state: absent

- name: Remove the Env tag if it's currently 'development'
  ecs_cluster_tag:
    region: eu-west-1
    cluster_name: mycluster
    resource_type: cluster
    tags:
      Env: development
    state: absent

- name: Remove all tags except for Name from a cluster
  ecs_cluster_tag:
    region: eu-west-1
    cluster_name: mycluster
    resource_type: cluster
    tags:
        Name: ''
    state: absent
    purge_tags: true
'''

RETURN = '''
tags:
  description: A dict containing the tags on the resource
  returned: always
  type: dict
added_tags:
  description: A dict of tags that were added to the resource
  returned: If tags were added
  type: dict
removed_tags:
  description: A dict of tags that were removed from the resource
  returned: If tags were removed
  type: dict
'''

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_tag_list_to_ansible_dict, ansible_dict_to_boto3_tag_list, compare_aws_tags

try:
    from botocore.exceptions import BotoCoreError, ClientError
except Exception:
    pass    # Handled by AnsibleAWSModule


def get_tags(ecs, module, resource):
    try:
        return boto3_tag_list_to_ansible_dict(ecs.list_tags_for_resource(resourceArn=resource)['tags'])
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg='Failed to fetch tags for resource {0}'.format(resource))


def main():
    argument_spec = dict(
        cluster_name=dict(required=True),
        resource=dict(required=False),
        tags=dict(type='dict'),
        purge_tags=dict(type='bool', default=False),
        state=dict(default='present', choices=['present', 'absent', 'list']),
        resource_type=dict(default='cluster', choices=['cluster', 'task', 'service', 'task_definition', 'container'])
    )
    required_if = [('state', 'present', ['tags']), ('state', 'absent', ['tags'])]

    module = AnsibleAWSModule(argument_spec=argument_spec, required_if=required_if, supports_check_mode=True)

    resource_type = module.params['resource_type']
    cluster_name = module.params['cluster_name']
    if resource_type == 'cluster':
        resource = cluster_name
    else:
        resource = module.params['resource']
    tags = module.params['tags']
    state = module.params['state']
    purge_tags = module.params['purge_tags']

    result = {'changed': False}

    ecs = module.client('ecs')

    try:
        if resource_type == 'cluster':
            description = ecs.describe_clusters(clusters=[resource])
            if len(description['clusters']) == 0:
                module.fail_json(msg='Failed to find {0} {1}'.format(resource_type, resource))
            resource_arn = description['clusters'][0]['clusterArn']
        elif resource_type == 'task':
            description = ecs.describe_tasks(cluster=cluster_name, tasks=[resource])
            if len(description['tasks']) == 0:
                module.fail_json(msg='Failed to find {0} {1}'.format(resource_type, resource))
            resource_arn = description['tasks'][0]['taskArn']
        elif resource_type == 'service':
            description = ecs.describe_services(cluster=cluster_name, services=[resource])
            if len(description['services']) == 0:
                module.fail_json(msg='Failed to find {0} {1}'.format(resource_type, resource))
            resource_arn = description['services'][0]['serviceArn']
        elif resource_type == 'task_definition':
            description = ecs.describe_task_definition(taskDefinition=resource)
            if 'taskDefinition' not in description or 'taskDefinitionArn' not in description['taskDefinition']:
                module.fail_json(msg='Failed to find {0} {1}'.format(resource_type, resource))
            resource_arn = description['taskDefinition']['taskDefinitionArn']
        elif resource_type == 'container':
            description = ecs.describe_container_instances(clusters=[resource])
            if len(description['containerInstances']) == 0:
                module.fail_json(msg='Failed to find {0} {1}'.format(resource_type, resource))
            resource_arn = description['containerInstances'][0]['containerInstanceArn']
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg='Failed to find {0} {1}'.format(resource_type, resource))

    current_tags = get_tags(ecs, module, resource_arn)

    if state == 'list':
        module.exit_json(changed=False, tags=current_tags)

    add_tags, remove = compare_aws_tags(current_tags, tags, purge_tags=purge_tags)

    remove_tags = {}
    if state == 'absent':
        for key in tags:
            if key in current_tags and (tags[key] is None or current_tags[key] == tags[key]):
                remove_tags[key] = current_tags[key]

    for key in remove:
        remove_tags[key] = current_tags[key]

    if remove_tags:
        result['changed'] = True
        result['removed_tags'] = remove_tags
        if not module.check_mode:
            try:
                ecs.untag_resource(resourceArn=resource_arn, tagKeys=remove_tags.keys())
            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e, msg='Failed to remove tags {0} from resource {1}'.format(remove_tags, resource))

    if state == 'present' and add_tags:
        result['changed'] = True
        result['added_tags'] = add_tags
        current_tags.update(add_tags)
        if not module.check_mode:
            try:
                tags = ansible_dict_to_boto3_tag_list(add_tags, tag_name_key_name='key', tag_value_key_name='value')
                ecs.tag_resource(resourceArn=resource_arn, tags=tags)
            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e, msg='Failed to set tags {0} on resource {1}'.format(add_tags, resource))

    result['tags'] = get_tags(ecs, module, resource_arn)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
