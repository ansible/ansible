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
module: bigip_firewall_rule
short_description: Manage AFM Firewall rules
description:
  - Manages firewall rules in an AFM firewall policy. New rules will always be added to the
    end of the policy. Rules can be re-ordered using the C(bigip_security_policy) module.
    Rules can also be pre-ordered using the C(bigip_security_policy) module and then later
    updated using the C(bigip_firewall_rule) module.
version_added: 2.7
options:
  name:
    description:
      - Specifies the name of the rule.
    type: str
    required: True
  parent_policy:
    description:
      - The policy which contains the rule to be managed.
      - One of either C(parent_policy) or C(parent_rule_list) is required.
    type: str
  parent_rule_list:
    description:
      - The rule list which contains the rule to be managed.
      - One of either C(parent_policy) or C(parent_rule_list) is required.
    type: str
  action:
    description:
      - Specifies the action for the firewall rule.
      - When C(accept), allows packets with the specified source, destination,
        and protocol to pass through the firewall. Packets that match the rule,
        and are accepted, traverse the system as if the firewall is not present.
      - When C(drop), drops packets with the specified source, destination, and
        protocol. Dropping a packet is a silent action with no notification to
        the source or destination systems. Dropping the packet causes the connection
        to be retried until the retry threshold is reached.
      - When C(reject), rejects packets with the specified source, destination,
        and protocol. When a packet is rejected the firewall sends a destination
        unreachable message to the sender.
      - When C(accept-decisively), allows packets with the specified source,
        destination, and protocol to pass through the firewall, and does not require
        any further processing by any of the further firewalls. Packets that match
        the rule, and are accepted, traverse the system as if the firewall is not
        present. If the Rule List is applied to a virtual server, management IP,
        or self IP firewall rule, then Accept Decisively is equivalent to Accept.
      - When creating a new rule, if this parameter is not provided, the default is
        C(reject).
    type: str
    choices:
      - accept
      - drop
      - reject
      - accept-decisively
  status:
    description:
      - Indicates the activity state of the rule or rule list.
      - When C(disabled), specifies that the rule or rule list does not apply at all.
      - When C(enabled), specifies that the system applies the firewall rule or rule
        list to the given context and addresses.
      - When C(scheduled), specifies that the system applies the rule or rule list
        according to the specified schedule.
      - When creating a new rule, if this parameter is not provided, the default
        is C(enabled).
    type: str
    choices:
      - enabled
      - disabled
      - scheduled
  schedule:
    description:
      - Specifies a schedule for the firewall rule.
      - You configure schedules to define days and times when the firewall rule is
        made active.
    type: str
  description:
    description:
      - The rule description.
    type: str
  irule:
    description:
      - Specifies an iRule that is applied to the firewall rule.
      - An iRule can be started when the firewall rule matches traffic.
    type: str
  protocol:
    description:
      - Specifies the protocol to which the rule applies.
      - Protocols may be specified by either their name or numeric value.
      - A special protocol value C(any) can be specified to match any protocol. The
        numeric equivalent of this protocol is C(255).
    type: str
  source:
    description:
      - Specifies packet sources to which the rule applies.
      - Leaving this field blank applies the rule to all addresses and all ports.
      - You can specify the following source items. An IPv4 or IPv6 address, an IPv4
        or IPv6 address range, geographic location, VLAN, address list, port,
        port range, port list or address list.
      - You can specify a mix of different types of items for the source address.
    suboptions:
      address:
        description:
          - Specifies a specific IP address.
        type: str
      address_list:
        description:
          - Specifies an existing address list.
        type: str
      address_range:
        description:
          - Specifies an address range.
        type: str
      country:
        description:
          - Specifies a country code.
        type: str
      port:
        description:
          - Specifies a single numeric port.
          - This option is only valid when C(protocol) is C(tcp)(6) or C(udp)(17).
        type: int
      port_list:
        description:
          - Specifes an existing port list.
          - This option is only valid when C(protocol) is C(tcp)(6) or C(udp)(17).
        type: str
      port_range:
        description:
          - Specifies a range of ports, which is two port values separated by
            a hyphen. The port to the left of the hyphen should be less than the
            port to the right.
          - This option is only valid when C(protocol) is C(tcp)(6) or C(udp)(17).
        type: str
      vlan:
        description:
          - Specifies VLANs to which the rule applies.
          - The VLAN source refers to the packet's source.
        type: str
    type: list
  destination:
    description:
      - Specifies packet destinations to which the rule applies.
      - Leaving this field blank applies the rule to all addresses and all ports.
      - You can specify the following destination items. An IPv4 or IPv6 address,
        an IPv4 or IPv6 address range, geographic location, VLAN, address list, port,
        port range, port list or address list.
      - You can specify a mix of different types of items for the source address.
    suboptions:
      address:
        description:
          - Specifies a specific IP address.
        type: str
      address_list:
        description:
          - Specifies an existing address list.
        type: str
      address_range:
        description:
          - Specifies an address range.
        type: str
      country:
        description:
          - Specifies a country code.
        type: str
      port:
        description:
          - Specifies a single numeric port.
          - This option is only valid when C(protocol) is C(tcp)(6) or C(udp)(17).
        type: int
      port_list:
        description:
          - Specifes an existing port list.
          - This option is only valid when C(protocol) is C(tcp)(6) or C(udp)(17).
        type: str
      port_range:
        description:
          - Specifies a range of ports, which is two port values separated by
            a hyphen. The port to the left of the hyphen should be less than the
            port to the right.
          - This option is only valid when C(protocol) is C(tcp)(6) or C(udp)(17).
        type: str
    type: list
  logging:
    description:
      - Specifies whether logging is enabled or disabled for the firewall rule.
      - When creating a new rule, if this parameter is not specified, the default
        if C(no).
    type: bool
  rule_list:
    description:
      - Specifies an existing rule list to use in the rule.
      - This parameter is mutually exclusive with many of the other individual-rule
        specific settings. This includes C(logging), C(action), C(source),
        C(destination), C(irule'), C(protocol) and C(logging).
    type: str
  icmp_message:
    description:
      - Specifies the Internet Control Message Protocol (ICMP) or ICMPv6 message
        C(type) and C(code) that the rule uses.
      - This parameter is only relevant when C(protocol) is either C(icmp)(1) or
        C(icmpv6)(58).
    suboptions:
      type:
        description:
          - Specifies the type of ICMP message.
          - You can specify control messages, such as Echo Reply (0) and Destination
            Unreachable (3), or you can specify C(any) to indicate that the system
            applies the rule for all ICMP messages.
          - You can also specify an arbitrary ICMP message.
          - The ICMP protocol contains definitions for the existing message type and
            number pairs.
        type: str
      code:
        description:
          - Specifies the code returned in response to the specified ICMP message type.
          - You can specify codes, each set appropriate to the associated type, such
            as No Code (0) (associated with Echo Reply (0)) and Host Unreachable (1)
            (associated with Destination Unreachable (3)), or you can specify C(any)
            to indicate that the system applies the rule for all codes in response to
            that specific ICMP message.
          - You can also specify an arbitrary code.
          - The ICMP protocol contains definitions for the existing message code and
            number pairs.
        type: str
    type: list
  partition:
    description:
      - Device partition to manage resources on.
    type: str
    default: Common
  state:
    description:
      - When C(state) is C(present), ensures that the rule exists.
      - When C(state) is C(absent), ensures that the rule is removed.
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
- name: Create a new rule in the foo firewall policy
  bigip_firewall_rule:
    name: foo
    parent_policy: policy1
    protocol: tcp
    source:
      - address: 1.2.3.4
      - address: "::1"
      - address_list: foo-list1
      - address_range: 1.1.1.1-2.2.2.2
      - vlan: vlan1
      - country: US
      - port: 22
      - port_list: port-list1
      - port_range: 80-443
    destination:
      - address: 1.2.3.4
      - address: "::1"
      - address_list: foo-list1
      - address_range: 1.1.1.1-2.2.2.2
      - country: US
      - port: 22
      - port_list: port-list1
      - port_range: 80-443
    irule: irule1
    action: accept
    logging: yes
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Create an ICMP specific rule
  bigip_firewall_rule:
    name: foo
    protocol: icmp
    icmp_message:
      type: 0
    source:
      - country: US
    action: drop
    logging: yes
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Add a new rule that is uses an existing rule list
  bigip_firewall_rule:
    name: foo
    rule_list: rule-list1
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
name:
  description: Name of the rule.
  returned: changed
  type: str
  sample: FooRule
parent_policy:
  description: The policy which contains the rule to be managed.
  returned: changed
  type: str
  sample: FooPolicy
parent_rule_list:
  description: The rule list which contains the rule to be managed.
  returned: changed
  type: str
  sample: FooRuleList
action:
  description: The action for the firewall rule.
  returned: changed
  type: str
  sample: drop
status:
  description: The activity state of the rule or rule list.
  returned: changed
  type: str
  sample: scheduled
schedule:
  description: The schedule for the firewall rule.
  returned: changed
  type: str
  sample: Foo_schedule
description:
  description: The rule description.
  returned: changed
  type: str
  sample: MyRule
irule:
  description: The iRule that is applied to the firewall rule.
  returned: changed
  type: str
  sample: _sys_auth_radius
protocol:
  description: The protocol to which the rule applies.
  returned: changed
  type: str
  sample: any
source:
  description: The packet sources to which the rule applies
  returned: changed
  type: complex
  contains:
    address:
      description: A specific IP address.
      returned: changed
      type: str
      sample: 192.168.1.1
    address_list:
      description: An existing address list.
      returned: changed
      type: str
      sample: foo-list1
    address_range:
      description: The address range.
      returned: changed
      type: str
      sample: 1.1.1.1-2.2.2.2
    country:
      description: A country code.
      returned: changed
      type: str
      sample: US
    port:
      description: Single numeric port.
      returned: changed
      type: int
      sample: 8080
    port_list:
      description: An existing port list.
      returned: changed
      type: str
      sample: port-list1
    port_range:
      description: The port range.
      returned: changed
      type: str
      sample: 80-443
    vlan:
      description: Source VLANs for the packets.
      returned: changed
      type: str
      sample: vlan1
  sample: hash/dictionary of values
destination:
  description: The packet destinations to which the rule applies.
  returned: changed
  type: complex
  contains:
    address:
      description: A specific IP address.
      returned: changed
      type: str
      sample: 192.168.1.1
    address_list:
      description: An existing address list.
      returned: changed
      type: str
      sample: foo-list1
    address_range:
      description: The address range.
      returned: changed
      type: str
      sample: 1.1.1.1-2.2.2.2
    country:
      description: A country code.
      returned: changed
      type: str
      sample: US
    port:
      description: Single numeric port.
      returned: changed
      type: int
      sample: 8080
    port_list:
      description: An existing port list.
      returned: changed
      type: str
      sample: port-list1
    port_range:
      description: The port range.
      returned: changed
      type: str
      sample: 80-443
  sample: hash/dictionary of values
logging:
  description: Enable or Disable logging for the firewall rule.
  returned: changed
  type: bool
  sample: yes
rule_list:
  description: An existing rule list to use in the rule.
  returned: changed
  type: str
  sample: rule-list-1
icmp_message:
  description: The (ICMP) or ICMPv6 message C(type) and C(code) that the rule uses.
  returned: changed
  type: complex
  contains:
    type:
      description: The type of ICMP message.
      returned: changed
      type: str
      sample: 0
    code:
      description: The code returned in response to the specified ICMP message type.
      returned: changed
      type: str
      sample: 1
  sample: hash/dictionary of values
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
        'ipProtocol': 'protocol',
        'log': 'logging',
        'icmp': 'icmp_message',
    }

    api_attributes = [
        'irule',
        'ipProtocol',
        'log',
        'schedule',
        'status',
        'destination',
        'source',
        'icmp',
        'action',
        'description',
    ]

    returnables = [
        'logging',
        'protocol',
        'irule',
        'source',
        'destination',
        'action',
        'status',
        'schedule',
        'description',
        'icmp_message',
    ]

    updatables = [
        'logging',
        'protocol',
        'irule',
        'source',
        'destination',
        'action',
        'status',
        'schedule',
        'description',
        'icmp_message',
    ]

    protocol_map = {
        '1': 'icmp',
        '6': 'tcp',
        '17': 'udp',
        '58': 'icmpv6',
        '255': 'any',
    }


class ApiParameters(Parameters):
    @property
    def logging(self):
        if self._values['logging'] is None:
            return None
        if self._values['logging'] == 'yes':
            return True
        return False

    @property
    def protocol(self):
        if self._values['protocol'] is None:
            return None
        if self._values['protocol'] in self.protocol_map:
            return self.protocol_map[self._values['protocol']]
        return self._values['protocol']

    @property
    def source(self):
        result = []
        if self._values['source'] is None:
            return None
        v = self._values['source']
        if 'addressLists' in v:
            result += [('address_list', x) for x in v['addressLists']]
        if 'vlans' in v:
            result += [('vlan', x) for x in v['vlans']]
        if 'geo' in v:
            result += [('geo', x['name']) for x in v['geo']]
        if 'addresses' in v:
            result += [('address', x['name']) for x in v['addresses']]
        if 'ports' in v:
            result += [('port', str(x['name'])) for x in v['ports']]
        if 'portLists' in v:
            result += [('port_list', x) for x in v['portLists']]
        if result:
            return result
        return None

    @property
    def destination(self):
        result = []
        if self._values['destination'] is None:
            return None
        v = self._values['destination']
        if 'addressLists' in v:
            result += [('address_list', x) for x in v['addressLists']]
        if 'geo' in v:
            result += [('geo', x['name']) for x in v['geo']]
        if 'addresses' in v:
            result += [('address', x['name']) for x in v['addresses']]
        if 'ports' in v:
            result += [('port', x['name']) for x in v['ports']]
        if 'portLists' in v:
            result += [('port_list', x) for x in v['portLists']]
        if result:
            return result
        return None

    @property
    def icmp_message(self):
        if self._values['icmp_message'] is None:
            return None
        result = [x['name'] for x in self._values['icmp_message']]
        return result


class ModuleParameters(Parameters):
    @property
    def irule(self):
        if self._values['irule'] is None:
            return None
        if self._values['irule'] == '':
            return ''
        return fq_name(self.partition, self._values['irule'])

    @property
    def description(self):
        if self._values['description'] is None:
            return None
        if self._values['description'] == '':
            return ''
        return self._values['description']

    @property
    def schedule(self):
        if self._values['schedule'] is None:
            return None
        if self._values['schedule'] == '':
            return ''
        return fq_name(self.partition, self._values['schedule'])

    @property
    def source(self):
        result = []
        if self._values['source'] is None:
            return None
        for x in self._values['source']:
            if 'address' in x and x['address'] is not None:
                result += [('address', x['address'])]
            elif 'address_range' in x and x['address_range'] is not None:
                result += [('address', x['address_range'])]
            elif 'address_list' in x and x['address_list'] is not None:
                result += [('address_list', x['address_list'])]
            elif 'country' in x and x['country'] is not None:
                result += [('geo', x['country'])]
            elif 'vlan' in x and x['vlan'] is not None:
                result += [('vlan', fq_name(self.partition, x['vlan']))]
            elif 'port' in x and x['port'] is not None:
                result += [('port', str(x['port']))]
            elif 'port_range' in x and x['port_range'] is not None:
                result += [('port', x['port_range'])]
            elif 'port_list' in x and x['port_list'] is not None:
                result += [('port_list', fq_name(self.partition, x['port_list']))]
        if result:
            return result
        return None

    @property
    def destination(self):
        result = []
        if self._values['destination'] is None:
            return None
        for x in self._values['destination']:
            if 'address' in x and x['address'] is not None:
                result += [('address', x['address'])]
            elif 'address_range' in x and x['address_range'] is not None:
                result += [('address', x['address_range'])]
            elif 'address_list' in x and x['address_list'] is not None:
                result += [('address_list', x['address_list'])]
            elif 'country' in x and x['country'] is not None:
                result += [('geo', x['country'])]
            elif 'port' in x and x['port'] is not None:
                result += [('port', str(x['port']))]
            elif 'port_range' in x and x['port_range'] is not None:
                result += [('port', x['port_range'])]
            elif 'port_list' in x and x['port_list'] is not None:
                result += [('port_list', fq_name(self.partition, x['port_list']))]
        if result:
            return result
        return None

    @property
    def icmp_message(self):
        if self._values['icmp_message'] is None:
            return None
        result = []
        for x in self._values['icmp_message']:
            type = x.get('type', '255')
            code = x.get('code', '255')

            if type is None or type == 'any':
                type = '255'
            if code is None or code == 'any':
                code = '255'

            if type == '255' and code == '255':
                result.append("255")
            elif type == '255' and code != '255':
                raise F5ModuleError(
                    "A type of 'any' (255) requires a code of 'any'."
                )
            elif code == '255':
                result.append(type)
            else:
                result.append('{0}:{1}'.format(type, code))
        result = list(set(result))
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
    def logging(self):
        if self._values['logging'] is None:
            return None
        if self._values['logging'] is True:
            return "yes"
        return "no"

    @property
    def source(self):
        if self._values['source'] is None:
            return None
        result = dict(
            addresses=[],
            addressLists=[],
            vlans=[],
            geo=[],
            ports=[],
            portLists=[]
        )
        for x in self._values['source']:
            if x[0] == 'address':
                result['addresses'].append({'name': x[1]})
            elif x[0] == 'address_list':
                result['addressLists'].append(x[1])
            elif x[0] == 'vlan':
                result['vlans'].append(x[1])
            elif x[0] == 'geo':
                result['geo'].append({'name': x[1]})
            elif x[0] == 'port':
                result['ports'].append({'name': str(x[1])})
            elif x[0] == 'port_list':
                result['portLists'].append(x[1])
        return result

    @property
    def destination(self):
        if self._values['destination'] is None:
            return None
        result = dict(
            addresses=[],
            addressLists=[],
            vlans=[],
            geo=[],
            ports=[],
            portLists=[]
        )
        for x in self._values['destination']:
            if x[0] == 'address':
                result['addresses'].append({'name': x[1]})
            elif x[0] == 'address_list':
                result['addressLists'].append(x[1])
            elif x[0] == 'geo':
                result['geo'].append({'name': x[1]})
            elif x[0] == 'port':
                result['ports'].append({'name': str(x[1])})
            elif x[0] == 'port_list':
                result['portLists'].append(x[1])
        return result

    @property
    def icmp_message(self):
        if self._values['icmp_message'] is None:
            return None
        result = []
        for x in self._values['icmp_message']:
            result.append({'name': x})
        return result


class ReportableChanges(Changes):
    @property
    def source(self):
        if self._values['source'] is None:
            return None
        result = []
        v = self._values['source']
        if v['addressLists']:
            result += [('address_list', x) for x in v['addressLists']]
        if v['vlans']:
            result += [('vlan', x) for x in v['vlans']]
        if v['geo']:
            result += [('geo', x['name']) for x in v['geo']]
        if v['addresses']:
            result += [('address', x['name']) for x in v['addresses']]
        if v['ports']:
            result += [('port', str(x)) for x in v['ports']]
        if v['portLists']:
            result += [('port_list', x['name']) for x in v['portLists']]
        if result:
            return dict(result)
        return None

    @property
    def destination(self):
        if self._values['destination'] is None:
            return None
        result = []
        v = self._values['destination']
        if v['addressLists']:
            result += [('address_list', x) for x in v['addressLists']]
        if v['geo']:
            result += [('geo', x['name']) for x in v['geo']]
        if v['addresses']:
            result += [('address', x['name']) for x in v['addresses']]
        if v['ports']:
            result += [('port', str(x)) for x in v['ports']]
        if v['portLists']:
            result += [('port_list', x['name']) for x in v['portLists']]
        if result:
            return dict(result)
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
    def irule(self):
        if self.want.irule is None:
            return None
        if self.have.irule is None and self.want.irule == '':
            return None
        if self.have.irule is None:
            return self.want.irule
        if self.want.irule != self.have.irule:
            return self.want.irule

    @property
    def description(self):
        if self.want.description is None:
            return None
        if self.have.description is None and self.want.description == '':
            return None
        if self.have.description is None:
            return self.want.description
        if self.want.description != self.have.description:
            return self.want.description

    @property
    def source(self):
        if self.want.source is None:
            return None
        if self.want.source is None and self.have.source is None:
            return None
        if self.have.source is None:
            return self.want.source
        if set(self.want.source) != set(self.have.source):
            return self.want.source

    @property
    def destination(self):
        if self.want.destination is None:
            return None
        if self.want.destination is None and self.have.destination is None:
            return None
        if self.have.destination is None:
            return self.want.destination
        if set(self.want.destination) != set(self.have.destination):
            return self.want.destination

    @property
    def icmp_message(self):
        if self.want.icmp_message is None:
            return None
        if self.want.icmp_message is None and self.have.icmp_message is None:
            return None
        if self.have.icmp_message is None:
            return self.want.icmp_message
        if set(self.want.icmp_message) != set(self.have.icmp_message):
            return self.want.icmp_message


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
        if self.want.parent_policy:
            uri = "https://{0}:{1}/mgmt/tm/security/firewall/policy/{2}/rules/{3}".format(
                self.client.provider['server'],
                self.client.provider['server_port'],
                transform_name(self.want.partition, self.want.parent_policy),
                self.want.name
            )
        else:
            uri = "https://{0}:{1}/mgmt/tm/security/firewall/rule-list/{2}/rules/{3}".format(
                self.client.provider['server'],
                self.client.provider['server_port'],
                transform_name(self.want.partition, self.want.parent_rule_list),
                self.want.name
            )
        resp = self.client.api.get(uri)
        if resp.ok:
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
        if self.want.rule_list is None and self.want.parent_rule_list is None:
            if self.want.action is None:
                self.changes.update({'action': 'reject'})
            if self.want.logging is None:
                self.changes.update({'logging': False})
        if self.want.status is None:
            self.changes.update({'status': 'enabled'})
        if self.want.status == 'scheduled' and self.want.schedule is None:
            raise F5ModuleError(
                "A 'schedule' must be specified when 'status' is 'scheduled'."
            )
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        params['placeAfter'] = 'last'

        if self.want.parent_policy:
            uri = "https://{0}:{1}/mgmt/tm/security/firewall/policy/{2}/rules/".format(
                self.client.provider['server'],
                self.client.provider['server_port'],
                transform_name(self.want.partition, self.want.parent_policy),
            )
        else:
            uri = "https://{0}:{1}/mgmt/tm/security/firewall/rule-list/{2}/rules/".format(
                self.client.provider['server'],
                self.client.provider['server_port'],
                transform_name(self.want.partition, self.want.parent_rule_list),
            )
        if self.changes.protocol not in ['icmp', 'icmpv6']:
            if self.changes.icmp_message is not None:
                raise F5ModuleError(
                    "The 'icmp_message' can only be specified when 'protocol' is 'icmp' or 'icmpv6'."
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
        if self.want.parent_policy:
            uri = "https://{0}:{1}/mgmt/tm/security/firewall/policy/{2}/rules/{3}".format(
                self.client.provider['server'],
                self.client.provider['server_port'],
                transform_name(self.want.partition, self.want.parent_policy),
                self.want.name
            )
        else:
            uri = "https://{0}:{1}/mgmt/tm/security/firewall/rule-list/{2}/rules/{3}".format(
                self.client.provider['server'],
                self.client.provider['server_port'],
                transform_name(self.want.partition, self.want.parent_rule_list),
                self.want.name
            )

        if self.have.protocol not in ['icmp', 'icmpv6'] and self.changes.protocol not in ['icmp', 'icmpv6']:
            if self.changes.icmp_message is not None:
                raise F5ModuleError(
                    "The 'icmp_message' can only be specified when 'protocol' is 'icmp' or 'icmpv6'."
                )
        if self.changes.protocol in ['icmp', 'icmpv6']:
            self.changes.update({'source': {}})
            self.changes.update({'destination': {}})

        params = self.changes.api_params()
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
        if self.want.parent_policy:
            uri = "https://{0}:{1}/mgmt/tm/security/firewall/policy/{2}/rules/{3}".format(
                self.client.provider['server'],
                self.client.provider['server_port'],
                transform_name(self.want.partition, self.want.parent_policy),
                self.want.name
            )
        else:
            uri = "https://{0}:{1}/mgmt/tm/security/firewall/rule-list/{2}/rules/{3}".format(
                self.client.provider['server'],
                self.client.provider['server_port'],
                transform_name(self.want.partition, self.want.parent_rule_list),
                self.want.name
            )

        resp = self.client.api.delete(uri)
        if resp.status == 200:
            return True

    def read_current_from_device(self):
        if self.want.parent_policy:
            uri = "https://{0}:{1}/mgmt/tm/security/firewall/policy/{2}/rules/{3}".format(
                self.client.provider['server'],
                self.client.provider['server_port'],
                transform_name(self.want.partition, self.want.parent_policy),
                self.want.name
            )
        else:
            uri = "https://{0}:{1}/mgmt/tm/security/firewall/rule-list/{2}/rules/{3}".format(
                self.client.provider['server'],
                self.client.provider['server_port'],
                transform_name(self.want.partition, self.want.parent_rule_list),
                self.want.name
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
            parent_policy=dict(),
            parent_rule_list=dict(),
            logging=dict(type='bool'),
            protocol=dict(),
            irule=dict(),
            description=dict(),
            source=dict(
                type='list',
                elements='dict',
                options=dict(
                    address=dict(),
                    address_list=dict(),
                    address_range=dict(),
                    country=dict(),
                    port=dict(type='int'),
                    port_list=dict(),
                    port_range=dict(),
                    vlan=dict(),
                ),
                mutually_exclusive=[[
                    'address', 'address_list', 'address_range', 'country', 'vlan',
                    'port', 'port_range', 'port_list'
                ]]
            ),
            destination=dict(
                type='list',
                elements='dict',
                options=dict(
                    address=dict(),
                    address_list=dict(),
                    address_range=dict(),
                    country=dict(),
                    port=dict(type='int'),
                    port_list=dict(),
                    port_range=dict(),
                ),
                mutually_exclusive=[[
                    'address', 'address_list', 'address_range', 'country',
                    'port', 'port_range', 'port_list'
                ]]
            ),
            action=dict(
                choices=['accept', 'drop', 'reject', 'accept-decisively']
            ),
            status=dict(
                choices=['enabled', 'disabled', 'scheduled']
            ),
            schedule=dict(),
            rule_list=dict(),
            icmp_message=dict(
                type='list',
                elements='dict',
                options=dict(
                    type=dict(),
                    code=dict(),
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
        self.mutually_exclusive = [
            ['rule_list', 'action'],
            ['rule_list', 'source'],
            ['rule_list', 'destination'],
            ['rule_list', 'irule'],
            ['rule_list', 'protocol'],
            ['rule_list', 'logging'],
            ['parent_policy', 'parent_rule_list']
        ]
        self.required_one_of = [
            ['parent_policy', 'parent_rule_list']
        ]


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        mutually_exclusive=spec.mutually_exclusive,
        required_one_of=spec.required_one_of
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
