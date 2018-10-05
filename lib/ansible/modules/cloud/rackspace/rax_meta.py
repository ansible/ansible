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
  meta:
    description:
      - A hash of metadata to associate with the instance
author: "Matt Martz (@sivel)"
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

import json

try:
    import pyrax
    HAS_PYRAX = True
except ImportError:
    HAS_PYRAX = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.rax import rax_argument_spec, rax_required_together, setup_rax_module
from ansible.module_utils.six import string_types


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
        elif not isinstance(v, string_types):
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


if __name__ == '__main__':
    main()
