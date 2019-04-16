#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: ec2_ami_find
version_added: '2.0'
short_description: Searches for AMIs to obtain the AMI ID and other information
deprecated:
  removed_in: "2.9"
  why: Various AWS modules have been combined and replaced with M(ec2_ami_facts).
  alternative: Use M(ec2_ami_facts) instead.
description:
  - Returns list of matching AMIs with AMI ID, along with other useful information
  - Can search AMIs with different owners
  - Can search by matching tag(s), by AMI name and/or other criteria
  - Results can be sorted and sliced
author: "Tom Bamford (@tombamford)"
notes:
  - This module is not backwards compatible with the previous version of the ec2_search_ami module which worked only for Ubuntu AMIs listed on
    cloud-images.ubuntu.com.
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
      - You can include wildcards in many of the search options. An asterisk (*) matches zero or more characters, and a question mark (?) matches exactly one
        character. You can escape special characters using a backslash (\) before the character. For example, a value of \*amazon\?\\ searches for the
        literal string *amazon?\.
  ami_id:
    description:
      - An AMI ID to match.
  ami_tags:
    description:
      - A hash/dictionary of tags to match for the AMI.
  architecture:
    description:
      - An architecture type to match (e.g. x86_64).
  hypervisor:
    description:
      - A hypervisor type type to match (e.g. xen).
  is_public:
    description:
      - Whether or not the image(s) are public.
    type: bool
  name:
    description:
      - An AMI name to match.
  platform:
    description:
      - Platform type to match.
  product_code:
    description:
      - Marketplace product code to match.
    version_added: "2.3"
  sort:
    description:
      - Optional attribute which with to sort the results.
      - If specifying 'tag', the 'tag_name' parameter is required.
      - Starting at version 2.1, additional sort choices of architecture, block_device_mapping, creationDate, hypervisor, is_public, location, owner_id,
        platform, root_device_name, root_device_type, state, and virtualization_type are supported.
    choices:
        - 'name'
        - 'description'
        - 'tag'
        - 'architecture'
        - 'block_device_mapping'
        - 'creationDate'
        - 'hypervisor'
        - 'is_public'
        - 'location'
        - 'owner_id'
        - 'platform'
        - 'root_device_name'
        - 'root_device_type'
        - 'state'
        - 'virtualization_type'
  sort_tag:
    description:
      - Tag name with which to sort results.
      - Required when specifying 'sort=tag'.
  sort_order:
    description:
      - Order in which to sort results.
      - Only used when the 'sort' parameter is specified.
    choices: ['ascending', 'descending']
    default: 'ascending'
  sort_start:
    description:
      - Which result to start with (when sorting).
      - Corresponds to Python slice notation.
  sort_end:
    description:
      - Which result to end with (when sorting).
      - Corresponds to Python slice notation.
  state:
    description:
      - AMI state to match.
    default: 'available'
  virtualization_type:
    description:
      - Virtualization type to match (e.g. hvm).
  root_device_type:
    description:
      - Root device type to match (e.g. ebs, instance-store).
    version_added: "2.5"
  no_result_action:
    description:
      - What to do when no results are found.
      - "'success' reports success and returns an empty array"
      - "'fail' causes the module to report failure"
    choices: ['success', 'fail']
    default: 'success'
extends_documentation_fragment:
    - aws
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

RETURN = '''
ami_id:
    description: id of found amazon image
    returned: when AMI found
    type: str
    sample: "ami-e9095e8c"
architecture:
    description: architecture of image
    returned: when AMI found
    type: str
    sample: "x86_64"
block_device_mapping:
    description: block device mapping associated with image
    returned: when AMI found
    type: dict
    sample: "{
        '/dev/xvda': {
            'delete_on_termination': true,
            'encrypted': false,
            'size': 8,
            'snapshot_id': 'snap-ca0330b8',
            'volume_type': 'gp2'
    }"
creationDate:
    description: creation date of image
    returned: when AMI found
    type: str
    sample: "2015-10-15T22:43:44.000Z"
description:
    description: description of image
    returned: when AMI found
    type: str
    sample: "test-server01"
hypervisor:
    description: type of hypervisor
    returned: when AMI found
    type: str
    sample: "xen"
is_public:
    description: whether image is public
    returned: when AMI found
    type: bool
    sample: false
location:
    description: location of image
    returned: when AMI found
    type: str
    sample: "435210894375/test-server01-20151015-234343"
name:
    description: ami name of image
    returned: when AMI found
    type: str
    sample: "test-server01-20151015-234343"
owner_id:
    description: owner of image
    returned: when AMI found
    type: str
    sample: "435210894375"
platform:
    description: platform of image
    returned: when AMI found
    type: str
    sample: null
root_device_name:
    description: root device name of image
    returned: when AMI found
    type: str
    sample: "/dev/xvda"
root_device_type:
    description: root device type of image
    returned: when AMI found
    type: str
    sample: "ebs"
state:
    description: state of image
    returned: when AMI found
    type: str
    sample: "available"
tags:
    description: tags assigned to image
    returned: when AMI found
    type: dict
    sample: "{
        'Environment': 'devel',
        'Name': 'test-server01',
        'Role': 'web'
    }"
virtualization_type:
    description: image virtualization type
    returned: when AMI found
    type: str
    sample: "hvm"
'''

import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import HAS_BOTO, ec2_argument_spec, ec2_connect


def get_block_device_mapping(image):
    """
    Retrieves block device mapping from AMI
    """

    bdm_dict = dict()
    bdm = getattr(image, 'block_device_mapping')
    for device_name in bdm.keys():
        bdm_dict[device_name] = {
            'size': bdm[device_name].size,
            'snapshot_id': bdm[device_name].snapshot_id,
            'volume_type': bdm[device_name].volume_type,
            'encrypted': bdm[device_name].encrypted,
            'delete_on_termination': bdm[device_name].delete_on_termination
        }

    return bdm_dict


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        owner=dict(required=False, default=None),
        ami_id=dict(required=False),
        ami_tags=dict(required=False, type='dict',
                      aliases=['search_tags', 'image_tags']),
        architecture=dict(required=False),
        hypervisor=dict(required=False),
        is_public=dict(required=False, type='bool'),
        name=dict(required=False),
        platform=dict(required=False),
        product_code=dict(required=False),
        sort=dict(required=False, default=None,
                  choices=['name', 'description', 'tag', 'architecture', 'block_device_mapping', 'creationDate', 'hypervisor', 'is_public', 'location',
                           'owner_id', 'platform', 'root_device_name', 'root_device_type', 'state', 'virtualization_type']),
        sort_tag=dict(required=False),
        sort_order=dict(required=False, default='ascending',
                        choices=['ascending', 'descending']),
        sort_start=dict(required=False),
        sort_end=dict(required=False),
        state=dict(required=False, default='available'),
        virtualization_type=dict(required=False),
        no_result_action=dict(required=False, default='success',
                              choices=['success', 'fail']),
    )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    module.deprecate("The 'ec2_ami_find' module has been deprecated. Use 'ec2_ami_facts' instead.", version=2.9)

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
    product_code = module.params.get('product_code')
    root_device_type = module.params.get('root_device_type')
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
            filter['tag:' + tag] = ami_tags[tag]
    if architecture:
        filter['architecture'] = architecture
    if hypervisor:
        filter['hypervisor'] = hypervisor
    if is_public:
        filter['is_public'] = 'true'
    if name:
        filter['name'] = name
    if platform:
        filter['platform'] = platform
    if product_code:
        filter['product-code'] = product_code
    if root_device_type:
        filter['root_device_type'] = root_device_type
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
            'block_device_mapping': get_block_device_mapping(image),
            'creationDate': image.creationDate,
            'description': image.description,
            'hypervisor': image.hypervisor,
            'is_public': image.is_public,
            'location': image.location,
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
        results.sort(key=lambda e: e['tags'][sort_tag], reverse=(sort_order == 'descending'))
    elif sort:
        results.sort(key=lambda e: e[sort], reverse=(sort_order == 'descending'))

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


if __name__ == '__main__':
    main()
