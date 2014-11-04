#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Matt Hite <mhite@hotmail.com>
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

DOCUMENTATION = '''
---
module: bigip_node
short_description: "Manages F5 BIG-IP LTM nodes"
description:
    - "Manages F5 BIG-IP LTM nodes via iControl SOAP API"
version_added: "1.4"
author: Matt Hite
notes:
    - "Requires BIG-IP software version >= 11"
    - "F5 developed module 'bigsuds' required (see http://devcentral.f5.com)"
    - "Best run as a local_action in your playbook"
requirements:
    - bigsuds
options:
    server:
        description:
            - BIG-IP host
        required: true
        default: null
        choices: []
        aliases: []
    user:
        description:
            - BIG-IP username
        required: true
        default: null
        choices: []
        aliases: []
    password:
        description:
            - BIG-IP password
        required: true
        default: null
        choices: []
        aliases: []
    state:
        description:
            - Pool member state
        required: true
        default: present
        choices: ['present', 'absent']
        aliases: []
    partition:
        description:
            - Partition
        required: false
        default: 'Common'
        choices: []
        aliases: []
    name:
        description:
            - "Node name"
        required: false
        default: null
        choices: []
    host:
        description:
            - "Node IP. Required when state=present and node does not exist. Error when state=absent."
        required: true
        default: null
        choices: []
        aliases: ['address', 'ip']
    description:
        description:
            - "Node description."
        required: false
        default: null
        choices: []
'''

EXAMPLES = '''

## playbook task examples:

---
# file bigip-test.yml
# ...
- hosts: bigip-test
  tasks:
  - name: Add node
    local_action: >
      bigip_node
      server=lb.mydomain.com
      user=admin
      password=mysecret
      state=present
      partition=matthite
      host="{{ ansible_default_ipv4["address"] }}"
      name="{{ ansible_default_ipv4["address"] }}"

# Note that the BIG-IP automatically names the node using the
# IP address specified in previous play's host parameter.
# Future plays referencing this node no longer use the host
# parameter but instead use the name parameter.
# Alternatively, you could have specified a name with the
# name parameter when state=present.

  - name: Modify node description
    local_action: >
      bigip_node
      server=lb.mydomain.com
      user=admin
      password=mysecret
      state=present
      partition=matthite
      name="{{ ansible_default_ipv4["address"] }}"
      description="Our best server yet"

  - name: Delete node
    local_action: >
      bigip_node
      server=lb.mydomain.com
      user=admin
      password=mysecret
      state=absent
      partition=matthite
      name="{{ ansible_default_ipv4["address"] }}"

'''

try:
    import bigsuds
except ImportError:
    bigsuds_found = False
else:
    bigsuds_found = True

# ==========================
# bigip_node module specific
#

def bigip_api(bigip, user, password):
    api = bigsuds.BIGIP(hostname=bigip, username=user, password=password)
    return api

def node_exists(api, address):
    # hack to determine if node exists
    result = False
    try:
        api.LocalLB.NodeAddressV2.get_object_status(nodes=[address])
        result = True
    except bigsuds.OperationFailed, e:
        if "was not found" in str(e):
            result = False
        else:
            # genuine exception
            raise
    return result

def create_node_address(api, address, name):
    try:
        api.LocalLB.NodeAddressV2.create(nodes=[name], addresses=[address], limits=[0])
        result = True
        desc = ""
    except bigsuds.OperationFailed, e:
        if "already exists" in str(e):
            result = False
            desc = "referenced name or IP already in use"
        else:
            # genuine exception
            raise
    return (result, desc)

def get_node_address(api, name):
    return api.LocalLB.NodeAddressV2.get_address(nodes=[name])[0]

def delete_node_address(api, address):
    try:
        api.LocalLB.NodeAddressV2.delete_node_address(nodes=[address])
        result = True
        desc = ""
    except bigsuds.OperationFailed, e:
        if "is referenced by a member of pool" in str(e):
            result = False
            desc = "node referenced by pool"
        else:
            # genuine exception
            raise
    return (result, desc)

def set_node_description(api, name, description):
    api.LocalLB.NodeAddressV2.set_description(nodes=[name],
                                                  descriptions=[description])

def get_node_description(api, name):
    return api.LocalLB.NodeAddressV2.get_description(nodes=[name])[0]

def main():
    module = AnsibleModule(
        argument_spec = dict(
            server = dict(type='str', required=True),
            user = dict(type='str', required=True),
            password = dict(type='str', required=True),
            state = dict(type='str', default='present', choices=['present', 'absent']),
            partition = dict(type='str', default='Common'),
            name = dict(type='str', required=True),
            host = dict(type='str', aliases=['address', 'ip']),
            description = dict(type='str')
        ),
        supports_check_mode=True
    )

    if not bigsuds_found:
        module.fail_json(msg="the python bigsuds module is required")

    server = module.params['server']
    user = module.params['user']
    password = module.params['password']
    state = module.params['state']
    partition = module.params['partition']
    host = module.params['host']
    name = module.params['name']
    address = "/%s/%s" % (partition, name)
    description = module.params['description']

    if state == 'absent' and host is not None:
        module.fail_json(msg="host parameter invalid when state=absent")

    try:
        api = bigip_api(server, user, password)
        result = {'changed': False}  # default

        if state == 'absent':
            if node_exists(api, address):
                if not module.check_mode:
                    deleted, desc = delete_node_address(api, address)
                    if not deleted:
                        module.fail_json(msg="unable to delete: %s" % desc)
                    else:
                        result = {'changed': True}
                else:
                    # check-mode return value
                    result = {'changed': True}

        elif state == 'present':
            if not node_exists(api, address):
                if host is None:
                    module.fail_json(msg="host parameter required when " \
                                         "state=present and node does not exist")
                if not module.check_mode:
                    created, desc = create_node_address(api, address=host, name=address)
                    if not created:
                        module.fail_json(msg="unable to create: %s" % desc)
                    else:
                        result = {'changed': True}
                    if description is not None:
                        set_node_description(api, address, description)
                        result = {'changed': True}
                else:
                    # check-mode return value
                    result = {'changed': True}
            else:
                # node exists -- potentially modify attributes
                if host is not None:
                    if get_node_address(api, address) != host:
                        module.fail_json(msg="Changing the node address is " \
                                             "not supported by the API; " \
                                             "delete and recreate the node.")
                if description is not None:
                    if get_node_description(api, address) != description:
                        if not module.check_mode:
                            set_node_description(api, address, description)
                        result = {'changed': True}

    except Exception, e:
        module.fail_json(msg="received exception: %s" % e)

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
main()

