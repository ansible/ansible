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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: bigip_gtm_datacenter
short_description: Manage Datacenter configuration in BIG-IP
description:
  - Manage BIG-IP data center configuration. A data center defines the location
    where the physical network components reside, such as the server and link
    objects that share the same subnet on the network. This module is able to
    manipulate the data center definitions in a BIG-IP
version_added: "2.2"
options:
  contact:
    description:
      - The name of the contact for the data center.
  description:
    description:
      - The description of the data center.
  enabled:
    description:
      - Whether the data center should be enabled. At least one of C(state) and
        C(enabled) are required.
    choices:
      - yes
      - no
  location:
    description:
      - The location of the data center.
  name:
    description:
      - The name of the data center.
    required: true
  state:
    description:
      - The state of the datacenter on the BIG-IP. When C(present), guarantees
        that the data center exists. When C(absent) removes the data center
        from the BIG-IP. C(enabled) will enable the data center and C(disabled)
        will ensure the data center is disabled. At least one of state and
        enabled are required.
    choices:
      - present
      - absent
notes:
  - Requires the f5-sdk Python package on the host. This is as easy as
    pip install f5-sdk.
extends_documentation_fragment: f5
requirements:
  - f5-sdk
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = '''
- name: Create data center "New York"
  bigip_gtm_datacenter:
      server: "big-ip"
      name: "New York"
      location: "222 West 23rd"
  delegate_to: localhost
'''

RETURN = '''
contact:
    description: The contact that was set on the datacenter
    returned: changed
    type: string
    sample: "admin@root.local"
description:
    description: The description that was set for the datacenter
    returned: changed
    type: string
    sample: "Datacenter in NYC"
enabled:
    description: Whether the datacenter is enabled or not
    returned: changed
    type: bool
    sample: true
location:
    description: The location that is set for the datacenter
    returned: changed
    type: string
    sample: "222 West 23rd"
name:
    description: Name of the datacenter being manipulated
    returned: changed
    type: string
    sample: "foo"
'''

try:
    from f5.bigip import ManagementRoot
    from icontrol.session import iControlUnexpectedHTTPError
    HAS_F5SDK = True
except ImportError:
    HAS_F5SDK = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import camel_dict_to_snake_dict
from ansible.module_utils.f5_utils import F5ModuleError, f5_argument_spec


class BigIpGtmDatacenter(object):
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

    def create(self):
        params = dict()

        check_mode = self.params['check_mode']
        contact = self.params['contact']
        description = self.params['description']
        location = self.params['location']
        name = self.params['name']
        partition = self.params['partition']
        enabled = self.params['enabled']

        # Specifically check for None because a person could supply empty
        # values which would technically still be valid
        if contact is not None:
            params['contact'] = contact

        if description is not None:
            params['description'] = description

        if location is not None:
            params['location'] = location

        if enabled is not None:
            params['enabled'] = True
        else:
            params['disabled'] = False

        params['name'] = name
        params['partition'] = partition

        self.cparams = camel_dict_to_snake_dict(params)
        if check_mode:
            return True

        d = self.api.tm.gtm.datacenters.datacenter
        d.create(**params)

        if not self.exists():
            raise F5ModuleError("Failed to create the datacenter")
        return True

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
        r = self.api.tm.gtm.datacenters.datacenter.load(
            name=name,
            partition=partition
        )

        if hasattr(r, 'servers'):
            # Deliberately using sets to suppress duplicates
            p['servers'] = set([str(x) for x in r.servers])
        if hasattr(r, 'contact'):
            p['contact'] = str(r.contact)
        if hasattr(r, 'location'):
            p['location'] = str(r.location)
        if hasattr(r, 'description'):
            p['description'] = str(r.description)
        if r.enabled:
            p['enabled'] = True
        else:
            p['enabled'] = False
        p['name'] = name
        return p

    def update(self):
        changed = False
        params = dict()
        current = self.read()

        check_mode = self.params['check_mode']
        contact = self.params['contact']
        description = self.params['description']
        location = self.params['location']
        name = self.params['name']
        partition = self.params['partition']
        enabled = self.params['enabled']

        if contact is not None:
            if 'contact' in current:
                if contact != current['contact']:
                    params['contact'] = contact
            else:
                params['contact'] = contact

        if description is not None:
            if 'description' in current:
                if description != current['description']:
                    params['description'] = description
            else:
                params['description'] = description

        if location is not None:
            if 'location' in current:
                if location != current['location']:
                    params['location'] = location
            else:
                params['location'] = location

        if enabled is not None:
            if current['enabled'] != enabled:
                if enabled is True:
                    params['enabled'] = True
                    params['disabled'] = False
                else:
                    params['disabled'] = True
                    params['enabled'] = False

        if params:
            changed = True
            if check_mode:
                return changed
            self.cparams = camel_dict_to_snake_dict(params)
        else:
            return changed

        r = self.api.tm.gtm.datacenters.datacenter.load(
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

        dc = self.api.tm.gtm.datacenters.datacenter.load(**params)
        dc.delete()

        if self.exists():
            raise F5ModuleError("Failed to delete the datacenter")
        return True

    def present(self):
        changed = False

        if self.exists():
            changed = self.update()
        else:
            changed = self.create()

        return changed

    def absent(self):
        changed = False

        if self.exists():
            changed = self.delete()

        return changed

    def exists(self):
        name = self.params['name']
        partition = self.params['partition']

        return self.api.tm.gtm.datacenters.datacenter.exists(
            name=name,
            partition=partition
        )

    def flush(self):
        result = dict()
        state = self.params['state']
        enabled = self.params['enabled']

        if state is None and enabled is None:
            raise F5ModuleError("Neither 'state' nor 'enabled' set")

        try:
            if state == "present":
                changed = self.present()

                # Ensure that this field is not returned to the user since it
                # is not a valid parameter to the module.
                if 'disabled' in self.cparams:
                    del self.cparams['disabled']
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
        contact=dict(required=False, default=None),
        description=dict(required=False, default=None),
        enabled=dict(required=False, type='bool', default=None),
        location=dict(required=False, default=None),
        name=dict(required=True)
    )
    argument_spec.update(meta_args)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    try:
        obj = BigIpGtmDatacenter(check_mode=module.check_mode, **module.params)
        result = obj.flush()

        module.exit_json(**result)
    except F5ModuleError as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
