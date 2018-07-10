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

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.rax import rax_argument_spec, rax_required_together, setup_rax_module


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


if __name__ == '__main__':
    main()
