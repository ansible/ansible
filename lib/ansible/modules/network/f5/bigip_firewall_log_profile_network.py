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
module: bigip_firewall_log_profile_network
short_description: Configures Network Firewall related settings of the log profile
description:
  - Configures Network Firewall related settings of the log profile.
version_added: 2.9
options:
  profile_name:
    description:
      - Specifies the name of the AFM log profile to be updated.
    type: str
    required: True
  log_publisher:
    description:
      - Specifies the name of the log publisher used for Network events.
      - To specify the log_publisher on a different partition from the AFM log profile, specify the name in fullpath
        format, e.g. C(/Foobar/log-publisher), otherwise the partition for log publisher is inferred from C(partition)
        module parameter.
    type: str
  rate_limit:
    description:
      - Defines a rate limit for all combined network firewall log messages per second. Beyond this rate limit,
        log messages are not logged.
      - To specify an indefinite rate, use the value C(indefinite).
      - If specifying a numeric rate, the value must be between C(1) and C(4294967295).
    type: str
  log_matches_accept_rule:
    description:
      - Modify log settings for ACL rules configured with an "accept" or "accept decisively" action.
    suboptions:
      enabled:
        description:
          - This option is used to enable or disable the logging of packets that match ACL rules configured with
            an "accept" or "accept decisively" action.
        type: bool
      rate_limit:
        description:
          - This option is used to set rate limits for the logging of packets that match ACL rules
            configured with an "accept" or "accept decisively" action.
          - This option is effective only if logging of this message type is enabled.
        type: int
    type: dict
  log_matches_drop_rule:
    description:
      - Modify log settings for ACL rules configured with a drop action.
    suboptions:
      enabled:
        description:
          - This option is used to enable or disable the logging of packets that match ACL rules
            configured with a drop action.
        type: bool
      rate_limit:
        description:
          - This option is used to set rate limits for the logging of packets that match ACL rules
            configured with a drop action.
          - This option is effective only if logging of this message type is enabled.
        type: int
    type: dict
  log_matches_reject_rule:
    description:
      - Modify log settings for ACL rules configured with a reject action.
    suboptions:
      enabled:
        description:
          - This option is used to enable or disable the logging of packets that match ACL rules
            configured with a reject action.
        type: bool
      rate_limit:
        description:
          - This option is used to set rate limits for the logging of packets that match ACL rules
            configured with a reject action.
          - This option is effective only if logging of this message type is enabled.
        type: int
    type: dict
  log_ip_errors:
    description:
      - Modify log settings for logging of IP error packets.
    suboptions:
      enabled:
        description:
          - This option is used to enable or disable the logging of IP error packets.
        type: bool
      rate_limit:
        description:
          - This option is used to set rate limits for the logging of IP error packets.
          - This option is effective only if logging of this message type is enabled.
        type: int
    type: dict
  log_tcp_errors:
    description:
      - Modify log settings for logging of TCP error packets.
    suboptions:
      enabled:
        description:
          - This option is used to enable or disable the logging of TCP error packets.
        type: bool
      rate_limit:
        description:
          - This option is used to set rate limits for the logging of TCP error packets.
          - This option is effective only if logging of this message type is enabled.
        type: int
    type: dict
  log_tcp_events:
    description:
      - Modify log settings for logging of TCP events on the client side.
    suboptions:
      enabled:
        description:
          - This option is used to enable or disable the logging of TCP events on the client side.
          - Only 'Established' and 'Closed' states of a TCP session are logged if this option is enabled.
        type: bool
      rate_limit:
        description:
          - This option is used to set rate limits for the logging of TCP events on the client side.
          - This option is effective only if logging of this message type is enabled.
        type: int
    type: dict
  log_translation_fields:
    description:
      - This option is used to enable or disable the logging of translated (i.e server side) fields in ACL
        match and TCP events.
      - Translated fields include (but are not limited to) source address/port, destination address/port,
        IP protocol, route domain, and VLAN.
    type: bool
  log_storage_format:
    description:
      - Specifies the type of the storage format.
      - When creating a new log profile, if this parameter is not specified, the default is C(none).
      - When C(field-list), specifies that the log displays only the items you specify in the C(log_message_fields) list
        with C(log_format_delimiter) as the delimiter between the items.
      - When C(none), the messages will be logged in the default format, which is C("management_ip_address",
        "bigip_hostname","context_type", "context_name","src_geo","src_ip", "dest_geo","dest_ip","src_port",
        "dest_port","vlan","protocol","route_domain", "translated_src_ip", "translated_dest_ip",
        "translated_src_port","translated_dest_port", "translated_vlan","translated_ip_protocol",
        "translated_route_domain", "acl_policy_type", "acl_policy_name","acl_rule_name","action",
        "drop_reason","sa_translation_type", "sa_translation_pool","flow_id", "source_user",
        "source_fqdn","dest_fqdn").
    choices:
      - field-list
      - none
    type: str
  log_format_delimiter:
    description:
      - Specifies the delimiter string when using a C(log_storage_format) of C(field-list).
      - When creating a new profile, if this parameter is not specified, the default value of C(,)
        (the comma character) will be used.
      - This option is valid when the C(log_storage_format) is set to C(field-list). It will be ignored otherwise.
      - Depending on the delimiter used, it may be necessary to wrap the delimiter
        in quotes to prevent YAML errors from occurring.
      - The special character C($) should not be used, and will raise an error if used,
        as it is reserved for internal use.
      - The maximum length allowed for this parameter is C(31) characters.
    type: str
  log_message_fields:
    description:
      - Specifies a set of fields to be logged.
      - This option is valid when the C(log_storage_format) is set to C(field-list). It will be ignored otherwise.
      - The order of the list is important as the server displays the selected traffic items in the log
        sequentially according to it.
    type: list
    choices:
      - acl_policy_name
      - acl_policy_type
      - acl_rule_name
      - action
      - bigip_hostname
      - context_name
      - context_type
      - date_time
      - dest_fqdn
      - dest_geo
      - dest_ip
      - dest_port
      - drop_reason
      - management_ip_address
      - protocol
      - route_domain
      - sa_translation_pool
      - sa_translation_type
      - source_fqdn
      - source_user
      - src_geo
      - src_ip
      - src_port
      - translated_dest_ip
      - translated_dest_port
      - translated_ip_protocol
      - translated_route_domain
      - translated_src_ip
      - translated_src_port
      - translated_vlan
      - vlan
  partition:
    description:
      - Device partition to create log profile on.
      - Parameter also used when specifying names for log publishers, unless log publisher names are in fullpath format.
    type: str
    default: Common
  state:
    description:
      - When C(state) is C(present), ensures the resource exists.
      - Only built-in profile that allows updating network log settings is global-network, attempts to do so on other
        built-in profiles will be ignored.
      - When C(state) is C(absent), ensures that resource is removed.
      - The C(absent) state is ignored for global-network log profile.
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
- name: Add network settings to log profile
  bigip_firewall_log_profile_network:
    profile_name: barbaz
    rate_limit: 150000
    log_publisher: local-db-pub
    log_tcp_errors:
      enabled: yes
      rate_limit: 10000
    log_tcp_events:
      enabled: yes
      rate_limit: 40000
    log_storage_format: "field-list"
    log_message_fields:
      - vlan
      - translated_vlan
      - src_ip
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Change delimiter and log fields
  bigip_firewall_log_profile_network:
    profile_name: barbaz
    log_format_delimiter: '.'
    log_message_fields:
      - translated_dest_ip
      - translated_dest_port
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Modify built-in profile
  bigip_firewall_log_profile_network:
    profile_name: "global-network"
    log_publisher: "/foobar/log1"
    log_ip_errors:
      enabled: yes
      rate_limit: 60000
    log_matches_reject_rule:
      enabled: yes
      rate_limit: 2000
    log_translation_fields: yes
    log_storage_format: "field-list"
    log_format_delimiter: '.'
    log_message_fields:
      - protocol
      - dest_ip
      - dest_port
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Remove custom log profile network log settings
  bigip_firewall_log_profile_network:
    profile_name: "{{ log_profile }}"
    state: absent
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
log_publisher:
  description: The name of the log publisher used for Network events.
  returned: changed
  type: str
  sample: /Common/log-publisher
rate_limit:
  description: The rate limit for all combined network firewall log messages per second.
  returned: changed
  type: str
  sample: "indefinite"
log_matches_accept_rule:
  description: Log settings for ACL rules configured with an "accept" or "accept decisively" action.
  type: complex
  returned: changed
  contains:
    enabled:
      description: Enable or disable the logging of packets that match ACL rules.
      returned: changed
      type: bool
      sample: yes
    rate_limit:
      description: The rate limit for the logging of packets that match ACL rules.
      returned: changed
      type: str
      sample: "indefinite"
  sample: hash/dictionary of values
log_matches_drop_rule:
  description: Log settings for ACL rules configured with a drop action.
  type: complex
  returned: changed
  contains:
    enabled:
      description: Enable or disable the logging of packets that match ACL rules.
      returned: changed
      type: bool
      sample: yes
    rate_limit:
      description: The rate limit for the logging of packets that match ACL rules.
      returned: changed
      type: str
      sample: "indefinite"
  sample: hash/dictionary of values
log_matches_reject_rule:
  description: Log settings for ACL rules configured with a reject action.
  type: complex
  returned: changed
  contains:
    enabled:
      description: Enable or disable the logging of packets that match ACL rules.
      returned: changed
      type: bool
      sample: yes
    rate_limit:
      description: The rate limit for the logging of packets that match ACL rules.
      returned: changed
      type: str
      sample: "indefinite"
  sample: hash/dictionary of values
log_ip_errors:
  description: Log settings for logging of IP error packets.
  type: complex
  returned: changed
  contains:
    enabled:
      description: Enable or disable the logging of IP error packets.
      returned: changed
      type: bool
      sample: yes
    rate_limit:
      description: The rate limit for the logging of IP error packets.
      returned: changed
      type: str
      sample: "indefinite"
  sample: hash/dictionary of values
log_tcp_errors:
  description: Log settings for logging of TCP error packets.
  type: complex
  returned: changed
  contains:
    enabled:
      description: Enable or disable the logging of TCP error packets.
      returned: changed
      type: bool
      sample: yes
    rate_limit:
      description: The rate limit for the logging of TCP error packets.
      returned: changed
      type: str
      sample: "indefinite"
  sample: hash/dictionary of values
log_tcp_events:
  description: Log settings for logging of TCP events on the client side.
  type: complex
  returned: changed
  contains:
    enabled:
      description: Enable or disable the logging of TCP events on the client side.
      returned: changed
      type: bool
      sample: yes
    rate_limit:
      description: The rate limit for the logging of TCP events on the client side.
      returned: changed
      type: str
      sample: "indefinite"
  sample: hash/dictionary of values
log_translation_fields:
  description: Enable or disable the logging of translated (i.e server side) fields in ACL match and TCP events.
  returned: changed
  type: bool
  sample: yes
log_storage_format:
  description: The type of the storage format.
  returned: changed
  type: str
  sample: "field-list"
log_format_delimiter:
  description: The delimiter string when using a log_storage_format of field-list.
  returned: changed
  type: str
  sample: "."
log_message_fields:
  description: The delimiter string when using a log_storage_format of field-list.
  returned: changed
  type: list
  sample: ["acl_policy_name", "acl_policy_type"]
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
    from library.module_utils.network.f5.compare import cmp_str_with_none
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.compare import cmp_str_with_none


class Parameters(AnsibleF5Parameters):
    api_map = {
        'publisher': 'log_publisher',
        'rateLimit': 'rate_limits',
    }

    api_attributes = [
        'publisher',
        'format',
        'rateLimit',
        'filter',
    ]

    returnables = [
        'rate_acl_match_accept',
        'rate_acl_match_drop',
        'rate_acl_match_reject',
        'rate_tcp_errors',
        'rate_tcp_events',
        'rate_ip_errors',
        'rate_limit',
        'log_acl_match_accept',
        'log_acl_match_drop',
        'log_acl_match_reject',
        'log_tcp_errors',
        'log_tcp_events',
        'log_ip_errors',
        'log_translation_fields',
        'log_publisher',
        'log_format_delimiter',
        'log_storage_format',
        'log_message_fields',
        'log_matches_accept_rule',
        'log_matches_drop_rule',
        'log_matches_reject_rule',
    ]

    updatables = [
        'rate_acl_match_accept',
        'rate_acl_match_drop',
        'rate_acl_match_reject',
        'rate_tcp_errors',
        'rate_tcp_events',
        'rate_ip_errors',
        'rate_limit',
        'log_acl_match_accept',
        'log_acl_match_drop',
        'log_acl_match_reject',
        'log_tcp_errors',
        'log_tcp_events',
        'log_ip_errors',
        'log_translation_fields',
        'log_publisher',
        'log_format_delimiter',
        'log_storage_format',
        'log_message_fields',
    ]


class ApiParameters(Parameters):
    @property
    def rate_acl_match_accept(self):
        if self._values['rate_limits'] is None:
            return None
        return self._values['rate_limits']['aclMatchAccept']

    @property
    def log_acl_match_accept(self):
        if self._values['filter'] is None:
            return None
        return self._values['filter']['logAclMatchAccept']

    @property
    def rate_acl_match_drop(self):
        if self._values['rate_limits'] is None:
            return None
        return self._values['rate_limits']['aclMatchDrop']

    @property
    def log_acl_match_drop(self):
        if self._values['filter'] is None:
            return None
        return self._values['filter']['logAclMatchDrop']

    @property
    def rate_acl_match_reject(self):
        if self._values['rate_limits'] is None:
            return None
        return self._values['rate_limits']['aclMatchReject']

    @property
    def log_acl_match_reject(self):
        if self._values['filter'] is None:
            return None
        return self._values['filter']['logAclMatchReject']

    @property
    def rate_tcp_errors(self):
        if self._values['rate_limits'] is None:
            return None
        return self._values['rate_limits']['tcpErrors']

    @property
    def log_tcp_errors(self):
        if self._values['filter'] is None:
            return None
        return self._values['filter']['logTcpErrors']

    @property
    def rate_tcp_events(self):
        if self._values['rate_limits'] is None:
            return None
        return self._values['rate_limits']['tcpEvents']

    @property
    def log_tcp_events(self):
        if self._values['filter'] is None:
            return None
        return self._values['filter']['logTcpEvents']

    @property
    def rate_ip_errors(self):
        if self._values['rate_limits'] is None:
            return None
        return self._values['rate_limits']['ipErrors']

    @property
    def log_ip_errors(self):
        if self._values['filter'] is None:
            return None
        return self._values['filter']['logIpErrors']

    @property
    def log_translation_fields(self):
        if self._values['filter'] is None:
            return None
        return self._values['filter']['logTranslationFields']

    @property
    def rate_limit(self):
        if self._values['rate_limits'] is None:
            return None
        return self._values['rate_limits']['aggregateRate']

    @property
    def log_format_delimiter(self):
        if self._values['format'] is None:
            return None
        return self._values['format']['fieldListDelimiter']

    @property
    def log_storage_format(self):
        if self._values['format'] is None:
            return None
        return self._values['format']['type']

    @property
    def log_message_fields(self):
        if self._values['format'] is None:
            return None
        if 'fieldList' in self._values['format']:
            return self._values['format']['fieldList']


class ModuleParameters(Parameters):
    def _validate_aggregate_rate(self, aggregate_rate):
        if aggregate_rate is None:
            return None
        if aggregate_rate == 'indefinite':
            return 4294967295
        if 0 <= int(aggregate_rate) <= 4294967295:
            return int(aggregate_rate)
        raise F5ModuleError(
            "Valid 'maximum_age' must be in range 0 - 4294967295, or 'indefinite'."
        )

    @property
    def rate_acl_match_accept(self):
        if self._values['log_matches_accept_rule'] is None:
            return None
        return self._validate_aggregate_rate(self._values['log_matches_accept_rule']['rate_limit'])

    @property
    def log_acl_match_accept(self):
        if self._values['log_matches_accept_rule'] is None:
            return None
        result = flatten_boolean(self._values['log_matches_accept_rule']['enabled'])
        if result == 'yes':
            return 'enabled'
        if result == 'no':
            return 'disabled'
        return result

    @property
    def rate_acl_match_drop(self):
        if self._values['log_matches_drop_rule'] is None:
            return None
        return self._validate_aggregate_rate(self._values['log_matches_drop_rule']['rate_limit'])

    @property
    def log_acl_match_drop(self):
        if self._values['log_matches_drop_rule'] is None:
            return None
        result = flatten_boolean(self._values['log_matches_drop_rule']['enabled'])
        if result == 'yes':
            return 'enabled'
        if result == 'no':
            return 'disabled'
        return result

    @property
    def rate_acl_match_reject(self):
        if self._values['log_matches_reject_rule'] is None:
            return None
        return self._validate_aggregate_rate(self._values['log_matches_reject_rule']['rate_limit'])

    @property
    def log_acl_match_reject(self):
        if self._values['log_matches_reject_rule'] is None:
            return None
        result = flatten_boolean(self._values['log_matches_reject_rule']['enabled'])
        if result == 'yes':
            return 'enabled'
        if result == 'no':
            return 'disabled'
        return result

    @property
    def rate_tcp_errors(self):
        if self._values['log_tcp_errors'] is None:
            return None
        return self._validate_aggregate_rate(self._values['log_tcp_errors']['rate_limit'])

    @property
    def log_tcp_errors(self):
        if self._values['log_tcp_errors'] is None:
            return None
        result = flatten_boolean(self._values['log_tcp_errors']['enabled'])
        if result == 'yes':
            return 'enabled'
        if result == 'no':
            return 'disabled'
        return result

    @property
    def rate_tcp_events(self):
        if self._values['log_tcp_events'] is None:
            return None
        return self._validate_aggregate_rate(self._values['log_tcp_events']['rate_limit'])

    @property
    def log_tcp_events(self):
        if self._values['log_tcp_events'] is None:
            return None
        result = flatten_boolean(self._values['log_tcp_events']['enabled'])
        if result == 'yes':
            return 'enabled'
        if result == 'no':
            return 'disabled'
        return result

    @property
    def rate_ip_errors(self):
        if self._values['log_ip_errors'] is None:
            return None
        return self._validate_aggregate_rate(self._values['log_ip_errors']['rate_limit'])

    @property
    def log_ip_errors(self):
        if self._values['log_ip_errors'] is None:
            return None
        result = flatten_boolean(self._values['log_ip_errors']['enabled'])
        if result == 'yes':
            return 'enabled'
        if result == 'no':
            return 'disabled'
        return result

    @property
    def log_translation_fields(self):
        result = flatten_boolean(self._values['log_translation_fields'])
        if result == 'yes':
            return 'enabled'
        if result == 'no':
            return 'disabled'
        return result

    @property
    def log_publisher(self):
        log_publisher = self._values['log_publisher']
        if log_publisher is None:
            return None
        if log_publisher in ['', 'none']:
            return log_publisher
        return fq_name(self.partition, log_publisher)

    @property
    def rate_limit(self):
        return self._validate_aggregate_rate(self._values['rate_limit'])

    @property
    def log_format_delimiter(self):
        if self._values['log_format_delimiter'] is None:
            return None
        if len(self._values['log_format_delimiter']) > 31:
            raise F5ModuleError('The maximum length of delimiter is 31 characters.')
        if "$" in self._values['log_format_delimiter']:
            raise F5ModuleError("Cannot use '$' character as a part of delimiter.")
        return self._values['log_format_delimiter']


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
    def rate_limits(self):
        to_filter = dict(
            aclMatchAccept=self._values['rate_acl_match_accept'],
            aclMatchDrop=self._values['rate_acl_match_drop'],
            aclMatchReject=self._values['rate_acl_match_reject'],
            ipErrors=self._values['rate_ip_errors'],
            tcpErrors=self._values['rate_tcp_errors'],
            tcpEvents=self._values['rate_tcp_events'],
            aggregateRate=self._values['rate_limit'],
        )
        result = self._filter_params(to_filter)
        return result

    @property
    def format(self):
        to_filter = dict(
            fieldListDelimiter=self._values['log_format_delimiter'],
            type=self._values['log_storage_format'],
            fieldList=self._values['log_message_fields']
        )
        result = self._filter_params(to_filter)
        return result

    @property
    def filter(self):
        to_filter = dict(
            logAclMatchAccept=self._values['log_acl_match_accept'],
            logAclMatchDrop=self._values['log_acl_match_drop'],
            logAclMatchReject=self._values['log_acl_match_reject'],
            logIpErrors=self._values['log_ip_errors'],
            logTcpErrors=self._values['log_tcp_errors'],
            logTcpEvents=self._values['log_tcp_events'],
            logTranslationFields=self._values['log_translation_fields'],
        )
        result = self._filter_params(to_filter)
        return result


class ReportableChanges(Changes):
    def _change_aggregate_rate_value(self, value):
        if value == 4294967295:
            return 'indefinite'
        else:
            return value

    def _rebuild_params(self, enabled, rate_limit):
        to_filter = dict(
            enabled=flatten_boolean(self._values[enabled]),
            rate_limit=self._change_aggregate_rate_value(self._values[rate_limit])
        )
        result = self._filter_params(to_filter)
        return result

    @property
    def log_matches_accept_rule(self):
        result = self._rebuild_params('log_acl_match_accept', 'rate_acl_match_accept')
        if result:
            return result

    @property
    def log_acl_match_accept(self):
        return None

    @property
    def rate_acl_match_accept(self):
        return None

    @property
    def log_matches_drop_rule(self):
        result = self._rebuild_params('log_acl_match_drop', 'rate_acl_match_drop')
        if result:
            return result

    @property
    def log_acl_match_drop(self):
        return None

    @property
    def rate_acl_match_drop(self):
        return None

    @property
    def log_matches_reject_rule(self):
        result = self._rebuild_params('log_acl_match_reject', 'rate_acl_match_reject')
        if result:
            return result

    @property
    def log_acl_match_reject(self):
        return None

    @property
    def rate_acl_match_reject(self):
        return None

    @property
    def log_ip_errors(self):
        result = self._rebuild_params('log_ip_errors', 'rate_ip_errors')
        if result:
            return result

    @property
    def rate_ip_errors(self):
        return None

    @property
    def log_tcp_errors(self):
        result = self._rebuild_params('log_tcp_errors', 'rate_tcp_errors')
        if result:
            return result

    @property
    def rate_tcp_errors(self):
        return None

    @property
    def log_tcp_events(self):
        result = self._rebuild_params('log_tcp_events', 'rate_tcp_events')
        if result:
            return result

    @property
    def rate_tcp_events(self):
        return None


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
    def log_message_fields(self):
        if self.want.log_message_fields is None:
            return None
        if len(self.want.log_message_fields) == 1:
            if self.have.log_message_fields is None and self.want.log_message_fields[0] in ['', 'none']:
                return None
            if self.have.log_message_fields is not None and self.want.log_message_fields[0] in ['', 'none']:
                return []
        if self.have.log_message_fields is None:
            return self.want.log_message_fields
        if set(self.want.log_message_fields) != set(self.have.log_message_fields):
            return self.want.log_message_fields
        return None

    @property
    def log_publisher(self):
        return cmp_str_with_none(self.want.log_publisher, self.have.log_publisher)


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
        built_ins = ['Log all requests', 'Log illegal requests', 'local-dos']
        if self.want.profile_name in built_ins:
            return False
        if self.exists():
            return self.update()
        else:
            return self.create()

    def absent(self):
        # Built-in profile global-network cannot disable network log profile
        if 'global-network' in self.want.profile_name:
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

    def _internal_name(self):
        name = self.want.profile_name
        partition = self.want.partition
        if 'global-network' in name:
            return 'global-network'
        return transform_name(partition, name)

    def _profile_exists(self):
        uri = "https://{0}:{1}/mgmt/tm/security/log/profile/{2}/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.profile_name),
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False
        return True

    def exists(self):
        if not self._profile_exists():
            raise F5ModuleError(
                "Specified AFM log profile: {0} does not exist".format(self.want.profile_name)
            )
        uri = "https://{0}:{1}/mgmt/tm/security/log/profile/{2}/network/{3}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.profile_name),
            self._internal_name()
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
        params['name'] = self.want.profile_name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/security/log/profile/{2}/network/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.profile_name)
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
        uri = "https://{0}:{1}/mgmt/tm/security/log/profile/{2}/network/{3}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.profile_name),
            self._internal_name()
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
        uri = "https://{0}:{1}/mgmt/tm/security/log/profile/{2}/network/{3}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.profile_name),
            self._internal_name()
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/security/log/profile/{2}/network/{3}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.profile_name),
            self._internal_name()
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
        self.choices = [
            'acl_policy_name', 'acl_policy_type', 'acl_rule_name', 'action',
            'bigip_hostname', 'context_name', 'context_type', 'date_time',
            'dest_fqdn', 'dest_geo', 'dest_ip', 'dest_port', 'drop_reason',
            'management_ip_address', 'protocol', 'route_domain', 'sa_translation_pool',
            'sa_translation_type', 'source_fqdn', 'source_user', 'src_geo', 'src_ip',
            'src_port', 'translated_dest_ip', 'translated_dest_port', 'translated_ip_protocol',
            'translated_route_domain', 'translated_src_ip', 'translated_src_port', 'translated_vlan',
            'vlan'
        ]
        argument_spec = dict(
            profile_name=dict(
                required=True
            ),
            rate_limit=dict(),
            log_publisher=dict(),
            log_matches_accept_rule=dict(
                type='dict',
                options=dict(
                    enabled=dict(type='bool'),
                    rate_limit=dict()
                )
            ),
            log_matches_drop_rule=dict(
                type='dict',
                options=dict(
                    enabled=dict(type='bool'),
                    rate_limit=dict()
                )
            ),
            log_matches_reject_rule=dict(
                type='dict',
                options=dict(
                    enabled=dict(type='bool'),
                    rate_limit=dict()
                )
            ),
            log_tcp_errors=dict(
                type='dict',
                options=dict(
                    enabled=dict(type='bool'),
                    rate_limit=dict()
                )
            ),
            log_tcp_events=dict(
                type='dict',
                options=dict(
                    enabled=dict(type='bool'),
                    rate_limit=dict()
                )
            ),
            log_ip_errors=dict(
                type='dict',
                options=dict(
                    enabled=dict(type='bool'),
                    rate_limit=dict()
                )
            ),
            log_translation_fields=dict(type='bool'),
            log_storage_format=dict(
                choices=['none', 'field-list']
            ),
            log_format_delimiter=dict(),
            log_message_fields=dict(
                type='list',
                choices=self.choices
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
