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
author: '"Hiroyuki Matsuo (@h-matsuo)"'
version_added: "2.8"

short_description: Manage the state of virtual host limits in RabbitMQ
description:
  - This module can enforce or clear limits on a virtual host.
  - Recognized limits are I(max_connections) and I(max-queues).

options:
    max_connections:
        description:
            - Max number of concurrent connections.
            - Negative value means "no limit".
        default: -1
    max_queues:
        description:
            - Max number of queues.
            - Negative value means "no limit".
        default: -1
    node:
        description:
            - Erlang node name of the rabbit to be configured.
    state:
        description:
            - Specify if limits are to be set or cleared.
        default: present
        choices: [present, absent]
    vhost:
        description:
            - RabbitMQ virtual host to apply these limits.
        default: /
'''

EXAMPLES = '''
# Limits both of the max number of connections and the max number of queues on / vhost.
- rabbitmq_vhost_limits:
    max_connections: 64
    max_queues: 256
    vhost: /
    state: present

# Limits the max number of connections on / vhost.
# This task implicitly clears the max number of queues limit using default value: -1.
- rabbitmq_vhost_limits:
    max_connections: 64
    vhost: /
    state: present

# Clears the limits on / vhost.
- rabbitmq_vhost_limits:
    vhost: /
    state: absent
'''

RETURN = '''
max_connections:
    description:
        - Current max number of concurrent connections; C(null) if there are no limits.
    returned: always
    type: int
    sample: 64
max_queues:
    description: Current max number of queues; C(null) if there are no limits.
    returned: always
    type: int
    sample: 256
node:
    description: Erlag node name to be configured in this task; C(null) if not specified.
    returned: always
    type: string
    sample: rabbit
vhost:
    description: RabbitMQ virtual host to be configured in this task.
    returned: always
    type: string
    sample: /
'''


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
        cmd = [self._rabbitmqctl, '-q']
        if self._node is not None:
            cmd.extend(['-n', self._node])
        rc, out, err = self._module.run_command(cmd + args, check_rc=True)
        return dict(rc=rc, out=out.splitlines(), err=err.splitlines())

    def list(self):
        exec_result = self._exec(['list_vhost_limits', '-p', self._vhost])
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
        json_str = '{{"max-connections": {0}, "max-queues": {1}}}'.format(self._max_connections, self._max_queues)
        self._exec(['set_vhost_limits', '-p', self._vhost, json_str])

    def clear(self):
        self._exec(['clear_vhost_limits', '-p', self._vhost])


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
        if state == 'present':
            if not module.check_mode:
                rabbitmq_vhost_limits.set()
            module_result['changed'] = True
        else:  # state == 'absent'
            if not module.check_mode:
                rabbitmq_vhost_limits.clear()
            module_result['changed'] = True

    current_status = rabbitmq_vhost_limits.list()
    module_result['max_connections'] = current_status['max_connections']
    module_result['max_queues'] = current_status['max_queues']
    module_result['node'] = node
    module_result['vhost'] = vhost

    module.exit_json(**module_result)


if __name__ == '__main__':
    main()
