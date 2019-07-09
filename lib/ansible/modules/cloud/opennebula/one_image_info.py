#!/usr/bin/python
# -*- coding: utf-8 -*-

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

"""
(c) 2018, Milan Ilic <milani@nordeus.com>

This file is part of Ansible

Ansible is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Ansible is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a clone of the GNU General Public License
along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
"""

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: one_image_info
short_description: Gather information on OpenNebula images
description:
  - Gather information on OpenNebula images.
  - This module was called C(one_image_facts) before Ansible 2.9. The usage did not change.
version_added: "2.6"
requirements:
  - python-oca
options:
  api_url:
    description:
      - URL of the OpenNebula RPC server.
      - It is recommended to use HTTPS so that the username/password are not
      - transferred over the network unencrypted.
      - If not set then the value of the C(ONE_URL) environment variable is used.
  api_username:
    description:
      - Name of the user to login into the OpenNebula RPC server. If not set
      - then the value of the C(ONE_USERNAME) environment variable is used.
  api_password:
    description:
      - Password of the user to login into OpenNebula RPC server. If not set
      - then the value of the C(ONE_PASSWORD) environment variable is used.
  ids:
    description:
      - A list of images ids whose facts you want to gather.
    aliases: ['id']
  name:
    description:
      - A C(name) of the image whose facts will be gathered.
      - If the C(name) begins with '~' the C(name) will be used as regex pattern
      - which restricts the list of images (whose facts will be returned) whose names match specified regex.
      - Also, if the C(name) begins with '~*' case-insensitive matching will be performed.
      - See examples for more details.
author:
    - "Milan Ilic (@ilicmilan)"
'''

EXAMPLES = '''
# Gather facts about all images
- one_image_info:
  register: result

# Print all images facts
- debug:
    msg: result

# Gather facts about an image using ID
- one_image_info:
    ids:
      - 123

# Gather facts about an image using the name
- one_image_info:
    name: 'foo-image'
  register: foo_image

# Gather facts about all IMAGEs whose name matches regex 'app-image-.*'
- one_image_info:
    name: '~app-image-.*'
  register: app_images

# Gather facts about all IMAGEs whose name matches regex 'foo-image-.*' ignoring cases
- one_image_info:
    name: '~*foo-image-.*'
  register: foo_images
'''

RETURN = '''
images:
    description: A list of images info
    type: complex
    returned: success
    contains:
        id:
            description: image id
            type: int
            sample: 153
        name:
            description: image name
            type: str
            sample: app1
        group_id:
            description: image's group id
            type: int
            sample: 1
        group_name:
            description: image's group name
            type: str
            sample: one-users
        owner_id:
            description: image's owner id
            type: int
            sample: 143
        owner_name:
            description: image's owner name
            type: str
            sample: ansible-test
        state:
            description: state of image instance
            type: str
            sample: READY
        used:
            description: is image in use
            type: bool
            sample: true
        running_vms:
            description: count of running vms that use this image
            type: int
            sample: 7
'''

try:
    import oca
    HAS_OCA = True
except ImportError:
    HAS_OCA = False

from ansible.module_utils.basic import AnsibleModule
import os


def get_all_images(client):
    pool = oca.ImagePool(client)
    # Filter -2 means fetch all images user can Use
    pool.info(filter=-2)

    return pool


IMAGE_STATES = ['INIT', 'READY', 'USED', 'DISABLED', 'LOCKED', 'ERROR', 'CLONE', 'DELETE', 'USED_PERS', 'LOCKED_USED', 'LOCKED_USED_PERS']


def get_image_info(image):
    image.info()

    info = {
        'id': image.id,
        'name': image.name,
        'state': IMAGE_STATES[image.state],
        'running_vms': image.running_vms,
        'used': bool(image.running_vms),
        'user_name': image.uname,
        'user_id': image.uid,
        'group_name': image.gname,
        'group_id': image.gid,
    }

    return info


def get_images_by_ids(module, client, ids):
    images = []
    pool = get_all_images(client)

    for image in pool:
        if str(image.id) in ids:
            images.append(image)
            ids.remove(str(image.id))
            if len(ids) == 0:
                break

    if len(ids) > 0:
        module.fail_json(msg='There is no IMAGE(s) with id(s)=' + ', '.join('{id}'.format(id=str(image_id)) for image_id in ids))

    return images


def get_images_by_name(module, client, name_pattern):

    images = []
    pattern = None

    pool = get_all_images(client)

    if name_pattern.startswith('~'):
        import re
        if name_pattern[1] == '*':
            pattern = re.compile(name_pattern[2:], re.IGNORECASE)
        else:
            pattern = re.compile(name_pattern[1:])

    for image in pool:
        if pattern is not None:
            if pattern.match(image.name):
                images.append(image)
        elif name_pattern == image.name:
            images.append(image)
            break

    # if the specific name is indicated
    if pattern is None and len(images) == 0:
        module.fail_json(msg="There is no IMAGE with name=" + name_pattern)

    return images


def get_connection_info(module):

    url = module.params.get('api_url')
    username = module.params.get('api_username')
    password = module.params.get('api_password')

    if not url:
        url = os.environ.get('ONE_URL')

    if not username:
        username = os.environ.get('ONE_USERNAME')

    if not password:
        password = os.environ.get('ONE_PASSWORD')

    if not(url and username and password):
        module.fail_json(msg="One or more connection parameters (api_url, api_username, api_password) were not specified")
    from collections import namedtuple

    auth_params = namedtuple('auth', ('url', 'username', 'password'))

    return auth_params(url=url, username=username, password=password)


def main():
    fields = {
        "api_url": {"required": False, "type": "str"},
        "api_username": {"required": False, "type": "str"},
        "api_password": {"required": False, "type": "str", "no_log": True},
        "ids": {"required": False, "aliases": ['id'], "type": "list"},
        "name": {"required": False, "type": "str"},
    }

    module = AnsibleModule(argument_spec=fields,
                           mutually_exclusive=[['ids', 'name']],
                           supports_check_mode=True)
    if module._name == 'one_image_facts':
        module.deprecate("The 'one_image_facts' module has been renamed to 'one_image_info'", version='2.13')

    if not HAS_OCA:
        module.fail_json(msg='This module requires python-oca to work!')

    auth = get_connection_info(module)
    params = module.params
    ids = params.get('ids')
    name = params.get('name')
    client = oca.Client(auth.username + ':' + auth.password, auth.url)

    result = {'images': []}
    images = []

    if ids:
        images = get_images_by_ids(module, client, ids)
    elif name:
        images = get_images_by_name(module, client, name)
    else:
        images = get_all_images(client)

    for image in images:
        result['images'].append(get_image_info(image))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
