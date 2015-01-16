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
author: Matt Martz
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

try:
    import pyrax
    HAS_PYRAX = True
except ImportError:
    HAS_PYRAX = False


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
            except Exception, e:
                module.fail_json(msg='Failed to load %s' % public_key)

        try:
            keypair = cs.keypairs.find(name=name)
        except cs.exceptions.NotFound:
            try:
                keypair = cs.keypairs.create(name, public_key)
                changed = True
            except Exception, e:
                module.fail_json(msg='%s' % e.message)
        except Exception, e:
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
            except Exception, e:
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


# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.rax import *

### invoke the module
main()
