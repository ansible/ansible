#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Opsview Ltd.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os.path

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: opsview_login
short_description: Log into Opsview
description:
  - Retrieves an authentication token from an Opsview API.
version_added: '2.5'
author: Joshua Griffiths (@jpgxs)
requirements: [pyopsview]
options:
  username:
    description:
      - Username for the Opsview API.
    required: true
  endpoint:
    description:
      - Opsview API endpoint, including schema.
      - The C(/rest) suffix is optional.
    required: true
  password:
    description:
      - Password for the Opsview API.
  verify_ssl:
    description:
      - Enable SSL verification for HTTPS endpoints.
      - Alternatively, a path to a CA can be provided.
    default: 'yes'
"""

EXAMPLES = """
---
- name: Log into Opsview
  opsview_login:
    username: admin
    password: initial
    endpoint: https://opsview.example.com
  register: ov_login

- debug:
    msg: '{{ ov_login.token }}'
"""

RETURN = """
---
token:
  description: The authentication token for the Opsview server.
  returned: success.
  type: string
opsview_version:
  description: The software version for the Opsview server.
  returned: success.
  type: string
"""

import traceback

from ansible.module_utils import opsview as ov
from ansible.module_utils.basic import to_native

ARG_SPEC = {
    "endpoint": {
        "required": True
    },
    "password": {
        "no_log": True,
        "required": True
    },
    "username": {
        "required": True
    },
    "verify_ssl": {
        "default": True
    }
}


def main():
    module = ov.new_module(ARG_SPEC)
    # Handle exception importing 'pyopsview'
    if ov.PYOV_IMPORT_EXC is not None:
        module.fail_json(msg=ov.PYOV_IMPORT_EXC[0],
                         exception=ov.PYOV_IMPORT_EXC[1])

    verify = module.params['verify_ssl']

    if not os.path.exists(verify):
        verify = module.boolean(verify)

    try:
        opsview_client = ov.new_opsview_client(
            username=module.params['username'],
            password=module.params['password'],
            endpoint=module.params['endpoint'],
            verify=verify,
        )

        summary = {'changed': True,
                   'token': opsview_client.token,
                   'opsview_version': opsview_client.version}

    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    module.exit_json(**summary)


if __name__ == '__main__':
    main()
