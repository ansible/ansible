#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Adam Števko <adam.stevko@gmail.com>
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
#

DOCUMENTATION = '''
---
module: ipadm_prop
short_description: Manage protocol properties on Solaris/illumos systems.
description:
    - Modify protocol properties on Solaris/illumos systems.
version_added: "2.2"
author: Adam Števko (@xen0l)
options:
    protocol:
        description:
            - Specifies the procotol for which we want to manage properties.
        required: true
    property:
        description:
            - Specifies the name of property we want to manage.
        required: true
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
        choices: [ "true", "false" ]
    state:
        description:
            - Set or reset the property value.
        required: false
        default: present
        choices: [ "present", "absent", "reset" ]
'''

EXAMPLES = '''
# Set TCP receive buffer size
ipadm_prop: protocol=tcp property=recv_buf value=65536

# Reset UDP send buffer size to the default value
ipadm_prop: protocol=udp property=send_buf state=reset
'''

RETURN = '''
protocol:
    description: property's protocol
    returned: always
    type: string
    sample: "TCP"
property:
    description: name of the property
    returned: always
    type: string
    sample: "recv_maxbuf"
state:
    description: state of the target
    returned: always
    type: string
    sample: "present"
temporary:
    description: property's persistence
    returned: always
    type: boolean
    sample: "True"
value:
    description: value of the property
    returned: always
    type: int/string (depends on property)
    sample: 1024/never
'''

SUPPORTED_PROTOCOLS = ['ipv4', 'ipv6', 'icmp', 'tcp', 'udp', 'sctp']


class Prop(object):

    def __init__(self, module):
        self.module = module

        self.protocol = module.params['protocol']
        self.property = module.params['property']
        self.value = module.params['value']
        self.temporary = module.params['temporary']
        self.state = module.params['state']

    def property_exists(self):
        cmd = [self.module.get_bin_path('ipadm')]

        cmd.append('show-prop')
        cmd.append('-p')
        cmd.append(self.property)
        cmd.append(self.protocol)

        (rc, _, _) = self.module.run_command(cmd)

        if rc == 0:
            return True
        else:
            self.module.fail_json(msg='Unknown property "%s" for protocol %s' %
                                  (self.property, self.protocol),
                                  protocol=self.protocol,
                                  property=self.property)

    def property_is_modified(self):
        cmd = [self.module.get_bin_path('ipadm')]

        cmd.append('show-prop')
        cmd.append('-c')
        cmd.append('-o')
        cmd.append('current,default')
        cmd.append('-p')
        cmd.append(self.property)
        cmd.append(self.protocol)

        (rc, out, _) = self.module.run_command(cmd)

        out = out.rstrip()
        (value, default) = out.split(':')

        if rc == 0 and value == default:
            return True
        else:
            return False

    def property_is_set(self):
        cmd = [self.module.get_bin_path('ipadm')]

        cmd.append('show-prop')
        cmd.append('-c')
        cmd.append('-o')
        cmd.append('current')
        cmd.append('-p')
        cmd.append(self.property)
        cmd.append(self.protocol)

        (rc, out, _) = self.module.run_command(cmd)

        out = out.rstrip()

        if rc == 0 and self.value == out:
            return True
        else:
            return False

    def set_property(self):
        cmd = [self.module.get_bin_path('ipadm')]

        cmd.append('set-prop')

        if self.temporary:
            cmd.append('-t')

        cmd.append('-p')
        cmd.append(self.property + "=" + self.value)
        cmd.append(self.protocol)

        return self.module.run_command(cmd)

    def reset_property(self):
        cmd = [self.module.get_bin_path('ipadm')]

        cmd.append('reset-prop')

        if self.temporary:
            cmd.append('-t')

        cmd.append('-p')
        cmd.append(self.property)
        cmd.append(self.protocol)

        return self.module.run_command(cmd)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            protocol=dict(required=True, choices=SUPPORTED_PROTOCOLS),
            property=dict(required=True),
            value=dict(required=False),
            temporary=dict(default=False, type='bool'),
            state=dict(
                default='present', choices=['absent', 'present', 'reset']),
        ),
        supports_check_mode=True
    )

    prop = Prop(module)

    rc = None
    out = ''
    err = ''
    result = {}
    result['protocol'] = prop.protocol
    result['property'] = prop.property
    result['state'] = prop.state
    result['temporary'] = prop.temporary
    if prop.value:
        result['value'] = prop.value

    if prop.state == 'absent' or prop.state == 'reset':
        if prop.property_exists():
            if not prop.property_is_modified():
                if module.check_mode:
                    module.exit_json(changed=True)
                (rc, out, err) = prop.reset_property()
                if rc != 0:
                    module.fail_json(protocol=prop.protocol,
                                     property=prop.property,
                                     msg=err,
                                     rc=rc)

    elif prop.state == 'present':
        if prop.value is None:
            module.fail_json(msg='Value is mandatory with state "present"')

        if prop.property_exists():
            if not prop.property_is_set():
                if module.check_mode:
                    module.exit_json(changed=True)

                (rc, out, err) = prop.set_property()
                if rc != 0:
                    module.fail_json(protocol=prop.protocol,
                                     property=prop.property,
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


from ansible.module_utils.basic import *
main()
