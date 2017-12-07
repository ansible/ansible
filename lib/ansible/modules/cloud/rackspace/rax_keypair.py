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
module: rax_keypair
short_description: Create a keypair for use with Rackspace Cloud Servers
description:
     - Create a keypair for use with Rackspace Cloud Servers
version_added: 1.5
options:
  name:
    description:
      - Name of keypair
    required: true
  public_key:
    description:
      - Public Key string to upload. Can be a file path or string
    default: null
  state:
    description:
      - Indicate desired state of the resource
    choices:
      - present
      - absent
    default: present
author: "Matt Martz (@sivel)"
notes:
  - Keypairs cannot be manipulated, only created and deleted. To "update" a
    keypair you must first delete and then recreate.
  - The ability to specify a file path for the public key was added in 1.7
extends_documentation_fragment: rackspace.openstack
'''

EXAMPLES = '''
- name: Create a keypair
  hosts: localhost
  gather_facts: False
  tasks:
    - name: keypair request
      local_action:
        module: rax_keypair
        credentials: ~/.raxpub
        name: my_keypair
        region: DFW
      register: keypair
    - name: Create local public key
      local_action:
        module: copy
        content: "{{ keypair.keypair.public_key }}"
        dest: "{{ inventory_dir }}/{{ keypair.keypair.name }}.pub"
    - name: Create local private key
      local_action:
        module: copy
        content: "{{ keypair.keypair.private_key }}"
        dest: "{{ inventory_dir }}/{{ keypair.keypair.name }}"

- name: Create a keypair
  hosts: localhost
  gather_facts: False
  tasks:
    - name: keypair request
      local_action:
        module: rax_keypair
        credentials: ~/.raxpub
        name: my_keypair
        public_key: "{{ lookup('file', 'authorized_keys/id_rsa.pub') }}"
        region: DFW
      register: keypair
'''
import os

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


def rax_keypair(module, name, public_key, state):
    changed = False

    cs = pyrax.cloudservers

    if cs is None:
        module.fail_json(msg='Failed to instantiate client. This '
                             'typically indicates an invalid region or an '
                             'incorrectly capitalized region name.')

    keypair = {}

    if state == 'present':
        if public_key and os.path.isfile(public_key):
            try:
                f = open(public_key)
                public_key = f.read()
                f.close()
            except Exception as e:
                module.fail_json(msg='Failed to load %s' % public_key)

        try:
            keypair = cs.keypairs.find(name=name)
        except cs.exceptions.NotFound:
            try:
                keypair = cs.keypairs.create(name, public_key)
                changed = True
            except Exception as e:
                module.fail_json(msg='%s' % e.message)
        except Exception as e:
            module.fail_json(msg='%s' % e.message)

    elif state == 'absent':
        try:
            keypair = cs.keypairs.find(name=name)
        except:
            pass

        if keypair:
            try:
                keypair.delete()
                changed = True
            except Exception as e:
                module.fail_json(msg='%s' % e.message)

    module.exit_json(changed=changed, keypair=rax_to_dict(keypair))


def main():
    argument_spec = rax_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True),
            public_key=dict(),
            state=dict(default='present', choices=['absent', 'present']),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=rax_required_together(),
    )

    if not HAS_PYRAX:
        module.fail_json(msg='pyrax is required for this module')

    name = module.params.get('name')
    public_key = module.params.get('public_key')
    state = module.params.get('state')

    setup_rax_module(module, pyrax)

    rax_keypair(module, name, public_key, state)


if __name__ == '__main__':
    main()
