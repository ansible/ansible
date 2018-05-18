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
module: bigip_partition
short_description: Manage BIG-IP partitions
description:
  - Manage BIG-IP partitions.
version_added: 2.5
options:
  name:
    description:
      - Name of the partition
    required: True
  description:
    description:
      - The description to attach to the Partition.
  route_domain:
    description:
      - The default Route Domain to assign to the Partition. If no route domain
        is specified, then the default route domain for the system (typically
        zero) will be used only when creating a new partition.
  state:
    description:
      - Whether the partition should exist or not.
    default: present
    choices:
      - present
      - absent
notes:
  - Requires BIG-IP software version >= 12
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create partition "foo" using the default route domain
  bigip_partition:
    name: foo
    password: secret
    server: lb.mydomain.com
    user: admin
  delegate_to: localhost

- name: Create partition "bar" using a custom route domain
  bigip_partition:
    name: bar
    route_domain: 3
    password: secret
    server: lb.mydomain.com
    user: admin
  delegate_to: localhost

- name: Change route domain of partition "foo"
  bigip_partition:
    name: foo
    route_domain: 8
    password: secret
    server: lb.mydomain.com
    user: admin
  delegate_to: localhost

- name: Set a description for partition "foo"
  bigip_partition:
    name: foo
    description: Tenant CompanyA
    password: secret
    server: lb.mydomain.com
    user: admin
  delegate_to: localhost

- name: Delete the "foo" partition
  bigip_partition:
    name: foo
    password: secret
    server: lb.mydomain.com
    user: admin
    state: absent
  delegate_to: localhost
'''

RETURN = r'''
route_domain:
  description: Name of the route domain associated with the partition.
  returned: changed and success
  type: int
  sample: 0
description:
  description: The description of the partition.
  returned: changed and success
  type: string
  sample: Example partition
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from library.module_utils.network.f5.bigip import HAS_F5SDK
    from library.module_utils.network.f5.bigip import F5Client
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import cleanup_tokens
    from library.module_utils.network.f5.common import f5_argument_spec
    try:
        from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False
except ImportError:
    from ansible.module_utils.network.f5.bigip import HAS_F5SDK
    from ansible.module_utils.network.f5.bigip import F5Client
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import cleanup_tokens
    from ansible.module_utils.network.f5.common import f5_argument_spec
    try:
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False


class Parameters(AnsibleF5Parameters):
    api_map = {
        'defaultRouteDomain': 'route_domain',
    }

    api_attributes = [
        'description', 'defaultRouteDomain'
    ]

    returnables = [
        'description', 'route_domain'
    ]

    updatables = [
        'description', 'route_domain'
    ]

    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
            return result
        except Exception:
            return result

    @property
    def partition(self):
        # Cannot create a partition in a partition, so nullify this
        return None

    @property
    def route_domain(self):
        if self._values['route_domain'] is None:
            return None
        return int(self._values['route_domain'])


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
            result = self.__default(param)
            return result

    def __default(self, param):
        attr1 = getattr(self.want, param)
        try:
            attr2 = getattr(self.have, param)
            if attr1 != attr2:
                return attr1
        except AttributeError:
            return attr1


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.have = None
        self.want = Parameters(params=self.module.params)
        self.changes = Changes()

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = Parameters(params=changed)

    def _update_changed_options(self):
        diff = Difference(self.want, self.have)
        updatables = Parameters.updatables
        changed = dict()
        for k in updatables:
            change = diff.compare(k)
            if change is None:
                continue
            else:
                changed[k] = change
        if changed:
            self.changes = Parameters(params=changed)
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
        return result

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def create(self):
        if self.module.check_mode:
            return True
        self.create_on_device()
        if not self.exists():
            raise F5ModuleError("Failed to create the partition.")
        return True

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
        self.update_on_device()
        return True

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the partition.")
        return True

    def read_current_from_device(self):
        resource = self.client.api.tm.auth.partitions.partition.load(
            name=self.want.name
        )
        result = resource.attrs
        return Parameters(params=result)

    def exists(self):
        result = self.client.api.tm.auth.partitions.partition.exists(
            name=self.want.name
        )
        return result

    def update_on_device(self):
        params = self.want.api_params()
        result = self.client.api.tm.auth.partitions.partition.load(
            name=self.want.name
        )
        result.modify(**params)

    def create_on_device(self):
        params = self.want.api_params()
        self.client.api.tm.auth.partitions.partition.create(
            name=self.want.name,
            **params
        )

    def remove_from_device(self):
        result = self.client.api.tm.auth.partitions.partition.load(
            name=self.want.name
        )
        if result:
            result.delete()


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(required=True),
            description=dict(),
            route_domain=dict(type='int'),
            state=dict(
                choices=['absent', 'present'],
                default='present'
            )
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode
    )
    if not HAS_F5SDK:
        module.fail_json(msg="The python f5-sdk module is required")

    try:
        client = F5Client(**module.params)
        mm = ModuleManager(module=module, client=client)
        results = mm.exec_module()
        cleanup_tokens(client)
        module.exit_json(**results)
    except F5ModuleError as ex:
        cleanup_tokens(client)
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
