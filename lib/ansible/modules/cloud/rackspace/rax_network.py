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
  cidr:
    description:
     - cidr of the network being created
author:
    - "Christopher H. Laco (@claco)"
    - "Jesse Keating (@omgjlk)"
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

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.rax import rax_argument_spec, rax_required_together, setup_rax_module


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
            except Exception as e:
                module.fail_json(msg='%s' % e.message)
        except Exception as e:
            module.fail_json(msg='%s' % e.message)

    elif state == 'absent':
        try:
            network = pyrax.cloud_networks.find_network_by_label(label)
            network.delete()
            changed = True
        except pyrax.exceptions.NetworkNotFound:
            pass
        except Exception as e:
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


if __name__ == '__main__':
    main()
