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
ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: rax_mon_notification_plan
short_description: Create or delete a Rackspace Cloud Monitoring notification
                   plan.
description:
- Create or delete a Rackspace Cloud Monitoring notification plan by
  associating existing rax_mon_notifications with severity levels. Rackspace
  monitoring module flow | rax_mon_entity -> rax_mon_check ->
  rax_mon_notification -> *rax_mon_notification_plan* -> rax_mon_alarm
version_added: "2.0"
options:
  state:
    description:
    - Ensure that the notification plan with this C(label) exists or does not
      exist.
    choices: ['present', 'absent']
  label:
    description:
    - Defines a friendly name for this notification plan. String between 1 and
      255 characters long.
    required: true
  critical_state:
    description:
    - Notification list to use when the alarm state is CRITICAL. Must be an
      array of valid rax_mon_notification ids.
  warning_state:
    description:
    - Notification list to use when the alarm state is WARNING. Must be an array
      of valid rax_mon_notification ids.
  ok_state:
    description:
    - Notification list to use when the alarm state is OK. Must be an array of
      valid rax_mon_notification ids.
author: Ash Wilson
extends_documentation_fragment: rackspace.openstack
'''

EXAMPLES = '''
- name: Example notification plan
  gather_facts: False
  hosts: local
  connection: local
  tasks:
  - name: Establish who gets called when.
    rax_mon_notification_plan:
      credentials: ~/.rax_pub
      state: present
      label: defcon1
      critical_state:
      - "{{ everyone['notification']['id'] }}"
      warning_state:
      - "{{ opsfloor['notification']['id'] }}"
    register: defcon1
'''

try:
    import pyrax
    HAS_PYRAX = True
except ImportError:
    HAS_PYRAX = False

def notification_plan(module, state, label, critical_state, warning_state, ok_state):

    if len(label) < 1 or len(label) > 255:
        module.fail_json(msg='label must be between 1 and 255 characters long')

    changed = False
    notification_plan = None

    cm = pyrax.cloud_monitoring
    if not cm:
        module.fail_json(msg='Failed to instantiate client. This typically '
                             'indicates an invalid region or an incorrectly '
                             'capitalized region name.')

    existing = []
    for n in cm.list_notification_plans():
        if n.label == label:
            existing.append(n)

    if existing:
        notification_plan = existing[0]

    if state == 'present':
        should_create = False
        should_delete = False

        if len(existing) > 1:
            module.fail_json(msg='%s notification plans are labelled %s.' %
                                 (len(existing), label))

        if notification_plan:
            should_delete = (critical_state and critical_state != notification_plan.critical_state) or \
                (warning_state and warning_state != notification_plan.warning_state) or \
                (ok_state and ok_state != notification_plan.ok_state)

            if should_delete:
                notification_plan.delete()
                should_create = True
        else:
            should_create = True

        if should_create:
            notification_plan = cm.create_notification_plan(label=label,
                                                            critical_state=critical_state,
                                                            warning_state=warning_state,
                                                            ok_state=ok_state)
            changed = True
    else:
        for np in existing:
            np.delete()
            changed = True

    if notification_plan:
        notification_plan_dict = {
            "id": notification_plan.id,
            "critical_state": notification_plan.critical_state,
            "warning_state": notification_plan.warning_state,
            "ok_state": notification_plan.ok_state,
            "metadata": notification_plan.metadata
        }
        module.exit_json(changed=changed, notification_plan=notification_plan_dict)
    else:
        module.exit_json(changed=changed)

def main():
    argument_spec = rax_argument_spec()
    argument_spec.update(
        dict(
            state=dict(default='present', choices=['present', 'absent']),
            label=dict(required=True),
            critical_state=dict(type='list'),
            warning_state=dict(type='list'),
            ok_state=dict(type='list')
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
    critical_state = module.params.get('critical_state')
    warning_state = module.params.get('warning_state')
    ok_state = module.params.get('ok_state')

    setup_rax_module(module, pyrax)

    notification_plan(module, state, label, critical_state, warning_state, ok_state)

# Import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.rax import *

# Invoke the module.
if __name__ == '__main__':
    main()
