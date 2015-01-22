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
module: rax_network
short_description: create / delete an isolated network in Rackspace Public Cloud
description:
     - creates / deletes a Rackspace Public Cloud isolated network.
version_added: "1.4"
options:
  state:
    description:
     - Indicate desired state of the resource
    choices:
      - present
      - absent
    default: present
  label:
    description:
     - Label (name) to give the network
    default: null
  cidr:
    description:
     - cidr of the network being created
    default: null
author: Christopher H. Laco, Jesse Keating
extends_documentation_fragment: rackspace.openstack
'''

EXAMPLES = '''
- name: Build an Isolated Network
  gather_facts: False

  tasks:
    - name: Network create request
      local_action:
        module: rax_network
        credentials: ~/.raxpub
        label: my-net
        cidr: 192.168.3.0/24
        state: present
'''

try:
    import pyrax
    HAS_PYRAX = True
except ImportError:
    HAS_PYRAX = False


def cloud_network(module, state, label, cidr):
    changed = False
    network = None
    networks = []

    if not pyrax.cloud_networks:
        module.fail_json(msg='Failed to instantiate client. This '
                             'typically indicates an invalid region or an '
                             'incorrectly capitalized region name.')

    if state == 'present':
        if not cidr:
            module.fail_json(msg='missing required arguments: cidr')

        try:
            network = pyrax.cloud_networks.find_network_by_label(label)
        except pyrax.exceptions.NetworkNotFound:
            try:
                network = pyrax.cloud_networks.create(label, cidr=cidr)
                changed = True
            except Exception, e:
                module.fail_json(msg='%s' % e.message)
        except Exception, e:
            module.fail_json(msg='%s' % e.message)

    elif state == 'absent':
        try:
            network = pyrax.cloud_networks.find_network_by_label(label)
            network.delete()
            changed = True
        except pyrax.exceptions.NetworkNotFound:
            pass
        except Exception, e:
            module.fail_json(msg='%s' % e.message)

    if network:
        instance = dict(id=network.id,
                        label=network.label,
                        cidr=network.cidr)
        networks.append(instance)

    module.exit_json(changed=changed, networks=networks)


def main():
    argument_spec = rax_argument_spec()
    argument_spec.update(
        dict(
            state=dict(default='present',
                       choices=['present', 'absent']),
            label=dict(required=True),
            cidr=dict()
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=rax_required_together(),
    )

    if not HAS_PYRAX:
        module.fail_json(msg='pyrax is required for this module')

    state = module.params.get('state')
    label = module.params.get('label')
    cidr = module.params.get('cidr')

    setup_rax_module(module, pyrax)

    cloud_network(module, state, label, cidr)


# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.rax import *

### invoke the module
main()
