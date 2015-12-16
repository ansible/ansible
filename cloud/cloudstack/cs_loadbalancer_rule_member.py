#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2015, Darren Worrall <darren@iweb.co.uk>
# (c) 2015, René Moser <mail@renemoser.net>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: cs_loadbalancer_rule_member
short_description: Manages load balancer rule members on Apache CloudStack based clouds.
description:
    - Add and remove load balancer rule members.
version_added: '2.0'
author:
    - "Darren Worrall (@dazworrall)"
    - "René Moser (@resmo)"
options:
  name:
    description:
      - The name of the load balancer rule.
    required: true
  ip_address:
    description:
      - Public IP address from where the network traffic will be load balanced from.
      - Only needed to find the rule if C(name) is not unique.
    required: false
    default: null
    aliases: [ 'public_ip' ]
  vms:
    description:
      - List of VMs to assign to or remove from the rule.
    required: true
    type: list
    aliases: [ 'vm' ]
  state:
    description:
      - Should the VMs be present or absent from the rule.
    required: true
    default: 'present'
    choices: [ 'present', 'absent' ]
  project:
    description:
      - Name of the project the firewall rule is related to.
    required: false
    default: null
  domain:
    description:
      - Domain the rule is related to.
    required: false
    default: null
  account:
    description:
      - Account the rule is related to.
    required: false
    default: null
  zone:
    description:
      - Name of the zone in which the rule should be located.
      - If not set, default zone is used.
    required: false
    default: null
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# Add VMs to an exising load balancer
- local_action:
    module: cs_loadbalancer_rule_member
    name: balance_http
    vms:
      - web01
      - web02

# Remove a VM from an existing load balancer
- local_action:
    module: cs_loadbalancer_rule_member
    name: balance_http
    vms:
      - web01
      - web02
    state: absent

# Rolling upgrade of hosts
- hosts: webservers
  serial: 1
  pre_tasks:
    - name: Remove from load balancer
      local_action:
      module: cs_loadbalancer_rule_member
      name: balance_http
      vm: "{{ ansible_hostname }}"
      state: absent
  tasks:
    # Perform update
  post_tasks:
    - name: Add to load balancer
      local_action:
      module: cs_loadbalancer_rule_member
      name: balance_http
      vm: "{{ ansible_hostname }}"
      state: present
'''

RETURN = '''
---
id:
  description: UUID of the rule.
  returned: success
  type: string
  sample: a6f7a5fc-43f8-11e5-a151-feff819cdc9f
zone:
  description: Name of zone the rule is related to.
  returned: success
  type: string
  sample: ch-gva-2
project:
  description: Name of project the rule is related to.
  returned: success
  type: string
  sample: Production
account:
  description: Account the rule is related to.
  returned: success
  type: string
  sample: example account
domain:
  description: Domain the rule is related to.
  returned: success
  type: string
  sample: example domain
algorithm:
  description: Load balancer algorithm used.
  returned: success
  type: string
  sample: "source"
cidr:
  description: CIDR to forward traffic from.
  returned: success
  type: string
  sample: ""
name:
  description: Name of the rule.
  returned: success
  type: string
  sample: "http-lb"
description:
  description: Description of the rule.
  returned: success
  type: string
  sample: "http load balancer rule"
protocol:
  description: Protocol of the rule.
  returned: success
  type: string
  sample: "tcp"
public_port:
  description: Public port.
  returned: success
  type: string
  sample: 80
private_port:
  description: Private IP address.
  returned: success
  type: string
  sample: 80
public_ip:
  description: Public IP address.
  returned: success
  type: string
  sample: "1.2.3.4"
vms:
  description: Rule members.
  returned: success
  type: list
  sample: '[ "web01", "web02" ]'
tags:
  description: List of resource tags associated with the rule.
  returned: success
  type: dict
  sample: '[ { "key": "foo", "value": "bar" } ]'
state:
  description: State of the rule.
  returned: success
  type: string
  sample: "Add"
'''

try:
    from cs import CloudStack, CloudStackException, read_config
    has_lib_cs = True
except ImportError:
    has_lib_cs = False

# import cloudstack common
from ansible.module_utils.cloudstack import *

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
        args               = self._get_common_args()
        args['name']       = self.module.params.get('name')
        args['zoneid']     = self.get_zone(key='id')
        if self.module.params.get('ip_address'):
            args['publicipid'] = self.get_ip_address(key='id')
        rules = self.cs.listLoadBalancerRules(**args)
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
        res = self.cs.listLoadBalancerRuleInstances(id=rule['id'])
        if 'errortext' in res:
            self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
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

        if operation =='add':
            cs_func = self.cs.assignToLoadBalancerRule
            to_change = set(wanted_names) - set(existing.keys())
        else:
            cs_func = self.cs.removeFromLoadBalancerRule
            to_change = set(wanted_names) & set(existing.keys())

        if not to_change:
            return rule

        args = self._get_common_args()
        vms = self.cs.listVirtualMachines(**args)
        to_change_ids = []
        for name in to_change:
            for vm in vms.get('virtualmachine', []):
                if vm['name'] == name:
                    to_change_ids.append(vm['id'])
                    break
            else:
                self.module.fail_json(msg="Unknown VM: %s" % name)

        if to_change_ids:
            self.result['changed'] = True

        if to_change_ids and not self.module.check_mode:
            res = cs_func(
                id = rule['id'],
                virtualmachineids = to_change_ids,
            )
            if 'errortext' in res:
                self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
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
        name = dict(required=True),
        ip_address = dict(default=None, aliases=['public_ip']),
        vms = dict(required=True, aliases=['vm'], type='list'),
        state = dict(choices=['present', 'absent'], default='present'),
        zone = dict(default=None),
        domain = dict(default=None),
        project = dict(default=None),
        account = dict(default=None),
        poll_async = dict(type='bool', default=True),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    if not has_lib_cs:
        module.fail_json(msg="python library cs required: pip install cs")

    try:
        acs_lb_rule_member = AnsibleCloudStackLBRuleMember(module)

        state = module.params.get('state')
        if state in ['absent']:
            rule = acs_lb_rule_member.remove_members()
        else:
            rule = acs_lb_rule_member.add_members()

        result = acs_lb_rule_member.get_result(rule)

    except CloudStackException as e:
        module.fail_json(msg='CloudStackException: %s' % str(e))

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
