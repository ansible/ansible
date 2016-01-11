#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, James Martin <jmartin@basho.com>, Drew Kerrigan <dkerrigan@basho.com>
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
#
DOCUMENTATION = '''
---
module: riak
short_description: This module handles some common Riak operations
description:
     - This module can be used to join nodes to a cluster, check
       the status of the cluster.
version_added: "1.2"
author:
    - "James Martin (@jsmartin)"
    - "Drew Kerrigan (@drewkerrigan)"
options:
  command:
    description:
      - The command you would like to perform against the cluster.
    required: false
    default: null
    aliases: []
    choices: ['ping', 'kv_test', 'join', 'plan', 'commit']
  config_dir:
    description:
      - The path to the riak configuration directory
    required: false
    default: /etc/riak
    aliases: []
  http_conn:
    description:
      - The ip address and port that is listening for Riak HTTP queries
    required: false
    default: 127.0.0.1:8098
    aliases: []
  target_node:
    description:
      - The target node for certain operations (join, ping)
    required: false
    default: riak@127.0.0.1
    aliases: []
  wait_for_handoffs:
    description:
      - Number of seconds to wait for handoffs to complete.
    required: false
    default: null
    aliases: []
    type: 'int'
  wait_for_ring:
    description:
      - Number of seconds to wait for all nodes to agree on the ring.
    required: false
    default: null
    aliases: []
    type: 'int'
  wait_for_service:
    description:
      - Waits for a riak service to come online before continuing.
    required: false
    default: None
    aliases: []
    choices: ['kv']
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be used
        on personally controlled sites using self-signed certificates.
    required: false
    default: 'yes'
    choices: ['yes', 'no']
    version_added: 1.5.1
'''

EXAMPLES = '''
# Join's a Riak node to another node
- riak: command=join target_node=riak@10.1.1.1

# Wait for handoffs to finish.  Use with async and poll.
- riak: wait_for_handoffs=yes

# Wait for riak_kv service to startup
- riak: wait_for_service=kv
'''

import time
import socket
import sys

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        # Let snippet from module_utils/basic.py return a proper error in this case
        pass


def ring_check(module, riak_admin_bin):
    cmd = '%s ringready' % riak_admin_bin
    rc, out, err = module.run_command(cmd)
    if rc == 0 and 'TRUE All nodes agree on the ring' in out:
        return True
    else:
        return False

def main():

    module = AnsibleModule(
        argument_spec=dict(
        command=dict(required=False, default=None, choices=[
                    'ping', 'kv_test', 'join', 'plan', 'commit']),
        config_dir=dict(default='/etc/riak'),
        http_conn=dict(required=False, default='127.0.0.1:8098'),
        target_node=dict(default='riak@127.0.0.1', required=False),
        wait_for_handoffs=dict(default=False, type='int'),
        wait_for_ring=dict(default=False, type='int'),
        wait_for_service=dict(
            required=False, default=None, choices=['kv']),
        validate_certs = dict(default='yes', type='bool'))
    )


    command = module.params.get('command')
    config_dir = module.params.get('config_dir')
    http_conn = module.params.get('http_conn')
    target_node = module.params.get('target_node')
    wait_for_handoffs = module.params.get('wait_for_handoffs')
    wait_for_ring = module.params.get('wait_for_ring')
    wait_for_service = module.params.get('wait_for_service')
    validate_certs =  module.params.get('validate_certs')


    #make sure riak commands are on the path
    riak_bin = module.get_bin_path('riak')
    riak_admin_bin = module.get_bin_path('riak-admin')

    timeout = time.time() + 120
    while True:
        if time.time() > timeout:
            module.fail_json(msg='Timeout, could not fetch Riak stats.')
        (response, info) = fetch_url(module, 'http://%s/stats' % (http_conn), force=True, timeout=5)
        if info['status'] == 200:
            stats_raw = response.read()
            break
        time.sleep(5)

    # here we attempt to load those stats,
    try:
        stats = json.loads(stats_raw)
    except:
        module.fail_json(msg='Could not parse Riak stats.')

    node_name = stats['nodename']
    nodes = stats['ring_members']
    ring_size = stats['ring_creation_size']
    rc, out, err = module.run_command([riak_bin, 'version'] )
    version = out.strip()
    
    result = dict(node_name=node_name,
              nodes=nodes,
              ring_size=ring_size,
              version=version)

    if command == 'ping':
        cmd = '%s ping %s' % ( riak_bin, target_node )
        rc, out, err = module.run_command(cmd)
        if rc == 0:
            result['ping'] = out
        else:
            module.fail_json(msg=out)

    elif command == 'kv_test':
        cmd = '%s test' % riak_admin_bin
        rc, out, err = module.run_command(cmd)
        if rc == 0:
            result['kv_test'] = out
        else:
            module.fail_json(msg=out)

    elif command == 'join':
        if nodes.count(node_name) == 1 and len(nodes) > 1:
            result['join'] = 'Node is already in cluster or staged to be in cluster.'
        else:
            cmd = '%s cluster join %s' % (riak_admin_bin, target_node)
            rc, out, err = module.run_command(cmd)
            if rc == 0:
                result['join'] = out
                result['changed'] = True
            else:
                module.fail_json(msg=out)

    elif command == 'plan':
        cmd = '%s cluster plan' % riak_admin_bin
        rc, out, err = module.run_command(cmd)
        if rc == 0:
            result['plan'] = out
            if 'Staged Changes' in out:
                result['changed'] = True
        else:
            module.fail_json(msg=out)

    elif command == 'commit':
        cmd = '%s cluster commit' % riak_admin_bin
        rc, out, err = module.run_command(cmd)
        if rc == 0:
            result['commit'] = out
            result['changed'] = True
        else:
            module.fail_json(msg=out)

# this could take a while, recommend to run in async mode
    if wait_for_handoffs:
        timeout = time.time() + wait_for_handoffs
        while True:
            cmd = '%s transfers' % riak_admin_bin
            rc, out, err = module.run_command(cmd)
            if 'No transfers active' in out:
                result['handoffs'] = 'No transfers active.'
                break
            time.sleep(10)
            if time.time() > timeout:
                module.fail_json(msg='Timeout waiting for handoffs.')

    if wait_for_service:
        cmd = [riak_admin_bin, 'wait_for_service', 'riak_%s' % wait_for_service, node_name ]
        rc, out, err = module.run_command(cmd)
        result['service'] = out

    if wait_for_ring:
        timeout = time.time() + wait_for_ring
        while True:
            if ring_check(module, riak_admin_bin):
                break
            time.sleep(10)
        if time.time() > timeout:
            module.fail_json(msg='Timeout waiting for nodes to agree on ring.')

    result['ring_ready'] = ring_check(module, riak_admin_bin)

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
if __name__ == '__main__':
    main()
