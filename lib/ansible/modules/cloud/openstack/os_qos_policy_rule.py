#!/usr/bin/python
# coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: os_qos_policy_rule
short_description: Manage a QoS Policy Rule in an OpenStack QoS Policy
extends_documentation_fragment: openstack
version_added: "2.10"
author: Daniel Speichert (@dasp)
description:
   - Manage a QoS Policy Rule in an OpenStack QoS Policy
options:
  state:
    description:
       - Indicate desired state of the resource
    choices: ['present', 'absent']
    default: present
    type: str
  policy_name:
    description:
      - Name or ID of the QoS policy in which the rule should be added/removed
    required: true
    type: str
  type:
    description:
      - The type of rule
    choices: ['bandwidth_limit', 'minimum_bandwidth', 'dscp_marking']
    type: str
  max_kbps:
    description:
      - The maximum KBPS (kilobits per second) value. If you specify this value, must
        be greater than 0 otherwise max_kbps will have no value.
      - Required when C(type) is bandwidth_limit
    default: 0
    type: int
  max_burst_kbps:
    description:
      - The maximum burst size (in kilobits).
      - Applies when C(type) is bandwidth_limit
    default: 0
    type: int
  min_kbps:
    description:
      - The minimum KBPS (kilobits per second) value which should be available for port.
      - Required when C(type) is minimum_limit
    type: int
  direction:
    description:
      - The direction of the traffic to which the QoS rule is applied, as
        seen from the point of view of the port. Valid values are egress and
        ingress. Default value is egress.
      - Applies when C(type) is bandwidth_limit or minimum_bandwidth
      - Not all versions of OpenStack Neutron support this parameter
      - Requires the qos-bw-limit-direction extension to Neutron
    choices: ['ingress', 'egress']
    type: str
  dscp_mark:
    description:
      - The DSCP mark value.
      - Required when C(type) is dscp_marking
    type: int
  project:
    description:
      - Project name or ID to look for QoS policy in (admin-only)
      - Mutually exclusive with C(project_id)
    type: str
  project_id:
    description:
      - Project ID to look for QoS policy in (admin-only)
      - Avoids project lookup call if ID is known
    type: str
notes:
  - Since OpenStack only allows one rule of each type, the updating of
    existing rule of given type is implicit if it exists.
requirements:
  - "python >= 2.7"
  - "openstacksdk"
'''

EXAMPLES = '''
# Create a new rule with DSCP marking
- os_qos_policy_rule:
    state: present
    policy_name: mark-cs1
    type: dscp_marking
    dscp_mark: 8

# Update the DSCP marking rule
- os_qos_policy_rule:
    state: present
    policy_name: mark-cs1
    type: dscp_marking
    dscp_mark: 16

# Delete the DSCP marking rule
- os_qos_policy_rule:
    state: absent
    policy_name: mark-cs1
    type: dscp_marking
'''

RETURN = '''
id:
    description: Policy Rule ID that was created or already exists
    returned: success
    type: str
    sample: 7cf120a1-f579-4e04-aa3e-ebd0cda0d988
qos_policy_rule:
    description: The policy rule representation object as returned by openstacksdk
    returned: success
    type: dict
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, \
    openstack_module_kwargs, openstack_cloud_from_module


def _needs_update(existing_rule, module):
    """Check for differences in the updatable values."""

    # now check for the things we are allowed to update
    max_kbps = module.params['max_kbps']
    max_burst_kbps = module.params['max_burst_kbps']
    min_kbps = module.params['min_kbps']
    direction = module.params['direction']
    dscp_mark = module.params['dscp_mark']

    if existing_rule['type'] != module.params['type']:
        raise AssertionError('Cannot update rule type')

    if existing_rule['type'] == 'dscp_marking':
        if dscp_mark != existing_rule['dscp_mark']:
            return True

    if existing_rule['type'] == 'minimum_bandwidth':
        if min_kbps != existing_rule['min_kbps']:
            return True
        if direction is not None and 'direction' in existing_rule:
            if direction != existing_rule['direction']:
                return True

    if existing_rule['type'] == 'bandwidth_limit':
        if max_kbps != existing_rule['max_kbps']:
            return True
        if max_burst_kbps is not None:
            if max_burst_kbps != existing_rule['max_burst_kbps']:
                return True
        if direction is not None and 'direction' in existing_rule:
            if direction != existing_rule['direction']:
                return True

    return False


def _system_state_change(module, existing_rule):
    state = module.params['state']
    if state == 'present':
        if not existing_rule:
            return True
        return _needs_update(existing_rule, module)
    if state == 'absent' and existing_rule:
        return True
    return False


def main():
    argument_spec = openstack_full_argument_spec(
        state=dict(type='str', default='present',
                   choices=['absent', 'present']),
        policy_name=dict(type='str', required=True),
        type=dict(type='str',
                  choices=[
                      'dscp_marking',
                      'bandwidth_limit',
                      'minimum_bandwidth'
                  ],
                  required=True),
        max_kbps=dict(type='int', required=False),
        max_burst_kbps=dict(type='int', default=0),
        min_kbps=dict(type='int', required=False),
        direction=dict(type='str', default=None,
                       choices=['ingress', 'egress'],
                       required=False),
        dscp_mark=dict(type='int', required=False),
        project=dict(type='str', required=False),
        project_id=dict(type='str', required=False),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec,
                           mutually_exclusive=[['project', 'project_id']],
                           supports_check_mode=True,
                           **module_kwargs)

    state = module.params['state']
    policy_name = module.params['policy_name']
    rule_type = module.params['type']
    max_kbps = module.params['max_kbps']
    max_burst_kbps = module.params['max_burst_kbps']
    min_kbps = module.params['min_kbps']
    direction = module.params['direction']
    dscp_mark = module.params['dscp_mark']
    project = module.params.pop('project')

    if state == 'present':
        if rule_type == 'dscp_marking':
            if not dscp_mark:
                module.fail_json(msg='dscp_mark required with dscp_marking type')

        elif rule_type == 'bandwidth_limit':
            if not max_kbps:
                module.fail_json(msg='max_kbps required with bandwidth_limit type')

        elif rule_type == 'minimum_bandwidth':
            if not min_kbps:
                module.fail_json(msg='min_kbps required with minimum_bandwidth type')

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        if project is not None:
            proj = cloud.get_project(project)
            if proj is None:
                module.fail_json(msg='Project %s could not be found' % project)
            filters = {'tenant_id': proj['id']}
        else:
            filters = None

        policy = cloud.get_qos_policy(policy_name, filters=filters)
        if not policy:
            # Short circuit for missing policy and absent rule
            if state == 'absent':
                module.exit_json(changed=False)
            module.fail_json(msg='No QoS policy found for %s' % policy_name)

        qos_policy_rule = None
        for rule in policy.rules:
            if rule['type'] == rule_type:
                qos_policy_rule = rule

        if module.check_mode:
            module.exit_json(changed=_system_state_change(module, qos_policy_rule))
        if state == 'present':
            if not qos_policy_rule:
                if rule_type == 'dscp_marking':
                    qos_policy_rule = cloud.create_qos_dscp_marking_rule(policy['id'],
                                                                         dscp_mark)
                elif rule_type == 'minimum_bandwidth':
                    kwargs = {}
                    if direction is not None:
                        kwargs['direction'] = direction
                    qos_policy_rule = cloud.create_qos_minimum_bandwidth_rule(policy['id'],
                                                                              min_kbps,
                                                                              **kwargs)
                elif rule_type == 'bandwidth_limit':
                    kwargs = {}
                    if max_burst_kbps is not None:
                        kwargs['max_burst_kbps'] = max_burst_kbps
                    if direction is not None:
                        kwargs['direction'] = direction
                    qos_policy_rule = cloud.create_qos_bandwidth_limit_rule(policy['id'],
                                                                            max_kbps,
                                                                            **kwargs)

                changed = True
            else:
                if _needs_update(qos_policy_rule, module):
                    if rule_type == 'dscp_marking':
                        qos_policy_rule = cloud.update_qos_dscp_marking_rule(policy['id'],
                                                                             qos_policy_rule['id'],
                                                                             dscp_mark)
                    elif rule_type == 'minimum_bandwidth':
                        kwargs = {}
                        if direction is not None:
                            kwargs['direction'] = direction
                        qos_policy_rule = cloud.update_qos_minimum_bandwidth_rule(policy['id'],
                                                                                  qos_policy_rule['id'],
                                                                                  min_kbps,
                                                                                  **kwargs)
                    elif rule_type == 'bandwidth_limit':
                        kwargs = {}
                        if max_burst_kbps is not None:
                            kwargs['max_burst_kbps'] = max_burst_kbps
                        if direction is not None:
                            kwargs['direction'] = direction
                        qos_policy_rule = cloud.update_qos_bandwidth_limit_rule(policy['id'],
                                                                                qos_policy_rule['id'],
                                                                                max_kbps,
                                                                                **kwargs)
                    changed = True
                else:
                    changed = False
            module.exit_json(changed=changed,
                             qos_policy_rule=qos_policy_rule,
                             id=qos_policy_rule['id'])

        elif state == 'absent':
            if not qos_policy_rule:
                changed = False
            else:
                changed = True
                if rule_type == 'dscp_marking':
                    cloud.delete_qos_dscp_marking_rule(policy['id'],
                                                       qos_policy_rule['id'])
                elif rule_type == 'minimum_bandwidth':
                    cloud.delete_qos_minimum_bandwidth_rule(policy['id'],
                                                            qos_policy_rule['id'])
                elif rule_type == 'bandwidth_limit':
                    cloud.delete_qos_bandwidth_limit_rule(policy['id'],
                                                          qos_policy_rule['id'])
            module.exit_json(changed=changed)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
