#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2016 F5 Networks Inc.
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: bigip_vlan
short_description: Manage VLANs on a BIG-IP system
description:
  - Manage VLANs on a BIG-IP system
version_added: "2.2"
options:
  description:
    description:
      - The description to give to the VLAN.
  tagged_interfaces:
    description:
      - Specifies a list of tagged interfaces and trunks that you want to
        configure for the VLAN. Use tagged interfaces or trunks when
        you want to assign a single interface or trunk to multiple VLANs.
    required: false
    aliases:
      - tagged_interface
  untagged_interfaces:
    description:
      - Specifies a list of untagged interfaces and trunks that you want to
        configure for the VLAN.
    required: false
    aliases:
      - untagged_interface
  name:
    description:
      - The VLAN to manage. If the special VLAN C(ALL) is specified with
        the C(state) value of C(absent) then all VLANs will be removed.
    required: true
  state:
    description:
      - The state of the VLAN on the system. When C(present), guarantees
        that the VLAN exists with the provided attributes. When C(absent),
        removes the VLAN from the system.
    required: false
    default: present
    choices:
      - absent
      - present
  tag:
    description:
      - Tag number for the VLAN. The tag number can be any integer between 1
        and 4094. The system automatically assigns a tag number if you do not
        specify a value.
notes:
  - Requires the f5-sdk Python package on the host. This is as easy as pip
    install f5-sdk.
  - Requires BIG-IP versions >= 12.0.0
extends_documentation_fragment: f5
requirements:
  - f5-sdk
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = '''
- name: Create VLAN
  bigip_vlan:
      name: "net1"
      password: "secret"
      server: "lb.mydomain.com"
      user: "admin"
      validate_certs: "no"
  delegate_to: localhost

- name: Set VLAN tag
  bigip_vlan:
      name: "net1"
      password: "secret"
      server: "lb.mydomain.com"
      tag: "2345"
      user: "admin"
      validate_certs: "no"
  delegate_to: localhost

- name: Add VLAN 2345 as tagged to interface 1.1
  bigip_vlan:
      tagged_interface: 1.1
      name: "net1"
      password: "secret"
      server: "lb.mydomain.com"
      tag: "2345"
      user: "admin"
      validate_certs: "no"
  delegate_to: localhost

- name: Add VLAN 1234 as tagged to interfaces 1.1 and 1.2
  bigip_vlan:
      tagged_interfaces:
          - 1.1
          - 1.2
      name: "net1"
      password: "secret"
      server: "lb.mydomain.com"
      tag: "1234"
      user: "admin"
      validate_certs: "no"
  delegate_to: localhost
'''

RETURN = '''
description:
    description: The description set on the VLAN
    returned: changed
    type: string
    sample: foo VLAN
interfaces:
    description: Interfaces that the VLAN is assigned to
    returned: changed
    type: list
    sample: ['1.1','1.2']
name:
    description: The name of the VLAN
    returned: changed
    type: string
    sample: net1
partition:
    description: The partition that the VLAN was created on
    returned: changed
    type: string
    sample: Common
tag:
    description: The ID of the VLAN
    returned: changed
    type: int
    sample: 2345
'''

try:
    from f5.bigip import ManagementRoot
    from icontrol.session import iControlUnexpectedHTTPError
    HAS_F5SDK = True
except ImportError:
    HAS_F5SDK = False


class BigIpVlan(object):
    def __init__(self, *args, **kwargs):
        if not HAS_F5SDK:
            raise F5ModuleError("The python f5-sdk module is required")

        # The params that change in the module
        self.cparams = dict()

        # Stores the params that are sent to the module
        self.params = kwargs
        self.api = ManagementRoot(kwargs['server'],
                                  kwargs['user'],
                                  kwargs['password'],
                                  port=kwargs['server_port'])

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def absent(self):
        changed = False

        if self.exists():
            changed = self.delete()

        return changed

    def read(self):
        """Read information and transform it

        The values that are returned by BIG-IP in the f5-sdk can have encoding
        attached to them as well as be completely missing in some cases.

        Therefore, this method will transform the data from the BIG-IP into a
        format that is more easily consumable by the rest of the class and the
        parameters that are supported by the module.
        """
        p = dict()
        name = self.params['name']
        partition = self.params['partition']
        r = self.api.tm.net.vlans.vlan.load(
            name=name,
            partition=partition
        )
        ifcs = r.interfaces_s.get_collection()
        if hasattr(r, 'tag'):
            p['tag'] = int(r.tag)
        if hasattr(r, 'description'):
            p['description'] = str(r.description)
        if len(ifcs) is not 0:
            untagged = []
            tagged = []
            for x in ifcs:
                if hasattr(x, 'tagged'):
                    tagged.append(str(x.name))
                elif hasattr(x, 'untagged'):
                    untagged.append(str(x.name))
            if untagged:
                p['untagged_interfaces'] = list(set(untagged))
            if tagged:
                p['tagged_interfaces'] = list(set(tagged))
        p['name'] = name
        return p

    def create(self):
        params = dict()

        check_mode = self.params['check_mode']
        description = self.params['description']
        name = self.params['name']
        untagged_interfaces = self.params['untagged_interfaces']
        tagged_interfaces = self.params['tagged_interfaces']
        partition = self.params['partition']
        tag = self.params['tag']

        if tag is not None:
            params['tag'] = tag

        if untagged_interfaces is not None or tagged_interfaces is not None:
            tmp = []
            ifcs = self.api.tm.net.interfaces.get_collection()
            ifcs = [str(x.name) for x in ifcs]

            if len(ifcs) is 0:
                raise F5ModuleError(
                    'No interfaces were found'
                )

            pinterfaces = []
            if untagged_interfaces:
                interfaces = untagged_interfaces
            elif tagged_interfaces:
                interfaces = tagged_interfaces

            for ifc in interfaces:
                ifc = str(ifc)
                if ifc in ifcs:
                    pinterfaces.append(ifc)

            if tagged_interfaces:
                tmp = [dict(name=x, tagged=True) for x in pinterfaces]
            elif untagged_interfaces:
                tmp = [dict(name=x, untagged=True) for x in pinterfaces]

            if tmp:
                params['interfaces'] = tmp

        if description is not None:
            params['description'] = self.params['description']

        params['name'] = name
        params['partition'] = partition

        self.cparams = camel_dict_to_snake_dict(params)
        if check_mode:
            return True

        d = self.api.tm.net.vlans.vlan
        d.create(**params)

        if self.exists():
            return True
        else:
            raise F5ModuleError("Failed to create the VLAN")

    def update(self):
        changed = False
        params = dict()
        current = self.read()

        check_mode = self.params['check_mode']
        description = self.params['description']
        name = self.params['name']
        tag = self.params['tag']
        partition = self.params['partition']
        tagged_interfaces = self.params['tagged_interfaces']
        untagged_interfaces = self.params['untagged_interfaces']

        if untagged_interfaces is not None or tagged_interfaces is not None:
            ifcs = self.api.tm.net.interfaces.get_collection()
            ifcs = [str(x.name) for x in ifcs]

            if len(ifcs) is 0:
                raise F5ModuleError(
                    'No interfaces were found'
                )

            pinterfaces = []
            if untagged_interfaces:
                interfaces = untagged_interfaces
            elif tagged_interfaces:
                interfaces = tagged_interfaces

            for ifc in interfaces:
                ifc = str(ifc)
                if ifc in ifcs:
                    pinterfaces.append(ifc)
                else:
                    raise F5ModuleError(
                        'The specified interface "%s" was not found' % (ifc)
                    )

            if tagged_interfaces:
                tmp = [dict(name=x, tagged=True) for x in pinterfaces]
                if 'tagged_interfaces' in current:
                    if pinterfaces != current['tagged_interfaces']:
                        params['interfaces'] = tmp
                else:
                    params['interfaces'] = tmp
            elif untagged_interfaces:
                tmp = [dict(name=x, untagged=True) for x in pinterfaces]
                if 'untagged_interfaces' in current:
                    if pinterfaces != current['untagged_interfaces']:
                        params['interfaces'] = tmp
                else:
                    params['interfaces'] = tmp

        if description is not None:
            if 'description' in current:
                if description != current['description']:
                    params['description'] = description
            else:
                params['description'] = description

        if tag is not None:
            if 'tag' in current:
                if tag != current['tag']:
                    params['tag'] = tag
            else:
                params['tag'] = tag

        if params:
            changed = True
            params['name'] = name
            params['partition'] = partition
            if check_mode:
                return changed
            self.cparams = camel_dict_to_snake_dict(params)
        else:
            return changed

        r = self.api.tm.net.vlans.vlan.load(
            name=name,
            partition=partition
        )
        r.update(**params)
        r.refresh()

        return True

    def delete(self):
        params = dict()
        check_mode = self.params['check_mode']

        params['name'] = self.params['name']
        params['partition'] = self.params['partition']

        self.cparams = camel_dict_to_snake_dict(params)
        if check_mode:
            return True

        dc = self.api.tm.net.vlans.vlan.load(**params)
        dc.delete()

        if self.exists():
            raise F5ModuleError("Failed to delete the VLAN")
        return True

    def exists(self):
        name = self.params['name']
        partition = self.params['partition']
        return self.api.tm.net.vlans.vlan.exists(
            name=name,
            partition=partition
        )

    def flush(self):
        result = dict()
        state = self.params['state']

        try:
            if state == "present":
                changed = self.present()
            elif state == "absent":
                changed = self.absent()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        result.update(**self.cparams)
        result.update(dict(changed=changed))
        return result


def main():
    argument_spec = f5_argument_spec()

    meta_args = dict(
        description=dict(required=False, default=None),
        tagged_interfaces=dict(required=False, default=None, type='list', aliases=['tagged_interface']),
        untagged_interfaces=dict(required=False, default=None, type='list', aliases=['untagged_interface']),
        name=dict(required=True),
        tag=dict(required=False, default=None, type='int')
    )
    argument_spec.update(meta_args)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ['tagged_interfaces', 'untagged_interfaces']
        ]
    )

    try:
        obj = BigIpVlan(check_mode=module.check_mode, **module.params)
        result = obj.flush()

        module.exit_json(**result)
    except F5ModuleError as e:
        module.fail_json(msg=str(e))

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import camel_dict_to_snake_dict
from ansible.module_utils.f5 import *

if __name__ == '__main__':
    main()
