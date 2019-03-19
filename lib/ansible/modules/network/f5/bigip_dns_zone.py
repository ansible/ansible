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
module: bigip_dns_zone
short_description: Manage DNS zones on BIG-IP
description:
  - Manage DNS zones on BIG-IP. The zones managed here are primarily used
    for configuring DNS Express on BIG-IP. This module does not configure
    zones that are found in BIG-IP ZoneRunner.
version_added: 2.8
options:
  name:
    description:
      - Specifies the name of the DNS zone.
      - The name must begin with a letter and contain only letters, numbers,
        and the underscore character.
    type: str
    required: True
  dns_express:
    description:
      - DNS express related settings.
    type: dict
    suboptions:
      server:
        description:
          - Specifies the back-end authoritative DNS server from which the BIG-IP
            system receives AXFR zone transfers for the DNS Express zone.
        type: str
      enabled:
        description:
          - Specifies the current status of the DNS Express zone.
        type: bool
      notify_action:
        description:
          - Specifies the action the system takes when a NOTIFY message is received
            for this DNS Express zone.
          - If a TSIG key is configured for the zone, the signature is only validated
            for C(consume) and C(repeat) actions.
          - When C(consume), the NOTIFY message is seen only by DNS Express.
          - When C(bypass), the NOTIFY message does not go to DNS Express, but
            instead goes to a back-end DNS server (subject to the value of the
            Unhandled Query Action configured in the DNS profile applied to the
            listener that handles the DNS request).
          - When C(repeat), the NOTIFY message goes to both DNS Express and any
            back-end DNS server.
        type: str
        choices:
          - consume
          - bypass
          - repeat
      allow_notify_from:
        description:
          - Specifies the IP addresses from which the system accepts NOTIFY messages
            for this DNS Express zone.
        type: list
      verify_tsig:
        description:
          - Specifies whether the system verifies the identity of the authoritative
            nameserver that sends updated information for this DNS Express zone.
        type: bool
      response_policy:
        description:
          - Specifies whether this DNS Express zone is a DNS response policy zone (RPZ).
        type: bool
  nameservers:
    description:
      - Specifies the DNS nameservers to which the system sends NOTIFY messages.
    type: list
  tsig_server_key:
    description:
      - Specifies the TSIG key the system uses to authenticate the back-end DNS
        authoritative server that sends AXFR zone transfers to the BIG-IP system.
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
- name: Create a DNS zone for DNS express
  bigip_dns_zone:
    name: foo.bar.com
    dns_express:
      enabled: yes
      server: dns-lab
      allow_notify_from:
        - 192.168.39.10
      notify_action: consume
      verify_tsig: no
      response_policy: no
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
enabled:
  description: Whether the zone is enabled or not.
  returned: changed
  type: bool
  sample: yes
allow_notify_from:
  description: The new DNS Express Allow NOTIFY From value.
  returned: changed
  type: list
  sample: ['1.1.1.1', '2.2.2.2']
notify_action:
  description: The new DNS Express Notify Action value.
  returned: changed
  type: str
  sample: consume
verify_tsig:
  description: The new DNS Express Verify Notify TSIG value.
  returned: changed
  type: bool
  sample: yes
express_server:
  description: The new DNS Express Server value.
  returned: changed
  type: str
  sample: server1
response_policy:
  description: The new DNS Express Response Policy value.
  returned: changed
  type: bool
  sample: no
nameservers:
  description: The new Zone Transfer Clients Nameservers value.
  returned: changed
  type: list
  sample: ['/Common/server1', '/Common/server2']
tsig_server_key:
  description: The new TSIG Server Key value.
  returned: changed
  type: str
  sample: /Common/key1
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
    from library.module_utils.network.f5.compare import cmp_simple_list
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.compare import cmp_simple_list


class Parameters(AnsibleF5Parameters):
    api_map = {
        'dnsExpressEnabled': 'enabled',
        'dnsExpressAllowNotify': 'allow_notify_from',
        'dnsExpressNotifyAction': 'notify_action',
        'dnsExpressNotifyTsigVerify': 'verify_tsig',
        'dnsExpressServer': 'express_server',
        'responsePolicy': 'response_policy',
        'transferClients': 'nameservers',
        'serverTsigKey': 'tsig_server_key',
    }

    api_attributes = [
        'dnsExpressEnabled',
        'dnsExpressAllowNotify',
        'dnsExpressNotifyAction',
        'dnsExpressNotifyTsigVerify',
        'dnsExpressServer',
        'responsePolicy',
        'transferClients',
        'serverTsigKey',
    ]

    returnables = [
        'enabled',
        'allow_notify_from',
        'notify_action',
        'verify_tsig',
        'express_server',
        'response_policy',
        'nameservers',
        'tsig_server_key',
    ]

    updatables = [
        'enabled',
        'allow_notify_from',
        'notify_action',
        'verify_tsig',
        'express_server',
        'response_policy',
        'nameservers',
        'tsig_server_key',
    ]


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    @property
    def express_server(self):
        try:
            if self._values['dns_express']['server'] is None:
                return None
            if self._values['dns_express']['server'] in ['', 'none']:
                return ''
            return fq_name(self.partition, self._values['dns_express']['server'])
        except (TypeError, KeyError):
            return None

    @property
    def nameservers(self):
        if self._values['nameservers'] is None:
            return None
        elif len(self._values['nameservers']) == 1 and self._values['nameservers'][0] in ['', 'none']:
            return ''
        return [fq_name(self.partition, x) for x in self._values['nameservers']]

    @property
    def tsig_server_key(self):
        if self._values['tsig_server_key'] is None:
            return None
        if self._values['tsig_server_key'] in ['', 'none']:
            return ''
        return fq_name(self.partition, self._values['tsig_server_key'])

    @property
    def enabled(self):
        try:
            return flatten_boolean(self._values['dns_express']['enabled'])
        except (TypeError, KeyError):
            return None

    @property
    def verify_tsig(self):
        try:
            return flatten_boolean(self._values['dns_express']['verify_tsig'])
        except (TypeError, KeyError):
            return None

    @property
    def notify_action(self):
        try:
            return self._values['dns_express']['notify_action']
        except (TypeError, KeyError):
            return None

    @property
    def response_policy(self):
        try:
            return flatten_boolean(self._values['dns_express']['response_policy'])
        except (TypeError, KeyError):
            return None

    @property
    def allow_notify_from(self):
        try:
            v = self._values['dns_express']['allow_notify_from']
            if v is None:
                return None
            elif len(v) == 1 and v[0] in ['', 'none']:
                return ''
            return v
        except (TypeError, KeyError):
            return None


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

    @property
    def allow_notify_from(self):
        return cmp_simple_list(self.want.allow_notify_from, self.have.allow_notify_from)

    @property
    def nameservers(self):
        return cmp_simple_list(self.want.nameservers, self.have.nameservers)

    @property
    def express_server(self):
        if self.want.express_server is None:
            return None
        if self.want.express_server == '' and self.have.express_server is None:
            return None
        if self.want.express_server != self.have.express_server:
            return self.want.express_server

    @property
    def tsig_server_key(self):
        if self.want.tsig_server_key is None:
            return None
        if self.want.tsig_server_key == '' and self.have.tsig_server_key is None:
            return None
        if self.want.tsig_server_key != self.have.tsig_server_key:
            return self.want.tsig_server_key

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
        uri = "https://{0}:{1}/mgmt/tm/ltm/dns/zone/{2}".format(
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/dns/zone/".format(
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/dns/zone/{2}".format(
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/dns/zone/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/dns/zone/{2}".format(
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
            dns_express=dict(
                type='dict',
                options=dict(
                    server=dict(),
                    enabled=dict(type='bool'),
                    notify_action=dict(
                        choices=['consume', 'bypass', 'repeat']
                    ),
                    allow_notify_from=dict(type='list'),
                    verify_tsig=dict(type='bool'),
                    response_policy=dict(type='bool')
                )
            ),
            nameservers=dict(type='list'),
            tsig_server_key=dict(),
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
