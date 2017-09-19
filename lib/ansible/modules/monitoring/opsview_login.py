#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import to_native

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """\
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

EXAMPLES = """\
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


try:
    from pyopsview import OpsviewClient
    HAS_PYOV = True
except ImportError:
    HAS_PYOV = False


def init_module():
    global module
    module = AnsibleModule(supports_check_mode=True, argument_spec=ARG_SPEC)
    return module


def init_client(username, endpoint, password, **kwds):
    try:
        return OpsviewClient(username=username, endpoint=endpoint,
                             password=password, **kwds)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


def main():
    init_module()

    if not HAS_PYOV:
        module.fail_json(msg='pyopsview is required')

    ov_client = init_client(username=module.params['username'],
                            password=module.params['password'],
                            endpoint=module.params['endpoint'],
                            verify=module.params['verify_ssl'])

    status = {
        'changed': True,
        'token': ov_client.token,
        'opsview_version': ov_client.version,
    }

    module.exit_json(**status)


if __name__ == '__main__':
    main()
