#!/usr/bin/python
# Copyright 2015 WP Engine, Inc. All rights reserved.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: znode
version_added: "2.0"
short_description: Create, delete, retrieve, and update znodes using ZooKeeper
description:
    - Create, delete, retrieve, and update znodes using ZooKeeper.
options:
    hosts:
        description:
            - A list of ZooKeeper servers (format '[server]:[port]').
        required: true
    name:
        description:
            - The path of the znode.
        required: true
    value:
        description:
            - The value assigned to the znode.
        default: None
        required: false
    op:
        description:
            - An operation to perform. Mutually exclusive with state.
        default: None
        required: false
    state:
        description:
            - The state to enforce. Mutually exclusive with op.
        default: None
        required: false
    timeout:
        description:
            - The amount of time to wait for a node to appear.
        default: 300
        required: false
    recursive:
        description:
            - Recursively delete node and all its children.
        default: False
        required: false
        version_added: "2.1"
requirements:
    - kazoo >= 2.1
    - python >= 2.6
author: "Trey Perry (@treyperry)"
"""

EXAMPLES = """
# Creating or updating a znode with a given value
- znode:
    hosts: 'localhost:2181'
    name: /mypath
    value: myvalue
    state: present

# Getting the value and stat structure for a znode
- znode:
    hosts: 'localhost:2181'
    name: /mypath
    op: get

# Listing a particular znode's children
- znode:
    hosts: 'localhost:2181'
    name: /zookeeper
    op: list

# Waiting 20 seconds for a znode to appear at path /mypath
- znode:
    hosts: 'localhost:2181'
    name: /mypath
    op: wait
    timeout: 20

# Deleting a znode at path /mypath
- znode:
    hosts: 'localhost:2181'
    name: /mypath
    state: absent

# Creating or updating a znode with a given value on a remote Zookeeper
- znode:
    hosts: 'my-zookeeper-node:2181'
    name: /mypath
    value: myvalue
    state: present
  delegate_to: 127.0.0.1
"""

import time

try:
    from kazoo.client import KazooClient
    from kazoo.handlers.threading import KazooTimeoutError
    KAZOO_INSTALLED = True
except ImportError:
    KAZOO_INSTALLED = False

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            hosts=dict(required=True, type='str'),
            name=dict(required=True, type='str'),
            value=dict(required=False, default=None, type='str'),
            op=dict(required=False, default=None, choices=['get', 'wait', 'list']),
            state=dict(choices=['present', 'absent']),
            timeout=dict(required=False, default=300, type='int'),
            recursive=dict(required=False, default=False, type='bool')
        ),
        supports_check_mode=False
    )

    if not KAZOO_INSTALLED:
        module.fail_json(msg='kazoo >= 2.1 is required to use this module. Use pip to install it.')

    check = check_params(module.params)
    if not check['success']:
        module.fail_json(msg=check['msg'])

    zoo = KazooCommandProxy(module)
    try:
        zoo.start()
    except KazooTimeoutError:
        module.fail_json(msg='The connection to the ZooKeeper ensemble timed out.')

    command_dict = {
        'op': {
            'get': zoo.get,
            'list': zoo.list,
            'wait': zoo.wait
        },
        'state': {
            'present': zoo.present,
            'absent': zoo.absent
        }
    }

    command_type = 'op' if 'op' in module.params and module.params['op'] is not None else 'state'
    method = module.params[command_type]
    result, result_dict = command_dict[command_type][method]()
    zoo.shutdown()

    if result:
        module.exit_json(**result_dict)
    else:
        module.fail_json(**result_dict)


def check_params(params):
    if not params['state'] and not params['op']:
        return {'success': False, 'msg': 'Please define an operation (op) or a state.'}

    if params['state'] and params['op']:
        return {'success': False, 'msg': 'Please choose an operation (op) or a state, but not both.'}

    return {'success': True}


class KazooCommandProxy():
    def __init__(self, module):
        self.module = module
        self.zk = KazooClient(module.params['hosts'])

    def absent(self):
        return self._absent(self.module.params['name'])

    def exists(self, znode):
        return self.zk.exists(znode)

    def list(self):
        children = self.zk.get_children(self.module.params['name'])
        return True, {'count': len(children), 'items': children, 'msg': 'Retrieved znodes in path.',
                      'znode': self.module.params['name']}

    def present(self):
        return self._present(self.module.params['name'], self.module.params['value'])

    def get(self):
        return self._get(self.module.params['name'])

    def shutdown(self):
        self.zk.stop()
        self.zk.close()

    def start(self):
        self.zk.start()

    def wait(self):
        return self._wait(self.module.params['name'], self.module.params['timeout'])

    def _absent(self, znode):
        if self.exists(znode):
            self.zk.delete(znode, recursive=self.module.params['recursive'])
            return True, {'changed': True, 'msg': 'The znode was deleted.'}
        else:
            return True, {'changed': False, 'msg': 'The znode does not exist.'}

    def _get(self, path):
        if self.exists(path):
            value, zstat = self.zk.get(path)
            stat_dict = {}
            for i in dir(zstat):
                if not i.startswith('_'):
                    attr = getattr(zstat, i)
                    if isinstance(attr, (int, str)):
                        stat_dict[i] = attr
            result = True, {'msg': 'The node was retrieved.', 'znode': path, 'value': value,
                            'stat': stat_dict}
        else:
            result = False, {'msg': 'The requested node does not exist.'}

        return result

    def _present(self, path, value):
        if self.exists(path):
            (current_value, zstat) = self.zk.get(path)
            if value != current_value:
                self.zk.set(path, value)
                return True, {'changed': True, 'msg': 'Updated the znode value.', 'znode': path,
                              'value': value}
            else:
                return True, {'changed': False, 'msg': 'No changes were necessary.', 'znode': path, 'value': value}
        else:
            self.zk.create(path, value, makepath=True)
            return True, {'changed': True, 'msg': 'Created a new znode.', 'znode': path, 'value': value}

    def _wait(self, path, timeout, interval=5):
        lim = time.time() + timeout

        while time.time() < lim:
            if self.exists(path):
                return True, {'msg': 'The node appeared before the configured timeout.',
                              'znode': path, 'timeout': timeout}
            else:
                time.sleep(interval)

        return False, {'msg': 'The node did not appear before the operation timed out.', 'timeout': timeout,
                       'znode': path}


if __name__ == '__main__':
    main()
