#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, First Last <email address>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module:
short_description:
description:
  -
version_added:
author: '"First Last (@GitHubID)"'
options:
'''


EXAMPLES = '''
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

    def _exec(self, args, run_in_check_mode=False):
        if (not self._module.check_mode) or run_in_check_mode:
            cmd = [self._rabbitmqctl, '-q']
            if self._node is not None:
                cmd.extend(['-n', self._node])
            rc, out, err = self._module.run_command(cmd + args, check_rc=True)
            return dict(rc=rc, out=out.splitlines(), err=err.splitlines())
        return list()

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
    state = module.params['state']

    module_result = dict(changed=False)
    rabbitmq_vhost_limits = RabbitMqVhostLimits(module)
    current_status = rabbitmq_vhost_limits.list()

    if state == 'present':
        wanted_status = dict(
            max_connections=max_connections,
            max_queues=max_queues
        )
    else: # state == 'absent'
        wanted_status = dict(
            max_connections=None,
            max_queues=None
        )

    if current_status != wanted_status:
        if state == 'present':
            rabbitmq_vhost_limits.set()
            module_result['changed'] = True
        else: # state == 'absent'
            rabbitmq_vhost_limits.clear()
            module_result['changed'] = True

    module.exit_json(**module_result)


if __name__ == '__main__':
    main()
