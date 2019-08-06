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
module: bigip_monitor_dns
short_description: Manage DNS monitors on a BIG-IP
description:
  - Manages DNS monitors on a BIG-IP.
version_added: 2.7
options:
  name:
    description:
      - Specifies the name of the monitor.
    type: str
    required: True
  parent:
    description:
      - The parent template of this monitor template. Once this value has
        been set, it cannot be changed. By default, this value is the C(dns)
        parent on the C(Common) partition.
    type: str
    default: /Common/dns
  description:
    description:
      - The description of the monitor.
    type: str
  interval:
    description:
      - The interval specifying how frequently the monitor instance of this
        template will run.
      - This value B(must) be less than the C(timeout) value.
      - When creating a new monitor, if this parameter is not provided, the
        default C(5) will be used.
    type: int
  up_interval:
    description:
      - Specifies the interval for the system to use to perform the health check
        when a resource is up.
      - When C(0), specifies that the system uses the interval specified in
        C(interval) to check the health of the resource.
      - When any other number, enables specification of a different interval to
        use when checking the health of a resource that is up.
      - When creating a new monitor, if this parameter is not provided, the
        default C(0) will be used.
    type: int
  timeout:
    description:
      - The number of seconds in which the node or service must respond to
        the monitor request.
      - If the target responds within the set time period, it is considered up.
      - If the target does not respond within the set time period, it is considered down.
      - You can change this number to any number you want, however, it should be 3 times the
        interval number of seconds plus 1 second.
      - If this parameter is not provided when creating a new monitor, then the default
        value will be C(16).
    type: int
  transparent:
    description:
      - Specifies whether the monitor operates in transparent mode.
      - Monitors in transparent mode can monitor pool members through firewalls.
      - When creating a new monitor, if this parameter is not provided, then the default
        value will be C(no).
    type: bool
  reverse:
    description:
      - Specifies whether the monitor operates in reverse mode.
      - When the monitor is in reverse mode, a successful receive string match
        marks the monitored object down instead of up. You can use the
        this mode only if you configure the C(receive) option.
      - This parameter is not compatible with the C(time_until_up) parameter. If
        C(time_until_up) is specified, it must be C(0). Or, if it already exists, it
        must be C(0).
    type: bool
  receive:
    description:
      - Specifies the IP address that the monitor uses from the resource record sections
        of the DNS response.
      - The IP address should be specified in the dotted-decimal notation or IPv6 notation.
    type: str
  time_until_up:
    description:
      - Specifies the amount of time in seconds after the first successful
        response before a node will be marked up.
      - A value of 0 will cause a node to be marked up immediately after a valid
        response is received from the node.
      - If this parameter is not provided when creating a new monitor, then the default
        value will be C(0).
    type: int
  manual_resume:
    description:
      - Specifies whether the system automatically changes the status of a resource
        to B(enabled) at the next successful monitor check.
      - If you set this option to C(yes), you must manually re-enable the resource
        before the system can use it for load balancing connections.
      - When creating a new monitor, if this parameter is not specified, the default
        value is C(no).
      - When C(yes), specifies that you must manually re-enable the resource after an
        unsuccessful monitor check.
      - When C(no), specifies that the system automatically changes the status of a
        resource to B(enabled) at the next successful monitor check.
    type: bool
  ip:
    description:
      - IP address part of the IP/port definition.
      - If this parameter is not provided when creating a new monitor, then the
        default value will be C(*).
    type: str
  port:
    description:
      - Port address part of the IP/port definition.
      - If this parameter is not provided when creating a new monitor, then the default
        value will be C(*).
      - Note that if specifying an IP address, a value between 1 and 65535 must be specified.
    type: str
  query_name:
    description:
      - Specifies a query name for the monitor to use in a DNS query.
    type: str
  query_type:
    description:
      - Specifies the type of DNS query that the monitor sends.
      - When creating a new monitor, if this parameter is not specified, the default
        value is C(a).
      - When C(a), specifies that the monitor will send a DNS query of type A.
      - When C(aaaa), specifies that the monitor will send a DNS query of type AAAA.
    type: str
    choices:
      - a
      - aaaa
  answer_section_contains:
    description:
      - Specifies the type of DNS query that the monitor sends.
      - When creating a new monitor, if this value is not specified, the default
        value is C(query-type).
      - When C(query-type), specifies that the response should contain at least one
        answer of which the resource record type matches the query type.
      - When C(any-type), specifies that the DNS message should contain at least one answer.
      - When C(anything), specifies that an empty answer is enough to mark the status of
        the node up.
    type: str
    choices:
      - any-type
      - anything
      - query-type
  accept_rcode:
    description:
      - Specifies the RCODE required in the response for an up status.
      - When creating a new monitor, if this parameter is not specified, the default
        value is C(no-error).
      - When C(no-error), specifies that the status of the node will be marked up if
        the received DNS message has no error.
      - When C(anything), specifies that the status of the node will be marked up
        irrespective of the RCODE in the DNS message received.
      - If this parameter is set to C(anything), it will disregard the C(receive)
        string, and nullify it if the monitor is being updated.
    type: str
    choices:
      - no-error
      - anything
  adaptive:
    description:
      - Specifies whether adaptive response time monitoring is enabled for this monitor.
      - When C(yes), the monitor determines the state of a service based on how divergent
        from the mean latency a monitor probe for that service is allowed to be.
        Also, values for the C(allowed_divergence), C(adaptive_limit), and
        and C(sampling_timespan) will be enforced.
      - When C(disabled), the monitor determines the state of a service based on the
        C(interval), C(up_interval), C(time_until_up), and C(timeout) monitor settings.
    type: bool
  allowed_divergence_type:
    description:
      - When specifying a new monitor, if C(adaptive) is C(yes), the default is
        C(relative)
      - When C(absolute), the number of milliseconds the latency of a monitor probe
        can exceed the mean latency of a monitor probe for the service being probed.
        In typical cases, if the monitor detects three probes in a row that miss the
        latency value you set, the pool member or node is marked down.
      - When C(relative), the percentage of deviation the latency of a monitor probe
        can exceed the mean latency of a monitor probe for the service being probed.
    type: str
    choices:
      - relative
      - absolute
  allowed_divergence_value:
    description:
      - When specifying a new monitor, if C(adaptive) is C(yes), and C(type) is
        C(relative), the default is C(25) percent.
    type: int
  adaptive_limit:
    description:
      - Specifies the absolute number of milliseconds that may not be exceeded by a monitor
        probe, regardless of C(allowed_divergence) setting, for a probe to be
        considered successful.
      - This value applies regardless of the value of the C(allowed_divergence) setting.
      - While this value can be configured when C(adaptive) is C(no), it will not take
        effect on the system until C(adaptive) is C(yes).
    type: int
  sampling_timespan:
    description:
      - Specifies the length, in seconds, of the probe history window that the system
        uses to calculate the mean latency and standard deviation of a monitor probe.
      - While this value can be configured when C(adaptive) is C(no), it will not take
        effect on the system until C(adaptive) is C(yes).
    type: int
  partition:
    description:
      - Device partition to manage resources on.
    type: str
    default: Common
  state:
    description:
      - When C(present), ensures that the monitor exists.
      - When C(absent), ensures the monitor is removed.
    type: str
    choices:
      - present
      - absent
    default: present
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Create a DNS monitor
  bigip_monitor_dns:
    name: DNS-UDP-V6
    interval: 2
    query_name: localhost
    query_type: aaaa
    up_interval: 5
    adaptive: no
    state: present
    provider:
      user: admin
      password: secret
      server: lb.mydomain.com
  delegate_to: localhost
'''

RETURN = r'''
parent:
  description: New parent template of the monitor.
  returned: changed
  type: str
  sample: http
ip:
  description: The new IP of IP/port definition.
  returned: changed
  type: str
  sample: 10.12.13.14
interval:
  description: The new interval in which to run the monitor check.
  returned: changed
  type: int
  sample: 2
timeout:
  description: The new timeout in which the remote system must respond to the monitor.
  returned: changed
  type: int
  sample: 10
time_until_up:
  description: The new time in which to mark a system as up after first successful response.
  returned: changed
  type: int
  sample: 2
adaptive:
  description: Whether adaptive is enabled or not.
  returned: changed
  type: bool
  sample: yes
accept_rcode:
  description: RCODE required in the response for an up status.
  returned: changed
  type: str
  sample: no-error
allowed_divergence_type:
  description: Type of divergence used for adaptive response time monitoring.
  returned: changed
  type: str
  sample: absolute
allowed_divergence_value:
  description:
    - Value of the type of divergence used for adaptive response time monitoring.
    - May be C(percent) or C(ms) depending on whether C(relative) or C(absolute).
  returned: changed
  type: int
  sample: 25
description:
  description: The description of the monitor.
  returned: changed
  type: str
  sample: Important Monitor
adaptive_limit:
  description: Absolute number of milliseconds that may not be exceeded by a monitor probe.
  returned: changed
  type: int
  sample: 200
sampling_timespan:
  description: Absolute number of milliseconds that may not be exceeded by a monitor probe.
  returned: changed
  type: int
  sample: 200
answer_section_contains:
  description: Type of DNS query that the monitor sends.
  returned: changed
  type: str
  sample: query-type
manual_resume:
  description:
    - Whether the system automatically changes the status of a resource to enabled at the
      next successful monitor check.
  returned: changed
  type: str
  sample: query-type
up_interval:
  description: Interval for the system to use to perform the health check when a resource is up.
  returned: changed
  type: int
  sample: 0
query_name:
  description: Query name for the monitor to use in a DNS query.
  returned: changed
  type: str
  sample: foo
query_type:
  description: Type of DNS query that the monitor sends. Either C(a) or C(aaaa).
  returned: changed
  type: str
  sample: aaaa
receive:
  description: IP address that the monitor uses from the resource record sections of the DNS response.
  returned: changed
  type: str
  sample: 2.3.2.4
reverse:
  description: Whether the monitor operates in reverse mode.
  returned: changed
  type: bool
  sample: yes
port:
  description:
    - Alias port or service for the monitor to check, on behalf of the pools or pool
      members with which the monitor is associated.
  returned: changed
  type: str
  sample: 80
transparent:
  description: Whether the monitor operates in transparent mode.
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
    from library.module_utils.network.f5.ipaddress import is_valid_ip
    from library.module_utils.network.f5.ipaddress import validate_ip_v6_address
    from library.module_utils.network.f5.ipaddress import validate_ip_address
    from library.module_utils.network.f5.compare import cmp_str_with_none
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.ipaddress import is_valid_ip
    from ansible.module_utils.network.f5.ipaddress import validate_ip_v6_address
    from ansible.module_utils.network.f5.ipaddress import validate_ip_address
    from ansible.module_utils.network.f5.compare import cmp_str_with_none


class Parameters(AnsibleF5Parameters):
    api_map = {
        'acceptRcode': 'accept_rcode',
        'adaptiveDivergenceType': 'allowed_divergence_type',
        'adaptiveDivergenceValue': 'allowed_divergence_value',
        'adaptiveLimit': 'adaptive_limit',
        'adaptiveSamplingTimespan': 'sampling_timespan',
        'answerContains': 'answer_section_contains',
        'manualResume': 'manual_resume',
        'timeUntilUp': 'time_until_up',
        'upInterval': 'up_interval',
        'qname': 'query_name',
        'qtype': 'query_type',
        'recv': 'receive',
        'defaultsFrom': 'parent',
    }

    api_attributes = [
        'adaptive',
        'acceptRcode',
        'adaptiveDivergenceType',
        'adaptiveDivergenceValue',
        'adaptiveLimit',
        'adaptiveSamplingTimespan',
        'answerContains',
        'defaultsFrom',
        'description',
        'destination',
        'interval',
        'manualResume',
        'qname',
        'qtype',
        'recv',
        'reverse',
        'timeout',
        'timeUntilUp',
        'transparent',
        'upInterval',
        'destination',
    ]

    returnables = [
        'adaptive',
        'accept_rcode',
        'allowed_divergence_type',
        'allowed_divergence_value',
        'description',
        'adaptive_limit',
        'sampling_timespan',
        'answer_section_contains',
        'manual_resume',
        'time_until_up',
        'up_interval',
        'query_name',
        'query_type',
        'receive',
        'reverse',
        'timeout',
        'interval',
        'transparent',
        'parent',
        'ip',
        'port',
    ]

    updatables = [
        'adaptive',
        'accept_rcode',
        'allowed_divergence_type',
        'allowed_divergence_value',
        'adaptive_limit',
        'sampling_timespan',
        'answer_section_contains',
        'description',
        'manual_resume',
        'time_until_up',
        'up_interval',
        'query_name',
        'query_type',
        'receive',
        'reverse',
        'timeout',
        'transparent',
        'parent',
        'destination',
        'interval',
    ]

    @property
    def type(self):
        return 'dns'

    @property
    def destination(self):
        if self.ip is None and self.port is None:
            return None
        destination = '{0}:{1}'.format(self.ip, self.port)
        return destination

    @destination.setter
    def destination(self, value):
        ip, port = value.split(':')
        self._values['ip'] = ip
        self._values['port'] = port

    @property
    def interval(self):
        if self._values['interval'] is None:
            return None

        # Per BZ617284, the BIG-IP UI does not raise a warning about this.
        # So I do
        if 1 > int(self._values['interval']) > 86400:
            raise F5ModuleError(
                "Interval value must be between 1 and 86400"
            )
        return int(self._values['interval'])

    @property
    def timeout(self):
        if self._values['timeout'] is None:
            return None
        return int(self._values['timeout'])

    @property
    def ip(self):
        if self._values['ip'] is None:
            return None
        if self._values['ip'] in ['*', '0.0.0.0']:
            return '*'
        elif is_valid_ip(self._values['ip']):
            return self._values['ip']
        else:
            raise F5ModuleError(
                "The provided 'ip' parameter is not an IP address."
            )

    @property
    def receive(self):
        if self._values['receive'] is None:
            return None
        if self._values['receive'] == '':
            return ''
        if is_valid_ip(self._values['receive']):
            return self._values['receive']
        raise F5ModuleError(
            "The specified 'receive' parameter must be either an IPv4 or v6 address."
        )

    @property
    def port(self):
        if self._values['port'] is None:
            return None
        elif self._values['port'] == '*':
            return '*'
        return int(self._values['port'])

    @property
    def time_until_up(self):
        if self._values['time_until_up'] is None:
            return None
        return int(self._values['time_until_up'])

    @property
    def parent(self):
        if self._values['parent'] is None:
            return None
        result = fq_name(self.partition, self._values['parent'])
        return result


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
    def manual_resume(self):
        if self._values['manual_resume'] is None:
            return None
        elif self._values['manual_resume'] is True:
            return 'enabled'
        return 'disabled'

    @property
    def reverse(self):
        if self._values['reverse'] is None:
            return None
        elif self._values['reverse'] is True:
            return 'enabled'
        return 'disabled'

    @property
    def transparent(self):
        if self._values['transparent'] is None:
            return None
        elif self._values['transparent'] is True:
            return 'enabled'
        return 'disabled'

    @property
    def adaptive(self):
        if self._values['adaptive'] is None:
            return None
        elif self._values['adaptive'] is True:
            return 'enabled'
        return 'disabled'


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
    @property
    def manual_resume(self):
        return flatten_boolean(self._values['manual_resume'])

    @property
    def reverse(self):
        return flatten_boolean(self._values['reverse'])

    @property
    def transparent(self):
        return flatten_boolean(self._values['transparent'])

    @property
    def adaptive(self):
        return flatten_boolean(self._values['adaptive'])


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
    def parent(self):
        if self.want.parent != self.have.parent:
            raise F5ModuleError(
                "The parent monitor cannot be changed"
            )

    @property
    def destination(self):
        if self.want.ip is None and self.want.port is None:
            return None
        if self.want.port is None:
            self.want.update({'port': self.have.port})
        if self.want.ip is None:
            self.want.update({'ip': self.have.ip})

        if self.want.port in [None, '*'] and self.want.ip != '*':
            raise F5ModuleError(
                "Specifying an IP address requires that a port number be specified"
            )

        if self.want.destination != self.have.destination:
            return self.want.destination

    @property
    def interval(self):
        if self.want.timeout is not None and self.want.interval is not None:
            if self.want.interval >= self.want.timeout:
                raise F5ModuleError(
                    "Parameter 'interval' must be less than 'timeout'."
                )
        elif self.want.timeout is not None:
            if self.have.interval >= self.want.timeout:
                raise F5ModuleError(
                    "Parameter 'interval' must be less than 'timeout'."
                )
        elif self.want.interval is not None:
            if self.want.interval >= self.have.timeout:
                raise F5ModuleError(
                    "Parameter 'interval' must be less than 'timeout'."
                )
        if self.want.interval != self.have.interval:
            return self.want.interval

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
        uri = "https://{0}:{1}/mgmt/tm/ltm/monitor/dns/{2}".format(
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

    def _address_type_matches_query_type(self, type, validator):
        if self.want.query_type == type and self.have.query_type == type:
            if self.want.receive is not None and validator(self.want.receive):
                return True
            if self.have.receive is not None and validator(self.have.receive):
                return True

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.want.reverse == 'enabled':
            if not self.want.receive and not self.have.receive:
                raise F5ModuleError(
                    "A 'receive' string must be specified when setting 'reverse'."
                )
            if self.want.time_until_up != 0 and self.have.time_until_up != 0:
                raise F5ModuleError(
                    "Monitors with the 'reverse' attribute are not currently compatible with 'time_until_up'."
                )
        if self._address_type_matches_query_type('a', validate_ip_v6_address):
            raise F5ModuleError(
                "Monitor has a IPv6 address. Only a 'query_type' of 'aaaa' is supported for IPv6."
            )
        elif self._address_type_matches_query_type('aaaa', validate_ip_address):
            raise F5ModuleError(
                "Monitor has a IPv4 address. Only a 'query_type' of 'a' is supported for IPv4."
            )

        if self.want.accept_rcode == 'anything':
            if self.want.receive is not None and is_valid_ip(self.want.receive) and self.have.receive is not None:
                raise F5ModuleError(
                    "No 'receive' string may be specified, or exist, when 'accept_rcode' is 'anything'."
                )
            elif self.want.receive is None and self.have.receive is not None:
                self.want.update({'receive': ''})
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
        if self.want.reverse == 'enabled':
            if self.want.time_until_up != 0:
                raise F5ModuleError(
                    "Monitors with the 'reverse' attribute are not currently compatible with 'time_until_up'."
                )
            if not self.want.receive:
                raise F5ModuleError(
                    "A 'receive' string must be specified when setting 'reverse'."
                )

        if self.want.receive is not None and validate_ip_v6_address(self.want.receive) and self.want.query_type == 'a':
            raise F5ModuleError(
                "Monitor has a IPv6 address. Only a 'query_type' of 'aaaa' is supported for IPv6."
            )
        elif self.want.receive is not None and validate_ip_address(self.want.receive) and self.want.query_type == 'aaaa':
            raise F5ModuleError(
                "Monitor has a IPv4 address. Only a 'query_type' of 'a' is supported for IPv4."
            )

        if self.want.accept_rcode == 'anything':
            if self.want.receive is not None and is_valid_ip(self.want.receive):
                raise F5ModuleError(
                    "No 'receive' string may be specified, or exist, when 'accept_rcode' is 'anything'."
                )
            elif self.want.receive is None:
                self.want.update({'receive': ''})

        if self.want.query_name is None:
            raise F5ModuleError(
                "'query_name' is required when creating a new DNS monitor."
            )
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/ltm/monitor/dns/".format(
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/monitor/dns/{2}".format(
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/monitor/dns/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.delete(uri)
        if resp.status == 200:
            return True

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/monitor/dns/{2}".format(
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
            parent=dict(default='/Common/dns'),
            receive=dict(),
            ip=dict(),
            description=dict(),
            port=dict(),
            interval=dict(type='int'),
            timeout=dict(type='int'),
            manual_resume=dict(type='bool'),
            reverse=dict(type='bool'),
            transparent=dict(type='bool'),
            time_until_up=dict(type='int'),
            up_interval=dict(type='int'),
            accept_rcode=dict(choices=['no-error', 'anything']),
            adaptive=dict(type='bool'),
            sampling_timespan=dict(type='int'),
            adaptive_limit=dict(type='int'),
            answer_section_contains=dict(
                choices=['any-type', 'anything', 'query-type']
            ),
            query_name=dict(),
            query_type=dict(choices=['a', 'aaaa']),
            allowed_divergence_type=dict(choices=['relative', 'absolute']),
            allowed_divergence_value=dict(type='int'),
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
