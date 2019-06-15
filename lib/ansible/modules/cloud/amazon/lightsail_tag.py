#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Timon Schroeder <thyme-87@posteo.me>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: lightsail_tag
short_description: create and remove tags on lightsail instances
description:
    - Creates, removes and lists tags for lightsail instances.The instance is referenced by its name.
      It is designed to mimic the behaviour of the ec2_tag module but supports key-only tags It is designed to be used with complex args (tags).
      See the examples.
version_added: '2.9'
requirements: [ "boto3", "botocore" ]
options:
  region:
    description:
      - If not specified then the value of the C(AWS_REGION) or C(EC2_REGION) environment variable, if any, is used.
      - See U(https://docs.aws.amazon.com/general/latest/gr/rande.html#ec2_region).
    aliases: [ 'aws_region', 'ec2_region' ]
    required: true
  instance_name:
    description:
      - The name of the lightsail instance.
    required: true
    type: str
  state:
    description:
      - Whether the tags should be present or absent on the resource. Use list to interrogate the tags of an instance.
    default: 'present'
    choices: ['present', 'absent', 'list']
    type: str
  tags:
    description:
      - A dictionary of tags to add or remove from the instance.
      - If the value of a tag is null, Null (unquoted) or absent, the module will create a key-only tag.
      - If the value provided for a tag is null and C(state) is I(absent), the tag will be removed regardless of its current value.
    required: true
    type: dict
  purge_tags:
    description:
      - Whether unspecified tags should be removed from the resource.
      - "Note that when combined with C(state: absent), specified tags with non-matching values are not purged."
    type: bool
    default: no
seealso:
    - module: ec2_tag
notes:
    - supports check mode.
author:
    - Timon Schroder (@thyme-87)
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = r'''
- name: Ensure tags are present on a resource
  lightsail_tag:
    region: eu-west-1
    instance_name: instance_foo
    state: present
    tags:
      Name: ubervol
      env: prod

- name: Three ways to create a key-only tag
  lightsail_tag:
    region: eu-west-1
    instance_name: instance_foo
    state: present
    tags:
      short_term_instance:
      remove_if_required: None
      auto_delete: null

- name: Retrieve all tags on an instance and register them in lightsail_tags
  lightail_tag:
    region: eu-west-1
    instance_name: instance_foo
    state: list
  register: lightsail_tags

- name: Remove the Env tag
  lightsail_tag:
    region: eu-west-1
    instance_name: instance_foo
    tags:
      Env:
    state: absent

- name: Remove the 'Env' tag if it's currently 'development'
  lightsail_tag:
    region: eu-west-1
    resource: instance_foo
    tags:
      Env: development
    state: absent

- name: Remove all tags except for 'Name' from an instance
  instance_tag:
    region: eu-west-1
    instance_name: instance_foo
    tags:
        Name: ''
    state: absent
    purge_tags: true
'''

RETURN = r'''
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
from ansible.module_utils.ec2 import boto3_tag_list_to_ansible_dict, compare_aws_tags

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass    # Handled by AnsibleAWSModule


def get_tags(lightsail, module, instance_name):

    """
    Get tags for an lightsail instance

    module: Ansible module object
    instance_name: name of the instance
    Return list of lightsail instance tags (as dicts). The dict contains the key and the value of the tag (if present).

    """
    try:
        return lightsail_tag_dict_to_ansible_dict(lightsail.get_instance(instanceName=instance_name)['instance']['tags'])
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to fetch tags for instance %s" % instance_name)


def lightsail_tag_dict_to_ansible_dict(tags_list):

    """ Convert a boto3 dict of lightsail instance tags to a flat dict of key:value pairs using boto3_tag_list_to_ansible_dict
    module:
    Args:
        tags_list (list): List of dicts representing AWS tags.
    Basic Usage:
        >>> tags_list = [{'Key': 'MyTagKey', 'Value': 'MyTagValue'},{'Key': 'LightsailTagOnlyKey'}]
        >>> lightsail_tag_dict_to_ansible_dict(tags_list)
        [
            {
                'key': 'MyTagKey',
                'value': 'MyTagValue'
            },
            {
                'key': "LightsailTagOnlyKey'
                'value': None
            }
    Returns:
        Dict: Dict of key:value pairs representing AWS lightsail tags
         {
            'MyTagKey': 'MyTagValue',
            'LightsailTagOnlyKey': None
        }
    """

    if not tags_list:
        return {}
    tags = []
    for element in tags_list:
        if len(element) == 1:
            tag = {'key': element['key'], 'value': None}

        elif len(element) == 2:
            if element['value'] == "None":
                tag = {'key': element['key'], 'value': None}
            else:
                tag = dict(element.items())
        else:
            raise ValueError("Failed to convert lightsail tags %s to ansible_tags" % str(tags_list))
        tags.append(tag)

    return boto3_tag_list_to_ansible_dict(tags)


def ansible_dict_to_lightsail_tag_list(tags_dict):

    """ Convert a flat dict of key:value pairs representing AWS lightsail instance tags to a boto3 list of dicts
    Args:
        tags_dict (dict): Dict representing AWS resource tags.
    Basic Usage:
        >>> tags_dict = {'MyTagKey': 'MyTagValue', 'MyKeyOnlyTag'}
        >>> ansible_dict_to_lightsail_tag_list(tags_dict)
        {
            'MyTagKey': 'MyTagValue',
            'MyKeyOnlyTag
        }
    Returns:
        List: List of dicts containing tag keys and values
        [
            {
                'key': 'MyTagKey',
                'value': 'MyTagValue'
            },
            {
                'key': 'MyKeyOnlyTag'
            }
        ]
    """
    if not tags_dict:
        return {}
    tags = []

    for key, value in tags_dict.items():
        if value is None:
            tag = {'key': key}
        else:
            tag = {'key': key, 'value': value}
        tags.append(tag)
    return tags


def main():
    module_args = dict(
        instance_name=dict(type='str', required=True),
        state=dict(default='present', choices=['present', 'absent', 'list']),
        purge_tags=dict(type='bool', default=False),
        tags=dict(type='dict', required=False)
    )

    module = AnsibleAWSModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[('state', 'present', ['tags']), ('state', 'absent', ['tags'])]
    )

    instance_name = module.params['instance_name']
    tags = module.params['tags']
    state = module.params['state']
    purge_tags = module.params['purge_tags']

    result = {'changed': False}

    lightsail = module.client('lightsail')

    current_tags = get_tags(lightsail, module, instance_name)

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
                lightsail.untag_resource(resourceName=instance_name, tagKeys=list(remove_tags))
            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e, msg='Failed to delete tags {0} on instance {1}'.format(remove_tags, instance_name))

    if state == 'present' and add_tags:
        result['changed'] = True
        result['added_tags'] = add_tags
        current_tags.update(add_tags)

        if not module.check_mode:
            try:
                lightsail.tag_resource(resourceName=instance_name, tags=ansible_dict_to_lightsail_tag_list(add_tags))
            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e, msg='Failed to set tags {0} on instance {1}'.format(add_tags, instance_name))

    module.exit_json(**result)


main()
