#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''
---
module: ec2_tag
short_description: create and remove tag(s) to ec2 resources.
description:
    - Creates, removes and lists tags from any EC2 resource.  The resource is referenced by its resource id (e.g. an instance being i-XXXXXXX).
      It is designed to be used with complex args (tags), see the examples.  This module has a dependency on python-boto.
version_added: "1.3"
options:
  resource:
    description:
      - The EC2 resource id.
    required: true
    default: null
    aliases: []
  state:
    description:
      - Whether the tags should be present or absent on the resource. Use list to interrogate the tags of an instance.
    required: false
    default: present
    choices: ['present', 'absent', 'list']
    aliases: []
  tags:
    description:
      - a hash/dictionary of tags to add to the resource; '{"key":"value"}' and '{"key":"value","key":"value"}'
    required: true
    default: null
    aliases: []

author: "Lester Wade (@lwade)"
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
- name: Ensure tags are present on a resource
  ec2_tag:
    region: eu-west-1
    resource: vol-XXXXXX
    state: present
    tags:
      Name: ubervol
      env: prod

- name: Ensure one dbserver is running
  ec2:
    count_tag:
      Name: dbserver
      Env: production
    exact_count: 1
    group: '{{ security_group }}'
    keypair: '{{ keypair }}'
    image: '{{ image_id }}'
    instance_tags:
      Name: dbserver
      Env: production
    instance_type: '{{ instance_type }}'
    region: eu-west-1
    volumes:
      - device_name: /dev/xvdb
        device_type: standard
        volume_size: 10
        delete_on_termination: True
    wait: True
  register: ec2

- name: Retrieve all volumes for a queried instance
  ec2_vol:
    instance: '{{ item.id }}'
    region: eu-west-1
    state: list
  with_items: '{{ ec2.tagged_instances }}'
  register: ec2_vol

- name: Ensure all volumes are tagged
  ec2_tag:
    region:  eu-west-1
    resource: '{{ item.id }}'
    state: present
    tags:
      Name: dbserver
      Env: production
  with_items:
    - ec2_vol.volumes

- name: Get EC2 facts
  action: ec2_facts

- name: Retrieve all tags on an instance
  ec2_tag:
    region: '{{ ansible_ec2_placement_region }}'
    resource: '{{ ansible_ec2_instance_id }}'
    state: list
  register: ec2_tags

- name: List tags, such as Name and env
  debug:
    msg: '{{ ec2_tags.tags.Name }} {{ ec2_tags.tags.env }}'
'''


try:
    import boto.ec2
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import HAS_BOTO, ec2_argument_spec, ec2_connect


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        resource=dict(required=True),
        tags=dict(type='dict'),
        state=dict(default='present', choices=['present', 'absent', 'list']),
    )
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    resource = module.params.get('resource')
    tags = module.params.get('tags')
    state = module.params.get('state')

    ec2 = ec2_connect(module)

    # We need a comparison here so that we can accurately report back changed status.
    # Need to expand the gettags return format and compare with "tags" and then tag or detag as appropriate.
    filters = {'resource-id': resource}
    gettags = ec2.get_all_tags(filters=filters)

    dictadd = {}
    dictremove = {}
    baddict = {}
    tagdict = {}
    for tag in gettags:
        tagdict[tag.name] = tag.value

    if state == 'present':
        if not tags:
            module.fail_json(msg="tags argument is required when state is present")
        if set(tags.items()).issubset(set(tagdict.items())):
            module.exit_json(msg="Tags already exists in %s." % resource, changed=False)
        else:
            for (key, value) in set(tags.items()):
                if (key, value) not in set(tagdict.items()):
                    dictadd[key] = value
        if not module.check_mode:
            ec2.create_tags(resource, dictadd)
        module.exit_json(msg="Tags %s created for resource %s." % (dictadd, resource), changed=True)

    if state == 'absent':
        if not tags:
            module.fail_json(msg="tags argument is required when state is absent")
        for (key, value) in set(tags.items()):
            if (key, value) not in set(tagdict.items()):
                baddict[key] = value
                if set(baddict) == set(tags):
                    module.exit_json(msg="Nothing to remove here. Move along.", changed=False)
        for (key, value) in set(tags.items()):
            if (key, value) in set(tagdict.items()):
                dictremove[key] = value
        if not module.check_mode:
            ec2.delete_tags(resource, dictremove)
        module.exit_json(msg="Tags %s removed for resource %s." % (dictremove, resource), changed=True)

    if state == 'list':
        module.exit_json(changed=False, tags=tagdict)


if __name__ == '__main__':
    main()
