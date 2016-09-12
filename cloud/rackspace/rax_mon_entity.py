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
module: rax_mon_entity
short_description: Create or delete a Rackspace Cloud Monitoring entity
description:
- Create or delete a Rackspace Cloud Monitoring entity, which represents a device
  to monitor. Entities associate checks and alarms with a target system and
  provide a convenient, centralized place to store IP addresses. Rackspace
  monitoring module flow | *rax_mon_entity* -> rax_mon_check ->
  rax_mon_notification -> rax_mon_notification_plan -> rax_mon_alarm
version_added: "2.0"
options:
  label:
    description:
    - Defines a name for this entity. Must be a non-empty string between 1 and
      255 characters long.
    required: true
  state:
    description:
    - Ensure that an entity with this C(name) exists or does not exist.
    choices: ["present", "absent"]
  agent_id:
    description:
    - Rackspace monitoring agent on the target device to which this entity is
      bound. Necessary to collect C(agent.) rax_mon_checks against this entity.
  named_ip_addresses:
    description:
    - Hash of IP addresses that may be referenced by name by rax_mon_checks
      added to this entity. Must be a dictionary of with keys that are names
      between 1 and 64 characters long, and values that are valid IPv4 or IPv6
      addresses.
  metadata:
    description:
    - Hash of arbitrary C(name), C(value) pairs that are passed to associated
      rax_mon_alarms. Names and values must all be between 1 and 255 characters
      long.
author: Ash Wilson
extends_documentation_fragment: rackspace.openstack
'''

EXAMPLES = '''
- name: Entity example
  gather_facts: False
  hosts: local
  connection: local
  tasks:
  - name: Ensure an entity exists
    rax_mon_entity:
      credentials: ~/.rax_pub
      state: present
      label: my_entity
      named_ip_addresses:
        web_box: 192.0.2.4
        db_box: 192.0.2.5
      meta:
        hurf: durf
    register: the_entity
'''

try:
    import pyrax
    HAS_PYRAX = True
except ImportError:
    HAS_PYRAX = False

def cloud_monitoring(module, state, label, agent_id, named_ip_addresses,
                     metadata):

    if len(label) < 1 or len(label) > 255:
        module.fail_json(msg='label must be between 1 and 255 characters long')

    changed = False

    cm = pyrax.cloud_monitoring
    if not cm:
        module.fail_json(msg='Failed to instantiate client. This typically '
                             'indicates an invalid region or an incorrectly '
                             'capitalized region name.')

    existing = []
    for entity in cm.list_entities():
        if label == entity.label:
            existing.append(entity)

    entity = None

    if existing:
        entity = existing[0]

    if state == 'present':
        should_update = False
        should_delete = False
        should_create = False

        if len(existing) > 1:
            module.fail_json(msg='%s existing entities have the label %s.' %
                                 (len(existing), label))

        if entity:
            if named_ip_addresses and named_ip_addresses != entity.ip_addresses:
                should_delete = should_create = True

            # Change an existing Entity, unless there's nothing to do.
            should_update = agent_id and agent_id != entity.agent_id or \
                (metadata and metadata != entity.metadata)

            if should_update and not should_delete:
                entity.update(agent_id, metadata)
                changed = True

            if should_delete:
                entity.delete()
        else:
            should_create = True

        if should_create:
            # Create a new Entity.
            entity = cm.create_entity(label=label, agent=agent_id,
                                      ip_addresses=named_ip_addresses,
                                      metadata=metadata)
            changed = True
    else:
        # Delete the existing Entities.
        for e in existing:
            e.delete()
            changed = True

    if entity:
        entity_dict = {
            "id": entity.id,
            "name": entity.name,
            "agent_id": entity.agent_id,
        }
        module.exit_json(changed=changed, entity=entity_dict)
    else:
        module.exit_json(changed=changed)

def main():
    argument_spec = rax_argument_spec()
    argument_spec.update(
        dict(
            state=dict(default='present', choices=['present', 'absent']),
            label=dict(required=True),
            agent_id=dict(),
            named_ip_addresses=dict(type='dict', default={}),
            metadata=dict(type='dict', default={})
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=rax_required_together()
    )

    if not HAS_PYRAX:
        module.fail_json(msg='pyrax is required for this module')

    state = module.params.get('state')

    label = module.params.get('label')
    agent_id = module.params.get('agent_id')
    named_ip_addresses = module.params.get('named_ip_addresses')
    metadata = module.params.get('metadata')

    setup_rax_module(module, pyrax)

    cloud_monitoring(module, state, label, agent_id, named_ip_addresses, metadata)

# Import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.rax import *

# Invoke the module.
main()
