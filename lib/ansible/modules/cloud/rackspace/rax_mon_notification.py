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
module: rax_mon_notification
short_description: Create or delete a Rackspace Cloud Monitoring notification.
description:
- Create or delete a Rackspace Cloud Monitoring notification that specifies a
  channel that can be used to communicate alarms, such as email, webhooks, or
  PagerDuty. Rackspace monitoring module flow | rax_mon_entity -> rax_mon_check ->
  *rax_mon_notification* -> rax_mon_notification_plan -> rax_mon_alarm
version_added: "2.0"
options:
  state:
    description:
    - Ensure that the notification with this C(label) exists or does not exist.
    choices: ['present', 'absent']
  label:
    description:
    - Defines a friendly name for this notification. String between 1 and 255
      characters long.
    required: true
  notification_type:
    description:
    - A supported notification type.
    choices: ["webhook", "email", "pagerduty"]
    required: true
  details:
    description:
    - Dictionary of key-value pairs used to initialize the notification.
      Required keys and meanings vary with notification type. See
      http://docs.rackspace.com/cm/api/v1.0/cm-devguide/content/
      service-notification-types-crud.html for details.
    required: true
author: Ash Wilson
extends_documentation_fragment: rackspace.openstack
'''

EXAMPLES = '''
- name: Monitoring notification example
  gather_facts: False
  hosts: local
  connection: local
  tasks:
  - name: Email me when something goes wrong.
    rax_mon_entity:
      credentials: ~/.rax_pub
      label: omg
      type: email
      details:
        address: me@mailhost.com
    register: the_notification
'''

try:
    import pyrax
    HAS_PYRAX = True
except ImportError:
    HAS_PYRAX = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.rax import rax_argument_spec, rax_required_together, setup_rax_module


def notification(module, state, label, notification_type, details):

    if len(label) < 1 or len(label) > 255:
        module.fail_json(msg='label must be between 1 and 255 characters long')

    changed = False
    notification = None

    cm = pyrax.cloud_monitoring
    if not cm:
        module.fail_json(msg='Failed to instantiate client. This typically '
                             'indicates an invalid region or an incorrectly '
                             'capitalized region name.')

    existing = []
    for n in cm.list_notifications():
        if n.label == label:
            existing.append(n)

    if existing:
        notification = existing[0]

    if state == 'present':
        should_update = False
        should_delete = False
        should_create = False

        if len(existing) > 1:
            module.fail_json(msg='%s existing notifications are labelled %s.' %
                                 (len(existing), label))

        if notification:
            should_delete = (notification_type != notification.type)

            should_update = (details != notification.details)

            if should_update and not should_delete:
                notification.update(details=notification.details)
                changed = True

            if should_delete:
                notification.delete()
        else:
            should_create = True

        if should_create:
            notification = cm.create_notification(notification_type,
                                                  label=label, details=details)
            changed = True
    else:
        for n in existing:
            n.delete()
            changed = True

    if notification:
        notification_dict = {
            "id": notification.id,
            "type": notification.type,
            "label": notification.label,
            "details": notification.details
        }
        module.exit_json(changed=changed, notification=notification_dict)
    else:
        module.exit_json(changed=changed)

def main():
    argument_spec = rax_argument_spec()
    argument_spec.update(
        dict(
            state=dict(default='present', choices=['present', 'absent']),
            label=dict(required=True),
            notification_type=dict(required=True, choices=['webhook', 'email', 'pagerduty']),
            details=dict(required=True, type='dict')
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
    notification_type = module.params.get('notification_type')
    details = module.params.get('details')

    setup_rax_module(module, pyrax)

    notification(module, state, label, notification_type, details)


if __name__ == '__main__':
    main()
