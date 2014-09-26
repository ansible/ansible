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
module: rax_meta
short_description: Manipulate metadata for Rackspace Cloud Servers
description:
     - Manipulate metadata for Rackspace Cloud Servers
version_added: 1.7
options:
  address:
    description:
      - Server IP address to modify metadata for, will match any IP assigned to
        the server
  id:
    description:
      - Server ID to modify metadata for
  name:
    description:
      - Server name to modify metadata for
    default: null
  meta:
    description:
      - A hash of metadata to associate with the instance
    default: null
author: Matt Martz
extends_documentation_fragment: rackspace.openstack
'''

EXAMPLES = '''
- name: Set metadata for a server
  hosts: all
  gather_facts: False
  tasks:
    - name: Set metadata
      local_action:
        module: rax_meta
        credentials: ~/.raxpub
        name: "{{ inventory_hostname }}"
        region: DFW
        meta:
          group: primary_group
          groups:
            - group_two
            - group_three
          app: my_app

    - name: Clear metadata
      local_action:
        module: rax_meta
        credentials: ~/.raxpub
        name: "{{ inventory_hostname }}"
        region: DFW
'''

try:
    import pyrax
    HAS_PYRAX = True
except ImportError:
    HAS_PYRAX = False


def rax_meta(module, address, name, server_id, meta):
    changed = False

    cs = pyrax.cloudservers

    if cs is None:
        module.fail_json(msg='Failed to instantiate client. This '
                             'typically indicates an invalid region or an '
                             'incorrectly capitalized region name.')

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
    elif not servers:
        module.fail_json(msg='Failed to find a server matching provided '
                             'search parameters')

    # Normalize and ensure all metadata values are strings
    for k, v in meta.items():
        if isinstance(v, list):
            meta[k] = ','.join(['%s' % i for i in v])
        elif isinstance(v, dict):
            meta[k] = json.dumps(v)
        elif not isinstance(v, basestring):
            meta[k] = '%s' % v

    server = servers[0]
    if server.metadata == meta:
        changed = False
    else:
        changed = True
        removed = set(server.metadata.keys()).difference(meta.keys())
        cs.servers.delete_meta(server, list(removed))
        cs.servers.set_meta(server, meta)
        server.get()

    module.exit_json(changed=changed, meta=server.metadata)


def main():
    argument_spec = rax_argument_spec()
    argument_spec.update(
        dict(
            address=dict(),
            id=dict(),
            name=dict(),
            meta=dict(type='dict', default=dict()),
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
    meta = module.params.get('meta')

    setup_rax_module(module, pyrax)

    rax_meta(module, address, name, server_id, meta)


# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.rax import *

### invoke the module
main()
