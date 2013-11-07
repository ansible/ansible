#!/usr/bin/python
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
  api_key:
    required: false
    description:
      - Rackspace API key (overrides C(credentials))
  condition:
    required: false
    choices: [ "enabled", "disabled", "draining" ]
    description:
      - Condition for the node, which determines its role within the load
        balancer
  credentials:
    required: false
    description:
      - File to find the Rackspace credentials in (ignored if C(api_key) and
        C(username) are provided)
  load_balancer_id:
    required: true
    type: integer
    description:
      - Load balancer id
  node_id:
    required: false
    type: integer
    description:
      - Node id
  port:
    required: false
    type: integer
    description:
      - Port number of the load balanced service on the node
  region:
    required: false
    description:
     - Region to authenticate in
  state:
    required: false
    default: "present"
    choices: [ "present", "absent" ]
    description:
      - Indicate desired state of the node
  type:
    required: false
    choices: [ "primary", "secondary" ]
    description:
      - Type of node
  username:
    required: false
    description:
     - Rackspace username (overrides C(credentials))
  virtualenv:
    required: false
    description:
      - Path to a virtualenv that should be activated before doing anything.
        The virtualenv has to already exist. Useful if installing pyrax
        globally is not an option.
  wait:
    required: false
    default: "no"
    choices: [ "yes", "no" ]
    description:
      - Wait for the load balancer to become active before returning
  wait_timeout:
    required: false
    type: integer
    default: 30
    description:
      - How long to wait before giving up and returning an error
  weight:
    required: false
    description:
      - Weight of node
requirements: [ "pyrax" ]
author: Lukasz Kawczynski
notes:
  - "The following environment variables can be used: C(RAX_USERNAME),
    C(RAX_API_KEY), C(RAX_CREDENTIALS) and C(RAX_REGION)."
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


def _activate_virtualenv(path):
    path = os.path.expanduser(path)
    activate_this = os.path.join(path, 'bin', 'activate_this.py')
    execfile(activate_this, dict(__file__=activate_this))


def _get_node(lb, node_id):
    """Return a node with the given `node_id`"""
    for node in lb.nodes:
        if node.id == node_id:
            return node
    return None


def _is_primary(node):
    """Return True if node is primary and enabled"""
    return (node.type.lower() == 'primary' and
            node.condition.lower() == 'enabled')


def _get_primary_nodes(lb):
    """Return a list of primary and enabled nodes"""
    nodes = []
    for node in lb.nodes:
        if _is_primary(node):
            nodes.append(node)
    return nodes


def _node_to_dict(node):
    """Return a dictionary containing node details"""
    if not node:
        return {}
    return {
        'address': node.address,
        'condition': node.condition,
        'id': node.id,
        'port': node.port,
        'type': node.type,
        'weight': node.weight,
    }


def main():
    module = AnsibleModule(
        argument_spec=dict(
            address=dict(),
            api_key=dict(),
            condition=dict(choices=['enabled', 'disabled', 'draining']),
            credentials=dict(),
            load_balancer_id=dict(required=True, type='int'),
            node_id=dict(type='int'),
            port=dict(type='int'),
            region=dict(),
            state=dict(default='present', choices=['present', 'absent']),
            type=dict(choices=['primary', 'secondary']),
            username=dict(),
            virtualenv=dict(),
            wait=dict(default=False, type='bool'),
            wait_timeout=dict(default=30, type='int'),
            weight=dict(type='int'),
        ),
        required_together=[
            ['api_key', 'username']
        ],
    )

    address = module.params['address']
    api_key = module.params['api_key']
    condition = (module.params['condition'] and
                 module.params['condition'].upper())
    credentials = module.params['credentials']
    load_balancer_id = module.params['load_balancer_id']
    node_id = module.params['node_id']
    port = module.params['port']
    region = module.params['region']
    state = module.params['state']
    typ = module.params['type'] and module.params['type'].upper()
    username = module.params['username']
    virtualenv = module.params['virtualenv']
    wait = module.params['wait']
    wait_timeout = module.params['wait_timeout'] or 1
    weight = module.params['weight']

    if virtualenv:
        try:
            _activate_virtualenv(virtualenv)
        except IOError, e:
            module.fail_json(msg='Failed to activate virtualenv %s (%s)' % (
                                 virtualenv, e))

    try:
        import pyrax
    except ImportError:
        module.fail_json(msg='pyrax is not installed')

    username = username or os.environ.get('RAX_USERNAME')
    api_key = api_key or os.environ.get('RAX_API_KEY')
    credentials = credentials or os.environ.get('RAX_CREDENTIALS')
    region = region or os.environ.get('RAX_REGION')

    pyrax.set_setting("identity_type", "rackspace")

    try:
        if api_key and username:
            pyrax.set_credentials(username, api_key=api_key, region=region)
        elif credentials:
            credentials = os.path.expanduser(credentials)
            pyrax.set_credential_file(credentials, region=region)
        else:
            module.fail_json(msg='Credentials not set')
    except pyrax.exc.PyraxException, e:
        module.fail_json(msg='%s' % e.message)

    if not pyrax.cloud_loadbalancers:
        module.fail_json(msg='Failed to instantiate load balancer client '
                             '(possibly incorrect region)')

    try:
        lb = pyrax.cloud_loadbalancers.get(load_balancer_id)
    except pyrax.exc.PyraxException, e:
        module.fail_json(msg='%s' % e.message)

    if node_id:
        node = _get_node(lb, node_id)
    else:
        node = None

    result = _node_to_dict(node)

    if state == 'absent':
        if not node:  # Removing a non-existent node
            module.exit_json(changed=False, state=state)

        # The API detects this as well but currently pyrax does not return a
        # meaningful error message
        if _is_primary(node) and len(_get_primary_nodes(lb)) == 1:
            module.fail_json(
                msg='At least one primary node has to be enabled')

        try:
            lb.delete_node(node)
            result = {}
        except pyrax.exc.NotFound:
            module.exit_json(changed=False, state=state)
        except pyrax.exc.PyraxException, e:
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
                except pyrax.exc.PyraxException, e:
                    module.fail_json(msg='%s' % e.message)
        else:  # Updating an existing node
            immutable = {
                'address': address,
                'port': port,
            }

            mutable = {
                'condition': condition,
                'type': typ,
                'weight': weight,
            }

            for name, value in immutable.items():
                if value:
                    module.fail_json(
                        msg='Attribute %s cannot be modified' % name)

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
            except pyrax.exc.PyraxException, e:
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

# this is magic, see lib/ansible/module_common.py
#<<INCLUDE_ANSIBLE_MODULE_COMMON>>
main()
