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
module: bigip_dns_cache_resolver
short_description: Manage DNS resolver cache configurations on BIG-IP
description:
  - Manage DNS resolver cache configurations on BIG-IP.
version_added: 2.8
options:
  name:
    description:
      - Specifies the name of the cache.
    type: str
    required: True
  answer_default_zones:
    description:
      - Specifies whether the system answers DNS queries for the default
        zones localhost, reverse 127.0.0.1 and ::1, and AS112.
      - When creating a new cache resolver, if this parameter is not specified, the
        default is C(no).
    type: bool
  forward_zones:
    description:
      - Forward zones associated with the cache.
      - To remove all forward zones, specify a value of C(none).
    suboptions:
      name:
        description:
          - Specifies a FQDN for the forward zone.
        type: str
        required: True
      nameservers:
        description:
          - Specifies the IP address and service port of a recursive
            nameserver that answers DNS queries for the zone when the
            response cannot be found in the DNS cache.
        suboptions:
          address:
            description:
              - Address of recursive nameserver.
            type: str
          port:
            description:
              - Port of recursive nameserver.
              - When specifying new nameservers, if this value is not provided, the
                default is C(53).
            type: int
        type: list
    type: raw
  route_domain:
    description:
      - Specifies the route domain the resolver uses for outbound traffic.
    type: str
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
- name: Create a DNS resolver cache
  bigip_dns_cache:
    name: foo
    answer_default_zones: yes
    forward_zones:
      - name: foo.bar.com
        nameservers:
          - address: 1.2.3.4
            port: 53
          - address: 5.6.7.8
    route_domain: 0
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
param1:
  description: The new param1 value of the resource.
  returned: changed
  type: bool
  sample: true
param2:
  description: The new param2 value of the resource.
  returned: changed
  type: str
  sample: Foo is bar
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import flatten_boolean
    from library.module_utils.network.f5.common import transform_name
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.common import transform_name


class Parameters(AnsibleF5Parameters):
    api_map = {
        'routeDomain': 'route_domain',
        'answerDefaultZones': 'answer_default_zones',
        'forwardZones': 'forward_zones',
    }

    api_attributes = [
        'routeDomain',
        'answerDefaultZones',
        'forwardZones',
    ]

    returnables = [
        'route_domain',
        'answer_default_zones',
        'forward_zones',
    ]

    updatables = [
        'route_domain',
        'answer_default_zones',
        'forward_zones',
    ]

    @property
    def route_domain(self):
        if self._values['route_domain'] is None:
            return None
        return fq_name(self.partition, self._values['route_domain'])

    @property
    def answer_default_zones(self):
        return flatten_boolean(self._values['answer_default_zones'])


class ApiParameters(Parameters):
    @property
    def forward_zones(self):
        if self._values['forward_zones'] is None:
            return None
        result = []
        for x in self._values['forward_zones']:
            tmp = dict(
                name=x['name'],
                nameservers=[]
            )
            if 'nameservers' in x:
                tmp['nameservers'] = [y['name'] for y in x['nameservers']]
                tmp['nameservers'].sort()
            result.append(tmp)
        return result


class ModuleParameters(Parameters):
    @property
    def forward_zones(self):
        if self._values['forward_zones'] is None:
            return None
        elif self._values['forward_zones'] in ['', 'none']:
            return ''
        result = []
        for x in self._values['forward_zones']:
            if 'name' not in x:
                raise F5ModuleError(
                    "A 'name' key must be provided when specifying a list of forward zones."
                )
            tmp = dict(
                name=x['name'],
                nameservers=[]
            )
            if 'nameservers' in x:
                for ns in x['nameservers']:
                    if 'address' not in ns:
                        raise F5ModuleError(
                            "An 'address' key must be provided when specifying a list of forward zone nameservers."
                        )
                    item = '{0}:{1}'.format(ns['address'], ns.get('port', 53))
                    tmp['nameservers'].append(item)
                tmp['nameservers'].sort()
            result.append(tmp)
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
    @property
    def forward_zones(self):
        if self._values['forward_zones'] is None:
            return None
        result = []
        for x in self._values['forward_zones']:
            tmp = {'name': x['name']}
            if 'nameservers' in x:
                tmp['nameservers'] = []
                for y in x['nameservers']:
                    tmp['nameservers'].append(dict(name=y))
            result.append(tmp)
        return result


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

    @property
    def forward_zones(self):
        if self.want.forward_zones is None:
            return None
        if self.have.forward_zones is None and self.want.forward_zones in ['', 'none']:
            return None
        if self.have.forward_zones is not None and self.want.forward_zones in ['', 'none']:
            return []
        if self.have.forward_zones is None:
            return dict(
                forward_zones=self.want.forward_zones
            )

        want = sorted(self.want.forward_zones, key=lambda x: x['name'])
        have = sorted(self.have.forward_zones, key=lambda x: x['name'])

        wnames = [x['name'] for x in want]
        hnames = [x['name'] for x in have]

        if set(wnames) != set(hnames):
            return dict(
                forward_zones=self.want.forward_zones
            )

        for idx, x in enumerate(want):
            wns = x.get('nameservers', [])
            hns = have[idx].get('nameservers', [])
            if set(wns) != set(hns):
                return dict(
                    forward_zones=self.want.forward_zones
                )


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
        uri = "https://{0}:{1}/mgmt/tm/ltm/dns/cache/resolver/{2}".format(
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/dns/cache/resolver/".format(
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/dns/cache/resolver/{2}".format(
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/dns/cache/resolver/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/dns/cache/resolver/{2}".format(
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
            route_domain=dict(),
            answer_default_zones=dict(type='bool'),
            forward_zones=dict(
                type='raw',
                options=dict(
                    name=dict(),
                    nameservers=dict(
                        type='list',
                        elements='dict',
                        options=dict(
                            address=dict(),
                            port=dict(type='int')
                        )
                    )
                )
            ),
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
