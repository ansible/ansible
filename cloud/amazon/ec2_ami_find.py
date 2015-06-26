#!/usr/bin/python
#
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

DOCUMENTATION = '''
---
module: ec2_ami_find
version_added: 2.0
short_description: Searches for AMIs to obtain the AMI ID and other information
description:
  - Returns list of matching AMIs with AMI ID, along with other useful information
  - Can search AMIs with different owners
  - Can search by matching tag(s), by AMI name and/or other criteria
  - Results can be sorted and sliced
author: "Tom Bamford (@tombamford)"
notes:
  - This module is not backwards compatible with the previous version of the ec2_search_ami module which worked only for Ubuntu AMIs listed on cloud-images.ubuntu.com.
  - See the example below for a suggestion of how to search by distro/release.
options:
  region:
    description:
      - The AWS region to use.
    required: true
    aliases: [ 'aws_region', 'ec2_region' ]
  owner:
    description:
      - Search AMIs owned by the specified owner
      - Can specify an AWS account ID, or one of the special IDs 'self', 'amazon' or 'aws-marketplace'
      - If not specified, all EC2 AMIs in the specified region will be searched.
      - You can include wildcards in many of the search options. An asterisk (*) matches zero or more characters, and a question mark (?) matches exactly one character. You can escape special characters using a backslash (\) before the character. For example, a value of \*amazon\?\\ searches for the literal string *amazon?\.
    required: false
    default: null
  ami_id:
    description:
      - An AMI ID to match.
    default: null
    required: false
  ami_tags:
    description:
      - A hash/dictionary of tags to match for the AMI.
    default: null
    required: false
  architecture:
    description:
      - An architecture type to match (e.g. x86_64).
    default: null
    required: false
  hypervisor:
    description:
      - A hypervisor type type to match (e.g. xen).
    default: null
    required: false
  is_public:
    description:
      - Whether or not the image(s) are public.
    choices: ['yes', 'no']
    default: null
    required: false
  name:
    description:
      - An AMI name to match.
    default: null
    required: false
  platform:
    description:
      - Platform type to match.
    default: null
    required: false
  sort:
    description:
      - Optional attribute which with to sort the results.
      - If specifying 'tag', the 'tag_name' parameter is required.
    choices: ['name', 'description', 'tag']
    default: null
    required: false
  sort_tag:
    description:
      - Tag name with which to sort results.
      - Required when specifying 'sort=tag'.
    default: null
    required: false
  sort_order:
    description:
      - Order in which to sort results.
      - Only used when the 'sort' parameter is specified.
    choices: ['ascending', 'descending']
    default: 'ascending'
    required: false
  sort_start:
    description:
      - Which result to start with (when sorting).
      - Corresponds to Python slice notation.
    default: null
    required: false
  sort_end:
    description:
      - Which result to end with (when sorting).
      - Corresponds to Python slice notation.
    default: null
    required: false
  state:
    description:
      - AMI state to match.
    default: 'available'
    required: false
  virtualization_type:
    description:
      - Virtualization type to match (e.g. hvm).
    default: null
    required: false
  no_result_action:
    description:
      - What to do when no results are found.
      - "'success' reports success and returns an empty array"
      - "'fail' causes the module to report failure"
    choices: ['success', 'fail']
    default: 'success'
    required: false
requirements:
  - "python >= 2.6"
  - boto

'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Search for the AMI tagged "project:website"
- ec2_ami_find:
    owner: self
    ami_tags:
      project: website
    no_result_action: fail
  register: ami_find

# Search for the latest Ubuntu 14.04 AMI
- ec2_ami_find:
    name: "ubuntu/images/ebs/ubuntu-trusty-14.04-amd64-server-*"
    owner: 099720109477
    sort: name
    sort_order: descending
    sort_end: 1
  register: ami_find

# Launch an EC2 instance
- ec2:
    image: "{{ ami_find.results[0].ami_id }}"
    instance_type: m3.medium
    key_name: mykey
    wait: yes
'''

try:
    import boto.ec2
    HAS_BOTO=True
except ImportError:
    HAS_BOTO=False

import json

def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
            region = dict(required=True,
                aliases = ['aws_region', 'ec2_region']),
            owner = dict(required=False, default=None),
            ami_id = dict(required=False),
            ami_tags = dict(required=False, type='dict',
                aliases = ['search_tags', 'image_tags']),
            architecture = dict(required=False),
            hypervisor = dict(required=False),
            is_public = dict(required=False),
            name = dict(required=False),
            platform = dict(required=False),
            sort = dict(required=False, default=None,
                choices=['name', 'description', 'tag']),
            sort_tag = dict(required=False),
            sort_order = dict(required=False, default='ascending',
                choices=['ascending', 'descending']),
            sort_start = dict(required=False),
            sort_end = dict(required=False),
            state = dict(required=False, default='available'),
            virtualization_type = dict(required=False),
            no_result_action = dict(required=False, default='success',
                choices = ['success', 'fail']),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module, install via pip or your package manager')

    ami_id = module.params.get('ami_id')
    ami_tags = module.params.get('ami_tags')
    architecture = module.params.get('architecture')
    hypervisor = module.params.get('hypervisor')
    is_public = module.params.get('is_public')
    name = module.params.get('name')
    owner = module.params.get('owner')
    platform = module.params.get('platform')
    sort = module.params.get('sort')
    sort_tag = module.params.get('sort_tag')
    sort_order = module.params.get('sort_order')
    sort_start = module.params.get('sort_start')
    sort_end = module.params.get('sort_end')
    state = module.params.get('state')
    virtualization_type = module.params.get('virtualization_type')
    no_result_action = module.params.get('no_result_action')

    filter = {'state': state}

    if ami_id:
        filter['image_id'] = ami_id
    if ami_tags:
        for tag in ami_tags:
            filter['tag:'+tag] = ami_tags[tag]
    if architecture:
        filter['architecture'] = architecture
    if hypervisor:
        filter['hypervisor'] = hypervisor
    if is_public:
        filter['is_public'] = is_public
    if name:
        filter['name'] = name
    if platform:
        filter['platform'] = platform
    if virtualization_type:
        filter['virtualization_type'] = virtualization_type

    ec2 = ec2_connect(module)

    images_result = ec2.get_all_images(owners=owner, filters=filter)

    if no_result_action == 'fail' and len(images_result) == 0:
        module.fail_json(msg="No AMIs matched the attributes: %s" % json.dumps(filter))

    results = []
    for image in images_result:
        data = {
            'ami_id': image.id,
            'architecture': image.architecture,
            'description': image.description,
            'is_public': image.is_public,
            'name': image.name,
            'owner_id': image.owner_id,
            'platform': image.platform,
            'root_device_name': image.root_device_name,
            'root_device_type': image.root_device_type,
            'state': image.state,
            'tags': image.tags,
            'virtualization_type': image.virtualization_type,
        }

        if image.kernel_id:
            data['kernel_id'] = image.kernel_id
        if image.ramdisk_id:
            data['ramdisk_id'] = image.ramdisk_id

        results.append(data)

    if sort == 'tag':
        if not sort_tag:
            module.fail_json(msg="'sort_tag' option must be given with 'sort=tag'")
        results.sort(key=lambda e: e['tags'][sort_tag], reverse=(sort_order=='descending'))
    elif sort:
        results.sort(key=lambda e: e[sort], reverse=(sort_order=='descending'))

    try:
        if sort and sort_start and sort_end:
            results = results[int(sort_start):int(sort_end)]
        elif sort and sort_start:
            results = results[int(sort_start):]
        elif sort and sort_end:
            results = results[:int(sort_end)]
    except TypeError:
        module.fail_json(msg="Please supply numeric values for sort_start and/or sort_end")

    module.exit_json(results=results)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()

