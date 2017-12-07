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
module: rax_mon_check
short_description: Create or delete a Rackspace Cloud Monitoring check for an
                   existing entity.
description:
- Create or delete a Rackspace Cloud Monitoring check associated with an
  existing rax_mon_entity. A check is a specific test or measurement that is
  performed, possibly from different monitoring zones, on the systems you
  monitor. Rackspace monitoring module flow | rax_mon_entity ->
  *rax_mon_check* -> rax_mon_notification -> rax_mon_notification_plan ->
  rax_mon_alarm
version_added: "2.0"
options:
  state:
    description:
    - Ensure that a check with this C(label) exists or does not exist.
    choices: ["present", "absent"]
  entity_id:
    description:
    - ID of the rax_mon_entity to target with this check.
    required: true
  label:
    description:
    - Defines a label for this check, between 1 and 64 characters long.
    required: true
  check_type:
    description:
    - The type of check to create. C(remote.) checks may be created on any
      rax_mon_entity. C(agent.) checks may only be created on rax_mon_entities
      that have a non-null C(agent_id).
    choices:
    - remote.dns
    - remote.ftp-banner
    - remote.http
    - remote.imap-banner
    - remote.mssql-banner
    - remote.mysql-banner
    - remote.ping
    - remote.pop3-banner
    - remote.postgresql-banner
    - remote.smtp-banner
    - remote.smtp
    - remote.ssh
    - remote.tcp
    - remote.telnet-banner
    - agent.filesystem
    - agent.memory
    - agent.load_average
    - agent.cpu
    - agent.disk
    - agent.network
    - agent.plugin
    required: true
  monitoring_zones_poll:
    description:
    - Comma-separated list of the names of the monitoring zones the check should
      run from. Available monitoring zones include mzdfw, mzhkg, mziad, mzlon,
      mzord and mzsyd. Required for remote.* checks; prohibited for agent.* checks.
  target_hostname:
    description:
    - One of `target_hostname` and `target_alias` is required for remote.* checks,
      but prohibited for agent.* checks. The hostname this check should target.
      Must be a valid IPv4, IPv6, or FQDN.
  target_alias:
    description:
    - One of `target_alias` and `target_hostname` is required for remote.* checks,
      but prohibited for agent.* checks. Use the corresponding key in the entity's
      `ip_addresses` hash to resolve an IP address to target.
  details:
    description:
    - Additional details specific to the check type. Must be a hash of strings
      between 1 and 255 characters long, or an array or object containing 0 to
      256 items.
  disabled:
    description:
    - If "yes", ensure the check is created, but don't actually use it yet.
    choices: [ "yes", "no" ]
  metadata:
    description:
    - Hash of arbitrary key-value pairs to accompany this check if it fires.
      Keys and values must be strings between 1 and 255 characters long.
  period:
    description:
    - The number of seconds between each time the check is performed. Must be
      greater than the minimum period set on your account.
  timeout:
    description:
    - The number of seconds this check will wait when attempting to collect
      results. Must be less than the period.
author: Ash Wilson
extends_documentation_fragment: rackspace.openstack
'''

EXAMPLES = '''
- name: Create a monitoring check
  gather_facts: False
  hosts: local
  connection: local
  tasks:
  - name: Associate a check with an existing entity.
    rax_mon_check:
      credentials: ~/.rax_pub
      state: present
      entity_id: "{{ the_entity['entity']['id'] }}"
      label: the_check
      check_type: remote.ping
      monitoring_zones_poll: mziad,mzord,mzdfw
      details:
        count: 10
      meta:
        hurf: durf
    register: the_check
'''

try:
    import pyrax
    HAS_PYRAX = True
except ImportError:
    HAS_PYRAX = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.rax import rax_argument_spec, rax_required_together, setup_rax_module


def cloud_check(module, state, entity_id, label, check_type,
                monitoring_zones_poll, target_hostname, target_alias, details,
                disabled, metadata, period, timeout):

    # Coerce attributes.

    if monitoring_zones_poll and not isinstance(monitoring_zones_poll, list):
        monitoring_zones_poll = [monitoring_zones_poll]

    if period:
        period = int(period)

    if timeout:
        timeout = int(timeout)

    changed = False
    check = None

    cm = pyrax.cloud_monitoring
    if not cm:
        module.fail_json(msg='Failed to instantiate client. This typically '
                             'indicates an invalid region or an incorrectly '
                             'capitalized region name.')

    entity = cm.get_entity(entity_id)
    if not entity:
        module.fail_json(msg='Failed to instantiate entity. "%s" may not be'
                             ' a valid entity id.' % entity_id)

    existing = [e for e in entity.list_checks() if e.label == label]

    if existing:
        check = existing[0]

    if state == 'present':
        if len(existing) > 1:
            module.fail_json(msg='%s existing checks have a label of %s.' %
                                 (len(existing), label))

        should_delete = False
        should_create = False
        should_update = False

        if check:
            # Details may include keys set to default values that are not
            # included in the initial creation.
            #
            # Only force a recreation of the check if one of the *specified*
            # keys is missing or has a different value.
            if details:
                for (key, value) in details.items():
                    if key not in check.details:
                        should_delete = should_create = True
                    elif value != check.details[key]:
                        should_delete = should_create = True

            should_update = label != check.label or \
                (target_hostname and target_hostname != check.target_hostname) or \
                (target_alias and target_alias != check.target_alias) or \
                (disabled != check.disabled) or \
                (metadata and metadata != check.metadata) or \
                (period and period != check.period) or \
                (timeout and timeout != check.timeout) or \
                (monitoring_zones_poll and monitoring_zones_poll != check.monitoring_zones_poll)

            if should_update and not should_delete:
                check.update(label=label,
                             disabled=disabled,
                             metadata=metadata,
                             monitoring_zones_poll=monitoring_zones_poll,
                             timeout=timeout,
                             period=period,
                             target_alias=target_alias,
                             target_hostname=target_hostname)
                changed = True
        else:
            # The check doesn't exist yet.
            should_create = True

        if should_delete:
            check.delete()

        if should_create:
            check = cm.create_check(entity,
                                    label=label,
                                    check_type=check_type,
                                    target_hostname=target_hostname,
                                    target_alias=target_alias,
                                    monitoring_zones_poll=monitoring_zones_poll,
                                    details=details,
                                    disabled=disabled,
                                    metadata=metadata,
                                    period=period,
                                    timeout=timeout)
            changed = True
    elif state == 'absent':
        if check:
            check.delete()
            changed = True
    else:
        module.fail_json(msg='state must be either present or absent.')

    if check:
        check_dict = {
            "id": check.id,
            "label": check.label,
            "type": check.type,
            "target_hostname": check.target_hostname,
            "target_alias": check.target_alias,
            "monitoring_zones_poll": check.monitoring_zones_poll,
            "details": check.details,
            "disabled": check.disabled,
            "metadata": check.metadata,
            "period": check.period,
            "timeout": check.timeout
        }
        module.exit_json(changed=changed, check=check_dict)
    else:
        module.exit_json(changed=changed)


def main():
    argument_spec = rax_argument_spec()
    argument_spec.update(
        dict(
            entity_id=dict(required=True),
            label=dict(required=True),
            check_type=dict(required=True),
            monitoring_zones_poll=dict(),
            target_hostname=dict(),
            target_alias=dict(),
            details=dict(type='dict', default={}),
            disabled=dict(type='bool', default=False),
            metadata=dict(type='dict', default={}),
            period=dict(type='int'),
            timeout=dict(type='int'),
            state=dict(default='present', choices=['present', 'absent'])
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=rax_required_together()
    )

    if not HAS_PYRAX:
        module.fail_json(msg='pyrax is required for this module')

    entity_id = module.params.get('entity_id')
    label = module.params.get('label')
    check_type = module.params.get('check_type')
    monitoring_zones_poll = module.params.get('monitoring_zones_poll')
    target_hostname = module.params.get('target_hostname')
    target_alias = module.params.get('target_alias')
    details = module.params.get('details')
    disabled = module.boolean(module.params.get('disabled'))
    metadata = module.params.get('metadata')
    period = module.params.get('period')
    timeout = module.params.get('timeout')

    state = module.params.get('state')

    setup_rax_module(module, pyrax)

    cloud_check(module, state, entity_id, label, check_type,
                monitoring_zones_poll, target_hostname, target_alias, details,
                disabled, metadata, period, timeout)


if __name__ == '__main__':
    main()
