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
module: opsview_reload
short_description: Reload Opsview
description:
  - Reloads an Opsview Monitor system
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
  token:
    description:
      - API token, usually returned by the C(opsview_login) module.
      - Required unless C(password) is specified.
  password:
    description:
      - Password for the Opsview API.
  verify_ssl:
    description:
      - Enable SSL verification for HTTPS endpoints.
      - Alternatively, a path to a CA can be provided.
    default: 'yes'
  force:
    description:
      - Force a reload even if there are no pending changes.
    default: no
    choices: ['yes', 'no']
  wait:
    description:
      - Wait for the reload to complete.
    default: 'yes'
    choices: ['yes', 'no']
"""

EXAMPLES = """
---
- name: Reload Opsview
  opsview_reload:
    username: admin
    password: initial
    endpoint: https://opsview.example.com

- name: Force-reload Opsview without waiting
  opsview_reload:
    username: admin
    password: initial
    endpoint: https://opsview.example.com
    force: yes
    wait: no
"""

RETURN = """
---
"""

import time
import traceback

from ansible.module_utils import opsview as ov
from ansible.module_utils.basic import to_native
from ansible.module_utils.six import iteritems
from ansible.module_utils.six import string_types

ARG_SPEC = {
    "endpoint": {
        "required": True
    },
    "password": {
        "no_log": True,
    },
    "token": {
        "no_log": True,
    },
    "username": {
        "required": True
    },
    "verify_ssl": {
        "default": True
    },
    "force": {
        "default": True,
        "type": "bool",
    },
    "wait": {
        "default": True,
        "type": "bool"
    }
}

# Used to ensure that none of the arguments are omitted
ARG_KEYS = tuple(ARG_SPEC.keys())

RELOAD_MESSAGES = {
    0: 'Server running with no warnings',
    1: 'Server reloading',
    2: 'Server not running',
    3: 'Configuration error or critical error',
    4: 'Warnings exist',
}


def get_reload_status(client):
    """Get the current reload status and convert the stringy numbers into
    real integers.
    """
    status = client.reload_status()
    for (k, v) in iteritems(status):
        try:
            status[k] = int(v)
        except Exception:
            pass

    return status


def do_reload(module, opsview_client):
    status = get_reload_status(opsview_client)
    reload_status = status['server_status']
    config_status = status['configuration_status']

    # Fail if a reload is not possible
    if reload_status in (1, 2):
        module.fail_json(
            msg='Unable to reload Opsview: %s' % RELOAD_MESSAGES[reload_status]
        )

    # Only reload if changes are pending or 'force' was specified
    if config_status.lower() == 'pending' or module.params.get('force'):
        changed = True

    module_status = {'changed': changed}

    # noop if check mode
    if module.check_mode or not changed:
        return module_status

    # requires a reload
    opsview_client.reload(async=True)

    # don't return additional info unless wait was specified
    if not module.params.get('wait'):
        return module_status

    # wait loop
    while True:
        status = get_reload_status(opsview_client)
        reload_status = status['server_status']
        config_status = status['configuration_status']

        if reload_status != 1:
            break

        # Must be different from the TCP keepalive seconds
        time.sleep(3.5)

    # Add warnings
    if reload_status == 4:
        for message in status.get('messages', []):
            if 'detail' in message:
                module.warn('Opsview: ' + message['detail'])

    elif reload_status in (2, 3):
        module.fail_json(msg='Failed to reload Opsview: %s' %
                         RELOAD_MESSAGES[reload_status])

    return module_status


def module_main(module):
    verify = module.params['verify_ssl']

    if not os.path.exists(verify):
        verify = module.boolean(verify)

    opsview_client = ov.new_opsview_client(
        username=module.params['username'],
        password=module.params['password'],
        endpoint=module.params['endpoint'],
        token=module.params['token'],
        verify=verify,
    )

    return do_reload(module, opsview_client)


def main():
    module = ov.new_module(ARG_SPEC, always_include=ARG_KEYS)
    # Handle exception importing 'pyopsview'
    if ov.PYOV_IMPORT_EXC is not None:
        module.fail_json(msg=ov.PYOV_IMPORT_EXC[0],
                         exception=ov.PYOV_IMPORT_EXC[1])

    try:
        summary = module_main(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    module.exit_json(**summary)


if __name__ == '__main__':
    main()
