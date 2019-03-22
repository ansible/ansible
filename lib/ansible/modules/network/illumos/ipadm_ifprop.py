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
module: ipadm_ifprop
short_description: Manage IP interface properties on Solaris/illumos systems.
description:
    - Modify IP interface properties on Solaris/illumos systems.
version_added: "2.3"
author: Adam Števko (@xen0l)
options:
    interface:
        description:
            - Specifies the IP interface we want to manage.
        required: true
        aliases: [nic]
    protocol:
        description:
            - Specifies the procotol for which we want to manage properties.
        required: true
    property:
        description:
            - Specifies the name of the property we want to manage.
        required: true
        aliases: [name]
    value:
        description:
            - Specifies the value we want to set for the property.
        required: false
    temporary:
        description:
            - Specifies that the property value is temporary. Temporary
              property values do not persist across reboots.
        required: false
        default: false
        type: bool
    state:
        description:
            - Set or reset the property value.
        required: false
        default: present
        choices: [ "present", "absent", "reset" ]
'''

EXAMPLES = '''
- name: Allow forwarding of IPv4 packets on network interface e1000g0
  ipadm_ifprop: protocol=ipv4 property=forwarding value=on interface=e1000g0

- name: Temporarily reset IPv4 forwarding property on network interface e1000g0
  ipadm_ifprop: protocol=ipv4 interface=e1000g0  temporary=true property=forwarding state=reset

- name: Configure IPv6 metric on network interface e1000g0
  ipadm_ifprop: protocol=ipv6 nic=e1000g0 name=metric value=100

- name: Set IPv6 MTU on network interface bge0
  ipadm_ifprop: interface=bge0 name=mtu value=1280 protocol=ipv6
'''

RETURN = '''
protocol:
    description: property's protocol
    returned: always
    type: str
    sample: ipv4
property:
    description: property's name
    returned: always
    type: str
    sample: mtu
interface:
    description: interface name we want to set property on
    returned: always
    type: str
    sample: e1000g0
state:
    description: state of the target
    returned: always
    type: str
    sample: present
value:
    description: property's value
    returned: when value is provided
    type: str
    sample: 1280
'''

from ansible.module_utils.basic import AnsibleModule


SUPPORTED_PROTOCOLS = ['ipv4', 'ipv6']


class IfProp(object):

    def __init__(self, module):
        self.module = module

        self.interface = module.params['interface']
        self.protocol = module.params['protocol']
        self.property = module.params['property']
        self.value = module.params['value']
        self.temporary = module.params['temporary']
        self.state = module.params['state']

    def property_exists(self):
        cmd = [self.module.get_bin_path('ipadm')]

        cmd.append('show-ifprop')
        cmd.append('-p')
        cmd.append(self.property)
        cmd.append('-m')
        cmd.append(self.protocol)
        cmd.append(self.interface)

        (rc, _, _) = self.module.run_command(cmd)

        if rc == 0:
            return True
        else:
            self.module.fail_json(msg='Unknown %s property "%s" on IP interface %s' %
                                  (self.protocol, self.property, self.interface),
                                  protocol=self.protocol,
                                  property=self.property,
                                  interface=self.interface)

    def property_is_modified(self):
        cmd = [self.module.get_bin_path('ipadm')]

        cmd.append('show-ifprop')
        cmd.append('-c')
        cmd.append('-o')
        cmd.append('current,default')
        cmd.append('-p')
        cmd.append(self.property)
        cmd.append('-m')
        cmd.append(self.protocol)
        cmd.append(self.interface)

        (rc, out, _) = self.module.run_command(cmd)

        out = out.rstrip()
        (value, default) = out.split(':')

        if rc == 0 and value == default:
            return True
        else:
            return False

    def property_is_set(self):
        cmd = [self.module.get_bin_path('ipadm')]

        cmd.append('show-ifprop')
        cmd.append('-c')
        cmd.append('-o')
        cmd.append('current')
        cmd.append('-p')
        cmd.append(self.property)
        cmd.append('-m')
        cmd.append(self.protocol)
        cmd.append(self.interface)

        (rc, out, _) = self.module.run_command(cmd)

        out = out.rstrip()

        if rc == 0 and self.value == out:
            return True
        else:
            return False

    def set_property(self):
        cmd = [self.module.get_bin_path('ipadm')]

        cmd.append('set-ifprop')

        if self.temporary:
            cmd.append('-t')

        cmd.append('-p')
        cmd.append(self.property + "=" + self.value)
        cmd.append('-m')
        cmd.append(self.protocol)
        cmd.append(self.interface)

        return self.module.run_command(cmd)

    def reset_property(self):
        cmd = [self.module.get_bin_path('ipadm')]

        cmd.append('reset-ifprop')

        if self.temporary:
            cmd.append('-t')

        cmd.append('-p')
        cmd.append(self.property)
        cmd.append('-m')
        cmd.append(self.protocol)
        cmd.append(self.interface)

        return self.module.run_command(cmd)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            protocol=dict(required=True, choices=SUPPORTED_PROTOCOLS),
            property=dict(required=True, aliases=['name']),
            value=dict(required=False),
            temporary=dict(default=False, type='bool'),
            interface=dict(required=True, default=None, aliases=['nic']),
            state=dict(
                default='present', choices=['absent', 'present', 'reset']),
        ),
        supports_check_mode=True
    )

    ifprop = IfProp(module)

    rc = None
    out = ''
    err = ''
    result = {}
    result['protocol'] = ifprop.protocol
    result['property'] = ifprop.property
    result['interface'] = ifprop.interface
    result['state'] = ifprop.state
    if ifprop.value:
        result['value'] = ifprop.value

    if ifprop.state == 'absent' or ifprop.state == 'reset':
        if ifprop.property_exists():
            if not ifprop.property_is_modified():
                if module.check_mode:
                    module.exit_json(changed=True)
                (rc, out, err) = ifprop.reset_property()
                if rc != 0:
                    module.fail_json(protocol=ifprop.protocol,
                                     property=ifprop.property,
                                     interface=ifprop.interface,
                                     msg=err,
                                     rc=rc)

    elif ifprop.state == 'present':
        if ifprop.value is None:
            module.fail_json(msg='Value is mandatory with state "present"')

        if ifprop.property_exists():
            if not ifprop.property_is_set():
                if module.check_mode:
                    module.exit_json(changed=True)

                (rc, out, err) = ifprop.set_property()
                if rc != 0:
                    module.fail_json(protocol=ifprop.protocol,
                                     property=ifprop.property,
                                     interface=ifprop.interface,
                                     msg=err,
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
