#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: bigip_profile_dns
short_description: Manage DNS profiles on a BIG-IP
description:
  - Manage DNS profiles on a BIG-IP. There are a variety of DNS profiles, each with their
    own adjustments to the standard C(dns) profile. Users of this module should be aware
    that many of the adjustable knobs have no module default. Instead, the default is
    assigned by the BIG-IP system itself which, in most cases, is acceptable.
version_added: 2.6
options:
  name:
    description:
      - Specifies the name of the DNS profile.
    required: True
  parent:
    description:
      - Specifies the profile from which this profile inherits settings.
      - When creating a new profile, if this parameter is not specified, the default
        is the system-supplied C(dns) profile.
  enable_dns_express:
    description:
      - Specifies whether the DNS Express engine is enabled.
      - When creating a new profile, if this parameter is not specified, the default is
        C(yes).
      - The DNS Express engine receives zone transfers from the authoritative DNS server
        for the zone. If the C(enable_zone_transfer) setting is also C(yes) on this profile,
        the DNS Express engine also responds to zone transfer requests made by the nameservers
        configured as zone transfer clients for the DNS Express zone.
    type: bool
  enable_zone_transfer:
    description:
      - Specifies whether the system answers zone transfer requests for a DNS zone created
        on the system.
      - When creating a new profile, if this parameter is not specified, the default is
        C(no).
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
      - When creating a new profile, if this parameter is not specified, the default is
        C(yes).
    type: bool
  enable_gtm:
    description:
      - Specifies whether the system uses Global Traffic Manager to manage the response.
      - When creating a new profile, if this parameter is not specified, the default is
        C(yes).
    type: bool
  process_recursion_desired:
    description:
      - Specifies whether to process client-side DNS packets with Recursion Desired set in
        the header.
      - When creating a new profile, if this parameter is not specified, the default is
        C(yes).
      - If set to C(no), processing of the packet is subject to the unhandled-query-action
        option.
    type: bool
  use_local_bind:
    description:
      - Specifies whether the system forwards non-wide IP queries to the local BIND server
        on the BIG-IP system.
      - For best performance, disable this setting when using a DNS cache.
      - When creating a new profile, if this parameter is not specified, the default is
        C(yes).
    type: bool
  enable_dns_firewall:
    description:
      - Specifies whether DNS firewall capability is enabled.
      - When creating a new profile, if this parameter is not specified, the default is
        C(no).
    type: bool
  partition:
    description:
      - Device partition to manage resources on.
    default: Common
  state:
    description:
      - When C(present), ensures that the profile exists.
      - When C(absent), ensures the profile is removed.
    default: present
    choices:
      - present
      - absent
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
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
  delegate_to: localhost
'''

RETURN = r'''
enable_dns_express:
  description: Whether DNS Express is enabled on the resource or not.
  returned: changed
  type: bool
  sample: True
enable_zone_transfer:
  description: Whether zone transfer are enabled on the resource or not.
  returned: changed
  type: bool
  sample: False
enable_dnssec:
  description: Whether DNSSEC is enabled on the resource or not.
  returned: changed
  type: bool
  sample: False
enable_gtm:
  description: Whether GTM is used to manage the resource or not.
  returned: changed
  type: bool
  sample: True
process_recursion_desired:
  description: Whether client-side DNS packets are processed with Recursion Desired set.
  returned: changed
  type: bool
  sample: True
use_local_bind:
  description: Whether non-wide IP queries are forwarded to the local BIND server or not.
  returned: changed
  type: bool
  sample: False
enable_dns_firewall:
  description: Whether DNS firewall capability is enabled or not.
  returned: changed
  type: bool
  sample: False
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
        'enableDnsFirewall': 'enable_dns_firewall',
        'useLocalBind': 'use_local_bind',
        'processRd': 'process_recursion_desired',
        'enableGtm': 'enable_gtm',
        'enableDnssec': 'enable_dnssec',
        'processXfr': 'enable_zone_transfer',
        'enableDnsExpress': 'enable_dns_express',
        'defaultsFrom': 'parent',
    }

    api_attributes = [
        'enableDnsFirewall',
        'useLocalBind',
        'processRd',
        'enableGtm',
        'enableDnssec',
        'processXfr',
        'enableDnsExpress',
        'defaultsFrom'
    ]

    returnables = [
        'enable_dns_firewall',
        'use_local_bind',
        'process_recursion_desired',
        'enable_gtm',
        'enable_dnssec',
        'enable_zone_transfer',
        'enable_dns_express',
    ]

    updatables = [
        'enable_dns_firewall',
        'use_local_bind',
        'process_recursion_desired',
        'enable_gtm',
        'enable_dnssec',
        'enable_zone_transfer',
        'enable_dns_express',
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


class ModuleParameters(Parameters):
    @property
    def parent(self):
        if self._values['parent'] is None:
            return None
        result = fq_name(self.partition, self._values['parent'])
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


class ReportableChanges(Changes):
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
        self.client = kwargs.get('client', None)
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
        result = self.client.api.tm.ltm.profile.dns_s.dns.exists(
            name=self.want.name,
            partition=self.want.partition
        )
        return result

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
        if self.want.enable_dns_express is None:
            self.want.update({'enable_dns_express': True})
        if self.want.enable_zone_transfer is None:
            self.want.update({'enable_zone_transfer': False})
        if self.want.enable_dnssec is None:
            self.want.update({'enable_dnssec': True})
        if self.want.enable_gtm is None:
            self.want.update({'enable_gtm': True})
        if self.want.process_recursion_desired is None:
            self.want.update({'process_recursion_desired': True})
        if self.want.use_local_bind is None:
            self.want.update({'use_local_bind': True})
        if self.want.enable_dns_firewall is None:
            self.want.update({'enable_dns_firewall': False})

        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        self.client.api.tm.ltm.profile.dns_s.dns.create(
            name=self.want.name,
            partition=self.want.partition,
            **params
        )

    def update_on_device(self):
        params = self.changes.api_params()
        resource = self.client.api.tm.ltm.profile.dns_s.dns.load(
            name=self.want.name,
            partition=self.want.partition
        )
        resource.modify(**params)

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove_from_device(self):
        resource = self.client.api.tm.ltm.profile.dns_s.dns.load(
            name=self.want.name,
            partition=self.want.partition
        )
        if resource:
            resource.delete()

    def read_current_from_device(self):
        resource = self.client.api.tm.ltm.profile.dns_s.dns.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result = resource.attrs
        return ApiParameters(params=result)


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
