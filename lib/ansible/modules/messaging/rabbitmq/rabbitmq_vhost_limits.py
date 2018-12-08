#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Hiroyuki Matsuo <h.matsuo.engineer@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: rabbitmq_vhost_limits
author: Hiroyuki Matsuo (@h-matsuo)
version_added: "2.8"

short_description: Manage the state of virtual host limits in RabbitMQ
description:
    - This module sets/clears certain limits on a virtual host.
    - The configurable limits are I(max_connections) and I(max-queues).

options:
    max_connections:
        description:
            - Max number of concurrent client connections.
            - Negative value means "no limit".
            - Ignored when the I(state) is C(absent).
        default: -1
    max_queues:
        description:
            - Max number of queues.
            - Negative value means "no limit".
            - Ignored when the I(state) is C(absent).
        default: -1
    node:
        description:
            - Name of the RabbitMQ Erlang node to manage.
    state:
        description:
            - Specify whether the limits are to be set or cleared.
            - If set to C(absent), the limits of both I(max_connections) and I(max-queues) will be cleared.
        default: present
        choices: [present, absent]
    vhost:
        description:
            - Name of the virtual host to manage.
        default: /
'''

EXAMPLES = '''
# Limit both of the max number of connections and queues on the vhost '/'.
- rabbitmq_vhost_limits:
    vhost: /
    max_connections: 64
    max_queues: 256
    state: present

# Limit the max number of connections on the vhost '/'.
# This task implicitly clears the max number of queues limit using default value: -1.
- rabbitmq_vhost_limits:
    vhost: /
    max_connections: 64
    state: present

# Clear the limits on the vhost '/'.
- rabbitmq_vhost_limits:
    vhost: /
    state: absent
'''

RETURN = ''' # '''


import json
from ansible.module_utils.basic import AnsibleModule


class RabbitMqVhostLimits(object):
    def __init__(self, module):
        self._module = module
        self._max_connections = module.params['max_connections']
        self._max_queues = module.params['max_queues']
        self._node = module.params['node']
        self._state = module.params['state']
        self._vhost = module.params['vhost']
        self._rabbitmqctl = module.get_bin_path('rabbitmqctl', True)

    def _exec(self, args):
        cmd = [self._rabbitmqctl, '-q', '-p', self._vhost]
        if self._node is not None:
            cmd.extend(['-n', self._node])
        rc, out, err = self._module.run_command(cmd + args, check_rc=True)
        return dict(rc=rc, out=out.splitlines(), err=err.splitlines())

    def list(self):
        exec_result = self._exec(['list_vhost_limits'])
        vhost_limits = exec_result['out'][0]
        max_connections = None
        max_queues = None
        if vhost_limits:
            vhost_limits = json.loads(vhost_limits)
            if 'max-connections' in vhost_limits:
                max_connections = vhost_limits['max-connections']
            if 'max-queues' in vhost_limits:
                max_queues = vhost_limits['max-queues']
        return dict(
            max_connections=max_connections,
            max_queues=max_queues
        )

    def set(self):
        if self._module.check_mode:
            return
        json_str = '{{"max-connections": {0}, "max-queues": {1}}}'.format(self._max_connections, self._max_queues)
        self._exec(['set_vhost_limits', json_str])

    def clear(self):
        if self._module.check_mode:
            return
        self._exec(['clear_vhost_limits'])


def main():
    arg_spec = dict(
        max_connections=dict(default=-1, type='int'),
        max_queues=dict(default=-1, type='int'),
        node=dict(default=None, type='str'),
        state=dict(default='present', choices=['present', 'absent'], type='str'),
        vhost=dict(default='/', type='str')
    )

    module = AnsibleModule(
        argument_spec=arg_spec,
        supports_check_mode=True
    )

    max_connections = module.params['max_connections']
    max_queues = module.params['max_queues']
    node = module.params['node']
    state = module.params['state']
    vhost = module.params['vhost']

    module_result = dict(changed=False)
    rabbitmq_vhost_limits = RabbitMqVhostLimits(module)
    current_status = rabbitmq_vhost_limits.list()

    if state == 'present':
        wanted_status = dict(
            max_connections=max_connections,
            max_queues=max_queues
        )
    else:  # state == 'absent'
        wanted_status = dict(
            max_connections=None,
            max_queues=None
        )

    if current_status != wanted_status:
        module_result['changed'] = True
        if state == 'present':
            rabbitmq_vhost_limits.set()
        else:  # state == 'absent'
            rabbitmq_vhost_limits.clear()

    module.exit_json(**module_result)


if __name__ == '__main__':
    main()
