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
module: ingate_download_install_upgrade
short_description: Download and install a firmware upgrade.
description:
  - Download and install a firmware upgrade. The upgrade(s) will be downloaded
    from the Ingate websystem. You can upgrade to the latest patch, minor or
    major version. You can also specify a desired version that is available in
    the respective level.
version_added: 2.8
extends_documentation_fragment: ingate
options:
  username:
    description:
      - Username for account login on ingate.com.
  password:
    description:
      - Password for account login on ingate.com.
  version:
    description:
      - The the desired version.
  latest_patch:
    description:
      - Upgrade to the latest patch level.
    type: bool
    default: false
  latest_minor:
    description:
      - Upgrade to the latest minor level.
    type: bool
    default: false
  latest_major:
    description:
      - Upgrade to the latest major level.
    type: bool
    default: false
  latest:
    description:
      - Upgrade to the latest available version.
    type: bool
    default: false
notes:
  - Note, after an upgrade has been installed the API client needs to
    re-authenticate. The re-authentication is performed automatically by this
    function.
  - This method assumes that the the preliminary configuration has been stored
    to the permanent configuration at least once (see store_edit method).
  - The Ansible host needs Internet connectivity.
  - Depending on how many upgrades that have to be performed in order to reach
    the desired level, this task may take a while to complete.
author:
  - Ingate Systems AB (@ingatesystems)
'''

EXAMPLES = '''
- name: Upgrade to the latest version available
  ingate_download_install_upgrade:
    client:
      version: v1
      scheme: http
      address: 192.168.1.1
      username: alice
      password: foobar
    latest: True
'''

RETURN = '''
download-install-upgrade:
  description: A command status message
  returned: success
  type: complex
  contains:
    msg:
      description: The command status message
      returned: success
      type: string
      sample: Your unit is upgraded to the latest version (6.3.2)
'''

try:
    from ingate import ingatesdk
    HAS_INGATESDK = True
except ImportError:
    HAS_INGATESDK = False


def main():
    argument_spec = ingate_argument_spec(
        username=dict(required=True, no_log=True),
        password=dict(required=True, no_log=True),
        version=dict(default=None),
        latest_patch=dict(type=bool, default=False),
        latest_minor=dict(type=bool, default=False),
        latest_major=dict(type=bool, default=False),
        latest=dict(type=bool, default=False),
    )
    mutually_exclusive = [('latest_patch', 'latest_minor', 'latest_major')]
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

        # Download and install upgrade(s).
        username = module.params.get('username')
        password = module.params.get('password')
        version = module.params.get('version')
        latest_patch = module.params.get('latest_patch')
        latest_minor = module.params.get('latest_minor')
        latest_major = module.params.get('latest_major')
        latest = module.params.get('latest')
        response = (api_client.
                    download_install_upgrade(username, password,
                                             version=version,
                                             latest_patch=latest_patch,
                                             latest_minor=latest_minor,
                                             latest_major=latest_major,
                                             latest=latest))
        result.update(response[0])
        result['changed'] = True

    except ingatesdk.SdkError as e:
        module.fail_json(msg=str(e))
    module.exit_json(**result)


from ansible.module_utils.basic import *
from ansible.module_utils.network.ingate.common import *

if __name__ == '__main__':
    main()
