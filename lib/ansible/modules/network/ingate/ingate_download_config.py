#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2018, Ingate Systems AB
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: ingate_download_config
short_description: Download configuration database from the unit.
description:
  - Download configuration database from the unit.
version_added: 2.8
extends_documentation_fragment: ingate
options:
  store:
    description:
      - If the configuration should be stored on disk.
    type: bool
    default: false
  path:
    description:
      - Where in the filesystem to store the configuration.
  filename:
    description:
      - The name of the file to store.
notes:
  - If store is set to True, and path and filename is omitted, the file will be
    stored in the current directory with an automatic filename.
author:
  - Ingate Systems AB (@ingatesystems)
'''

EXAMPLES = '''
- name: Do backup of the configuration database
  ingate_download_config:
    client:
      version: v1
      scheme: http
      address: 192.168.1.1
      username: alice
      password: foobar
    store: True
'''

RETURN = '''
download-config:
  description: Configuraton database and meta data
  returned: success
  type: complex
  contains:
    config:
      description: The configuration database
      returned: success
      type: string
    filename:
      description: A suggested name for the configuration
      returned: success
      type: string
      sample: testname_2018-10-01T214040.cfg
    mimetype:
      description: The mimetype
      returned: success
      type: string
      sample: application/x-config-database
'''

try:
    from ingate import ingatesdk
    HAS_INGATESDK = True
except ImportError:
    HAS_INGATESDK = False


def main():
    argument_spec = ingate_argument_spec(
        store=dict(default=False, type=bool),
        path=dict(default=None),
        filename=dict(default=None),
    )
    mutually_exclusive = []
    required_if = []
    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           required_if=required_if,
                           supports_check_mode=False)
    if not HAS_INGATESDK:
        module.fail_json(msg='The Ingate Python SDK module is required')

    result = dict(changed=False)
    try:
        # Create client and authenticate.
        api_client = ingate_create_client(**module.params)

        # Download the configuration database.
        store = module.params.get('store')
        path = module.params.get('path')
        filename = module.params.get('filename')
        response = api_client.download_config(store=store, path=path,
                                              filename=filename)
        result.update(response[0])

    except ingatesdk.SdkError as e:
        module.fail_json(msg=str(e))
    module.exit_json(**result)


from ansible.module_utils.basic import *
from ansible.module_utils.network.ingate.common import *

if __name__ == '__main__':
    main()
