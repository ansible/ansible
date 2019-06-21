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
module: bigip_firewall_schedule
short_description: Manage BIG-IP AFM schedule configurations
description:
  - Manage BIG-IP AFM schedule configurations.
version_added: 2.9
options:
  name:
    description:
      - Specifies the name of the AFM schedule configuration.
    type: str
    required: True
  description:
    description:
      - Specifies the user defined description text.
    type: str
  daily_hour_end:
    description:
      - Specifies the time of day the rule will stop being used.
      - When not defined, the default of C(24:00) is used when creating a new schedule.
      - The time zone is always assumed to be UTC and values must be provided as C(HH:MM) using 24hour clock format.
    type: str
  daily_hour_start:
    description:
      - Specifies the time of day the rule will start to be in use.
      - The value must be a time before C(daily_hour_end).
      - When not defined, the default of C(0:00) is used when creating a new schedule.
      - When the value is set to C(all-day) both C(daily_hour_end) and C(daily_hour_start) are reset to their respective
        defaults.
      - The time zone is always assumed to be UTC and values must be provided as C(HH:MM) using 24hour clock format.
    type: str
  date_valid_end:
    description:
      - Specifies the end date/time this schedule will apply to the rule.
      - The date must be after C(date_valid_start)
      - When not defined the default of C(indefinite) is used when creating a new schedule.
      - The time zone is always assumed to be UTC.
      - The datetime format should always be the following C(YYYY-MM-DD:HH:MM:SS) format.
    type: str
  date_valid_start:
    description:
      - Specifies the start date/time this schedule will apply to the rule.
      - When not defined the default of C(epoch) is used when creating a new schedule.
      - The time zone is always assumed to be UTC.
      - The datetime format should always be the following C(YYYY-MM-DD:HH:MM:SS) format.
    type: str
  days_of_week:
    description:
      - Specifies which days of the week the rule will be applied.
      - When not defined the default value of C(all) is used when creating a new schedule.
      - The C(all) value is mutually exclusive with other choices.
    type: list
    choices:
      - sunday
      - monday
      - tuesday
      - wednesday
      - thursday
      - friday
      - saturday
      - all
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
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Create a 6 hour two day schedule, no start/end date
  bigip_firewall_schedule:
    name: barfoo
    daily_hour_start: 13:00
    daily_hour_end: 19:00
    days_of_week:
      - monday
      - tuesday
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Create a seven day schedule with start/end date
  bigip_firewall_schedule:
    name: foobar
    date_valid_start: "{{ lookup('pipe','date +%Y-%m-%d:%H:%M:%S') }}"
    date_valid_end: "{{ lookup('pipe','date -d \"now + 7 days\" +%Y-%m-%d:%H:%M:%S') }}"
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Modify created schedule to all-day
  bigip_firewall_schedule:
    name: barfoo
    daily_hour_start: all-day
    days_of_week:
      - monday
      - tuesday
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Modify a schedule to have no end date
  bigip_firewall_schedule:
    name: foobar
    date_valid_start: "{{ lookup('pipe','date +%Y-%m-%d:%H:%M:%S') }}"
    date_valid_end: "indefinite"
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Remove created schedule
  bigip_firewall_schedule:
    name: foobar
    state: absent
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
daily_hour_start:
  description: The time of day the rule will start to be in use.
  returned: changed
  type: str
  sample: '13:00'
daily_hour_end:
  description: The time of day the rule will stop being used.
  returned: changed
  type: str
  sample: '18:00'
date_valid_start:
  description: The start date/time schedule will apply to the rule.
  returned: changed
  type: str
  sample: 2019-03-01:15:30:00
date_valid_end:
  description: The end date/time schedule will apply to the rule.
  returned: changed
  type: str
  sample: 2019-03-11:15:30:00
days_of_week:
  description: The days of the week the rule will be applied.
  returned: changed
  type: list
  sample: ["monday","tuesday"]
description:
  description: The user defined description text.
  returned: changed
  type: str
  sample: Foo is bar
'''

import re
import datetime
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.compare import cmp_str_with_none
    from library.module_utils.network.f5.compare import cmp_simple_list
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.compare import cmp_str_with_none
    from ansible.module_utils.network.f5.compare import cmp_simple_list


class Parameters(AnsibleF5Parameters):
    api_map = {
        'dailyHourEnd': 'daily_hour_end',
        'dailyHourStart': 'daily_hour_start',
        'dateValidEnd': 'date_valid_end',
        'dateValidStart': 'date_valid_start',
        'daysOfWeek': 'days_of_week',
    }

    api_attributes = [
        'dailyHourEnd',
        'dailyHourStart',
        'dateValidEnd',
        'dateValidStart',
        'daysOfWeek',
        'description',
    ]

    returnables = [
        'daily_hour_end',
        'daily_hour_start',
        'date_valid_end',
        'date_valid_start',
        'days_of_week',
        'description'
    ]

    updatables = [
        'daily_hour_end',
        'daily_hour_start',
        'date_valid_end',
        'date_valid_start',
        'days_of_week',
        'description'
    ]


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    def _convert_datetime(self, value):
        p = r'(\d{4})-(\d{1,2})-(\d{1,2})[:, T](\d{2}):(\d{2}):(\d{2})'
        match = re.match(p, value)
        if match:
            date = '{0}-{1}-{2}T{3}:{4}:{5}Z'.format(*match.group(1, 2, 3, 4, 5, 6))
            return date
        raise F5ModuleError(
            'Invalid datetime provided.'
        )

    def _validate_time(self, value):
        p = r'(\d{2}):(\d{2})'
        match = re.match(p, value)
        if match:
            time = int(match.group(1)), int(match.group(2))
            try:
                datetime.time(*time)
            except ValueError as ex:
                raise F5ModuleError(str(ex))

    def _compare_date_time(self, value1, value2, time=False):
        if time:
            p1 = r'(\d{2}):(\d{2})'
            m1 = re.match(p1, value1)
            m2 = re.match(p1, value2)
            if m1 and m2:
                start = tuple(int(i) for i in m1.group(1, 2))
                end = tuple(int(i) for i in m2.group(1, 2))
                if datetime.time(*start) > datetime.time(*end):
                    raise F5ModuleError(
                        'End time must be later than start time.'
                    )
        else:
            p1 = r'(\d{4})-(\d{1,2})-(\d{1,2})[:, T](\d{2}):(\d{2}):(\d{2})'
            m1 = re.match(p1, value1)
            m2 = re.match(p1, value2)
            if m1 and m2:
                start = tuple(int(i) for i in m1.group(1, 2, 3, 4, 5, 6))
                end = tuple(int(i) for i in m2.group(1, 2, 3, 4, 5, 6))
                if datetime.datetime(*start) > datetime.datetime(*end):
                    raise F5ModuleError(
                        'End date must be later than start date.'
                    )

    @property
    def daily_hour_start(self):
        if self._values['daily_hour_start'] is None:
            return None
        if self._values['daily_hour_start'] == 'all-day':
            return '0:00'
        self._validate_time(self._values['daily_hour_start'])
        if self._values['daily_hour_end'] is not None and self.daily_hour_end != '24:00':
            self._compare_date_time(self._values['daily_hour_start'], self.daily_hour_end, time=True)
        return self._values['daily_hour_start']

    @property
    def daily_hour_end(self):
        if self._values['daily_hour_end'] is None:
            return None
        if self._values['daily_hour_start'] == 'all-day':
            return '24:00'
        if not self._values['daily_hour_end'] == '24:00':
            self._validate_time(self._values['daily_hour_end'])
        return self._values['daily_hour_end']

    @property
    def date_valid_end(self):
        if self._values['date_valid_end'] is None:
            return None
        if self._values['date_valid_end'] in ['2038-1-18:19:14:07', 'indefinite']:
            return 'indefinite'
        result = self._convert_datetime(self._values['date_valid_end'])
        return result

    @property
    def date_valid_start(self):
        if self._values['date_valid_start'] is None:
            return None
        if self._values['date_valid_start'] in ['1970-1-1:00:00:00', 'epoch']:
            return 'epoch'
        result = self._convert_datetime(self._values['date_valid_start'])
        if self._values['date_valid_end']:
            if self._values['date_valid_end'] not in ['2038-1-18:19:14:07', 'indefinite']:
                self._compare_date_time(result, self.date_valid_end)
        return result

    @property
    def days_of_week(self):
        if self._values['days_of_week'] is None:
            return None
        if 'all' in self._values['days_of_week']:
            if len(self._values['days_of_week']) > 1 and self._values['days_of_week'] is list:
                raise F5ModuleError(
                    "The 'all' value must not be specified with other choices."
                )
            week = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
            return week
        return self._values['days_of_week']


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
    def _convert_datetime(self, value):
        if value is None:
            return None
        p = r'(\d{4})-(\d{1,2})-(\d{1,2})[:, T](\d{2}):(\d{2}):(\d{2})'
        match = re.match(p, value)
        if match:
            date = '{0}-{1}-{2}:{3}:{4}:{5}'.format(*match.group(1, 2, 3, 4, 5, 6))
            return date

    @property
    def date_valid_end(self):
        result = self._convert_datetime(self._values['date_valid_end'])
        return result

    @property
    def date_valid_start(self):
        result = self._convert_datetime(self._values['date_valid_start'])
        return result

    @property
    def days_of_week(self):
        if self._values['days_of_week'] is None:
            return None
        if len(self._values['days_of_week']) == 7:
            return 'all'


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
    def description(self):
        return cmp_str_with_none(self.want.description, self.have.description)

    @property
    def days_of_week(self):
        return cmp_simple_list(self.want.days_of_week, self.have.days_of_week)


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
        uri = "https://{0}:{1}/mgmt/tm/security/firewall/schedule/{2}".format(
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
        uri = "https://{0}:{1}/mgmt/tm/security/firewall/schedule/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 409]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return True

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/security/firewall/schedule/{2}".format(
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

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/security/firewall/schedule/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/security/firewall/schedule/{2}".format(
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
            name=dict(
                required=True
            ),
            description=dict(),
            daily_hour_end=dict(),
            daily_hour_start=dict(),
            date_valid_end=dict(),
            date_valid_start=dict(),
            days_of_week=dict(
                type='list',
                choices=[
                    'sunday',
                    'monday',
                    'tuesday',
                    'wednesday',
                    'thursday',
                    'friday',
                    'saturday',
                    'all',
                ]
            ),
            state=dict(default='present', choices=['absent', 'present']),
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
