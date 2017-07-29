#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: rax_clb_nodes
short_description: add, modify and remove nodes from a Rackspace Cloud Load Balancer
description:
  - Adds, modifies and removes nodes from a Rackspace Cloud Load Balancer
version_added: "1.4"
options:
  address:
    required: false
    description:
      - IP address or domain name of the node
  condition:
    required: false
    choices:
      - enabled
      - disabled
      - draining
    description:
      - Condition for the node, which determines its role within the load
        balancer
  load_balancer_id:
    required: true
    description:
      - Load balancer id
  node_id:
    required: false
    description:
      - Node id
  port:
    required: false
    description:
      - Port number of the load balanced service on the node
  state:
    required: false
    default: "present"
    choices:
      - present
      - absent
    description:
      - Indicate desired state of the node
  type:
    required: false
    choices:
      - primary
      - secondary
    description:
      - Type of node
  wait:
    required: false
    default: "no"
    choices:
      - "yes"
      - "no"
    description:
      - Wait for the load balancer to become active before returning
  wait_timeout:
    required: false
    default: 30
    description:
      - How long to wait before giving up and returning an error
  weight:
    required: false
    description:
      - Weight of node
author: "Lukasz Kawczynski (@neuroid)"
extends_documentation_fragment: rackspace
'''

EXAMPLES = '''
# Add a new node to the load balancer
- local_action:
    module: rax_clb_nodes
    load_balancer_id: 71
    address: 10.2.2.3
    port: 80
    condition: enabled
    type: primary
    wait: yes
    credentials: /path/to/credentials

# Drain connections from a node
- local_action:
    module: rax_clb_nodes
    load_balancer_id: 71
    node_id: 410
    condition: draining
    wait: yes
    credentials: /path/to/credentials

# Remove a node from the load balancer
- local_action:
    module: rax_clb_nodes
    load_balancer_id: 71
    node_id: 410
    state: absent
    wait: yes
    credentials: /path/to/credentials
'''

import os

try:
    import pyrax
    HAS_PYRAX = True
except ImportError:
    HAS_PYRAX = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.rax import rax_argument_spec, rax_clb_node_to_dict, rax_required_together, setup_rax_module


def _activate_virtualenv(path):
    path = os.path.expanduser(path)
    activate_this = os.path.join(path, 'bin', 'activate_this.py')
    with open(activate_this) as f:
        code = compile(f.read(), activate_this, 'exec')
        exec(code)


def _get_node(lb, node_id=None, address=None, port=None):
    """Return a matching node"""
    for node in getattr(lb, 'nodes', []):
        match_list = []
        if node_id is not None:
            match_list.append(getattr(node, 'id', None) == node_id)
        if address is not None:
            match_list.append(getattr(node, 'address', None) == address)
        if port is not None:
            match_list.append(getattr(node, 'port', None) == port)

        if match_list and all(match_list):
            return node

    return None


def main():
    argument_spec = rax_argument_spec()
    argument_spec.update(
        dict(
            address=dict(),
            condition=dict(choices=['enabled', 'disabled', 'draining']),
            load_balancer_id=dict(required=True, type='int'),
            node_id=dict(type='int'),
            port=dict(type='int'),
            state=dict(default='present', choices=['present', 'absent']),
            type=dict(choices=['primary', 'secondary']),
            virtualenv=dict(),
            wait=dict(default=False, type='bool'),
            wait_timeout=dict(default=30, type='int'),
            weight=dict(type='int'),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=rax_required_together(),
    )

    if not HAS_PYRAX:
        module.fail_json(msg='pyrax is required for this module')

    address = module.params['address']
    condition = (module.params['condition'] and
                 module.params['condition'].upper())
    load_balancer_id = module.params['load_balancer_id']
    node_id = module.params['node_id']
    port = module.params['port']
    state = module.params['state']
    typ = module.params['type'] and module.params['type'].upper()
    virtualenv = module.params['virtualenv']
    wait = module.params['wait']
    wait_timeout = module.params['wait_timeout'] or 1
    weight = module.params['weight']

    if virtualenv:
        try:
            _activate_virtualenv(virtualenv)
        except IOError as e:
            module.fail_json(msg='Failed to activate virtualenv %s (%s)' % (
                                 virtualenv, e))

    setup_rax_module(module, pyrax)

    if not pyrax.cloud_loadbalancers:
        module.fail_json(msg='Failed to instantiate client. This '
                             'typically indicates an invalid region or an '
                             'incorrectly capitalized region name.')

    try:
        lb = pyrax.cloud_loadbalancers.get(load_balancer_id)
    except pyrax.exc.PyraxException as e:
        module.fail_json(msg='%s' % e.message)

    node = _get_node(lb, node_id, address, port)

    result = rax_clb_node_to_dict(node)

    if state == 'absent':
        if not node:  # Removing a non-existent node
            module.exit_json(changed=False, state=state)
        try:
            lb.delete_node(node)
            result = {}
        except pyrax.exc.NotFound:
            module.exit_json(changed=False, state=state)
        except pyrax.exc.PyraxException as e:
            module.fail_json(msg='%s' % e.message)
    else:  # present
        if not node:
            if node_id:  # Updating a non-existent node
                msg = 'Node %d not found' % node_id
                if lb.nodes:
                    msg += (' (available nodes: %s)' %
                            ', '.join([str(x.id) for x in lb.nodes]))
                module.fail_json(msg=msg)
            else:  # Creating a new node
                try:
                    node = pyrax.cloudloadbalancers.Node(
                        address=address, port=port, condition=condition,
                        weight=weight, type=typ)
                    resp, body = lb.add_nodes([node])
                    result.update(body['nodes'][0])
                except pyrax.exc.PyraxException as e:
                    module.fail_json(msg='%s' % e.message)
        else:  # Updating an existing node
            mutable = {
                'condition': condition,
                'type': typ,
                'weight': weight,
            }

            for name, value in mutable.items():
                if value is None or value == getattr(node, name):
                    mutable.pop(name)

            if not mutable:
                module.exit_json(changed=False, state=state, node=result)

            try:
                # The diff has to be set explicitly to update node's weight and
                # type; this should probably be fixed in pyrax
                lb.update_node(node, diff=mutable)
                result.update(mutable)
            except pyrax.exc.PyraxException as e:
                module.fail_json(msg='%s' % e.message)

    if wait:
        pyrax.utils.wait_until(lb, "status", "ACTIVE", interval=1,
                               attempts=wait_timeout)
        if lb.status != 'ACTIVE':
            module.fail_json(
                msg='Load balancer not active after %ds (current status: %s)' %
                    (wait_timeout, lb.status.lower()))

    kwargs = {'node': result} if result else {}
    module.exit_json(changed=True, state=state, **kwargs)


if __name__ == '__main__':
    main()
