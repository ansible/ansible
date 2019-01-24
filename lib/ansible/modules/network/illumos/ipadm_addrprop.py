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
module: ipadm_addrprop
short_description: Manage IP address properties on Solaris/illumos systems.
description:
    - Modify IP address properties on Solaris/illumos systems.
version_added: "2.3"
author: Adam Števko (@xen0l)
options:
    addrobj:
        description:
            - Specifies the address object we want to manage.
        required: true
        aliases: [nic, interface]
    property:
        description:
            - Specifies the name of the address property we want to manage.
        required: true
        aliases: [name]
    value:
        description:
            - Specifies the value we want to set for the address property.
        required: false
    temporary:
        description:
            - Specifies that the address property value is temporary.
              Temporary values do not persist across reboots.
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
- name: Mark address on addrobj as deprecated
  ipadm_addrprop: property=deprecated value=on addrobj=e1000g0/v6

- name: Set network prefix length for addrobj
  ipadm_addrprop: addrobj=bge0/v4 name=prefixlen value=26
'''

RETURN = '''
property:
    description: property name
    returned: always
    type: str
    sample: deprecated
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
value:
    description: property value
    returned: when value is provided
    type: str
    sample: 26
'''

from ansible.module_utils.basic import AnsibleModule


class AddrProp(object):

    def __init__(self, module):
        self.module = module

        self.addrobj = module.params['addrobj']
        self.property = module.params['property']
        self.value = module.params['value']
        self.temporary = module.params['temporary']
        self.state = module.params['state']

    def property_exists(self):
        cmd = [self.module.get_bin_path('ipadm')]

        cmd.append('show-addrprop')
        cmd.append('-p')
        cmd.append(self.property)
        cmd.append(self.addrobj)

        (rc, _, _) = self.module.run_command(cmd)

        if rc == 0:
            return True
        else:
            self.module.fail_json(msg='Unknown property "%s" on addrobj %s' %
                                  (self.property, self.addrobj),
                                  property=self.property,
                                  addrobj=self.addrobj)

    def property_is_modified(self):
        cmd = [self.module.get_bin_path('ipadm')]

        cmd.append('show-addrprop')
        cmd.append('-c')
        cmd.append('-o')
        cmd.append('current,default')
        cmd.append('-p')
        cmd.append(self.property)
        cmd.append(self.addrobj)

        (rc, out, _) = self.module.run_command(cmd)

        out = out.rstrip()
        (value, default) = out.split(':')

        if rc == 0 and value == default:
            return True
        else:
            return False

    def property_is_set(self):
        cmd = [self.module.get_bin_path('ipadm')]

        cmd.append('show-addrprop')
        cmd.append('-c')
        cmd.append('-o')
        cmd.append('current')
        cmd.append('-p')
        cmd.append(self.property)
        cmd.append(self.addrobj)

        (rc, out, _) = self.module.run_command(cmd)

        out = out.rstrip()

        if rc == 0 and self.value == out:
            return True
        else:
            return False

    def set_property(self):
        cmd = [self.module.get_bin_path('ipadm')]

        cmd.append('set-addrprop')

        if self.temporary:
            cmd.append('-t')

        cmd.append('-p')
        cmd.append(self.property + '=' + self.value)
        cmd.append(self.addrobj)

        return self.module.run_command(cmd)

    def reset_property(self):
        cmd = [self.module.get_bin_path('ipadm')]

        cmd.append('reset-addrprop')

        if self.temporary:
            cmd.append('-t')

        cmd.append('-p')
        cmd.append(self.property)
        cmd.append(self.addrobj)

        return self.module.run_command(cmd)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            addrobj=dict(required=True, default=None, aliases=['nic', 'interface']),
            property=dict(required=True, aliases=['name']),
            value=dict(required=False),
            temporary=dict(default=False, type='bool'),
            state=dict(
                default='present', choices=['absent', 'present', 'reset']),
        ),
        supports_check_mode=True
    )

    addrprop = AddrProp(module)

    rc = None
    out = ''
    err = ''
    result = {}
    result['property'] = addrprop.property
    result['addrobj'] = addrprop.addrobj
    result['state'] = addrprop.state
    result['temporary'] = addrprop.temporary
    if addrprop.value:
        result['value'] = addrprop.value

    if addrprop.state == 'absent' or addrprop.state == 'reset':
        if addrprop.property_exists():
            if not addrprop.property_is_modified():
                if module.check_mode:
                    module.exit_json(changed=True)
                (rc, out, err) = addrprop.reset_property()
                if rc != 0:
                    module.fail_json(property=addrprop.property,
                                     addrobj=addrprop.addrobj,
                                     msg=err,
                                     rc=rc)

    elif addrprop.state == 'present':
        if addrprop.value is None:
            module.fail_json(msg='Value is mandatory with state "present"')

        if addrprop.property_exists():
            if not addrprop.property_is_set():
                if module.check_mode:
                    module.exit_json(changed=True)

                (rc, out, err) = addrprop.set_property()
                if rc != 0:
                    module.fail_json(property=addrprop.property,
                                     addrobj=addrprop.addrobj,
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
