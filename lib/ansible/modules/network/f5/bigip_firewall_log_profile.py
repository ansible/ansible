#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_firewall_log_profile
short_description: Manages AFM logging profiles configured in the system
description:
  - Manages AFM logging profiles configured in the system along with basic information about each profile.
version_added: 2.9
options:
  name:
    description:
      - Specifies the name of the log profile.
    type: str
    required: True
  description:
    description:
      - Description of the log profile.
    type: str
  dos_protection:
    description:
      - Configures DoS related settings of the log profile.
    suboptions:
      dns_publisher:
        description:
          - Specifies the name of the log publisher used for DNS DoS events.
          - To specify the log_publisher on a different partition from the AFM log profile, specify the name in fullpath
            format, e.g. C(/Foobar/log-publisher), otherwise the partition for log publisher
            is inferred from C(partition) module parameter.
        type: str
      sip_publisher:
        description:
          - Specifies the name of the log publisher used for SIP DoS events.
          - To specify the log_publisher on a different partition from the AFM log profile, specify the name in fullpath
            format, e.g. C(/Foobar/log-publisher), otherwise the partition for log publisher
            is inferred from C(partition) module parameter.
        type: str
      network_publisher:
        description:
          - Specifies the name of the log publisher used for DoS Network events.
          - To specify the log_publisher on a different partition from the AFM log profile, specify the name in fullpath
            format, e.g. C(/Foobar/log-publisher), otherwise the partition for log publisher
            is inferred from C(partition) module parameter.
        type: str
    type: dict
  ip_intelligence:
    description:
      - Configures IP Intelligence related settings of the log profile.
    suboptions:
      log_publisher:
        description:
          - Specifies the name of the log publisher used for IP Intelligence events.
          - To specify the log_publisher on a different partition from the AFM log profile, specify the name in fullpath
            format, e.g. C(/Foobar/log-publisher), otherwise the partition for log publisher
            is inferred from C(partition) module parameter.
        type: str
      rate_limit:
        description:
          - Defines a rate limit for all combined IP intelligence log messages per second. Beyond this rate limit,
            log messages are not logged until the threshold drops below the specified rate.
          - To specify an indefinite rate, use the value C(indefinite).
          - If specifying a numeric rate, the value must be between C(1) and C(4294967295).
        type: str
      log_rtbh:
        description:
          - Specifies, when C(yes), that remotely triggered blackholing events are logged.
        type: bool
      log_shun:
        description:
          - Specifies, when C(yes), that IP Intelligence shun list events are logged.
          - This option can only be set on C(global-network) built-in profile
        type: bool
      log_translation_fields:
        description:
          - This option is used to enable or disable the logging of translated (i.e server side) fields in IP
            Intelligence log messages.
          - Translated fields include (but are not limited to) source address/port, destination address/port,
            IP protocol, route domain, and VLAN.
        type: bool
    type: dict
  port_misuse:
    description:
      - Port Misuse log configuration.
    suboptions:
      log_publisher:
        description:
          - Specifies the name of the log publisher used for Port Misuse events.
          - To specify the log_publisher on a different partition from the AFM log profile, specify the name in fullpath
            format, e.g. C(/Foobar/log-publisher), otherwise the partition for log publisher
            is inferred from C(partition) module parameter.
        type: str
      rate_limit:
        description:
          - Defines a rate limit for all combined port misuse log messages per second. Beyond this rate limit,
            log messages are not logged until the threshold drops below the specified rate.
          - To specify an indefinite rate, use the value C(indefinite).
          - If specifying a numeric rate, the value must be between C(1) and C(4294967295).
        type: str
    type: dict
  partition:
    description:
      - Device partition to create log profile on.
      - Parameter also used when specifying names for log publishers, unless log publisher names are in fullpath format.
    type: str
    default: Common
  state:
    description:
      - When C(state) is C(present), ensures the resource exists.
      - When C(state) is C(absent), ensures that resource is removed. Attempts to remove built-in system profiles are
        ignored and no change is returned.
    type: str
    choices:
      - present
      - absent
    default: present
extends_documentation_fragment: f5
author:
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Create a basic log profile with port misuse
  bigip_firewall_log_profile:
    name: barbaz
    port_misuse:
      rate_limit: 30000
      log_publisher: local-db-pub
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Change ip_intelligence settings, publisher on different partition, remove port misuse
  bigip_firewall_log_profile:
    name: barbaz
    ip_intelligence:
      rate_limit: 400000
      log_translation_fields: yes
      log_rtbh: yes
      log_publisher: "/foobar/non-local-db"
    port_misuse:
      log_publisher: ""
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Create a log profile with dos protection, different partition
  bigip_firewall_log_profile:
    name: foobar
    partition: foobar
    dos_protection:
      dns_publisher: "/Common/local-db-pub"
      sip_publisher: "non-local-db"
      network_publisher: "/Common/local-db-pub"
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Remove log profile
  bigip_firewall_log_profile:
    name: barbaz
    partition: Common
    state: absent
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
description:
  description: New description of the AFM log profile.
  returned: changed
  type: str
  sample: This is my description
dos_protection:
  description: Log publishers used in DoS related settings of the log profile.
  type: complex
  returned: changed
  contains:
    dns_publisher:
      description: The name of the log publisher used for DNS DoS events.
      returned: changed
      type: str
      sample: "/Common/local-db-publisher"
    sip_publisher:
      description: The name of the log publisher used for SIP DoS events.
      returned: changed
      type: str
      sample: "/Common/local-db-publisher"
    network_publisher:
      description: The name of the log publisher used for DoS Network events.
      returned: changed
      type: str
      sample: "/Common/local-db-publisher"
  sample: hash/dictionary of values
ip_intelligence:
  description: IP Intelligence related settings of the log profile.
  type: complex
  returned: changed
  contains:
    log_publisher:
      description: The name of the log publisher used for IP Intelligence events.
      returned: changed
      type: str
      sample: "/Common/local-db-publisher"
    rate_limit:
      description: The rate limit for all combined IP intelligence log messages per second.
      returned: changed
      type: str
      sample: "indefinite"
    log_rtbh:
      description: Logging of remotely triggered blackholing events.
      returned: changed
      type: bool
      sample: yes
    log_shun:
      description: Logging of IP Intelligence shun list events.
      returned: changed
      type: bool
      sample: no
    log_translation_fields:
      description: Logging of translated fields in IP Intelligence log messages.
      returned: changed
      type: bool
      sample: no
  sample: hash/dictionary of values
port_misuse:
  description: Port Misuse related settings of the log profile.
  type: complex
  returned: changed
  contains:
    log_publisher:
      description: The name of the log publisher used for Port Misuse events.
      returned: changed
      type: str
      sample: "/Common/local-db-publisher"
    rate_limit:
      description: The rate limit for all combined Port Misuse log messages per second.
      returned: changed
      type: str
      sample: "indefinite"
  sample: hash/dictionary of values
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
    from library.module_utils.network.f5.common import flatten_boolean
    from library.module_utils.network.f5.compare import compare_dictionary
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.compare import compare_dictionary


class Parameters(AnsibleF5Parameters):
    api_map = {
        'ipIntelligence': 'ip_intelligence',
        'portMisuse': 'port_misuse',
        'protocolDnsDosPublisher': 'dns_publisher',
        'protocolSipDosPublisher': 'sip_publisher',
        'dosNetworkPublisher': 'network_publisher',
    }

    api_attributes = [
        'description',
        'ipIntelligence',
        'portMisuse',
        'dosNetworkPublisher',
        'protocolDnsDosPublisher',
        'protocolSipDosPublisher',
    ]

    returnables = [
        'ip_intelligence',
        'dns_publisher',
        'sip_publisher',
        'network_publisher',
        'port_misuse',
        'description',
        'ip_log_publisher',
        'ip_rate_limit',
        'ip_log_rthb',
        'ip_log_shun',
        'ip_log_translation_fields',
        'port_rate_limit',
        'port_log_publisher',
    ]

    updatables = [
        'dns_publisher',
        'sip_publisher',
        'network_publisher',
        'description',
        'ip_log_publisher',
        'ip_rate_limit',
        'ip_log_rthb',
        'ip_log_shun',
        'ip_log_translation_fields',
        'port_rate_limit',
        'port_log_publisher',
    ]


class ApiParameters(Parameters):
    @property
    def ip_log_publisher(self):
        result = self._values['ip_intelligence'].get('logPublisher', None)
        return result

    @property
    def ip_rate_limit(self):
        return self._values['ip_intelligence']['aggregateRate']

    @property
    def port_rate_limit(self):
        return self._values['port_misuse']['aggregateRate']

    @property
    def port_log_publisher(self):
        result = self._values['port_misuse'].get('logPublisher', None)
        return result

    @property
    def ip_log_rtbh(self):
        return self._values['ip_intelligence']['logRtbh']

    @property
    def ip_log_shun(self):
        if self._values['name'] != 'global-network':
            return None
        return self._values['ip_intelligence']['logShun']

    @property
    def ip_log_translation_fields(self):
        return self._values['ip_intelligence']['logTranslationFields']


class ModuleParameters(Parameters):
    def _transform_log_publisher(self, log_publisher):
        if log_publisher is None:
            return None
        if log_publisher in ['', 'none']:
            return {}
        return fq_name(self.partition, log_publisher)

    def _validate_rate_limit(self, rate_limit):
        if rate_limit is None:
            return None
        if rate_limit == 'indefinite':
            return 4294967295
        if 0 <= int(rate_limit) <= 4294967295:
            return int(rate_limit)
        raise F5ModuleError(
            "Valid 'maximum_age' must be in range 0 - 4294967295, or 'indefinite'."
        )

    @property
    def ip_log_rtbh(self):
        if self._values['ip_intelligence'] is None:
            return None
        result = flatten_boolean(self._values['ip_intelligence']['log_rtbh'])
        if result == 'yes':
            return 'enabled'
        if result == 'no':
            return 'disabled'
        return result

    @property
    def ip_log_shun(self):
        if self._values['ip_intelligence'] is None:
            return None
        if 'global-network' not in self._values['name']:
            return None
        result = flatten_boolean(self._values['ip_intelligence']['log_shun'])
        if result == 'yes':
            return 'enabled'
        if result == 'no':
            return 'disabled'
        return result

    @property
    def ip_log_translation_fields(self):
        if self._values['ip_intelligence'] is None:
            return None
        result = flatten_boolean(self._values['ip_intelligence']['log_translation_fields'])
        if result == 'yes':
            return 'enabled'
        if result == 'no':
            return 'disabled'
        return result

    @property
    def ip_log_publisher(self):
        if self._values['ip_intelligence'] is None:
            return None
        result = self._transform_log_publisher(self._values['ip_intelligence']['log_publisher'])
        return result

    @property
    def ip_rate_limit(self):
        if self._values['ip_intelligence'] is None:
            return None
        return self._validate_rate_limit(self._values['ip_intelligence']['rate_limit'])

    @property
    def port_rate_limit(self):
        if self._values['port_misuse'] is None:
            return None
        return self._validate_rate_limit(self._values['port_misuse']['rate_limit'])

    @property
    def port_log_publisher(self):
        if self._values['port_misuse'] is None:
            return None
        result = self._transform_log_publisher(self._values['port_misuse']['log_publisher'])
        return result

    @property
    def dns_publisher(self):
        if self._values['dos_protection'] is None:
            return None
        result = self._transform_log_publisher(self._values['dos_protection']['dns_publisher'])
        return result

    @property
    def sip_publisher(self):
        if self._values['dos_protection'] is None:
            return None
        result = self._transform_log_publisher(self._values['dos_protection']['sip_publisher'])
        return result

    @property
    def network_publisher(self):
        if self._values['dos_protection'] is None:
            return None
        result = self._transform_log_publisher(self._values['dos_protection']['network_publisher'])
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
    def ip_intelligence(self):
        to_filter = dict(
            logPublisher=self._values['ip_log_publisher'],
            aggregateRate=self._values['ip_rate_limit'],
            logRtbh=self._values['ip_log_rtbh'],
            logShun=self._values['ip_log_shun'],
            logTranslationFields=self._values['ip_log_translation_fields']
        )
        result = self._filter_params(to_filter)
        if result:
            return result

    @property
    def port_misuse(self):
        to_filter = dict(
            logPublisher=self._values['port_log_publisher'],
            aggregateRate=self._values['port_rate_limit']
        )
        result = self._filter_params(to_filter)
        if result:
            return result


class ReportableChanges(Changes):
    returnables = [
        'ip_intelligence',
        'port_misuse',
        'description',
        'dos_protection',
    ]

    def _change_rate_limit_value(self, value):
        if value == 4294967295:
            return 'indefinite'
        else:
            return value

    @property
    def ip_log_rthb(self):
        result = flatten_boolean(self._values['ip_log_rtbh'])
        return result

    @property
    def ip_log_shun(self):
        result = flatten_boolean(self._values['ip_log_shun'])
        return result

    @property
    def ip_log_translation_fields(self):
        result = flatten_boolean(self._values['ip_log_translation_fields'])
        return result

    @property
    def ip_intelligence(self):
        if self._values['ip_intelligence'] is None:
            return None
        to_filter = dict(
            log_publisher=self._values['ip_log_publisher'],
            rate_limit=self._change_rate_limit_value(self._values['ip_rate_limit']),
            log_rtbh=self.ip_log_rtbh,
            log_shun=self.ip_log_shun,
            log_translation_fields=self.ip_log_translation_fields
        )
        result = self._filter_params(to_filter)
        if result:
            return result

    @property
    def port_misuse(self):
        if self._values['port_misuse'] is None:
            return None
        to_filter = dict(
            log_publisher=self._values['port_log_publisher'],
            rate_limit=self._change_rate_limit_value(self._values['port_rate_limit']),
        )
        result = self._filter_params(to_filter)
        if result:
            return result

    @property
    def dos_protection(self):
        to_filter = dict(
            dns_publisher=self._values['dns_publisher'],
            sip_publisher=self._values['sip_publisher'],
            network_publisher=self._values['network_publisher'],
        )
        result = self._filter_params(to_filter)
        return result


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
    def ip_log_publisher(self):
        result = compare_dictionary(self.want.ip_log_publisher, self.have.ip_log_publisher)
        return result

    @property
    def port_log_publisher(self):
        result = compare_dictionary(self.want.port_log_publisher, self.have.port_log_publisher)
        return result

    @property
    def dns_publisher(self):
        result = compare_dictionary(self.want.dns_publisher, self.have.dns_publisher)
        return result

    @property
    def sip_publisher(self):
        result = compare_dictionary(self.want.sip_publisher, self.have.sip_publisher)
        return result

    @property
    def network_publisher(self):
        result = compare_dictionary(self.want.network_publisher, self.have.network_publisher)
        return result


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

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.client.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

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

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def absent(self):
        # Built-in profiles cannot be removed
        built_ins = [
            'Log all requests', 'Log illegal requests',
            'global-network', 'local-dos'
        ]
        if self.want.name in built_ins:
            return False
        if self.exists():
            return self.remove()
        return False

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

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/security/log/profile/{2}".format(
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

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/security/log/profile/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 404, 409]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return True

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/security/log/profile/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.patch(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 404, 409]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/security/log/profile/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/security/log/profile/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 404, 409]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return ApiParameters(params=response)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(
                required=True
            ),
            description=dict(),
            dos_protection=dict(
                type='dict',
                options=dict(
                    dns_publisher=dict(),
                    sip_publisher=dict(),
                    network_publisher=dict()
                )
            ),
            ip_intelligence=dict(
                type='dict',
                options=dict(
                    log_publisher=dict(),
                    log_translation_fields=dict(type='bool'),
                    rate_limit=dict(),
                    log_rtbh=dict(type='bool'),
                    log_shun=dict(type='bool')
                )
            ),
            port_misuse=dict(
                type='dict',
                options=dict(
                    log_publisher=dict(),
                    rate_limit=dict()
                )
            ),
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
