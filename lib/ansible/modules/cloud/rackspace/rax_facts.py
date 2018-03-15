#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: rax_facts
short_description: Gather facts for Rackspace Cloud Servers
description:
     - Gather facts for Rackspace Cloud Servers.
version_added: "1.4"
options:
  address:
    description:
      - Server IP address to retrieve facts for, will match any IP assigned to
        the server
  id:
    description:
      - Server ID to retrieve facts for
  name:
    description:
      - Server name to retrieve facts for
author: "Matt Martz (@sivel)"
extends_documentation_fragment: rackspace.openstack
'''

EXAMPLES = '''
- name: Gather info about servers
  hosts: all
  gather_facts: False
  tasks:
    - name: Get facts about servers
      local_action:
        module: rax_facts
        credentials: ~/.raxpub
        name: "{{ inventory_hostname }}"
        region: DFW
    - name: Map some facts
      set_fact:
        ansible_ssh_host: "{{ rax_accessipv4 }}"
'''

try:
    import pyrax
    HAS_PYRAX = True
except ImportError:
    HAS_PYRAX = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.rax import (rax_argument_spec,
                                      rax_required_together,
                                      rax_to_dict,
                                      setup_rax_module,
                                      )


def rax_facts(module, address, name, server_id):
    changed = False

    cs = pyrax.cloudservers

    if cs is None:
        module.fail_json(msg='Failed to instantiate client. This '
                             'typically indicates an invalid region or an '
                             'incorrectly capitalized region name.')

    ansible_facts = {}

    search_opts = {}
    if name:
        search_opts = dict(name='^%s$' % name)
        try:
            servers = cs.servers.list(search_opts=search_opts)
        except Exception as e:
            module.fail_json(msg='%s' % e.message)
    elif address:
        servers = []
        try:
            for server in cs.servers.list():
                for addresses in server.networks.values():
                    if address in addresses:
                        servers.append(server)
                        break
        except Exception as e:
            module.fail_json(msg='%s' % e.message)
    elif server_id:
        servers = []
        try:
            servers.append(cs.servers.get(server_id))
        except Exception as e:
            pass

    servers[:] = [server for server in servers if server.status != "DELETED"]

    if len(servers) > 1:
        module.fail_json(msg='Multiple servers found matching provided '
                             'search parameters')
    elif len(servers) == 1:
        ansible_facts = rax_to_dict(servers[0], 'server')

    module.exit_json(changed=changed, ansible_facts=ansible_facts)


def main():
    argument_spec = rax_argument_spec()
    argument_spec.update(
        dict(
            address=dict(),
            id=dict(),
            name=dict(),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=rax_required_together(),
        mutually_exclusive=[['address', 'id', 'name']],
        required_one_of=[['address', 'id', 'name']],
    )

    if not HAS_PYRAX:
        module.fail_json(msg='pyrax is required for this module')

    address = module.params.get('address')
    server_id = module.params.get('id')
    name = module.params.get('name')

    setup_rax_module(module, pyrax)

    rax_facts(module, address, name, server_id)


if __name__ == '__main__':
    main()
