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
module: rax_identity
short_description: Load Rackspace Cloud Identity
description:
     - Verifies Rackspace Cloud credentials and returns identity information
version_added: "1.5"
options:
  state:
    description:
      - Indicate desired state of the resource
    choices: ['present', 'absent']
    default: present
author: Christopher H. Laco, Matt Martz
extends_documentation_fragment: rackspace.openstack
'''

EXAMPLES = '''
- name: Load Rackspace Cloud Identity
  gather_facts: False
  hosts: local
  connection: local
  tasks:
    - name: Load Identity
      local_action:
        module: rax_identity
        credentials: ~/.raxpub
        region: DFW
      register: rackspace_identity
'''

try:
    import pyrax
    HAS_PYRAX = True
except ImportError:
    HAS_PYRAX = False


def cloud_identity(module, state, identity):
    instance = dict(
        authenticated=identity.authenticated,
        credentials=identity._creds_file
    )
    changed = False

    instance.update(rax_to_dict(identity))
    instance['services'] = instance.get('services', {}).keys()

    if state == 'present':
        if not identity.authenticated:
            module.fail_json(msg='Credentials could not be verified!')

    module.exit_json(changed=changed, identity=instance)


def main():
    argument_spec = rax_argument_spec()
    argument_spec.update(
        dict(
            state=dict(default='present', choices=['present'])
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=rax_required_together()
    )

    if not HAS_PYRAX:
        module.fail_json(msg='pyrax is required for this module')

    state = module.params.get('state')

    setup_rax_module(module, pyrax)

    if not pyrax.identity:
        module.fail_json(msg='Failed to instantiate client. This '
                             'typically indicates an invalid region or an '
                             'incorrectly capitalized region name.')

    cloud_identity(module, state, pyrax.identity)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.rax import *

# invoke the module
main()
