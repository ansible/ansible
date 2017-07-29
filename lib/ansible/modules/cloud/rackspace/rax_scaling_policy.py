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
module: rax_scaling_policy
short_description: Manipulate Rackspace Cloud Autoscale Scaling Policy
description:
    - Manipulate Rackspace Cloud Autoscale Scaling Policy
version_added: 1.7
options:
  at:
    description:
      - The UTC time when this policy will be executed. The time must be
        formatted according to C(yyyy-MM-dd'T'HH:mm:ss.SSS) such as
        C(2013-05-19T08:07:08Z)
  change:
    description:
      - The change, either as a number of servers or as a percentage, to make
        in the scaling group. If this is a percentage, you must set
        I(is_percent) to C(true) also.
  cron:
    description:
      - The time when the policy will be executed, as a cron entry. For
        example, if this is parameter is set to C(1 0 * * *)
  cooldown:
    description:
      - The period of time, in seconds, that must pass before any scaling can
        occur after the previous scaling. Must be an integer between 0 and
        86400 (24 hrs).
  desired_capacity:
    description:
      - The desired server capacity of the scaling the group; that is, how
        many servers should be in the scaling group.
  is_percent:
    description:
      - Whether the value in I(change) is a percent value
    default: false
  name:
    description:
      - Name to give the policy
    required: true
  policy_type:
    description:
      - The type of policy that will be executed for the current release.
    choices:
      - webhook
      - schedule
    required: true
  scaling_group:
    description:
      - Name of the scaling group that this policy will be added to
    required: true
  state:
    description:
      - Indicate desired state of the resource
    choices:
      - present
      - absent
    default: present
author: "Matt Martz (@sivel)"
extends_documentation_fragment: rackspace
'''

EXAMPLES = '''
---
- hosts: localhost
  gather_facts: false
  connection: local
  tasks:
    - rax_scaling_policy:
        credentials: ~/.raxpub
        region: ORD
        at: '2013-05-19T08:07:08Z'
        change: 25
        cooldown: 300
        is_percent: true
        name: ASG Test Policy - at
        policy_type: schedule
        scaling_group: ASG Test
      register: asps_at

    - rax_scaling_policy:
        credentials: ~/.raxpub
        region: ORD
        cron: '1 0 * * *'
        change: 25
        cooldown: 300
        is_percent: true
        name: ASG Test Policy - cron
        policy_type: schedule
        scaling_group: ASG Test
      register: asp_cron

    - rax_scaling_policy:
        credentials: ~/.raxpub
        region: ORD
        cooldown: 300
        desired_capacity: 5
        name: ASG Test Policy - webhook
        policy_type: webhook
        scaling_group: ASG Test
      register: asp_webhook
'''

try:
    import pyrax
    HAS_PYRAX = True
except ImportError:
    HAS_PYRAX = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.rax import (UUID, rax_argument_spec, rax_required_together, rax_to_dict,
                                      setup_rax_module)


def rax_asp(module, at=None, change=0, cron=None, cooldown=300,
            desired_capacity=0, is_percent=False, name=None,
            policy_type=None, scaling_group=None, state='present'):
    changed = False

    au = pyrax.autoscale
    if not au:
        module.fail_json(msg='Failed to instantiate client. This '
                             'typically indicates an invalid region or an '
                             'incorrectly capitalized region name.')

    try:
        UUID(scaling_group)
    except ValueError:
        try:
            sg = au.find(name=scaling_group)
        except Exception as e:
            module.fail_json(msg='%s' % e.message)
    else:
        try:
            sg = au.get(scaling_group)
        except Exception as e:
            module.fail_json(msg='%s' % e.message)

    if state == 'present':
        policies = filter(lambda p: name == p.name, sg.list_policies())
        if len(policies) > 1:
            module.fail_json(msg='No unique policy match found by name')
        if at:
            args = dict(at=at)
        elif cron:
            args = dict(cron=cron)
        else:
            args = None

        if not policies:
            try:
                policy = sg.add_policy(name, policy_type=policy_type,
                                       cooldown=cooldown, change=change,
                                       is_percent=is_percent,
                                       desired_capacity=desired_capacity,
                                       args=args)
                changed = True
            except Exception as e:
                module.fail_json(msg='%s' % e.message)

        else:
            policy = policies[0]
            kwargs = {}
            if policy_type != policy.type:
                kwargs['policy_type'] = policy_type

            if cooldown != policy.cooldown:
                kwargs['cooldown'] = cooldown

            if hasattr(policy, 'change') and change != policy.change:
                kwargs['change'] = change

            if hasattr(policy, 'changePercent') and is_percent is False:
                kwargs['change'] = change
                kwargs['is_percent'] = False
            elif hasattr(policy, 'change') and is_percent is True:
                kwargs['change'] = change
                kwargs['is_percent'] = True

            if hasattr(policy, 'desiredCapacity') and change:
                kwargs['change'] = change
            elif ((hasattr(policy, 'change') or
                    hasattr(policy, 'changePercent')) and desired_capacity):
                kwargs['desired_capacity'] = desired_capacity

            if hasattr(policy, 'args') and args != policy.args:
                kwargs['args'] = args

            if kwargs:
                policy.update(**kwargs)
                changed = True

        policy.get()

        module.exit_json(changed=changed, autoscale_policy=rax_to_dict(policy))

    else:
        try:
            policies = filter(lambda p: name == p.name, sg.list_policies())
            if len(policies) > 1:
                module.fail_json(msg='No unique policy match found by name')
            elif not policies:
                policy = {}
            else:
                policy.delete()
                changed = True
        except Exception as e:
            module.fail_json(msg='%s' % e.message)

        module.exit_json(changed=changed, autoscale_policy=rax_to_dict(policy))


def main():
    argument_spec = rax_argument_spec()
    argument_spec.update(
        dict(
            at=dict(),
            change=dict(type='int'),
            cron=dict(),
            cooldown=dict(type='int', default=300),
            desired_capacity=dict(type='int'),
            is_percent=dict(type='bool', default=False),
            name=dict(required=True),
            policy_type=dict(required=True, choices=['webhook', 'schedule']),
            scaling_group=dict(required=True),
            state=dict(default='present', choices=['present', 'absent']),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=rax_required_together(),
        mutually_exclusive=[
            ['cron', 'at'],
            ['change', 'desired_capacity'],
        ]
    )

    if not HAS_PYRAX:
        module.fail_json(msg='pyrax is required for this module')

    at = module.params.get('at')
    change = module.params.get('change')
    cron = module.params.get('cron')
    cooldown = module.params.get('cooldown')
    desired_capacity = module.params.get('desired_capacity')
    is_percent = module.params.get('is_percent')
    name = module.params.get('name')
    policy_type = module.params.get('policy_type')
    scaling_group = module.params.get('scaling_group')
    state = module.params.get('state')

    if (at or cron) and policy_type == 'webhook':
        module.fail_json(msg='policy_type=schedule is required for a time '
                             'based policy')

    setup_rax_module(module, pyrax)

    rax_asp(module, at=at, change=change, cron=cron, cooldown=cooldown,
            desired_capacity=desired_capacity, is_percent=is_percent,
            name=name, policy_type=policy_type, scaling_group=scaling_group,
            state=state)


if __name__ == '__main__':
    main()
