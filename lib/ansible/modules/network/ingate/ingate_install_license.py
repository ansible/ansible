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
module: ingate_install_license
short_description: Download and install a license.
description:
  - Download and install a license from the Ingate licensing system.
version_added: 2.8
extends_documentation_fragment: ingate
options:
  username:
    description:
      - Username for account login on ingate.com.
  password:
    description:
      - Password for account login on ingate.com.
  liccode:
    description:
      - The license code (e.g. KRJM-Q625-FUVG).
  cache_lic:
    description:
      - Toggels if the license should be stored to disk when downloaded.
    type: bool
    default: false
  license_b64:
    description:
      - A base64 encoded license file.
notes:
  - If you specify license_b64 the value of the other parameters doesn't
    matter.
  - The Ansible host needs Internet connectivity if license_b64 is omitted.
author:
  - Ingate Systems AB (@ingatesystems)
'''

EXAMPLES = '''
- name: Install a license via ingate.com
  ingate_install_license:
    client:
      version: v1
      scheme: http
      address: 192.168.1.1
      username: alice
      password: foobar
    username: myaccount
    password: mypassword
    liccode: KRJM-Q625-FUVG
'''

RETURN = '''
install-license:
  description: A command status message
  returned: success
  type: complex
  contains:
    msg:
      description: The command status message
      returned: success
      type: string
'''

try:
    from ingate import ingatesdk
    HAS_INGATESDK = True
except ImportError:
    HAS_INGATESDK = False


def __check_missing_args(module, spec, **kwargs):
        if spec is None:
            return
        for (key, val, requirements) in spec:
            missing = []
            if key in kwargs and kwargs[key] == val:
                for req in requirements:
                    if req not in kwargs:
                        missing.append(req)
                    elif kwargs[req] is None:
                        missing.append(req)
            if len(missing) > 0:
                msg = '%s is %s, the following arguments are missing: %s'
                module.fail_json(msg=msg % (key, val, ', '.join(missing)))


def main():
    argument_spec = ingate_argument_spec(
        username=dict(default=None, no_log=True),
        password=dict(default=None, no_log=True),
        liccode=dict(default=None),
        cache_lic=dict(default=False, type=bool),
        license_b64=dict(default=None),
    )
    mutually_exclusive = []
    required_if_own = [
        ('license_b64', None, ['username', 'password', 'liccode']),
    ]
    required_together = [
        ('username', 'password', 'liccode'),
    ]

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           required_together=required_together,
                           supports_check_mode=False)
    if not HAS_INGATESDK:
        module.fail_json(msg='The Ingate Python SDK module is required')

    __check_missing_args(module, required_if_own, **module.params)
    result = dict(changed=False)
    try:
        # Create client and authenticate.
        api_client = ingate_create_client(**module.params)

        # Install a license.
        username = module.params.get('username')
        password = module.params.get('password')
        liccode = module.params.get('liccode')
        cache_lic = module.params.get('cache_lic')
        license_b64 = module.params.get('license_b64')
        response = api_client.install_license(username, password, liccode,
                                              cache_lic, license_b64)
        result.update(response[0])
        result['changed'] = True

    except ingatesdk.SdkError as e:
        module.fail_json(msg=str(e))
    module.exit_json(**result)


from ansible.module_utils.basic import *
from ansible.module_utils.network.ingate.common import *

if __name__ == '__main__':
    main()
