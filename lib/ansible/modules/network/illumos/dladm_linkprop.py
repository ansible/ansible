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
module: dladm_linkprop
short_description: Manage link properties on Solaris/illumos systems.
description:
    - Set / reset link properties on Solaris/illumos systems.
version_added: "2.3"
author: Adam Števko (@xen0l)
options:
    link:
        description:
            - Link interface name.
        required: true
        aliases: [ "nic", "interface" ]
    property:
        description:
            - Specifies the name of the property we want to manage.
        required: true
        aliases: [ "name" ]
    value:
        description:
            - Specifies the value we want to set for the link property.
        required: false
    temporary:
        description:
            - Specifies that lin property configuration is temporary. Temporary
              link property configuration does not persist across reboots.
        required: false
        type: bool
        default: false
    state:
        description:
            - Set or reset the property value.
        required: false
        default: "present"
        choices: [ "present", "absent", "reset" ]
'''

EXAMPLES = '''
- name: Set 'maxbw' to 100M on e1000g1
  dladm_linkprop: name=e1000g1 property=maxbw value=100M state=present

- name: Set 'mtu' to 9000 on e1000g1
  dladm_linkprop: name=e1000g1 property=mtu value=9000

- name: Reset 'mtu' property on e1000g1
  dladm_linkprop: name=e1000g1 property=mtu state=reset
'''

RETURN = '''
property:
    description: property name
    returned: always
    type: str
    sample: mtu
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
link:
    description: link name
    returned: always
    type: str
    sample: e100g0
value:
    description: property value
    returned: always
    type: str
    sample: 9000
'''

from ansible.module_utils.basic import AnsibleModule


class LinkProp(object):

    def __init__(self, module):
        self.module = module

        self.link = module.params['link']
        self.property = module.params['property']
        self.value = module.params['value']
        self.temporary = module.params['temporary']
        self.state = module.params['state']

        self.dladm_bin = self.module.get_bin_path('dladm', True)

    def property_exists(self):
        cmd = [self.dladm_bin]

        cmd.append('show-linkprop')
        cmd.append('-p')
        cmd.append(self.property)
        cmd.append(self.link)

        (rc, _, _) = self.module.run_command(cmd)

        if rc == 0:
            return True
        else:
            self.module.fail_json(msg='Unknown property "%s" on link %s' %
                                  (self.property, self.link),
                                  property=self.property,
                                  link=self.link)

    def property_is_modified(self):
        cmd = [self.dladm_bin]

        cmd.append('show-linkprop')
        cmd.append('-c')
        cmd.append('-o')
        cmd.append('value,default')
        cmd.append('-p')
        cmd.append(self.property)
        cmd.append(self.link)

        (rc, out, _) = self.module.run_command(cmd)

        out = out.rstrip()
        (value, default) = out.split(':')

        if rc == 0 and value == default:
            return True
        else:
            return False

    def property_is_readonly(self):
        cmd = [self.dladm_bin]

        cmd.append('show-linkprop')
        cmd.append('-c')
        cmd.append('-o')
        cmd.append('perm')
        cmd.append('-p')
        cmd.append(self.property)
        cmd.append(self.link)

        (rc, out, _) = self.module.run_command(cmd)

        out = out.rstrip()

        if rc == 0 and out == 'r-':
            return True
        else:
            return False

    def property_is_set(self):
        cmd = [self.dladm_bin]

        cmd.append('show-linkprop')
        cmd.append('-c')
        cmd.append('-o')
        cmd.append('value')
        cmd.append('-p')
        cmd.append(self.property)
        cmd.append(self.link)

        (rc, out, _) = self.module.run_command(cmd)

        out = out.rstrip()

        if rc == 0 and self.value == out:
            return True
        else:
            return False

    def set_property(self):
        cmd = [self.dladm_bin]

        cmd.append('set-linkprop')

        if self.temporary:
            cmd.append('-t')

        cmd.append('-p')
        cmd.append(self.property + '=' + self.value)
        cmd.append(self.link)

        return self.module.run_command(cmd)

    def reset_property(self):
        cmd = [self.dladm_bin]

        cmd.append('reset-linkprop')

        if self.temporary:
            cmd.append('-t')

        cmd.append('-p')
        cmd.append(self.property)
        cmd.append(self.link)

        return self.module.run_command(cmd)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            link=dict(required=True, default=None, type='str', aliases=['nic', 'interface']),
            property=dict(required=True, type='str', aliases=['name']),
            value=dict(required=False, type='str'),
            temporary=dict(default=False, type='bool'),
            state=dict(
                default='present', choices=['absent', 'present', 'reset']),
        ),
        required_if=[
            ['state', 'present', ['value']],
        ],

        supports_check_mode=True
    )

    linkprop = LinkProp(module)

    rc = None
    out = ''
    err = ''
    result = {}
    result['property'] = linkprop.property
    result['link'] = linkprop.link
    result['state'] = linkprop.state
    if linkprop.value:
        result['value'] = linkprop.value

    if linkprop.state == 'absent' or linkprop.state == 'reset':
        if linkprop.property_exists():
            if not linkprop.property_is_modified():
                if module.check_mode:
                    module.exit_json(changed=True)
                (rc, out, err) = linkprop.reset_property()
                if rc != 0:
                    module.fail_json(property=linkprop.property,
                                     link=linkprop.link,
                                     msg=err,
                                     rc=rc)

    elif linkprop.state == 'present':
        if linkprop.property_exists():
            if not linkprop.property_is_readonly():
                if not linkprop.property_is_set():
                    if module.check_mode:
                        module.exit_json(changed=True)

                    (rc, out, err) = linkprop.set_property()
                    if rc != 0:
                        module.fail_json(property=linkprop.property,
                                         link=linkprop.link,
                                         msg=err,
                                         rc=rc)
            else:
                module.fail_json(msg='Property "%s" is read-only!' % (linkprop.property),
                                 property=linkprop.property,
                                 link=linkprop.link)

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
