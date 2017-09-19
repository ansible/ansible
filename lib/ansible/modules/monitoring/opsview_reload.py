#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import time
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import to_native

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """\
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

EXAMPLES = """\
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

RELOAD_MESSAGES = {
    0: 'Server running with no warnings',
    1: 'Server reloading',
    2: 'Server not running',
    3: 'Configuration error or critical error',
    4: 'Warnings exist',
}


try:
    from pyopsview import OpsviewClient
    import six
    HAS_PYOV = True
except ImportError:
    HAS_PYOV = False


def init_module():
    global module
    module = AnsibleModule(supports_check_mode=True, argument_spec=ARG_SPEC)
    return module


def warn(message):
    module._warnings.append(message)
    module.log('[WARNING] ' + message)


def init_client(username, endpoint, token=None, password=None, **kwds):
    if not (password or token):
        module.fail_json(msg='\'password\' or \'token\' must be specified')

    if password and not token:
        warn('Consider using \'token\' instead of \'password\'. '
             'See the \'opsview_login\' module.')

    try:
        return OpsviewClient(username=username, token=token, endpoint=endpoint,
                             password=password, **kwds)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


def get_reload_status(client):
    status = client.reload_status()
    for (key, value) in six.iteritems(status):
        try:
            status[key] = int(value)
        except Exception:
            pass

    return status


def do_reload(client):
    status = get_reload_status(client)
    reload_status = status['server_status']
    config_status = status['configuration_status']

    # Fail if a reload is not possible
    if reload_status in (1, 2):
        module.fail_json(msg=RELOAD_MESSAGES[reload_status])

    # Only reload if changes are pending or 'force' was specified
    if config_status.lower() == 'pending' or module.params.get('force'):
        changed = True

    module_status = {'changed': changed}

    # noop if check mode
    if module.check_mode or not changed:
        return module_status

    # requires a reload
    client.reload(async=True)

    # don't return additional info unless wait was specified
    if not module.params.get('wait'):
        return module_status

    while True:
        status = get_reload_status(client)
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
                warn('Opsview: ' + message['detail'])

    elif reload_status in (2, 3):
        module.fail_json(msg='Failed to reload Opsview: %s' %
                         RELOAD_MESSAGES[reload_status])

    module_status.update(status)
    return module_status


def main():
    init_module()

    if not HAS_PYOV:
        module.fail_json(msg='pyopsview is required')

    ov_client = init_client(username=module.params['username'],
                            password=module.params['password'],
                            endpoint=module.params['endpoint'],
                            token=module.params['token'],
                            verify=module.params['verify_ssl'])

    status = do_reload(ov_client)
    module.exit_json(**status)


if __name__ == '__main__':
    main()
