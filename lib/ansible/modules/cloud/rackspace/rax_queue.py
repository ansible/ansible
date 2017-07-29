#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


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
author:
    - "Christopher H. Laco (@claco)"
    - "Matt Martz (@sivel)"
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

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.rax import rax_argument_spec, rax_required_together, setup_rax_module


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
            except Exception as e:
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
            except Exception as e:
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


if __name__ == '__main__':
    main()
