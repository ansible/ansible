#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: bigip_gtm_datacenter
short_description: Manage Datacenter configuration in BIG-IP
description:
  - Manage BIG-IP data center configuration. A data center defines the location
    where the physical network components reside, such as the server and link
    objects that share the same subnet on the network. This module is able to
    manipulate the data center definitions in a BIG-IP.
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
      - Deprecated in 2.4. Use C(state) and either C(enabled) or C(disabled)
        instead.
    choices:
      - yes
      - no
  location:
    description:
      - The location of the data center.
  name:
    description:
      - The name of the data center.
    required: True
  state:
    description:
      - The virtual address state. If C(absent), an attempt to delete the
        virtual address will be made. This will only succeed if this
        virtual address is not in use by a virtual server. C(present) creates
        the virtual address and enables it. If C(enabled), enable the virtual
        address if it exists. If C(disabled), create the virtual address if
        needed, and set state to C(disabled).
    required: False
    default: present
    choices:
      - present
      - absent
      - enabled
      - disabled
notes:
  - Requires the f5-sdk Python package on the host. This is as easy as
    pip install f5-sdk.
extends_documentation_fragment: f5
requirements:
  - f5-sdk
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create data center "New York"
  bigip_gtm_datacenter:
    server: lb.mydomain.com
    user: admin
    password: secret
    name: New York
    location: 222 West 23rd
  delegate_to: localhost
'''

RETURN = r'''
contact:
  description: The contact that was set on the datacenter.
  returned: changed
  type: string
  sample: admin@root.local
description:
  description: The description that was set for the datacenter.
  returned: changed
  type: string
  sample: Datacenter in NYC
enabled:
  description: Whether the datacenter is enabled or not
  returned: changed
  type: bool
  sample: true
location:
  description: The location that is set for the datacenter.
  returned: changed
  type: string
  sample: 222 West 23rd
'''

from ansible.module_utils.parsing.convert_bool import BOOLEANS_TRUE
from ansible.module_utils.parsing.convert_bool import BOOLEANS_FALSE
from ansible.module_utils.f5_utils import AnsibleF5Client
from ansible.module_utils.f5_utils import AnsibleF5Parameters
from ansible.module_utils.f5_utils import HAS_F5SDK
from ansible.module_utils.f5_utils import F5ModuleError

try:
    from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
except ImportError:
    HAS_F5SDK = False


class Parameters(AnsibleF5Parameters):
    api_map = {}

    updatables = [
        'location', 'description', 'contact',

        # TODO: Remove this method in v2.5
        'enabled'
    ]

    returnables = [
        'location', 'description', 'contact',

        # TODO: Remove this method in v2.5
        'enabled'
    ]

    api_attributes = [
        'enabled', 'location', 'description', 'contact'
    ]

    @property
    def disabled(self):
        if self._values['state'] == 'disabled':
            return True
        # TODO: Remove this method in v2.5
        elif self._values['disabled'] in BOOLEANS_TRUE:
            return True
        # TODO: Remove this method in v2.5
        elif self._values['disabled'] in BOOLEANS_FALSE:
            return False
        # TODO: Remove this method in v2.5
        elif self._values['enabled'] in BOOLEANS_FALSE:
            return True
        # TODO: Remove this method in v2.5
        elif self._values['enabled'] in BOOLEANS_TRUE:
            return False
        elif self._values['state'] == 'enabled':
            return False
        else:
            return None

    @property
    def enabled(self):
        if self._values['state'] == 'enabled':
            return True
        # TODO: Remove this method in v2.5
        elif self._values['enabled'] in BOOLEANS_TRUE:
            return True
        # TODO: Remove this method in v2.5
        elif self._values['enabled'] in BOOLEANS_FALSE:
            return False
        # TODO: Remove this method in v2.5
        elif self._values['disabled'] in BOOLEANS_FALSE:
            return True
        # TODO: Remove this method in v2.5
        elif self._values['disabled'] in BOOLEANS_TRUE:
            return False
        elif self._values['state'] == 'disabled':
            return False
        else:
            return None

    @property
    def state(self):
        if self.enabled and self._values['state'] != 'present':
            return 'enabled'
        elif self.disabled and self._values['state'] != 'present':
            return 'disabled'
        else:
            return self._values['state']

    # TODO: Remove this method in v2.5
    @state.setter
    def state(self, value):
        self._values['state'] = value

        # Only do this if not using legacy params
        if self._values['enabled'] is None:
            if self._values['state'] in ['enabled', 'present']:
                self._values['enabled'] = True
                self._values['disabled'] = False
            elif self._values['state'] == 'disabled':
                self._values['enabled'] = False
                self._values['disabled'] = True
        else:
            if self._values['__warnings'] is None:
                self._values['__warnings'] = []
            self._values['__warnings'].append(
                dict(
                    msg="Usage of the 'enabled' parameter is deprecated",
                    version='2.4'
                )
            )

    def to_return(self):
        result = {}
        for returnable in self.returnables:
            result[returnable] = getattr(self, returnable)
        result = self._filter_params(result)
        return result

    def api_params(self):
        result = {}
        for api_attribute in self.api_attributes:
            if api_attribute in self.api_map:
                result[api_attribute] = getattr(
                    self, self.api_map[api_attribute])
            else:
                result[api_attribute] = getattr(self, api_attribute)
        result = self._filter_params(result)
        return result


class Changes(Parameters):
    @property
    def enabled(self):
        if self._values['enabled'] in BOOLEANS_TRUE:
            return True
        else:
            return False


class ModuleManager(object):
    def __init__(self, client):
        self.client = client
        self.have = None
        self.want = Parameters(self.client.module.params)
        self.changes = Changes()

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = Changes(changed)

    def _update_changed_options(self):
        changed = {}
        for key in Parameters.updatables:
            if getattr(self.want, key) is not None:
                attr1 = getattr(self.want, key)
                attr2 = getattr(self.have, key)
                if attr1 != attr2:
                    changed[key] = attr1
        if changed:
            self.changes = Changes(changed)
            return True
        return False

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        try:
            if state in ['present', 'enabled', 'disabled']:
                changed = self.present()
            elif state == "absent":
                changed = self.absent()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        changes = self.changes.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations()
        return result

    def _announce_deprecations(self):
        warnings = []
        if self.want:
            warnings += self.want._values.get('__warnings', [])
        if self.have:
            warnings += self.have._values.get('__warnings', [])
        for warning in warnings:
            self.client.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def absent(self):
        changed = False
        if self.exists():
            changed = self.remove()
        return changed

    def read_current_from_device(self):
        resource = self.client.api.tm.gtm.datacenters.datacenter.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result = resource.attrs
        return Parameters(result)

    def exists(self):
        result = self.client.api.tm.gtm.datacenters.datacenter.exists(
            name=self.want.name,
            partition=self.want.partition
        )
        return result

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.client.check_mode:
            return True
        self.update_on_device()
        return True

    def update_on_device(self):
        params = self.want.api_params()
        resource = self.client.api.tm.gtm.datacenters.datacenter.load(
            name=self.want.name,
            partition=self.want.partition
        )
        resource.modify(**params)

    def create(self):
        self._set_changed_options()
        if self.client.check_mode:
            return True
        self.create_on_device()
        if self.exists():
            return True
        else:
            raise F5ModuleError("Failed to create the datacenter")

    def create_on_device(self):
        params = self.want.api_params()
        self.client.api.tm.gtm.datacenters.datacenter.create(
            name=self.want.name,
            partition=self.want.partition,
            **params
        )

    def remove(self):
        if self.client.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the datacenter")
        return True

    def remove_from_device(self):
        resource = self.client.api.tm.gtm.datacenters.datacenter.load(
            name=self.want.name,
            partition=self.want.partition
        )
        resource.delete()


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        self.argument_spec = dict(
            contact=dict(),
            description=dict(),
            enabled=dict(
                type='bool',
            ),
            location=dict(),
            name=dict(required=True),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent', 'disabled', 'enabled']
            )
        )
        self.f5_product_name = 'bigip'


def main():
    if not HAS_F5SDK:
        raise F5ModuleError("The python f5-sdk module is required")

    spec = ArgumentSpec()

    client = AnsibleF5Client(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        f5_product_name=spec.f5_product_name
    )

    try:
        mm = ModuleManager(client)
        results = mm.exec_module()
        client.module.exit_json(**results)
    except F5ModuleError as e:
        client.module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
