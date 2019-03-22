#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2016, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

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
    type: str
    version_added: 2.5
  bwc_policy:
    description:
      - The bandwidth controller for the route domain.
    type: str
  connection_limit:
    description:
      - The maximum number of concurrent connections allowed for the
        route domain. Setting this to C(0) turns off connection limits.
    type: int
  description:
    description:
      - Specifies descriptive text that identifies the route domain.
    type: str
  flow_eviction_policy:
    description:
      - The eviction policy to use with this route domain. Apply an eviction
        policy to provide customized responses to flow overflows and slow
        flows on the route domain.
    type: str
  id:
    description:
      - The unique identifying integer representing the route domain.
      - This field is required when creating a new route domain.
      - In version 2.5, this value is no longer used to reference a route domain when
        making modifications to it (for instance during update and delete operations).
        Instead, the C(name) parameter is used. In version 2.6, the C(name) value will
        become a required parameter.
    type: int
  parent:
    description:
      - Specifies the route domain the system searches when it cannot
        find a route in the configured domain.
    type: str
  partition:
    description:
      - Partition to create the route domain on. Partitions cannot be updated
        once they are created.
    type: str
    default: Common
    version_added: 2.5
  routing_protocol:
    description:
      - Dynamic routing protocols for the system to use in the route domain.
    type: list
    choices:
      - none
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
    type: str
  state:
    description:
      - Whether the route domain should exist or not.
    type: str
    choices:
      - present
      - absent
    default: present
  strict:
    description:
      - Specifies whether the system enforces cross-routing restrictions or not.
    type: bool
  vlans:
    description:
      - VLANs for the system to use in the route domain.
    type: list
  fw_enforced_policy:
    description:
      - Specifies AFM policy to be attached to route domain.
    type: str
    version_added: 2.8
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Create a route domain
  bigip_routedomain:
    name: foo
    id: 1234
    state: present
    provider:
      user: admin
      password: secret
      server: lb.mydomain.com
  delegate_to: localhost

- name: Set VLANs on the route domain
  bigip_routedomain:
    name: bar
    state: present
    vlans:
      - net1
      - foo
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
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
  type: str
  sample: route domain foo
strict:
  description: The new strict isolation setting.
  returned: changed
  type: str
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
  type: str
  sample: /Common/foo
connection_limit:
  description: The new connection limit for the route domain.
  returned: changed
  type: int
  sample: 100
flow_eviction_policy:
  description: The new eviction policy to use with this route domain.
  returned: changed
  type: str
  sample: /Common/default-eviction-policy
service_policy:
  description: The new service policy to use with this route domain.
  returned: changed
  type: str
  sample: /Common-my-service-policy
fw_enforced_policy:
  description: Specfies AFM policy to be attached to route domain.
  returned: changed
  type: str
  sample: /Common/afm-blocking-policy
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.compare import cmp_simple_list
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.compare import cmp_simple_list


class Parameters(AnsibleF5Parameters):
    api_map = {
        'connectionLimit': 'connection_limit',
        'servicePolicy': 'service_policy',
        'bwcPolicy': 'bwc_policy',
        'flowEvictionPolicy': 'flow_eviction_policy',
        'routingProtocol': 'routing_protocol',
        'fwEnforcedPolicy': 'fw_enforced_policy',
        'fwEnforcedPolicyReference': 'fw_policy_link',
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
        'id',
        'fwEnforcedPolicy',
        'fwEnforcedPolicyReference',
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
        'id',
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
        'id',
        'fw_enforced_policy',
        'fw_policy_link',
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
        result = [x['fullPath'] for x in domains['items']]
        return result

    def read_domains_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/net/route-domain/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return response


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
        if len(self._values['routing_protocol']) == 1 and self._values['routing_protocol'][0] in ['', 'none']:
            return ''
        return self._values['routing_protocol']

    @property
    def fw_enforced_policy(self):
        if self._values['fw_enforced_policy'] is None:
            return None
        if self._values['fw_enforced_policy'] in ['none', '']:
            return None
        name = self._values['fw_enforced_policy']
        return fq_name(self.partition, name)

    @property
    def fw_policy_link(self):
        policy = self.fw_enforced_policy
        if policy is None:
            return None
        tmp = policy.split('/')
        link = dict(link='https://localhost/mgmt/tm/security/firewall/policy/~{0}~{1}'.format(tmp[1], tmp[2]))
        return link


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
        return cmp_simple_list(self.want.routing_protocol, self.have.routing_protocol)

    @property
    def vlans(self):
        return cmp_simple_list(self.want.vlans, self.have.vlans)

    @property
    def fw_policy_link(self):
        if self.want.fw_enforced_policy is None:
            return None
        if self.want.fw_enforced_policy == self.have.fw_enforced_policy:
            return None
        if self.want.fw_policy_link != self.have.fw_policy_link:
            return self.want.fw_policy_link


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
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

        if state == "present":
            changed = self.present()
        elif state == "absent":
            changed = self.absent()

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

    def absent(self):
        if self.exists():
            return self.remove()
        return False

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

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/net/route-domain/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name),
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/net/route-domain/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if self.want.fw_enforced_policy:
            payload = dict(
                fwEnforcedPolicy=self.want.fw_enforced_policy,
                fwEnforcedPolicyReference=self.want.fw_policy_link
            )
            uri = "https://{0}:{1}/mgmt/tm/net/route-domain/{2}".format(
                self.client.provider['server'],
                self.client.provider['server_port'],
                transform_name(self.want.partition, self.want.name),
            )
            resp = self.client.api.patch(uri, json=payload)

            try:
                response = resp.json()
            except ValueError as ex:
                raise F5ModuleError(str(ex))

            if 'code' in response and response['code'] in [400, 403]:
                if 'message' in response:
                    raise F5ModuleError(response['message'])
                else:
                    raise F5ModuleError(resp.content)
        return True

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/net/route-domain/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name),
        )
        resp = self.client.api.patch(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/net/route-domain/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name),
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/net/route-domain/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name),
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return ApiParameters(params=response, client=self.client)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(),
            id=dict(type='int'),
            description=dict(),
            strict=dict(type='bool'),
            parent=dict(),
            vlans=dict(type='list'),
            routing_protocol=dict(
                type='list',
                choices=['BFD', 'BGP', 'IS-IS', 'OSPFv2', 'OSPFv3', 'PIM', 'RIP', 'RIPng', 'none']
            ),
            bwc_policy=dict(),
            connection_limit=dict(type='int'),
            flow_eviction_policy=dict(),
            service_policy=dict(),
            fw_enforced_policy=dict(),
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
        supports_check_mode=spec.supports_check_mode,
        required_one_of=spec.required_one_of
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
