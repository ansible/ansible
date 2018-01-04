#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: bigip_traffic_group
short_description: Manages traffic groups on BIG-IP
description:
  - Supports managing traffic groups and their attributes on a BIG-IP.
version_added: "2.5"
options:
  name:
    description:
      - The name of the traffic group.
    required: True
notes:
  - Requires the f5-sdk Python package on the host. This is as easy as
    C(pip install f5-sdk).
requirements:
  - f5-sdk >= 3.0.5
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create a traffic group
  bigip_traffic_group:
    name: foo
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
  delegate_to: localhost
'''

RETURN = r'''
# only common fields returned
'''


from ansible.module_utils.f5_utils import AnsibleF5Client
from ansible.module_utils.f5_utils import AnsibleF5Parameters
from ansible.module_utils.f5_utils import HAS_F5SDK
from ansible.module_utils.f5_utils import F5ModuleError
from ansible.module_utils.six import iteritems
from collections import defaultdict

try:
    from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
except ImportError:
    HAS_F5SDK = False


class Parameters(AnsibleF5Parameters):
    api_map = {

    }

    api_attributes = [

    ]

    returnables = [

    ]

    updatables = [

    ]

    def __init__(self, params=None):
        self._values = defaultdict(lambda: None)
        self._values['__warnings'] = []
        if params:
            self.update(params=params)

    def update(self, params=None):
        if params:
            for k, v in iteritems(params):
                if self.api_map is not None and k in self.api_map:
                    map_key = self.api_map[k]
                else:
                    map_key = k

                # Handle weird API parameters like `dns.proxy.__iter__` by
                # using a map provided by the module developer
                class_attr = getattr(type(self), map_key, None)
                if isinstance(class_attr, property):
                    # There is a mapped value for the api_map key
                    if class_attr.fset is None:
                        # If the mapped value does not have
                        # an associated setter
                        self._values[map_key] = v
                    else:
                        # The mapped value has a setter
                        setattr(self, map_key, v)
                else:
                    # If the mapped value is not a @property
                    self._values[map_key] = v

    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result

    def api_params(self):
        result = {}
        for api_attribute in self.api_attributes:
            if self.api_map is not None and api_attribute in self.api_map:
                result[api_attribute] = getattr(self, self.api_map[api_attribute])
            else:
                result[api_attribute] = getattr(self, api_attribute)
        result = self._filter_params(result)
        return result


class Changes(Parameters):
    pass


class Difference(object):
    def __init__(self, want, have=None):
        self.want = want
        self.have = have

    def compare(self, param):
        try:
            result = getattr(self, param)
            return result
        except AttributeError:
            return self.__default(param)

    def __default(self, param):
        attr1 = getattr(self.want, param)
        try:
            attr2 = getattr(self.have, param)
            if attr1 != attr2:
                return attr1
        except AttributeError:
            return attr1

    @property
    def partition(self):
        raise F5ModuleError(
            "Partition cannot be changed for a traffic group. Only /Common is allowed."
        )


class ModuleManager(object):
    def __init__(self, client):
        self.client = client
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
        """Sets the changed updatables when updating a resource

        A module needs to know what changed to determine whether to update
        a resource (or set of resources). This method accomplishes this by
        invoking the Difference engine code.

        Each parameter in the `Parameter` class' `updatables` array will be
        given to the Difference engine's `compare` method. This is done in the
        order the updatables are listed in the array.

        The `compare` method updates the `changes` dictionary if the following
        way,

        * If `None` is returned, a change will not be registered.
        * If a dictionary is returned, the `changes` dictionary will be updated
          with the values in what was returned.
        * Otherwise, the `changes` dictionary's key (the parameter being
          compared) will be set to the value that is returned by `compare`

        The dictionary behavior is in place to allow you to change the key
        that is set in the `changes` dictionary. There are frequently cases
        where there is not a clean API map that can be set, nor a way to
        otherwise allow you to change the attribute name of the resource being
        updated before it is sent off to the remote device. Using a dictionary
        return value of `compare` allows you to do this.

        Returns:
            bool: True when changes are present. False otherwise.
        """
        diff = Difference(self.want, self.have)
        updatables = Parameters.updatables
        changed = dict()
        for k in updatables:
            change = diff.compare(k)
            if change is None:
                continue
            else:
                if isinstance(change, dict):
                    changed.update(change)
                else:
                    changed[k] = change
        if changed:
            self.changes = Changes(changed)
            return True
        return False

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        try:
            if state == "present":
                changed = self.present()
            elif state == "absent":
                changed = self.absent()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        changes = self.changes.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        return result

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.client.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def exists(self):
        result = self.client.api.tm.cm.traffic_groups.traffic_group.exists(
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

    def remove(self):
        if self.client.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the resource.")
        return True

    def create(self):
        self._set_changed_options()
        if self.want.partition.lower().strip('/') != 'common':
            raise F5ModuleError(
                "Traffic groups can only be created in the /Common partition"
            )
        if self.client.check_mode:
            return True
        self.create_on_device()
        return True

    def create_on_device(self):
        params = self.want.api_params()
        self.client.api.tm.cm.traffic_groups.traffic_group.create(
            name=self.want.name,
            partition=self.want.partition,
            **params
        )

    def update_on_device(self):
        params = self.want.api_params()
        resource = self.client.api.tm.cm.traffic_groups.traffic_group.load(
            name=self.want.name,
            partition=self.want.partition
        )
        resource.modify(**params)

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove_from_device(self):
        resource = self.client.api.tm.cm.traffic_groups.traffic_group.load(
            name=self.want.name,
            partition=self.want.partition
        )
        if resource:
            resource.delete()

    def read_current_from_device(self):
        resource = self.client.api.tm.cm.traffic_groups.traffic_group.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result = resource.attrs
        return Parameters(result)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        self.argument_spec = dict(
            name=dict(required=True),
            state=dict(default='present', choices=['absent', 'present'])
        )
        self.f5_product_name = 'bigip'


def cleanup_tokens(client):
    try:
        resource = client.api.shared.authz.tokens_s.token.load(
            name=client.api.icrs.token
        )
        resource.delete()
    except Exception:
        pass


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
        cleanup_tokens(client)
        client.module.exit_json(**results)
    except F5ModuleError as e:
        cleanup_tokens(client)
        client.module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
