#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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
module: cs_portforward
short_description: Manages port forwarding rules on Apache CloudStack based clouds.
description:
    - Create, update and remove port forwarding rules.
version_added: '2.0'
author: René Moser
options:
  ip_address:
    description:
      - Public IP address the rule is assigned to.
    required: true
  vm:
    description:
      - Name of virtual machine which we make the port forwarding rule for. Required if C(state=present).
    required: false
    default: null
  state:
    description:
      - State of the port forwarding rule.
    required: false
    default: 'present'
    choices: [ 'present', 'absent' ]
  protocol:
    description:
      - Protocol of the port forwarding rule.
    required: false
    default: 'tcp'
    choices: [ 'tcp', 'udp' ]
  public_port
    description:
      - Start public port for this rule.
    required: true
  public_end_port
    description:
      - End public port for this rule. If not specific, equal C(public_port).
    required: false
    default: null
  private_port
    description:
      - Start private port for this rule.
    required: true
  private_end_port
    description:
      - End private port for this rule. If not specific, equal C(private_port)
    required: false
    default: null
  open_firewall:
    description:
      - Whether the firewall rule for public port should be created, while creating the new rule.
      - Use M(cs_firewall) for managing firewall rules.
    required: false
    default: false
  vm_guest_ip:
    description:
      - VM guest NIC secondary IP address for the port forwarding rule.
    required: false
    default: false
  domain:
    description:
      - Domain the C(vm) is related to.
    required: false
    default: null
  account:
    description:
      - Account the C(vm) is related to.
    required: false
    default: null
  project:
    description:
      - Name of the project the c(vm) is located in.
    required: false
    default: null
  zone:
    description:
      - Name of the zone in which the virtual machine is in. If not set, default zone is used.
    required: false
    default: null
  poll_async:
    description:
      - Poll async jobs until job has finished.
    required: false
    default: true
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
---
# 1.2.3.4:80 -> web01:8080
- local_action:
    module: cs_portforward
    ip_address: 1.2.3.4
    vm: web01
    public_port: 80
    private_port: 8080


# forward SSH and open firewall
- local_action:
    module: cs_portforward
    ip_address: '{{ public_ip }}'
    vm: '{{ inventory_hostname }}'
    public_port: '{{ ansible_ssh_port }}'
    private_port: 22
    open_firewall: true


# forward DNS traffic, but do not open firewall
- local_action:
    module: cs_portforward
    ip_address: 1.2.3.4
    vm: '{{ inventory_hostname }}'
    public_port: 53
    private_port: 53
    protocol: udp
    open_firewall: true


# remove ssh port forwarding
- local_action:
    module: cs_portforward
    ip_address: 1.2.3.4
    public_port: 22
    private_port: 22
    state: absent

'''

RETURN = '''
---
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
  description: Private start port.
  returned: success
  type: int
  sample: 80
private_end_port:
  description: Private end port.
  returned: success
  type: int
public_port:
  description: Public start port.
  returned: success
  type: int
  sample: 80
public_end_port:
  description: Public end port.
  returned: success
  type: int
  sample: 80
tags:
  description: Tag srelated to the port forwarding.
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
'''


try:
    from cs import CloudStack, CloudStackException, read_config
    has_lib_cs = True
except ImportError:
    has_lib_cs = False

# import cloudstack common
from ansible.module_utils.cloudstack import *


class AnsibleCloudStackPortforwarding(AnsibleCloudStack):

    def __init__(self, module):
        AnsibleCloudStack.__init__(self, module)
        self.portforwarding_rule = None
        self.vm_default_nic = None


    def get_public_end_port(self):
        if not self.module.params.get('public_end_port'):
            return self.module.params.get('public_port')
        return self.module.params.get('public_end_port')


    def get_private_end_port(self):
        if not self.module.params.get('private_end_port'):
            return self.module.params.get('private_port')
        return self.module.params.get('private_end_port')


    def get_vm_guest_ip(self):
        vm_guest_ip = self.module.params.get('vm_guest_ip')
        default_nic = self.get_vm_default_nic()

        if not vm_guest_ip:
            return default_nic['ipaddress']

        for secondary_ip in default_nic['secondaryip']:
            if vm_guest_ip == secondary_ip['ipaddress']:
                return vm_guest_ip
        self.module.fail_json(msg="Secondary IP '%s' not assigned to VM" % vm_guest_ip)


    def get_vm_default_nic(self):
        if self.vm_default_nic:
            return self.vm_default_nic

        nics = self.cs.listNics(virtualmachineid=self.get_vm(key='id'))
        if nics:
            for n in nics['nic']:
                if n['isdefault']:
                    self.vm_default_nic = n
                    return self.vm_default_nic
        self.module.fail_json(msg="No default IP address of VM '%s' found" % self.module.params.get('vm'))


    def get_portforwarding_rule(self):
        if not self.portforwarding_rule:
            protocol            = self.module.params.get('protocol')
            public_port         = self.module.params.get('public_port')
            public_end_port     = self.get_public_end_port()
            private_port        = self.module.params.get('private_port')
            private_end_port    = self.get_public_end_port()

            args = {}
            args['ipaddressid'] = self.get_ip_address(key='id')
            args['projectid'] = self.get_project(key='id')
            portforwarding_rules = self.cs.listPortForwardingRules(**args)

            if portforwarding_rules and 'portforwardingrule' in portforwarding_rules:
                for rule in portforwarding_rules['portforwardingrule']:
                    if protocol == rule['protocol'] \
                        and public_port == int(rule['publicport']):
                        self.portforwarding_rule = rule
                        break
        return self.portforwarding_rule


    def present_portforwarding_rule(self):
        portforwarding_rule = self.get_portforwarding_rule()
        if portforwarding_rule:
            portforwarding_rule = self.update_portforwarding_rule(portforwarding_rule)
        else:
            portforwarding_rule = self.create_portforwarding_rule()
        return portforwarding_rule


    def create_portforwarding_rule(self):
        args = {}
        args['protocol']            = self.module.params.get('protocol')
        args['publicport']          = self.module.params.get('public_port')
        args['publicendport']       = self.get_public_end_port()
        args['privateport']         = self.module.params.get('private_port')
        args['privateendport']      = self.get_private_end_port()
        args['openfirewall']        = self.module.params.get('open_firewall')
        args['vmguestip']           = self.get_vm_guest_ip()
        args['ipaddressid']         = self.get_ip_address(key='id')
        args['virtualmachineid']    = self.get_vm(key='id')

        portforwarding_rule = None
        self.result['changed'] = True
        if not self.module.check_mode:
            portforwarding_rule = self.cs.createPortForwardingRule(**args)
            poll_async = self.module.params.get('poll_async')
            if poll_async:
                portforwarding_rule = self._poll_job(portforwarding_rule, 'portforwardingrule')
        return portforwarding_rule


    def update_portforwarding_rule(self, portforwarding_rule):
        args = {}
        args['protocol']            = self.module.params.get('protocol')
        args['publicport']          = self.module.params.get('public_port')
        args['publicendport']       = self.get_public_end_port()
        args['privateport']         = self.module.params.get('private_port')
        args['privateendport']      = self.get_private_end_port()
        args['openfirewall']        = self.module.params.get('open_firewall')
        args['vmguestip']           = self.get_vm_guest_ip()
        args['ipaddressid']         = self.get_ip_address(key='id')
        args['virtualmachineid']    = self.get_vm(key='id')

        if self._has_changed(args, portforwarding_rule):
            self.result['changed'] = True
            if not self.module.check_mode:
                # API broken in 4.2.1?, workaround using remove/create instead of update
                # portforwarding_rule = self.cs.updatePortForwardingRule(**args)
                self.absent_portforwarding_rule()
                portforwarding_rule = self.cs.createPortForwardingRule(**args)
                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    portforwarding_rule = self._poll_job(portforwarding_rule, 'portforwardingrule')
        return portforwarding_rule


    def absent_portforwarding_rule(self):
        portforwarding_rule = self.get_portforwarding_rule()

        if portforwarding_rule:
            self.result['changed'] = True
            args = {}
            args['id'] = portforwarding_rule['id']

            if not self.module.check_mode:
                res = self.cs.deletePortForwardingRule(**args)
                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    self._poll_job(res, 'portforwardingrule')
        return portforwarding_rule


    def get_result(self, portforwarding_rule):
        if portforwarding_rule:
            if 'id' in portforwarding_rule:
                self.result['id'] = portforwarding_rule['id']
            if 'virtualmachinedisplayname' in portforwarding_rule:
                self.result['vm_display_name'] = portforwarding_rule['virtualmachinedisplayname']
            if 'virtualmachinename' in portforwarding_rule:
                self.result['vm_name'] = portforwarding_rule['virtualmachinename']
            if 'ipaddress' in portforwarding_rule:
                self.result['ip_address'] = portforwarding_rule['ipaddress']
            if 'vmguestip' in portforwarding_rule:
                self.result['vm_guest_ip'] = portforwarding_rule['vmguestip']
            if 'publicport' in portforwarding_rule:
                self.result['public_port'] = portforwarding_rule['publicport']
            if 'publicendport' in portforwarding_rule:
                self.result['public_end_port'] = portforwarding_rule['publicendport']
            if 'privateport' in portforwarding_rule:
                self.result['private_port'] = portforwarding_rule['privateport']
            if 'privateendport' in portforwarding_rule:
                self.result['private_end_port'] = portforwarding_rule['privateendport']
            if 'protocol' in portforwarding_rule:
                self.result['protocol'] = portforwarding_rule['protocol']
            if 'tags' in portforwarding_rule:
                self.result['tags'] = []
                for tag in portforwarding_rule['tags']:
                    result_tag          = {}
                    result_tag['key']   = tag['key']
                    result_tag['value'] = tag['value']
                    self.result['tags'].append(result_tag)
        return self.result


def main():
    module = AnsibleModule(
        argument_spec = dict(
            ip_address = dict(required=True),
            protocol= dict(choices=['tcp', 'udp'], default='tcp'),
            public_port = dict(type='int', required=True),
            public_end_port = dict(type='int', default=None),
            private_port = dict(type='int', required=True),
            private_end_port = dict(type='int', default=None),
            state = dict(choices=['present', 'absent'], default='present'),
            open_firewall = dict(choices=BOOLEANS, default=False),
            vm_guest_ip = dict(default=None),
            vm = dict(default=None),
            zone = dict(default=None),
            domain = dict(default=None),
            account = dict(default=None),
            project = dict(default=None),
            poll_async = dict(choices=BOOLEANS, default=True),
            api_key = dict(default=None),
            api_secret = dict(default=None),
            api_url = dict(default=None),
            api_http_method = dict(default='get'),
        ),
        supports_check_mode=True
    )

    if not has_lib_cs:
        module.fail_json(msg="python library cs required: pip install cs")

    try:
        acs_pf = AnsibleCloudStackPortforwarding(module)
        state = module.params.get('state')
        if state in ['absent']:
            pf_rule = acs_pf.absent_portforwarding_rule()
        else:
            pf_rule = acs_pf.present_portforwarding_rule()

        result = acs_pf.get_result(pf_rule)

    except CloudStackException, e:
        module.fail_json(msg='CloudStackException: %s' % str(e))

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
main()
