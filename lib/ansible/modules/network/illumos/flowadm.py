#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Adam Števko <adam.stevko@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: flowadm
short_description: Manage bandwidth resource control and priority for protocols, services and zones on Solaris/illumos systems
description:
    - Create/modify/remove networking bandwidth and associated resources for a type of traffic on a particular link.
version_added: "2.2"
author: Adam Števko (@xen0l)
options:
    name:
        description: >
            - A flow is defined as a set of attributes based on Layer 3 and Layer 4
            headers, which can be used to identify a protocol, service, or a zone.
        required: true
        aliases: [ 'flow' ]
    link:
        description:
            - Specifiies a link to configure flow on.
        required: false
    local_ip:
        description:
            - Identifies a network flow by the local IP address.
        required: false
    remote_ip:
        description:
            - Identifies a network flow by the remote IP address.
        required: false
    transport:
        description: >
            - Specifies a Layer 4 protocol to be used. It is typically used in combination with I(local_port) to
            identify the service that needs special attention.
        required: false
    local_port:
        description:
            - Identifies a service specified by the local port.
        required: false
    dsfield:
        description: >
            - Identifies the 8-bit differentiated services field (as defined in
            RFC 2474). The optional dsfield_mask is used to state the bits of interest in
            the differentiated services field when comparing with the dsfield
            value. Both values must be in hexadecimal.
        required: false
    maxbw:
        description: >
            - Sets the full duplex bandwidth for the flow. The bandwidth is
            specified as an integer with one of the scale suffixes(K, M, or G
            for Kbps, Mbps, and Gbps). If no units are specified, the input
            value will be read as Mbps.
        required: false
    priority:
        description:
            - Sets the relative priority for the flow.
        required: false
        default: 'medium'
        choices: [ 'low', 'medium', 'high' ]
    temporary:
        description:
            - Specifies that the configured flow is temporary. Temporary
              flows do not persist across reboots.
        required: false
        default: false
        type: bool
    state:
        description:
            - Create/delete/enable/disable an IP address on the network interface.
        required: false
        default: present
        choices: [ 'absent', 'present', 'resetted' ]
'''

EXAMPLES = '''
# Limit SSH traffic to 100M via vnic0 interface
- flowadm:
    link: vnic0
    flow: ssh_out
    transport: tcp
    local_port: 22
    maxbw: 100M
    state: present

# Reset flow properties
- flowadm:
    name: dns
    state: resetted

# Configure policy for EF PHB (DSCP value of 101110 from RFC 2598) with a bandwidth of 500 Mbps and a high priority.
- flowadm:
    link: bge0
    dsfield: '0x2e:0xfc'
    maxbw: 500M
    priority: high
    flow: efphb-flow
    state: present
'''

RETURN = '''
name:
    description: flow name
    returned: always
    type: string
    sample: "http_drop"
link:
    description: flow's link
    returned: if link is defined
    type: string
    sample: "vnic0"
state:
    description: state of the target
    returned: always
    type: string
    sample: "present"
temporary:
    description: flow's persistence
    returned: always
    type: boolean
    sample: "True"
priority:
    description: flow's priority
    returned: if priority is defined
    type: string
    sample: "low"
transport:
    description: flow's transport
    returned: if transport is defined
    type: string
    sample: "tcp"
maxbw:
    description: flow's maximum bandwidth
    returned: if maxbw is defined
    type: string
    sample: "100M"
local_Ip:
    description: flow's local IP address
    returned: if local_ip is defined
    type: string
    sample: "10.0.0.42"
local_port:
    description: flow's local port
    returned: if local_port is defined
    type: int
    sample: 1337
remote_Ip:
    description: flow's remote IP address
    returned: if remote_ip is defined
    type: string
    sample: "10.0.0.42"
dsfield:
    description: flow's differentiated services value
    returned: if dsfield is defined
    type: string
    sample: "0x2e:0xfc"
'''


import socket

from ansible.module_utils.basic import AnsibleModule


SUPPORTED_TRANSPORTS = ['tcp', 'udp', 'sctp', 'icmp', 'icmpv6']
SUPPORTED_PRIORITIES = ['low', 'medium', 'high']

SUPPORTED_ATTRIBUTES = ['local_ip', 'remote_ip', 'transport', 'local_port', 'dsfield']
SUPPORTPED_PROPERTIES = ['maxbw', 'priority']


class Flow(object):

    def __init__(self, module):
        self.module = module

        self.name = module.params['name']
        self.link = module.params['link']
        self.local_ip = module.params['local_ip']
        self.remote_ip = module.params['remote_ip']
        self.transport = module.params['transport']
        self.local_port = module.params['local_port']
        self.dsfield = module.params['dsfield']
        self.maxbw = module.params['maxbw']
        self.priority = module.params['priority']
        self.temporary = module.params['temporary']
        self.state = module.params['state']

        self._needs_updating = {
            'maxbw': False,
            'priority': False,
        }

    @classmethod
    def is_valid_port(cls, port):
        return 1 <= int(port) <= 65535

    @classmethod
    def is_valid_address(cls, ip):

        if ip.count('/') == 1:
            ip_address, netmask = ip.split('/')
        else:
            ip_address = ip

        if len(ip_address.split('.')) == 4:
            try:
                socket.inet_pton(socket.AF_INET, ip_address)
            except socket.error:
                return False

            if not 0 <= netmask <= 32:
                return False
        else:
            try:
                socket.inet_pton(socket.AF_INET6, ip_address)
            except socket.error:
                return False

            if not 0 <= netmask <= 128:
                return False

        return True

    @classmethod
    def is_hex(cls, number):
        try:
            int(number, 16)
        except ValueError:
            return False

        return True

    @classmethod
    def is_valid_dsfield(cls, dsfield):

        dsmask = None

        if dsfield.count(':') == 1:
            dsval = dsfield.split(':')[0]
        else:
            dsval, dsmask = dsfield.split(':')

        if dsmask and not 0x01 <= int(dsmask, 16) <= 0xff and not 0x01 <= int(dsval, 16) <= 0xff:
            return False
        elif not 0x01 <= int(dsval, 16) <= 0xff:
            return False

        return True

    def flow_exists(self):
        cmd = [self.module.get_bin_path('flowadm')]

        cmd.append('show-flow')
        cmd.append(self.name)

        (rc, _, _) = self.module.run_command(cmd)

        if rc == 0:
            return True
        else:
            return False

    def delete_flow(self):
        cmd = [self.module.get_bin_path('flowadm')]

        cmd.append('remove-flow')
        if self.temporary:
            cmd.append('-t')
        cmd.append(self.name)

        return self.module.run_command(cmd)

    def create_flow(self):
        cmd = [self.module.get_bin_path('flowadm')]

        cmd.append('add-flow')
        cmd.append('-l')
        cmd.append(self.link)

        if self.local_ip:
            cmd.append('-a')
            cmd.append('local_ip=' + self.local_ip)

        if self.remote_ip:
            cmd.append('-a')
            cmd.append('remote_ip=' + self.remote_ip)

        if self.transport:
            cmd.append('-a')
            cmd.append('transport=' + self.transport)

        if self.local_port:
            cmd.append('-a')
            cmd.append('local_port=' + self.local_port)

        if self.dsfield:
            cmd.append('-a')
            cmd.append('dsfield=' + self.dsfield)

        if self.maxbw:
            cmd.append('-p')
            cmd.append('maxbw=' + self.maxbw)

        if self.priority:
            cmd.append('-p')
            cmd.append('priority=' + self.priority)

        if self.temporary:
            cmd.append('-t')
        cmd.append(self.name)

        return self.module.run_command(cmd)

    def _query_flow_props(self):
        cmd = [self.module.get_bin_path('flowadm')]

        cmd.append('show-flowprop')
        cmd.append('-c')
        cmd.append('-o')
        cmd.append('property,possible')
        cmd.append(self.name)

        return self.module.run_command(cmd)

    def flow_needs_udpating(self):
        (rc, out, err) = self._query_flow_props()

        NEEDS_UPDATING = False

        if rc == 0:
            properties = (line.split(':') for line in out.rstrip().split('\n'))
            for prop, value in properties:
                if prop == 'maxbw' and self.maxbw != value:
                    self._needs_updating.update({prop: True})
                    NEEDS_UPDATING = True

                elif prop == 'priority' and self.priority != value:
                    self._needs_updating.update({prop: True})
                    NEEDS_UPDATING = True

            return NEEDS_UPDATING
        else:
            self.module.fail_json(msg='Error while checking flow properties: %s' % err,
                                  stderr=err,
                                  rc=rc)

    def update_flow(self):
        cmd = [self.module.get_bin_path('flowadm')]

        cmd.append('set-flowprop')

        if self.maxbw and self._needs_updating['maxbw']:
            cmd.append('-p')
            cmd.append('maxbw=' + self.maxbw)

        if self.priority and self._needs_updating['priority']:
            cmd.append('-p')
            cmd.append('priority=' + self.priority)

        if self.temporary:
            cmd.append('-t')
        cmd.append(self.name)

        return self.module.run_command(cmd)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True, aliases=['flow']),
            link=dict(required=False),
            local_ip=dict(required=False),
            remote_ip=dict(required=False),
            transport=dict(required=False, choices=SUPPORTED_TRANSPORTS),
            local_port=dict(required=False),
            dsfield=dict(required=False),
            maxbw=dict(required=False),
            priority=dict(required=False,
                          default='medium',
                          choices=SUPPORTED_PRIORITIES),
            temporary=dict(default=False, type='bool'),
            state=dict(required=False,
                       default='present',
                       choices=['absent', 'present', 'resetted']),
        ),
        mutually_exclusive=[
            ('local_ip', 'remote_ip'),
            ('local_ip', 'transport'),
            ('local_ip', 'local_port'),
            ('local_ip', 'dsfield'),
            ('remote_ip', 'transport'),
            ('remote_ip', 'local_port'),
            ('remote_ip', 'dsfield'),
            ('transport', 'dsfield'),
            ('local_port', 'dsfield'),
        ],
        supports_check_mode=True
    )

    flow = Flow(module)

    rc = None
    out = ''
    err = ''
    result = {}
    result['name'] = flow.name
    result['state'] = flow.state
    result['temporary'] = flow.temporary

    if flow.link:
        result['link'] = flow.link

    if flow.maxbw:
        result['maxbw'] = flow.maxbw

    if flow.priority:
        result['priority'] = flow.priority

    if flow.local_ip:
        if flow.is_valid_address(flow.local_ip):
            result['local_ip'] = flow.local_ip

    if flow.remote_ip:
        if flow.is_valid_address(flow.remote_ip):
            result['remote_ip'] = flow.remote_ip

    if flow.transport:
        result['transport'] = flow.transport

    if flow.local_port:
        if flow.is_valid_port(flow.local_port):
            result['local_port'] = flow.local_port
        else:
            module.fail_json(msg='Invalid port: %s' % flow.local_port,
                             rc=1)

    if flow.dsfield:
        if flow.is_valid_dsfield(flow.dsfield):
            result['dsfield'] = flow.dsfield
        else:
            module.fail_json(msg='Invalid dsfield: %s' % flow.dsfield,
                             rc=1)

    if flow.state == 'absent':
        if flow.flow_exists():
            if module.check_mode:
                module.exit_json(changed=True)

            (rc, out, err) = flow.delete_flow()
            if rc != 0:
                module.fail_json(msg='Error while deleting flow: "%s"' % err,
                                 name=flow.name,
                                 stderr=err,
                                 rc=rc)

    elif flow.state == 'present':
        if not flow.flow_exists():
            if module.check_mode:
                module.exit_json(changed=True)

            (rc, out, err) = flow.create_flow()
            if rc != 0:
                module.fail_json(msg='Error while creating flow: "%s"' % err,
                                 name=flow.name,
                                 stderr=err,
                                 rc=rc)
        else:
            if flow.flow_needs_udpating():
                (rc, out, err) = flow.update_flow()
                if rc != 0:
                    module.fail_json(msg='Error while updating flow: "%s"' % err,
                                     name=flow.name,
                                     stderr=err,
                                     rc=rc)

    elif flow.state == 'resetted':
        if flow.flow_exists():
            if module.check_mode:
                module.exit_json(changed=True)

            (rc, out, err) = flow.reset_flow()
            if rc != 0:
                module.fail_json(msg='Error while resetting flow: "%s"' % err,
                                 name=flow.name,
                                 stderr=err,
                                 rc=rc)

    if rc is None:
        result['changed'] = False
    else:
        result['changed'] = True

    if out:
        result['stdout'] = out
    if err:
        result['stderr'] = err

    module.exit_json(**result)


if __name__ == '__main__':
    main()
