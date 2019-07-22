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
module: bigip_profile_analytics
short_description: Manage HTTP analytics profiles on a BIG-IP
description:
  - Manage HTTP analytics profiles on a BIG-IP.
version_added: 2.8
options:
  name:
    description:
      - Specifies the name of the profile.
    type: str
    required: True
  parent:
    description:
      - Specifies the profile from which this profile inherits settings.
      - When creating a new profile, if this parameter is not specified, the default
        is the system-supplied C(analytics) profile.
    type: str
  description:
    description:
      - Description of the profile.
    type: str
  collect_geo:
    description:
      - Enables or disables the collection of the names of the countries
        from where the traffic was sent.
    type: bool
  collect_ip:
    description:
      - Enables or disables the collection of client IPs statistics.
    type: bool
  collect_max_tps_and_throughput:
    description:
      - Enables or disables the collection of maximum TPS and throughput
        for all collected entities.
    type: bool
  collect_page_load_time:
    description:
      - Enables or disables the collection of the page load time
        statistics.
    type: bool
  collect_url:
    description:
      - Enables or disables the collection of requested URL statistics.
    type: bool
  collect_user_agent:
    description:
      - Enables or disables the collection of user agents.
    type: bool
  collect_user_sessions:
    description:
      - Enables or disables the collection of the unique user sessions.
    type: bool
  collected_stats_external_logging:
    description:
      - Enables or disables the external logging of the collected
        statistics.
    type: bool
  collected_stats_internal_logging:
    description:
      - Enables or disables the internal logging of the collected
        statistics.
    type: bool
  external_logging_publisher:
    description:
      - Specifies the external logging publisher used to send statistical
        data to one or more destinations.
    type: str
  notification_by_syslog:
    description:
      - Enables or disables logging of the analytics alerts into the
        Syslog.
    type: bool
  notification_by_email:
    description:
      - Enables or disables sending the analytics alerts by email.
    type: bool
  notification_email_addresses:
    description:
      - Specifies which email addresses receive alerts by email when
        C(notification_by_email) is enabled.
    type: list
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
- name: Create a profile
  bigip_profile_analytics:
    name: profile1
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
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import flatten_boolean
    from library.module_utils.network.f5.compare import cmp_simple_list
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.compare import cmp_simple_list


class Parameters(AnsibleF5Parameters):
    api_map = {
        'defaultsFrom': 'parent',
        'collectGeo': 'collect_geo',
        'collectIp': 'collect_ip',
        'collectMaxTpsAndThroughput': 'collect_max_tps_and_throughput',
        'collectPageLoadTime': 'collect_page_load_time',
        'collectUrl': 'collect_url',
        'collectUserAgent': 'collect_user_agent',
        'collectUserSessions': 'collect_user_sessions',
        'collectedStatsExternalLogging': 'collected_stats_external_logging',
        'collectedStatsInternalLogging': 'collected_stats_internal_logging',
        'externalLoggingPublisher': 'external_logging_publisher',
        'notificationBySyslog': 'notification_by_syslog',
        'notificationByEmail': 'notification_by_email',
        'notificationEmailAddresses': 'notification_email_addresses'
    }

    api_attributes = [
        'description',
        'defaultsFrom',
        'collectGeo',
        'collectIp',
        'collectMaxTpsAndThroughput',
        'collectPageLoadTime',
        'collectUrl',
        'collectUserAgent',
        'collectUserSessions',
        'collectedStatsExternalLogging',
        'collectedStatsInternalLogging',
        'externalLoggingPublisher',
        'notificationBySyslog',
        'notificationByEmail',
        'notificationEmailAddresses',
    ]

    returnables = [
        'collect_geo',
        'collect_ip',
        'collect_max_tps_and_throughput',
        'collect_page_load_time',
        'collect_url',
        'collect_user_agent',
        'collect_user_sessions',
        'collected_stats_external_logging',
        'collected_stats_internal_logging',
        'description',
        'external_logging_publisher',
        'notification_by_syslog',
        'notification_by_email',
        'notification_email_addresses',
        'parent',
    ]

    updatables = [
        'collect_geo',
        'collect_ip',
        'collect_max_tps_and_throughput',
        'collect_page_load_time',
        'collect_url',
        'collect_user_agent',
        'collect_user_sessions',
        'collected_stats_external_logging',
        'collected_stats_internal_logging',
        'description',
        'external_logging_publisher',
        'notification_by_syslog',
        'notification_by_email',
        'notification_email_addresses',
        'parent',
    ]

    @property
    def external_logging_publisher(self):
        if self._values['external_logging_publisher'] is None:
            return None
        if self._values['external_logging_publisher'] in ['none', '']:
            return ''
        result = fq_name(self.partition, self._values['external_logging_publisher'])
        return result

    @property
    def collect_geo(self):
        return flatten_boolean(self._values['collect_geo'])

    @property
    def collect_ip(self):
        return flatten_boolean(self._values['collect_ip'])

    @property
    def collect_max_tps_and_throughput(self):
        return flatten_boolean(self._values['collect_max_tps_and_throughput'])

    @property
    def collect_page_load_time(self):
        return flatten_boolean(self._values['collect_page_load_time'])

    @property
    def collect_url(self):
        return flatten_boolean(self._values['collect_url'])

    @property
    def collect_user_agent(self):
        return flatten_boolean(self._values['collect_user_agent'])

    @property
    def collect_user_sessions(self):
        return flatten_boolean(self._values['collect_user_sessions'])

    @property
    def collected_stats_external_logging(self):
        return flatten_boolean(self._values['collected_stats_external_logging'])

    @property
    def collected_stats_internal_logging(self):
        return flatten_boolean(self._values['collected_stats_internal_logging'])

    @property
    def notification_by_syslog(self):
        return flatten_boolean(self._values['notification_by_syslog'])

    @property
    def notification_by_email(self):
        return flatten_boolean(self._values['notification_by_email'])


class ApiParameters(Parameters):
    @property
    def description(self):
        if self._values['description'] in [None, 'none']:
            return None
        return self._values['description']


class ModuleParameters(Parameters):
    @property
    def description(self):
        if self._values['description'] is None:
            return None
        elif self._values['description'] in ['none', '']:
            return ''
        return self._values['description']

    @property
    def parent(self):
        if self._values['parent'] is None:
            return None
        result = fq_name(self.partition, self._values['parent'])
        return result

    @property
    def notification_email_addresses(self):
        if self._values['notification_email_addresses'] is None:
            return None
        elif len(self._values['notification_email_addresses']) == 1 and self._values['notification_email_addresses'][0] in ['', 'none']:
            return []
        return self._values['notification_email_addresses']


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
    def collect_geo(self):
        if self._values['collect_geo'] is None:
            return None
        elif self._values['collect_geo'] == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def collect_ip(self):
        if self._values['collect_ip'] is None:
            return None
        elif self._values['collect_ip'] == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def collect_max_tps_and_throughput(self):
        if self._values['collect_max_tps_and_throughput'] is None:
            return None
        elif self._values['collect_max_tps_and_throughput'] == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def collect_page_load_time(self):
        if self._values['collect_page_load_time'] is None:
            return None
        elif self._values['collect_page_load_time'] == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def collect_url(self):
        if self._values['collect_url'] is None:
            return None
        elif self._values['collect_url'] == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def collect_user_agent(self):
        if self._values['collect_user_agent'] is None:
            return None
        elif self._values['collect_user_agent'] == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def collect_user_sessions(self):
        if self._values['collect_user_sessions'] is None:
            return None
        elif self._values['collect_user_sessions'] == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def collected_stats_external_logging(self):
        if self._values['collected_stats_external_logging'] is None:
            return None
        elif self._values['collected_stats_external_logging'] == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def collected_stats_internal_logging(self):
        if self._values['collected_stats_internal_logging'] is None:
            return None
        elif self._values['collected_stats_internal_logging'] == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def notification_by_syslog(self):
        if self._values['notification_by_syslog'] is None:
            return None
        elif self._values['notification_by_syslog'] == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def notification_by_email(self):
        if self._values['notification_by_email'] is None:
            return None
        elif self._values['notification_by_email'] == 'yes':
            return 'enabled'
        return 'disabled'


class ReportableChanges(Changes):
    @property
    def collect_geo(self):
        return flatten_boolean(self._values['collect_geo'])

    @property
    def collect_ip(self):
        return flatten_boolean(self._values['collect_ip'])

    @property
    def collect_max_tps_and_throughput(self):
        return flatten_boolean(self._values['collect_max_tps_and_throughput'])

    @property
    def collect_page_load_time(self):
        return flatten_boolean(self._values['collect_page_load_time'])

    @property
    def collect_url(self):
        return flatten_boolean(self._values['collect_url'])

    @property
    def collect_user_agent(self):
        return flatten_boolean(self._values['collect_user_agent'])

    @property
    def collect_user_sessions(self):
        return flatten_boolean(self._values['collect_user_sessions'])

    @property
    def collected_stats_external_logging(self):
        return flatten_boolean(self._values['collected_stats_external_logging'])

    @property
    def collected_stats_internal_logging(self):
        return flatten_boolean(self._values['collected_stats_internal_logging'])

    @property
    def notification_by_syslog(self):
        return flatten_boolean(self._values['notification_by_syslog'])

    @property
    def notification_by_email(self):
        return flatten_boolean(self._values['notification_by_email'])


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
    def parent(self):
        if self.want.parent is None:
            return None
        if self.want.parent != self.have.parent:
            raise F5ModuleError(
                "The parent profile cannot be changed"
            )

    @property
    def description(self):
        if self.want.description is None:
            return None
        if self.have.description is None and self.want.description == '':
            return None
        if self.want.description != self.have.description:
            return self.want.description

    @property
    def notification_email_addresses(self):
        return cmp_simple_list(self.want.notification_email_addresses, self.have.notification_email_addresses)

    @property
    def external_logging_publisher(self):
        if self.want.external_logging_publisher is None:
            return None
        if self.have.external_logging_publisher is None and self.want.external_logging_publisher == '':
            return None
        if self.want.external_logging_publisher != self.have.external_logging_publisher:
            return self.want.external_logging_publisher


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
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/analytics/{2}".format(
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/analytics/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 409, 404]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return True

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/analytics/{2}".format(
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

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/analytics/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/analytics/{2}".format(
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
            description=dict(),
            collect_geo=dict(type='bool'),
            collect_ip=dict(type='bool'),
            collect_max_tps_and_throughput=dict(type='bool'),
            collect_page_load_time=dict(type='bool'),
            collect_url=dict(type='bool'),
            collect_user_agent=dict(type='bool'),
            collect_user_sessions=dict(type='bool'),
            collected_stats_external_logging=dict(type='bool'),
            collected_stats_internal_logging=dict(type='bool'),
            external_logging_publisher=dict(),
            notification_by_syslog=dict(type='bool'),
            notification_by_email=dict(type='bool'),
            notification_email_addresses=dict(type='list'),
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
