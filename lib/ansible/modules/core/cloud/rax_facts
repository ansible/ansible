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

# This is a DOCUMENTATION stub specific to this module, it extends
# a documentation fragment located in ansible.utils.module_docs_fragments
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
    default: null
author: Matt Martz
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
        except Exception, e:
            module.fail_json(msg='%s' % e.message)
    elif address:
        servers = []
        try:
            for server in cs.servers.list():
                for addresses in server.networks.values():
                    if address in addresses:
                        servers.append(server)
                        break
        except Exception, e:
            module.fail_json(msg='%s' % e.message)
    elif server_id:
        servers = []
        try:
            servers.append(cs.servers.get(server_id))
        except Exception, e:
            pass

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


# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.rax import *

### invoke the module
main()
