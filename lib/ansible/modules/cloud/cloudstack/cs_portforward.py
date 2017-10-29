#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2015, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_portforward
short_description: Manages port forwarding rules on Apache CloudStack based clouds.
description:
    - Create, update and remove port forwarding rules.
version_added: '2.0'
author: "René Moser (@resmo)"
options:
  ip_address:
    description:
      - Public IP address the rule is assigned to.
    required: true
  vm:
    description:
      - Name of virtual machine which we make the port forwarding rule for.
      - Required if C(state=present).
  state:
    description:
      - State of the port forwarding rule.
    default: present
    choices: [ present, absent ]
  protocol:
    description:
      - Protocol of the port forwarding rule.
    default: tcp
    choices: [ tcp, udp ]
  public_port:
    description:
      - Start public port for this rule.
    required: true
  public_end_port:
    description:
      - End public port for this rule.
      - If not specified equal C(public_port).
  private_port:
    description:
      - Start private port for this rule.
    required: true
  private_end_port:
    description:
      - End private port for this rule.
      - If not specified equal C(private_port).
  open_firewall:
    description:
      - Whether the firewall rule for public port should be created, while creating the new rule.
      - Use M(cs_firewall) for managing firewall rules.
    default: false
  vm_guest_ip:
    description:
      - VM guest NIC secondary IP address for the port forwarding rule.
    default: false
  network:
    description:
      - Name of the network.
    version_added: "2.3"
  vpc:
    description:
      - Name of the VPC.
    version_added: "2.3"
  domain:
    description:
      - Domain the C(vm) is related to.
  account:
    description:
      - Account the C(vm) is related to.
  project:
    description:
      - Name of the project the C(vm) is located in.
  zone:
    description:
      - Name of the zone in which the virtual machine is in.
      - If not set, default zone is used.
  poll_async:
    description:
      - Poll async jobs until job has finished.
    default: true
  tags:
    description:
      - List of tags. Tags are a list of dictionaries having keys C(key) and C(value).
      - "To delete all tags, set a empty list e.g. C(tags: [])."
    aliases: [ tag ]
    version_added: "2.4"
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: 1.2.3.4:80 -> web01:8080
  local_action:
    module: cs_portforward
    ip_address: 1.2.3.4
    vm: web01
    public_port: 80
    private_port: 8080

- name: forward SSH and open firewall
  local_action:
    module: cs_portforward
    ip_address: '{{ public_ip }}'
    vm: '{{ inventory_hostname }}'
    public_port: '{{ ansible_ssh_port }}'
    private_port: 22
    open_firewall: true

- name: forward DNS traffic, but do not open firewall
  local_action:
    module: cs_portforward
    ip_address: 1.2.3.4
    vm: '{{ inventory_hostname }}'
    public_port: 53
    private_port: 53
    protocol: udp

- name: remove ssh port forwarding
  local_action:
    module: cs_portforward
    ip_address: 1.2.3.4
    public_port: 22
    private_port: 22
    state: absent
'''

RETURN = '''
---
id:
  description: UUID of the public IP address.
  returned: success
  type: string
  sample: a6f7a5fc-43f8-11e5-a151-feff819cdc9f
ip_address:
  description: Public IP address.
  returned: success
  type: string
  sample: 1.2.3.4
protocol:
  description: Protocol.
  returned: success
  type: string
  sample: tcp
private_port:
  description: Start port on the virtual machine's IP address.
  returned: success
  type: int
  sample: 80
private_end_port:
  description: End port on the virtual machine's IP address.
  returned: success
  type: int
public_port:
  description: Start port on the public IP address.
  returned: success
  type: int
  sample: 80
public_end_port:
  description: End port on the public IP address.
  returned: success
  type: int
  sample: 80
tags:
  description: Tags related to the port forwarding.
  returned: success
  type: list
  sample: []
vm_name:
  description: Name of the virtual machine.
  returned: success
  type: string
  sample: web-01
vm_display_name:
  description: Display name of the virtual machine.
  returned: success
  type: string
  sample: web-01
vm_guest_ip:
  description: IP of the virtual machine.
  returned: success
  type: string
  sample: 10.101.65.152
vpc:
  description: Name of the VPC.
  returned: success
  type: string
  sample: my_vpc
network:
  description: Name of the network.
  returned: success
  type: string
  sample: dmz
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import AnsibleCloudStack, cs_argument_spec, cs_required_together


class AnsibleCloudStackPortforwarding(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackPortforwarding, self).__init__(module)
        self.returns = {
            'virtualmachinedisplayname': 'vm_display_name',
            'virtualmachinename': 'vm_name',
            'ipaddress': 'ip_address',
            'vmguestip': 'vm_guest_ip',
            'publicip': 'public_ip',
            'protocol': 'protocol',
        }
        # these values will be casted to int
        self.returns_to_int = {
            'publicport': 'public_port',
            'publicendport': 'public_end_port',
            'privateport': 'private_port',
            'privateendport': 'private_end_port',
        }
        self.portforwarding_rule = None

    def get_portforwarding_rule(self):
        if not self.portforwarding_rule:
            protocol = self.module.params.get('protocol')
            public_port = self.module.params.get('public_port')

            args = {
                'ipaddressid': self.get_ip_address(key='id'),
                'account': self.get_account(key='name'),
                'domainid': self.get_domain(key='id'),
                'projectid': self.get_project(key='id'),
            }
            portforwarding_rules = self.query_api('listPortForwardingRules', **args)

            if portforwarding_rules and 'portforwardingrule' in portforwarding_rules:
                for rule in portforwarding_rules['portforwardingrule']:
                    if (protocol == rule['protocol'] and
                            public_port == int(rule['publicport'])):
                        self.portforwarding_rule = rule
                        break
        return self.portforwarding_rule

    def present_portforwarding_rule(self):
        portforwarding_rule = self.get_portforwarding_rule()
        if portforwarding_rule:
            portforwarding_rule = self.update_portforwarding_rule(portforwarding_rule)
        else:
            portforwarding_rule = self.create_portforwarding_rule()

        if portforwarding_rule:
            portforwarding_rule = self.ensure_tags(resource=portforwarding_rule, resource_type='PortForwardingRule')
            self.portforwarding_rule = portforwarding_rule

        return portforwarding_rule

    def create_portforwarding_rule(self):
        args = {
            'protocol': self.module.params.get('protocol'),
            'publicport': self.module.params.get('public_port'),
            'publicendport': self.get_or_fallback('public_end_port', 'public_port'),
            'privateport': self.module.params.get('private_port'),
            'privateendport': self.get_or_fallback('private_end_port', 'private_port'),
            'openfirewall': self.module.params.get('open_firewall'),
            'vmguestip': self.get_vm_guest_ip(),
            'ipaddressid': self.get_ip_address(key='id'),
            'virtualmachineid': self.get_vm(key='id'),
            'account': self.get_account(key='name'),
            'domainid': self.get_domain(key='id'),
            'networkid': self.get_network(key='id'),
        }

        portforwarding_rule = None
        self.result['changed'] = True
        if not self.module.check_mode:
            portforwarding_rule = self.query_api('createPortForwardingRule', **args)
            poll_async = self.module.params.get('poll_async')
            if poll_async:
                portforwarding_rule = self.poll_job(portforwarding_rule, 'portforwardingrule')
        return portforwarding_rule

    def update_portforwarding_rule(self, portforwarding_rule):
        args = {
            'protocol': self.module.params.get('protocol'),
            'publicport': self.module.params.get('public_port'),
            'publicendport': self.get_or_fallback('public_end_port', 'public_port'),
            'privateport': self.module.params.get('private_port'),
            'privateendport': self.get_or_fallback('private_end_port', 'private_port'),
            'vmguestip': self.get_vm_guest_ip(),
            'ipaddressid': self.get_ip_address(key='id'),
            'virtualmachineid': self.get_vm(key='id'),
            'networkid': self.get_network(key='id'),
        }

        if self.has_changed(args, portforwarding_rule):
            self.result['changed'] = True
            if not self.module.check_mode:
                # API broken in 4.2.1?, workaround using remove/create instead of update
                # portforwarding_rule = self.query_api('updatePortForwardingRule', **args)
                self.absent_portforwarding_rule()
                portforwarding_rule = self.query_api('createPortForwardingRule', **args)
                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    portforwarding_rule = self.poll_job(portforwarding_rule, 'portforwardingrule')
        return portforwarding_rule

    def absent_portforwarding_rule(self):
        portforwarding_rule = self.get_portforwarding_rule()

        if portforwarding_rule:
            self.result['changed'] = True
            args = {
                'id': portforwarding_rule['id'],
            }
            if not self.module.check_mode:
                res = self.query_api('deletePortForwardingRule', **args)
                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    self.poll_job(res, 'portforwardingrule')
        return portforwarding_rule

    def get_result(self, portforwarding_rule):
        super(AnsibleCloudStackPortforwarding, self).get_result(portforwarding_rule)
        if portforwarding_rule:
            for search_key, return_key in self.returns_to_int.items():
                if search_key in portforwarding_rule:
                    self.result[return_key] = int(portforwarding_rule[search_key])
        return self.result


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        ip_address=dict(required=True),
        protocol=dict(choices=['tcp', 'udp'], default='tcp'),
        public_port=dict(type='int', required=True),
        public_end_port=dict(type='int'),
        private_port=dict(type='int', required=True),
        private_end_port=dict(type='int'),
        state=dict(choices=['present', 'absent'], default='present'),
        open_firewall=dict(type='bool', default=False),
        vm_guest_ip=dict(),
        vm=dict(),
        vpc=dict(),
        network=dict(),
        zone=dict(),
        domain=dict(),
        account=dict(),
        project=dict(),
        poll_async=dict(type='bool', default=True),
        tags=dict(type='list', aliases=['tag']),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    acs_pf = AnsibleCloudStackPortforwarding(module)
    state = module.params.get('state')
    if state in ['absent']:
        pf_rule = acs_pf.absent_portforwarding_rule()
    else:
        pf_rule = acs_pf.present_portforwarding_rule()

    result = acs_pf.get_result(pf_rule)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
