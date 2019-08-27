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
module: ipadm_addr
short_description: Manage IP addresses on an interface on Solaris/illumos systems
description:
    - Create/delete static/dynamic IP addresses on network interfaces on Solaris/illumos systems.
    - Up/down static/dynamic IP addresses on network interfaces on Solaris/illumos systems.
    - Manage IPv6 link-local addresses on network interfaces on Solaris/illumos systems.
version_added: "2.3"
author: Adam Števko (@xen0l)
options:
    address:
        description:
            - Specifiies an IP address to configure in CIDR notation.
        required: false
        aliases: [ "addr" ]
    addrtype:
        description:
            - Specifiies a type of IP address to configure.
        required: false
        default: static
        choices: [ 'static', 'dhcp', 'addrconf' ]
    addrobj:
        description:
            - Specifies an unique IP address on the system.
        required: true
    temporary:
        description:
            - Specifies that the configured IP address is temporary. Temporary
              IP addresses do not persist across reboots.
        required: false
        default: false
        type: bool
    wait:
        description:
            - Specifies the time in seconds we wait for obtaining address via DHCP.
        required: false
        default: 60
    state:
        description:
            - Create/delete/enable/disable an IP address on the network interface.
        required: false
        default: present
        choices: [ 'absent', 'present', 'up', 'down', 'enabled', 'disabled', 'refreshed' ]
'''

EXAMPLES = '''
- name: Configure IP address 10.0.0.1 on e1000g0
  ipadm_addr: addr=10.0.0.1/32 addrobj=e1000g0/v4 state=present

- name: Delete addrobj
  ipadm_addr: addrobj=e1000g0/v4 state=absent

- name: Configure link-local IPv6 address
  ipadm_addr: addtype=addrconf addrobj=vnic0/v6

- name: Configure address via DHCP and wait 180 seconds for address obtaining
  ipadm_addr: addrobj=vnic0/dhcp addrtype=dhcp wait=180
'''

RETURN = '''
addrobj:
    description: address object name
    returned: always
    type: str
    sample: bge0/v4
state:
    description: state of the target
    returned: always
    type: str
    sample: present
temporary:
    description: specifies if operation will persist across reboots
    returned: always
    type: bool
    sample: True
addrtype:
    description: address type
    returned: always
    type: str
    sample: static
address:
    description: IP address
    returned: only if addrtype is 'static'
    type: str
    sample: 1.3.3.7/32
wait:
    description: time we wait for DHCP
    returned: only if addrtype is 'dhcp'
    type: str
    sample: 10
'''

import socket

from ansible.module_utils.basic import AnsibleModule


SUPPORTED_TYPES = ['static', 'addrconf', 'dhcp']


class Addr(object):

    def __init__(self, module):
        self.module = module

        self.address = module.params['address']
        self.addrtype = module.params['addrtype']
        self.addrobj = module.params['addrobj']
        self.temporary = module.params['temporary']
        self.state = module.params['state']
        self.wait = module.params['wait']

    def is_cidr_notation(self):

        return self.address.count('/') == 1

    def is_valid_address(self):

        ip_address = self.address.split('/')[0]

        try:
            if len(ip_address.split('.')) == 4:
                socket.inet_pton(socket.AF_INET, ip_address)
            else:
                socket.inet_pton(socket.AF_INET6, ip_address)
        except socket.error:
            return False

        return True

    def is_dhcp(self):
        cmd = [self.module.get_bin_path('ipadm')]

        cmd.append('show-addr')
        cmd.append('-p')
        cmd.append('-o')
        cmd.append('type')
        cmd.append(self.addrobj)

        (rc, out, err) = self.module.run_command(cmd)

        if rc == 0:
            if out.rstrip() != 'dhcp':
                return False

            return True
        else:
            self.module.fail_json(msg='Wrong addrtype %s for addrobj "%s": %s' % (out, self.addrobj, err),
                                  rc=rc,
                                  stderr=err)

    def addrobj_exists(self):
        cmd = [self.module.get_bin_path('ipadm')]

        cmd.append('show-addr')
        cmd.append(self.addrobj)

        (rc, _, _) = self.module.run_command(cmd)

        if rc == 0:
            return True
        else:
            return False

    def delete_addr(self):
        cmd = [self.module.get_bin_path('ipadm')]

        cmd.append('delete-addr')
        cmd.append(self.addrobj)

        return self.module.run_command(cmd)

    def create_addr(self):
        cmd = [self.module.get_bin_path('ipadm')]

        cmd.append('create-addr')
        cmd.append('-T')
        cmd.append(self.addrtype)

        if self.temporary:
            cmd.append('-t')

        if self.addrtype == 'static':
            cmd.append('-a')
            cmd.append(self.address)

        if self.addrtype == 'dhcp' and self.wait:
            cmd.append('-w')
            cmd.append(self.wait)

        cmd.append(self.addrobj)

        return self.module.run_command(cmd)

    def up_addr(self):
        cmd = [self.module.get_bin_path('ipadm')]

        cmd.append('up-addr')

        if self.temporary:
            cmd.append('-t')

        cmd.append(self.addrobj)

        return self.module.run_command(cmd)

    def down_addr(self):
        cmd = [self.module.get_bin_path('ipadm')]

        cmd.append('down-addr')

        if self.temporary:
            cmd.append('-t')

        cmd.append(self.addrobj)

        return self.module.run_command(cmd)

    def enable_addr(self):
        cmd = [self.module.get_bin_path('ipadm')]

        cmd.append('enable-addr')
        cmd.append('-t')
        cmd.append(self.addrobj)

        return self.module.run_command(cmd)

    def disable_addr(self):
        cmd = [self.module.get_bin_path('ipadm')]

        cmd.append('disable-addr')
        cmd.append('-t')
        cmd.append(self.addrobj)

        return self.module.run_command(cmd)

    def refresh_addr(self):
        cmd = [self.module.get_bin_path('ipadm')]

        cmd.append('refresh-addr')
        cmd.append(self.addrobj)

        return self.module.run_command(cmd)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            address=dict(aliases=['addr']),
            addrtype=dict(default='static', choices=SUPPORTED_TYPES),
            addrobj=dict(required=True),
            temporary=dict(default=False, type='bool'),
            state=dict(
                default='present', choices=['absent', 'present', 'up', 'down', 'enabled', 'disabled', 'refreshed']),
            wait=dict(default=60, type='int'),
        ),
        mutually_exclusive=[
            ('address', 'wait'),
        ],
        supports_check_mode=True
    )

    addr = Addr(module)

    rc = None
    out = ''
    err = ''
    result = {}
    result['addrobj'] = addr.addrobj
    result['state'] = addr.state
    result['temporary'] = addr.temporary
    result['addrtype'] = addr.addrtype

    if addr.addrtype == 'static' and addr.address:
        if addr.is_cidr_notation() and addr.is_valid_address():
            result['address'] = addr.address
        else:
            module.fail_json(msg='Invalid IP address: %s' % addr.address)

    if addr.addrtype == 'dhcp' and addr.wait:
        result['wait'] = addr.wait

    if addr.state == 'absent':
        if addr.addrobj_exists():
            if module.check_mode:
                module.exit_json(changed=True)

            (rc, out, err) = addr.delete_addr()
            if rc != 0:
                module.fail_json(msg='Error while deleting addrobj: "%s"' % err,
                                 addrobj=addr.addrobj,
                                 stderr=err,
                                 rc=rc)

    elif addr.state == 'present':
        if not addr.addrobj_exists():
            if module.check_mode:
                module.exit_json(changed=True)

            (rc, out, err) = addr.create_addr()
            if rc != 0:
                module.fail_json(msg='Error while configuring IP address: "%s"' % err,
                                 addrobj=addr.addrobj,
                                 addr=addr.address,
                                 stderr=err,
                                 rc=rc)

    elif addr.state == 'up':
        if addr.addrobj_exists():
            if module.check_mode:
                module.exit_json(changed=True)

            (rc, out, err) = addr.up_addr()
            if rc != 0:
                module.fail_json(msg='Error while bringing IP address up: "%s"' % err,
                                 addrobj=addr.addrobj,
                                 stderr=err,
                                 rc=rc)

    elif addr.state == 'down':
        if addr.addrobj_exists():
            if module.check_mode:
                module.exit_json(changed=True)

            (rc, out, err) = addr.down_addr()
            if rc != 0:
                module.fail_json(msg='Error while bringing IP address down: "%s"' % err,
                                 addrobj=addr.addrobj,
                                 stderr=err,
                                 rc=rc)

    elif addr.state == 'refreshed':
        if addr.addrobj_exists():
            if addr.is_dhcp():
                if module.check_mode:
                    module.exit_json(changed=True)

                (rc, out, err) = addr.refresh_addr()
                if rc != 0:
                    module.fail_json(msg='Error while refreshing IP address: "%s"' % err,
                                     addrobj=addr.addrobj,
                                     stderr=err,
                                     rc=rc)
            else:
                module.fail_json(msg='state "refreshed" cannot be used with "%s" addrtype' % addr.addrtype,
                                 addrobj=addr.addrobj,
                                 stderr=err,
                                 rc=1)

    elif addr.state == 'enabled':
        if addr.addrobj_exists():
            if module.check_mode:
                module.exit_json(changed=True)

            (rc, out, err) = addr.enable_addr()
            if rc != 0:
                module.fail_json(msg='Error while enabling IP address: "%s"' % err,
                                 addrobj=addr.addrobj,
                                 stderr=err,
                                 rc=rc)

    elif addr.state == 'disabled':
        if addr.addrobj_exists():
            if module.check_mode:
                module.exit_json(changed=True)

            (rc, out, err) = addr.disable_addr()
            if rc != 0:
                module.fail_json(msg='Error while disabling IP address: "%s"' % err,
                                 addrobj=addr.addrobj,
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
