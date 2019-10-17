#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_dns_resolver
short_description: Manage DNS resolvers on a BIG-IP
description:
  - Manage DNS resolver on a BIG-IP.
version_added: 2.8
options:
  name:
    description:
      - Specifies the name of the DNS resolver.
    type: str
    required: True
  route_domain:
    description:
      - Specifies the route domain the resolver uses for outbound traffic.
    type: int
  cache_size:
    description:
      - Specifies the size of the internal DNS resolver cache.
      - When creating a new resolver, if this parameter is not specified, the default
        is 5767168 bytes.
      - After the cache reaches this size, when new or refreshed content arrives, the
        system removes expired and older content and caches the new or updated content.
    type: int
  answer_default_zones:
    description:
      - Specifies whether the system answers DNS queries for the default zones localhost,
        reverse 127.0.0.1 and ::1, and AS112.
      - When creating a new resolver, if this parameter is not specified, the default
        is C(no), meaning that the system passes along the DNS queries for the default zones.
    type: bool
  randomize_query_case:
    description:
      - When C(yes), specifies that the internal DNS resolver randomizes character case
        in domain name queries issued to the root DNS servers.
      - When creating a new resolver, if this parameter is not specified, the default
        is C(yes).
    type: bool
  use_ipv4:
    description:
      - Specifies whether the system can use IPv4 to query backend nameservers.
      - An IPv4 Self IP and default route must be available for these queries to work
        successfully.
      - When creating a new resolver, if this parameter is not specified, the default
        is C(yes).
    type: bool
  use_ipv6:
    description:
      - Specifies whether the system can use IPv6 to query backend nameservers.
      - An IPv6 Self IP and default route must be available for these queries to work
        successfully.
      - When creating a new resolver, if this parameter is not specified, the default
        is C(yes).
    type: bool
  use_udp:
    description:
      - Specifies whether the system answers and issues UDP-formatted queries.
      - When creating a new resolver, if this parameter is not specified, the default
        is C(yes).
    type: bool
  use_tcp:
    description:
      - Specifies whether the system answers and issues TCP-formatted queries.
      - When creating a new resolver, if this parameter is not specified, the default
        is C(yes).
    type: bool
  state:
    description:
      - When C(present), ensures that the resource exists.
      - When C(absent), ensures the resource is removed.
    type: str
    choices:
      - present
      - absent
    default: present
  partition:
    description:
      - Device partition to manage resources on.
    type: str
    default: Common
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create a simple DNS responder for OCSP stapling
  bigip_dns_resolver:
    name: resolver1
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
route_domain:
  description: The new route domain of the resource.
  returned: changed
  type: str
  sample: /Common/0
cache_size:
  description: The new cache size of the resource.
  returned: changed
  type: int
  sample: 50000
answer_default_zones:
  description: The new Answer Default Zones setting.
  returned: changed
  type: bool
  sample: yes
randomize_query_case:
  description: The new Randomize Query Character Case setting.
  returned: changed
  type: bool
  sample: no
use_ipv4:
  description: The new Use IPv4 setting.
  returned: changed
  type: bool
  sample: yes
use_ipv6:
  description: The new Use IPv6 setting.
  returned: changed
  type: bool
  sample: no
use_udp:
  description: The new Use UDP setting.
  returned: changed
  type: bool
  sample: yes
use_tcp:
  description: The new Use TCP setting.
  returned: changed
  type: bool
  sample: no
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.common import flatten_boolean
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import flatten_boolean


class Parameters(AnsibleF5Parameters):
    api_map = {
        'answerDefaultZones': 'answer_default_zones',
        'cacheSize': 'cache_size',
        'randomizeQueryNameCase': 'randomize_query_case',
        'routeDomain': 'route_domain',
        'useIpv4': 'use_ipv4',
        'useIpv6': 'use_ipv6',
        'useTcp': 'use_tcp',
        'useUdp': 'use_udp',
    }

    api_attributes = [
        'answerDefaultZones',
        'cacheSize',
        'randomizeQueryNameCase',
        'routeDomain',
        'useIpv4',
        'useIpv6',
        'useTcp',
        'useUdp',
    ]

    returnables = [
        'answer_default_zones',
        'cache_size',
        'randomize_query_case',
        'route_domain',
        'use_ipv4',
        'use_ipv6',
        'use_tcp',
        'use_udp',
    ]

    updatables = [
        'answer_default_zones',
        'cache_size',
        'randomize_query_case',
        'route_domain',
        'use_ipv4',
        'use_ipv6',
        'use_tcp',
        'use_udp',
    ]

    @property
    def answer_default_zones(self):
        result = flatten_boolean(self._values['answer_default_zones'])
        return result

    @property
    def randomize_query_case(self):
        result = flatten_boolean(self._values['randomize_query_case'])
        return result

    @property
    def use_ipv4(self):
        result = flatten_boolean(self._values['use_ipv4'])
        return result

    @property
    def use_ipv6(self):
        result = flatten_boolean(self._values['use_ipv6'])
        return result

    @property
    def use_tcp(self):
        result = flatten_boolean(self._values['use_tcp'])
        return result

    @property
    def use_udp(self):
        result = flatten_boolean(self._values['use_udp'])
        return result


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    @property
    def route_domain(self):
        if self._values['route_domain'] is None:
            return None
        result = fq_name(self.partition, self._values['route_domain'])
        return result


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
    pass


class ReportableChanges(Changes):
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


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = ModuleParameters(params=self.module.params)
        self.have = ApiParameters()
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

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/net/dns-resolver/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False
        return True

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
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
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/net/dns-resolver/".format(
            self.client.provider['server'],
            self.client.provider['server_port']
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

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/net/dns-resolver/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
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

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/net/dns-resolver/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/net/dns-resolver/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
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
        return ApiParameters(params=response)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(required=True),
            route_domain=dict(type='int'),
            cache_size=dict(type='int'),
            answer_default_zones=dict(type='bool'),
            randomize_query_case=dict(type='bool'),
            use_ipv4=dict(type='bool'),
            use_ipv6=dict(type='bool'),
            use_udp=dict(type='bool'),
            use_tcp=dict(type='bool'),
            state=dict(
                default='present',
                choices=['present', 'absent']
            ),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            )
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
