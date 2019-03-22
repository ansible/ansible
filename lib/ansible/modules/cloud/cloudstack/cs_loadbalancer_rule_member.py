#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2015, Darren Worrall <darren@iweb.co.uk>
# Copyright (c) 2015, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_loadbalancer_rule_member
short_description: Manages load balancer rule members on Apache CloudStack based clouds.
description:
    - Add and remove load balancer rule members.
version_added: '2.0'
author:
    - Darren Worrall (@dazworrall)
    - René Moser (@resmo)
options:
  name:
    description:
      - The name of the load balancer rule.
    type: str
    required: true
  ip_address:
    description:
      - Public IP address from where the network traffic will be load balanced from.
      - Only needed to find the rule if I(name) is not unique.
    type: str
    aliases: [ public_ip ]
  vms:
    description:
      - List of VMs to assign to or remove from the rule.
    type: list
    required: true
    aliases: [ vm ]
  state:
    description:
      - Should the VMs be present or absent from the rule.
    type: str
    default: present
    choices: [ present, absent ]
  project:
    description:
      - Name of the project the firewall rule is related to.
    type: str
  domain:
    description:
      - Domain the rule is related to.
    type: str
  account:
    description:
      - Account the rule is related to.
    type: str
  zone:
    description:
      - Name of the zone in which the rule should be located.
      - If not set, default zone is used.
    type: str
  poll_async:
    description:
      - Poll async jobs until job has finished.
    type: bool
    default: yes
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: Add VMs to an existing load balancer
  cs_loadbalancer_rule_member:
    name: balance_http
    vms:
      - web01
      - web02
  delegate_to: localhost

- name: Remove a VM from an existing load balancer
  cs_loadbalancer_rule_member:
    name: balance_http
    vms:
      - web01
      - web02
    state: absent
  delegate_to: localhost

# Rolling upgrade of hosts
- hosts: webservers
  serial: 1
  pre_tasks:
    - name: Remove from load balancer
      cs_loadbalancer_rule_member:
        name: balance_http
        vm: "{{ ansible_hostname }}"
        state: absent
      delegate_to: localhost
  tasks:
    # Perform update
  post_tasks:
    - name: Add to load balancer
      cs_loadbalancer_rule_member:
        name: balance_http
        vm: "{{ ansible_hostname }}"
        state: present
      delegate_to: localhost
'''

RETURN = '''
---
id:
  description: UUID of the rule.
  returned: success
  type: str
  sample: a6f7a5fc-43f8-11e5-a151-feff819cdc9f
zone:
  description: Name of zone the rule is related to.
  returned: success
  type: str
  sample: ch-gva-2
project:
  description: Name of project the rule is related to.
  returned: success
  type: str
  sample: Production
account:
  description: Account the rule is related to.
  returned: success
  type: str
  sample: example account
domain:
  description: Domain the rule is related to.
  returned: success
  type: str
  sample: example domain
algorithm:
  description: Load balancer algorithm used.
  returned: success
  type: str
  sample: source
cidr:
  description: CIDR to forward traffic from.
  returned: success
  type: str
  sample: 0.0.0.0/0
name:
  description: Name of the rule.
  returned: success
  type: str
  sample: http-lb
description:
  description: Description of the rule.
  returned: success
  type: str
  sample: http load balancer rule
protocol:
  description: Protocol of the rule.
  returned: success
  type: str
  sample: tcp
public_port:
  description: Public port.
  returned: success
  type: int
  sample: 80
private_port:
  description: Private IP address.
  returned: success
  type: int
  sample: 80
public_ip:
  description: Public IP address.
  returned: success
  type: str
  sample: 1.2.3.4
vms:
  description: Rule members.
  returned: success
  type: list
  sample: '[ "web01", "web02" ]'
tags:
  description: List of resource tags associated with the rule.
  returned: success
  type: list
  sample: '[ { "key": "foo", "value": "bar" } ]'
state:
  description: State of the rule.
  returned: success
  type: str
  sample: Add
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together,
)


class AnsibleCloudStackLBRuleMember(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackLBRuleMember, self).__init__(module)
        self.returns = {
            'publicip': 'public_ip',
            'algorithm': 'algorithm',
            'cidrlist': 'cidr',
            'protocol': 'protocol',
        }
        # these values will be casted to int
        self.returns_to_int = {
            'publicport': 'public_port',
            'privateport': 'private_port',
        }

    def get_rule(self):
        args = self._get_common_args()
        args.update({
            'name': self.module.params.get('name'),
            'zoneid': self.get_zone(key='id') if self.module.params.get('zone') else None,
        })
        if self.module.params.get('ip_address'):
            args['publicipid'] = self.get_ip_address(key='id')

        rules = self.query_api('listLoadBalancerRules', **args)
        if rules:
            if len(rules['loadbalancerrule']) > 1:
                self.module.fail_json(msg="More than one rule having name %s. Please pass 'ip_address' as well." % args['name'])
            return rules['loadbalancerrule'][0]
        return None

    def _get_common_args(self):
        return {
            'account': self.get_account(key='name'),
            'domainid': self.get_domain(key='id'),
            'projectid': self.get_project(key='id'),
        }

    def _get_members_of_rule(self, rule):
        res = self.query_api('listLoadBalancerRuleInstances', id=rule['id'])
        return res.get('loadbalancerruleinstance', [])

    def _ensure_members(self, operation):
        if operation not in ['add', 'remove']:
            self.module.fail_json(msg="Bad operation: %s" % operation)

        rule = self.get_rule()
        if not rule:
            self.module.fail_json(msg="Unknown rule: %s" % self.module.params.get('name'))

        existing = {}
        for vm in self._get_members_of_rule(rule=rule):
            existing[vm['name']] = vm['id']

        wanted_names = self.module.params.get('vms')

        if operation == 'add':
            cs_func = 'assignToLoadBalancerRule'
            to_change = set(wanted_names) - set(existing.keys())
        else:
            cs_func = 'removeFromLoadBalancerRule'
            to_change = set(wanted_names) & set(existing.keys())

        if not to_change:
            return rule

        args = self._get_common_args()
        args['fetch_list'] = True
        vms = self.query_api('listVirtualMachines', **args)
        to_change_ids = []
        for name in to_change:
            for vm in vms:
                if vm['name'] == name:
                    to_change_ids.append(vm['id'])
                    break
            else:
                self.module.fail_json(msg="Unknown VM: %s" % name)

        if to_change_ids:
            self.result['changed'] = True

        if to_change_ids and not self.module.check_mode:
            res = self.query_api(
                cs_func,
                id=rule['id'],
                virtualmachineids=to_change_ids,
            )

            poll_async = self.module.params.get('poll_async')
            if poll_async:
                self.poll_job(res)
                rule = self.get_rule()
        return rule

    def add_members(self):
        return self._ensure_members('add')

    def remove_members(self):
        return self._ensure_members('remove')

    def get_result(self, rule):
        super(AnsibleCloudStackLBRuleMember, self).get_result(rule)
        if rule:
            self.result['vms'] = []
            for vm in self._get_members_of_rule(rule=rule):
                self.result['vms'].append(vm['name'])
        return self.result


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        ip_address=dict(aliases=['public_ip']),
        vms=dict(required=True, aliases=['vm'], type='list'),
        state=dict(choices=['present', 'absent'], default='present'),
        zone=dict(),
        domain=dict(),
        project=dict(),
        account=dict(),
        poll_async=dict(type='bool', default=True),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    acs_lb_rule_member = AnsibleCloudStackLBRuleMember(module)

    state = module.params.get('state')
    if state in ['absent']:
        rule = acs_lb_rule_member.remove_members()
    else:
        rule = acs_lb_rule_member.add_members()

    result = acs_lb_rule_member.get_result(rule)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
