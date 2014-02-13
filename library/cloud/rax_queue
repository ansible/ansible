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
module: rax_queue
short_description: create / delete a queue in Rackspace Public Cloud
description:
     - creates / deletes a Rackspace Public Cloud queue.
version_added: "1.5"
options:
  name:
    description:
      - Name to give the queue
    default: null
  state:
    description:
      - Indicate desired state of the resource
    choices:
      - present
      - absent
    default: present
author: Christopher H. Laco, Matt Martz
extends_documentation_fragment: rackspace
'''

EXAMPLES = '''
- name: Build a Queue
  gather_facts: False
  hosts: local
  connection: local
  tasks:
    - name: Queue create request
      local_action:
        module: rax_queue
        credentials: ~/.raxpub
        name: my-queue
        region: DFW
        state: present
      register: my_queue
'''

try:
    import pyrax
    HAS_PYRAX = True
except ImportError:
    HAS_PYRAX = False


def cloud_queue(module, state, name):
    for arg in (state, name):
        if not arg:
            module.fail_json(msg='%s is required for rax_queue' % arg)

    changed = False
    queues = []
    instance = {}

    cq = pyrax.queues
    if not cq:
        module.fail_json(msg='Failed to instantiate client. This '
                             'typically indicates an invalid region or an '
                             'incorrectly capitalized region name.')

    for queue in cq.list():
        if name != queue.name:
            continue

        queues.append(queue)

    if len(queues) > 1:
        module.fail_json(msg='Multiple Queues were matched by name')

    if state == 'present':
        if not queues:
            try:
                queue = cq.create(name)
                changed = True
            except Exception, e:
                module.fail_json(msg='%s' % e.message)
        else:
            queue = queues[0]

        instance = dict(name=queue.name)
        result = dict(changed=changed, queue=instance)
        module.exit_json(**result)

    elif state == 'absent':
        if queues:
            queue = queues[0]
            try:
                queue.delete()
                changed = True
            except Exception, e:
                module.fail_json(msg='%s' % e.message)

    module.exit_json(changed=changed, queue=instance)


def main():
    argument_spec = rax_argument_spec()
    argument_spec.update(
        dict(
            name=dict(),
            state=dict(default='present', choices=['present', 'absent']),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=rax_required_together()
    )

    if not HAS_PYRAX:
        module.fail_json(msg='pyrax is required for this module')

    name = module.params.get('name')
    state = module.params.get('state')

    setup_rax_module(module, pyrax)

    cloud_queue(module, state, name)


# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.rax import *

### invoke the module
main()
