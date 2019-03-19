#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_profile_dns
short_description: Manage DNS profiles on a BIG-IP
description:
  - Manage DNS profiles on a BIG-IP. Many DNS profiles; each with their
    own adjustments to the standard C(dns) profile. Users of this module should be aware
    that many of the adjustable knobs have no module default. Instead, the default is
    assigned by the BIG-IP system itself which, in most cases, is acceptable.
version_added: 2.6
options:
  name:
    description:
      - Specifies the name of the DNS profile.
    type: str
    required: True
  parent:
    description:
      - Specifies the profile from which this profile inherits settings.
      - When creating a new profile, if this parameter is not specified, the default
        is the system-supplied C(dns) profile.
    type: str
  enable_dns_express:
    description:
      - Specifies whether the DNS Express engine is enabled.
      - When creating a new profile, if this parameter is not specified, the default
        is provided by the parent profile.
      - The DNS Express engine receives zone transfers from the authoritative DNS server
        for the zone. If the C(enable_zone_transfer) setting is also C(yes) on this profile,
        the DNS Express engine also responds to zone transfer requests made by the nameservers
        configured as zone transfer clients for the DNS Express zone.
    type: bool
  enable_zone_transfer:
    description:
      - Specifies whether the system answers zone transfer requests for a DNS zone created
        on the system.
      - When creating a new profile, if this parameter is not specified, the default
        is provided by the parent profile.
      - The C(enable_dns_express) and C(enable_zone_transfer) settings on a DNS profile
        affect how the system responds to zone transfer requests.
      - When the C(enable_dns_express) and C(enable_zone_transfer) settings are both C(yes),
        if a zone transfer request matches a DNS Express zone, then DNS Express answers the
        request.
      - When the C(enable_dns_express) setting is C(no) and the C(enable_zone_transfer)
        setting is C(yes), the BIG-IP system processes zone transfer requests based on the
        last action and answers the request from local BIND or a pool member.
    type: bool
  enable_dnssec:
    description:
      - Specifies whether the system signs responses with DNSSEC keys and replies to DNSSEC
        specific queries (e.g., DNSKEY query type).
      - When creating a new profile, if this parameter is not specified, the default
        is provided by the parent profile.
    type: bool
  enable_gtm:
    description:
      - Specifies whether the system uses Global Traffic Manager to manage the response.
      - When creating a new profile, if this parameter is not specified, the default
        is provided by the parent profile.
    type: bool
  process_recursion_desired:
    description:
      - Specifies whether to process client-side DNS packets with Recursion Desired set in
        the header.
      - When creating a new profile, if this parameter is not specified, the default
        is provided by the parent profile.
      - If set to C(no), processing of the packet is subject to the unhandled-query-action
        option.
    type: bool
  use_local_bind:
    description:
      - Specifies whether the system forwards non-wide IP queries to the local BIND server
        on the BIG-IP system.
      - For best performance, disable this setting when using a DNS cache.
      - When creating a new profile, if this parameter is not specified, the default
        is provided by the parent profile.
    type: bool
  enable_dns_firewall:
    description:
      - Specifies whether DNS firewall capability is enabled.
      - When creating a new profile, if this parameter is not specified, the default
        is provided by the parent profile.
    type: bool
  enable_cache:
    description:
      - Specifies whether the system caches DNS responses.
      - When creating a new profile, if this parameter is not specified, the default
        is provided by the parent profile.
      - When C(yes), the BIG-IP system caches DNS responses handled by the virtual
        servers associated with this profile. When you enable this setting, you must
        also specify a value for C(cache_name).
      - When C(no), the BIG-IP system does not cache DNS responses handled by the
        virtual servers associated with this profile. However, the profile retains
        the association with the DNS cache in the C(cache_name) parameter. Disable
        this setting when you want to debug the system.
    type: bool
    version_added: 2.7
  cache_name:
    description:
      - Specifies the user-created cache that the system uses to cache DNS responses.
      - When you select a cache for the system to use, you must also set C(enable_dns_cache)
        to C(yes)
    type: str
    version_added: 2.7
  unhandled_query_action:
    description:
      - Specifies the action to take when a query does not match a Wide IP or a DNS Express Zone.
      - When C(allow), the BIG-IP system forwards queries to a DNS server or pool member.
        If a pool is not associated with a listener and the Use BIND Server on BIG-IP setting
        is set to Enabled, requests are forwarded to the local BIND server.
      - When C(drop), the BIG-IP system does not respond to the query.
      - When C(reject), the BIG-IP system returns the query with the REFUSED return code.
      - When C(hint), the BIG-IP system returns the query with a list of root name servers.
      - When C(no-error), the BIG-IP system returns the query with the NOERROR return code.
      - When creating a new profile, if this parameter is not specified, the default
        is provided by the parent profile.
    type: str
    choices:
      - allow
      - drop
      - reject
      - hint
      - no-error
    version_added: 2.7
  partition:
    description:
      - Device partition to manage resources on.
    type: str
    default: Common
  state:
    description:
      - When C(present), ensures that the profile exists.
      - When C(absent), ensures the profile is removed.
    type: str
    choices:
      - present
      - absent
    default: present
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create a DNS profile
  bigip_profile_dns:
    name: foo
    enable_dns_express: no
    enable_dnssec: no
    enable_gtm: no
    process_recursion_desired: no
    use_local_bind: no
    enable_dns_firewall: yes
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
enable_dns_express:
  description: Whether DNS Express is enabled on the resource or not.
  returned: changed
  type: bool
  sample: yes
enable_zone_transfer:
  description: Whether zone transfer are enabled on the resource or not.
  returned: changed
  type: bool
  sample: no
enable_dnssec:
  description: Whether DNSSEC is enabled on the resource or not.
  returned: changed
  type: bool
  sample: no
enable_gtm:
  description: Whether GTM is used to manage the resource or not.
  returned: changed
  type: bool
  sample: yes
process_recursion_desired:
  description: Whether client-side DNS packets are processed with Recursion Desired set.
  returned: changed
  type: bool
  sample: yes
use_local_bind:
  description: Whether non-wide IP queries are forwarded to the local BIND server or not.
  returned: changed
  type: bool
  sample: no
enable_dns_firewall:
  description: Whether DNS firewall capability is enabled or not.
  returned: changed
  type: bool
  sample: no
enable_cache:
  description: Whether DNS caching is enabled or not.
  returned: changed
  type: bool
  sample: no
cache_name:
  description: Name of the cache used by DNS.
  returned: changed
  type: str
  sample: /Common/cache1
unhandled_query_action:
  description: What to do with unhandled queries
  returned: changed
  type: str
  sample: allow
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
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import transform_name


class Parameters(AnsibleF5Parameters):
    api_map = {
        'enableDnsFirewall': 'enable_dns_firewall',
        'useLocalBind': 'use_local_bind',
        'processRd': 'process_recursion_desired',
        'enableGtm': 'enable_gtm',
        'enableDnssec': 'enable_dnssec',
        'processXfr': 'enable_zone_transfer',
        'enableDnsExpress': 'enable_dns_express',
        'defaultsFrom': 'parent',
        'enableCache': 'enable_cache',
        'cache': 'cache_name',
        'unhandledQueryAction': 'unhandled_query_action',
    }

    api_attributes = [
        'enableDnsFirewall',
        'useLocalBind',
        'processRd',
        'enableGtm',
        'enableDnssec',
        'processXfr',
        'enableDnsExpress',
        'defaultsFrom',
        'cache',
        'enableCache',
        'unhandledQueryAction',
    ]

    returnables = [
        'enable_dns_firewall',
        'use_local_bind',
        'process_recursion_desired',
        'enable_gtm',
        'enable_dnssec',
        'enable_zone_transfer',
        'enable_dns_express',
        'cache_name',
        'enable_cache',
        'unhandled_query_action',
    ]

    updatables = [
        'enable_dns_firewall',
        'use_local_bind',
        'process_recursion_desired',
        'enable_gtm',
        'enable_dnssec',
        'enable_zone_transfer',
        'enable_dns_express',
        'cache_name',
        'enable_cache',
        'unhandled_query_action',
    ]


class ApiParameters(Parameters):
    @property
    def enable_dns_firewall(self):
        if self._values['enable_dns_firewall'] is None:
            return None
        if self._values['enable_dns_firewall'] == 'yes':
            return True
        return False

    @property
    def use_local_bind(self):
        if self._values['use_local_bind'] is None:
            return None
        if self._values['use_local_bind'] == 'yes':
            return True
        return False

    @property
    def process_recursion_desired(self):
        if self._values['process_recursion_desired'] is None:
            return None
        if self._values['process_recursion_desired'] == 'yes':
            return True
        return False

    @property
    def enable_gtm(self):
        if self._values['enable_gtm'] is None:
            return None
        if self._values['enable_gtm'] == 'yes':
            return True
        return False

    @property
    def enable_cache(self):
        if self._values['enable_cache'] is None:
            return None
        if self._values['enable_cache'] == 'yes':
            return True
        return False

    @property
    def enable_dnssec(self):
        if self._values['enable_dnssec'] is None:
            return None
        if self._values['enable_dnssec'] == 'yes':
            return True
        return False

    @property
    def enable_zone_transfer(self):
        if self._values['enable_zone_transfer'] is None:
            return None
        if self._values['enable_zone_transfer'] == 'yes':
            return True
        return False

    @property
    def enable_dns_express(self):
        if self._values['enable_dns_express'] is None:
            return None
        if self._values['enable_dns_express'] == 'yes':
            return True
        return False

    @property
    def unhandled_query_action(self):
        if self._values['unhandled_query_action'] is None:
            return None
        elif self._values['unhandled_query_action'] == 'noerror':
            return 'no-error'
        return self._values['unhandled_query_action']


class ModuleParameters(Parameters):
    @property
    def parent(self):
        if self._values['parent'] is None:
            return None
        result = fq_name(self.partition, self._values['parent'])
        return result

    @property
    def cache_name(self):
        if self._values['cache_name'] is None:
            return None
        if self._values['cache_name'] == '':
            return ''
        result = fq_name(self.partition, self._values['cache_name'])
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
    def enable_dns_firewall(self):
        if self._values['enable_dns_firewall'] is None:
            return None
        if self._values['enable_dns_firewall']:
            return 'yes'
        return 'no'

    @property
    def use_local_bind(self):
        if self._values['use_local_bind'] is None:
            return None
        if self._values['use_local_bind']:
            return 'yes'
        return 'no'

    @property
    def process_recursion_desired(self):
        if self._values['process_recursion_desired'] is None:
            return None
        if self._values['process_recursion_desired']:
            return 'yes'
        return 'no'

    @property
    def enable_gtm(self):
        if self._values['enable_gtm'] is None:
            return None
        if self._values['enable_gtm']:
            return 'yes'
        return 'no'

    @property
    def enable_cache(self):
        if self._values['enable_cache'] is None:
            return None
        if self._values['enable_cache']:
            return 'yes'
        return 'no'

    @property
    def enable_dnssec(self):
        if self._values['enable_dnssec'] is None:
            return None
        if self._values['enable_dnssec']:
            return 'yes'
        return 'no'

    @property
    def enable_zone_transfer(self):
        if self._values['enable_zone_transfer'] is None:
            return None
        if self._values['enable_zone_transfer']:
            return 'yes'
        return 'no'

    @property
    def enable_dns_express(self):
        if self._values['enable_dns_express'] is None:
            return None
        if self._values['enable_dns_express']:
            return 'yes'
        return 'no'

    @property
    def unhandled_query_action(self):
        if self._values['unhandled_query_action'] is None:
            return None
        elif self._values['unhandled_query_action'] == 'no-error':
            return 'noerror'
        return self._values['unhandled_query_action']


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
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/dns/{2}".format(
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
        if self.changes.enable_cache is True or self.have.enable_cache is True:
            if not self.have.cache_name or self.changes.cache_name == '':
                raise F5ModuleError(
                    "To enable DNS cache, a DNS cache must be specified."
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
        self._set_changed_options()
        if self.want.enable_cache is True and not self.want.cache_name:
            raise F5ModuleError(
                "You must specify a 'cache_name' when creating a DNS profile that sets 'enable_cache' to 'yes'."
            )

        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/dns/".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 403, 404]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/dns/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.patch(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 404]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/dns/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/dns/{2}".format(
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
            parent=dict(),
            enable_dns_express=dict(type='bool'),
            enable_zone_transfer=dict(type='bool'),
            enable_dnssec=dict(type='bool'),
            enable_gtm=dict(type='bool'),
            process_recursion_desired=dict(type='bool'),
            use_local_bind=dict(type='bool'),
            enable_dns_firewall=dict(type='bool'),
            enable_cache=dict(type='bool'),
            unhandled_query_action=dict(
                choices=['allow', 'drop', 'reject', 'hint', 'no-error']
            ),
            cache_name=dict(),
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
        supports_check_mode=spec.supports_check_mode
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
