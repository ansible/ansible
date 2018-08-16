#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: bigip_routedomain
short_description: Manage route domains on a BIG-IP
description:
  - Manage route domains on a BIG-IP.
version_added: 2.2
options:
  name:
    description:
      - The name of the route domain.
    version_added: 2.5
  bwc_policy:
    description:
      - The bandwidth controller for the route domain.
  connection_limit:
    description:
      - The maximum number of concurrent connections allowed for the
        route domain. Setting this to C(0) turns off connection limits.
  description:
    description:
      - Specifies descriptive text that identifies the route domain.
  flow_eviction_policy:
    description:
      - The eviction policy to use with this route domain. Apply an eviction
        policy to provide customized responses to flow overflows and slow
        flows on the route domain.
  id:
    description:
      - The unique identifying integer representing the route domain.
      - This field is required when creating a new route domain.
      - In version 2.5, this value is no longer used to reference a route domain when
        making modifications to it (for instance during update and delete operations).
        Instead, the C(name) parameter is used. In version 2.6, the C(name) value will
        become a required parameter.
  parent:
    description:
      - Specifies the route domain the system searches when it cannot
        find a route in the configured domain.
  partition:
    description:
      - Partition to create the route domain on. Partitions cannot be updated
        once they are created.
    default: Common
    version_added: 2.5
  routing_protocol:
    description:
      - Dynamic routing protocols for the system to use in the route domain.
    choices:
      - BFD
      - BGP
      - IS-IS
      - OSPFv2
      - OSPFv3
      - PIM
      - RIP
      - RIPng
  service_policy:
    description:
      - Service policy to associate with the route domain.
  state:
    description:
      - Whether the route domain should exist or not.
    default: present
    choices:
      - present
      - absent
  strict:
    description:
      - Specifies whether the system enforces cross-routing restrictions or not.
    type: bool
  vlans:
    description:
      - VLANs for the system to use in the route domain.
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create a route domain
  bigip_routedomain:
    name: foo
    id: 1234
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
  delegate_to: localhost

- name: Set VLANs on the route domain
  bigip_routedomain:
    name: bar
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
    vlans:
      - net1
      - foo
  delegate_to: localhost
'''

RETURN = r'''
id:
  description: The ID of the route domain that was changed.
  returned: changed
  type: int
  sample: 2
description:
  description: The description of the route domain.
  returned: changed
  type: string
  sample: route domain foo
strict:
  description: The new strict isolation setting.
  returned: changed
  type: string
  sample: enabled
parent:
  description: The new parent route domain.
  returned: changed
  type: int
  sample: 0
vlans:
  description: List of new VLANs the route domain is applied to.
  returned: changed
  type: list
  sample: ['/Common/http-tunnel', '/Common/socks-tunnel']
routing_protocol:
  description: List of routing protocols applied to the route domain.
  returned: changed
  type: list
  sample: ['bfd', 'bgp']
bwc_policy:
  description: The new bandwidth controller.
  returned: changed
  type: string
  sample: /Common/foo
connection_limit:
  description: The new connection limit for the route domain.
  returned: changed
  type: int
  sample: 100
flow_eviction_policy:
  description: The new eviction policy to use with this route domain.
  returned: changed
  type: string
  sample: /Common/default-eviction-policy
service_policy:
  description: The new service policy to use with this route domain.
  returned: changed
  type: string
  sample: /Common-my-service-policy
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from library.module_utils.network.f5.bigip import HAS_F5SDK
    from library.module_utils.network.f5.bigip import F5Client
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import cleanup_tokens
    from library.module_utils.network.f5.common import fq_name
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
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    try:
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False


class Parameters(AnsibleF5Parameters):
    api_map = {
        'connectionLimit': 'connection_limit',
        'servicePolicy': 'service_policy',
        'bwcPolicy': 'bwc_policy',
        'flowEvictionPolicy': 'flow_eviction_policy',
        'routingProtocol': 'routing_protocol'
    }

    api_attributes = [
        'connectionLimit',
        'description',
        'strict',
        'parent',
        'servicePolicy',
        'bwcPolicy',
        'flowEvictionPolicy',
        'routingProtocol',
        'vlans',
        'id'
    ]

    returnables = [
        'description',
        'strict',
        'parent',
        'service_policy',
        'bwc_policy',
        'flow_eviction_policy',
        'routing_protocol',
        'vlans',
        'connection_limit',
        'id'
    ]

    updatables = [
        'description',
        'strict',
        'parent',
        'service_policy',
        'bwc_policy',
        'flow_eviction_policy',
        'routing_protocol',
        'vlans',
        'connection_limit',
        'id'
    ]

    @property
    def connection_limit(self):
        if self._values['connection_limit'] is None:
            return None
        return int(self._values['connection_limit'])

    @property
    def id(self):
        if self._values['id'] is None:
            return None
        return int(self._values['id'])


class ApiParameters(Parameters):
    @property
    def strict(self):
        if self._values['strict'] is None:
            return None
        if self._values['strict'] == 'enabled':
            return True
        return False

    @property
    def domains(self):
        domains = self.read_domains_from_device()
        result = [x.fullPath for x in domains]
        return result

    def read_domains_from_device(self):
        collection = self.client.api.tm.net.route_domains.get_collection()
        return collection


class ModuleParameters(Parameters):
    @property
    def bwc_policy(self):
        if self._values['bwc_policy'] is None:
            return None
        return fq_name(self.partition, self._values['bwc_policy'])

    @property
    def flow_eviction_policy(self):
        if self._values['flow_eviction_policy'] is None:
            return None
        return fq_name(self.partition, self._values['flow_eviction_policy'])

    @property
    def service_policy(self):
        if self._values['service_policy'] is None:
            return None
        return fq_name(self.partition, self._values['service_policy'])

    @property
    def parent(self):
        if self._values['parent'] is None:
            return None
        result = fq_name(self.partition, self._values['parent'])
        return result

    @property
    def vlans(self):
        if self._values['vlans'] is None:
            return None
        if len(self._values['vlans']) == 1 and self._values['vlans'][0] == '':
            return ''
        return [fq_name(self.partition, x) for x in self._values['vlans']]

    @property
    def name(self):
        if self._values['name'] is None:
            return str(self.id)
        return self._values['name']

    @property
    def routing_protocol(self):
        if self._values['routing_protocol'] is None:
            return None
        if len(self._values['routing_protocol']) == 1 and self._values['routing_protocol'][0] == '':
            return ''
        return self._values['routing_protocol']


class Changes(Parameters):
    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result


class UsableChanges(Changes):
    @property
    def strict(self):
        if self._values['strict'] is None:
            return None
        if self._values['strict']:
            return 'enabled'
        return 'disabled'


class ReportableChanges(Changes):
    @property
    def strict(self):
        if self._values['strict'] is None:
            return None
        if self._values['strict'] == 'enabled':
            return 'yes'
        return 'no'


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
    def routing_protocol(self):
        if self.want.routing_protocol is None:
            return None
        if self.want.routing_protocol == '' and self.have.routing_protocol is None:
            return None
        if self.want.routing_protocol == '' and len(self.have.routing_protocol) > 0:
            return []
        if self.have.routing_protocol is None:
            return self.want.routing_protocol
        want = set(self.want.routing_protocol)
        have = set(self.have.routing_protocol)
        if want != have:
            return list(want)

    @property
    def vlans(self):
        if self.want.vlans is None:
            return None
        if self.want.vlans == '' and self.have.vlans is None:
            return None
        if self.want.vlans == '' and len(self.have.vlans) > 0:
            return []
        if self.have.vlans is None:
            return self.want.vlans
        want = set(self.want.vlans)
        have = set(self.have.vlans)
        if want != have:
            return list(want)


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.want = ModuleParameters(params=self.module.params, client=self.client)
        self.have = ApiParameters(client=self.client)
        self.changes = UsableChanges()

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = UsableChanges(params=changed)

    def _update_changed_options(self):
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
            self.changes = UsableChanges(params=changed)
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

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
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
        result = self.client.api.tm.net.route_domains.route_domain.exists(
            name=self.want.name,
            partition=self.want.partition
        )
        return result

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.want.parent and self.want.parent not in self.have.domains:
            raise F5ModuleError(
                "The parent route domain was not found."
            )
        if self.module.check_mode:
            return True
        self.update_on_device()
        return True

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the resource.")
        return True

    def create(self):
        if self.want.id is None:
            raise F5ModuleError(
                "The 'id' parameter is required when creating new route domains."
            )
        if self.want.parent and self.want.parent not in self.have.domains:
            raise F5ModuleError(
                "The parent route domain was not found."
            )
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        self.client.api.tm.net.route_domains.route_domain.create(
            name=self.want.name,
            partition=self.want.partition,
            **params
        )

    def update_on_device(self):
        params = self.changes.api_params()
        resource = self.client.api.tm.net.route_domains.route_domain.load(
            name=self.want.name,
            partition=self.want.partition
        )
        resource.modify(**params)

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove_from_device(self):
        resource = self.client.api.tm.net.route_domains.route_domain.load(
            name=self.want.name,
            partition=self.want.partition
        )
        if resource:
            resource.delete()

    def read_current_from_device(self):
        resource = self.client.api.tm.net.route_domains.route_domain.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result = resource.attrs
        return ApiParameters(params=result, client=self.client)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(),
            id=dict(type='int'),
            description=dict(),
            strict=dict(type='bool'),
            parent=dict(type='int'),
            vlans=dict(type='list'),
            routing_protocol=dict(
                type='list',
                choices=['BFD', 'BGP', 'IS-IS', 'OSPFv2', 'OSPFv3', 'PIM', 'RIP', 'RIPng']
            ),
            bwc_policy=dict(),
            connection_limit=dict(type='int'),
            flow_eviction_policy=dict(),
            service_policy=dict(),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            ),
            state=dict(
                default='present',
                choices=['present', 'absent']
            )
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)
        self.required_one_of = [
            ['name', 'id']
        ]


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
