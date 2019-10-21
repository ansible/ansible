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
module: bigip_firewall_dos_vector
short_description: Manage attack vector configuration in an AFM DoS profile
description:
  - Manage attack vector configuration in an AFM DoS profile. In addition to the normal
    AFM DoS profile vectors, this module can manage the device-configuration vectors.
    See the module documentation for details about this method.
version_added: 2.8
options:
  name:
    description:
      - Specifies the name of the vector to modify.
      - Vectors that ship with the device are "hard-coded" so-to-speak in that the list
        of vectors is known to the system and users cannot add new vectors. Users only
        manipulate the existing vectors; all of which are disabled by default.
      - When C(ext-hdr-too-large), configures the "IPv6 extension header too large"
        Network Security vector.
      - When C(hop-cnt-low), configures the "IPv6 hop count <= <tunable>" Network
        Security vector.
      - When C(host-unreachable), configures the "Host Unreachable" Network Security
        vector.
      - When C(icmp-frag), configures the "ICMP Fragment" Network Security vector.
      - When C(icmpv4-flood), configures the "ICMPv4 flood" Network Security vector.
      - When C(icmpv6-flood), configures the "ICMPv6 flood" Network Security vector.
      - When C(ip-frag-flood), configures the "IP Fragment Flood" Network Security vector.
      - When C(ip-low-ttl), configures the "TTL <= <tunable>" Network Security vector.
      - When C(ip-opt-frames), configures the "IP Option Frames" Network Security vector.
      - When C(ipv6-ext-hdr-frames), configures the "IPv6 Extended Header Frames"
        Network Security vector.
      - When C(ipv6-frag-flood), configures the "IPv6 Fragment Flood" Network Security
        vector.
      - When C(opt-present-with-illegal-len), configures the "Option Present With Illegal
        Length" Network Security vector.
      - When C(sweep), configures the "Sweep" Network Security vector.
      - When C(tcp-bad-urg), configures the "TCP Flags-Bad URG" Network Security vector.
      - When C(tcp-half-open), configures the "TCP Half Open" Network Security vector.
      - When C(tcp-opt-overruns-tcp-hdr), configures the "TCP Option Overruns TCP Header"
        Network Security vector.
      - When C(tcp-psh-flood), configures the "TCP PUSH Flood" Network Security vector.
      - When C(tcp-rst-flood), configures the "TCP RST Flood" Network Security vector.
      - When C(tcp-syn-flood), configures the "TCP SYN Flood" Network Security vector.
      - When C(tcp-syn-oversize), configures the "TCP SYN Oversize" Network Security
        vector.
      - When C(tcp-synack-flood), configures the "TCP SYN ACK Flood" Network Security
        vector.
      - When C(tcp-window-size), configures the "TCP Window Size" Network Security
        vector.
      - When C(tidcmp), configures the "TIDCMP" Network Security vector.
      - When C(too-many-ext-hdrs), configures the "Too Many Extension Headers" Network
        Security vector.
      - When C(udp-flood), configures the "UDP Flood" Network Security vector.
      - When C(unk-tcp-opt-type), configures the "Unknown TCP Option Type" Network
        Security vector.
      - When C(a), configures the "DNS A Query" DNS Protocol Security vector.
      - When C(aaaa), configures the "DNS AAAA Query" DNS Protocol Security vector.
      - When C(any), configures the "DNS ANY Query" DNS Protocol Security vector.
      - When C(axfr), configures the "DNS AXFR Query" DNS Protocol Security vector.
      - When C(cname), configures the "DNS CNAME Query" DNS Protocol Security vector.
      - When C(dns-malformed), configures the "dns-malformed" DNS Protocol Security vector.
      - When C(ixfr), configures the "DNS IXFR Query" DNS Protocol Security vector.
      - When C(mx), configures the "DNS MX Query" DNS Protocol Security vector.
      - When C(ns), configures the "DNS NS Query" DNS Protocol Security vector.
      - When C(other), configures the "DNS OTHER Query" DNS Protocol Security vector.
      - When C(ptr), configures the "DNS PTR Query" DNS Protocol Security vector.
      - When C(qdcount), configures the "DNS QDCOUNT Query" DNS Protocol Security vector.
      - When C(soa), configures the "DNS SOA Query" DNS Protocol Security vector.
      - When C(srv), configures the "DNS SRV Query" DNS Protocol Security vector.
      - When C(txt), configures the "DNS TXT Query" DNS Protocol Security vector.
      - When C(ack), configures the "SIP ACK Method" SIP Protocol Security vector.
      - When C(bye), configures the "SIP BYE Method" SIP Protocol Security vector.
      - When C(cancel), configures the "SIP CANCEL Method" SIP Protocol Security vector.
      - When C(invite), configures the "SIP INVITE Method" SIP Protocol Security vector.
      - When C(message), configures the "SIP MESSAGE Method" SIP Protocol Security vector.
      - When C(notify), configures the "SIP NOTIFY Method" SIP Protocol Security vector.
      - When C(options), configures the "SIP OPTIONS Method" SIP Protocol Security vector.
      - When C(other), configures the "SIP OTHER Method" SIP Protocol Security vector.
      - When C(prack), configures the "SIP PRACK Method" SIP Protocol Security vector.
      - When C(publish), configures the "SIP PUBLISH Method" SIP Protocol Security vector.
      - When C(register), configures the "SIP REGISTER Method" SIP Protocol Security vector.
      - When C(sip-malformed), configures the "sip-malformed" SIP Protocol Security vector.
      - When C(subscribe), configures the "SIP SUBSCRIBE Method" SIP Protocol Security vector.
      - When C(uri-limit), configures the "uri-limit" SIP Protocol Security vector.
    type: str
    choices:
      - ext-hdr-too-large
      - hop-cnt-low
      - host-unreachable
      - icmp-frag
      - icmpv4-flood
      - icmpv6-flood
      - ip-frag-flood
      - ip-low-ttl
      - ip-opt-frames
      - ipv6-frag-flood
      - opt-present-with-illegal-len
      - sweep
      - tcp-bad-urg
      - tcp-half-open
      - tcp-opt-overruns-tcp-hdr
      - tcp-psh-flood
      - tcp-rst-flood
      - tcp-syn-flood
      - tcp-syn-oversize
      - tcp-synack-flood
      - tcp-window-size
      - tidcmp
      - too-many-ext-hdrs
      - udp-flood
      - unk-tcp-opt-type
      - a
      - aaaa
      - any
      - axfr
      - cname
      - dns-malformed
      - ixfr
      - mx
      - ns
      - other
      - ptr
      - qdcount
      - soa
      - srv
      - txt
      - ack
      - bye
      - cancel
      - invite
      - message
      - notify
      - options
      - other
      - prack
      - publish
      - register
      - sip-malformed
      - subscribe
      - uri-limit
  profile:
    description:
      - Specifies the name of the profile to manage vectors in.
      - The name C(device-config) is reserved for use by this module.
      - Vectors can be managed in either DoS Profiles, or Device Configuration. By
        specifying a profile of 'device-config', this module will specifically tailor
        configuration of the provided vectors to the Device Configuration.
    type: str
    required: True
  auto_blacklist:
    description:
      - Automatically blacklists detected bad actors.
      - To enable this parameter, the C(bad_actor_detection) must also be enabled.
      - This parameter is not supported by the C(dns-malformed) vector.
      - This parameter is not supported by the C(qdcount) vector.
    type: bool
  bad_actor_detection:
    description:
      - Whether Bad Actor detection is enabled or disabled for a vector, if available.
      - This parameter must be enabled to enable the C(auto_blacklist) parameter.
      - This parameter is not supported by the C(dns-malformed) vector.
      - This parameter is not supported by the C(qdcount) vector.
    type: bool
  attack_ceiling:
    description:
      - Specifies the absolute maximum allowable for packets of this type.
      - This setting rate limits packets to the packets per second setting, when
        specified.
      - To set no hard limit and allow automatic thresholds to manage all rate limiting,
        set this to C(infinite).
    type: str
  attack_floor:
    description:
      - Specifies packets per second to identify an attack.
      - These settings provide an absolute minimum of packets to allow before the attack
        is identified.
      - As the automatic detection thresholds adjust to traffic and CPU usage on the
        system over time, this attack floor becomes less relevant.
      - This value may not exceed the value in C(attack_floor).
    type: str
  allow_advertisement:
    description:
      - Specifies that addresses that are identified for blacklisting are advertised to
        BGP routers
    type: bool
  simulate_auto_threshold:
    description:
      - Specifies that results of the current automatic thresholds are logged, though
        manual thresholds are enforced, and no action is taken on automatic thresholds.
      - The C(sweep) vector does not support this parameter.
    type: bool
  blacklist_detection_seconds:
    description:
      - Detection, in seconds, before blacklisting occurs.
    type: int
  blacklist_duration:
    description:
      - Duration, in seconds, that the blacklist will last.
    type: int
  per_source_ip_detection_threshold:
    description:
      - Specifies the number of packets per second to identify an IP address as a bad
        actor.
    type: str
  per_source_ip_mitigation_threshold:
    description:
      - Specifies the rate limit applied to a source IP that is identified as a bad
        actor.
    type: str
  detection_threshold_percent:
    description:
      - Lists the threshold percent increase over time that the system must detect in
        traffic in order to detect this attack.
      - The C(tcp-half-open) vector does not support this parameter.
    type: str
    aliases:
      - rate_increase
  detection_threshold_eps:
    description:
      - Lists how many packets per second the system must discover in traffic in order
        to detect this attack.
    type: str
    aliases:
      - rate_threshold
  mitigation_threshold_eps:
    description:
      - Specify the maximum number of this type of packet per second the system allows
        for a vector.
      - The system drops packets once the traffic level exceeds the rate limit.
    type: str
    aliases:
      - rate_limit
  threshold_mode:
    description:
      - The C(dns-malformed) vector does not support C(fully-automatic), or C(stress-based-mitigation)
        for this parameter.
      - The C(qdcount) vector does not support C(fully-automatic), or C(stress-based-mitigation)
        for this parameter.
      - The C(sip-malformed) vector does not support C(fully-automatic), or C(stress-based-mitigation)
        for this parameter.
    type: str
    choices:
      - manual
      - stress-based-mitigation
      - fully-automatic
  state:
    description:
      - When C(state) is C(mitigate), ensures that the vector enforces limits and
        thresholds.
      - When C(state) is C(detect-only), ensures that the vector does not enforce limits
        and thresholds (rate limiting, dopping, etc), but is still tracked in logs and statistics.
      - When C(state) is C(disabled), ensures that the vector does not enforce limits
        and thresholds, but is still tracked in logs and statistics.
      - When C(state) is C(learn-only), ensures that the vector does not "detect" any attacks.
        Only learning and stat collecting is performed.
    type: str
    choices:
      - mitigate
      - detect-only
      - learn-only
      - disabled
    required: True
  partition:
    description:
      - Device partition to manage resources on.
    type: str
    default: Common
extends_documentation_fragment: f5
requirements:
  - BIG-IP >= v13.0.0
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Enable DNS AAAA vector mitigation
  bigip_firewall_dos_vector:
    name: aaaa
    state: mitigate
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
allow_advertisement:
  description: The new Allow External Advertisement setting.
  returned: changed
  type: bool
  sample: yes
auto_blacklist:
  description: The new Auto Blacklist setting.
  returned: changed
  type: bool
  sample: no
bad_actor_detection:
  description: The new Bad Actor Detection setting.
  returned: changed
  type: bool
  sample: no
blacklist_detection_seconds:
  description: The new Sustained Attack Detection Time setting.
  returned: changed
  type: int
  sample: 60
blacklist_duration:
  description: The new Category Duration Time setting.
  returned: changed
  type: int
  sample: 14400
attack_ceiling:
  description: The new Attack Ceiling EPS setting.
  returned: changed
  type: str
  sample: infinite
attack_floor:
  description: The new Attack Floor EPS setting.
  returned: changed
  type: str
  sample: infinite
blacklist_category:
  description: The new Category Name setting.
  returned: changed
  type: str
  sample: /Common/cloud_provider_networks
per_source_ip_detection_threshold:
  description: The new Per Source IP Detection Threshold EPS setting.
  returned: changed
  type: str
  sample: 23
per_source_ip_mitigation_threshold:
  description: The new Per Source IP Mitigation Threshold EPS setting.
  returned: changed
  type: str
  sample: infinite
detection_threshold_percent:
  description: The new Detection Threshold Percent setting.
  returned: changed
  type: str
  sample: infinite
detection_threshold_eps:
  description: The new Detection Threshold EPS setting.
  returned: changed
  type: str
  sample: infinite
mitigation_threshold_eps:
  description: The new Mitigation Threshold EPS setting.
  returned: changed
  type: str
  sample: infinite
threshold_mode:
  description: The new Mitigation Threshold EPS setting.
  returned: changed
  type: str
  sample: infinite
simulate_auto_threshold:
  description: The new Simulate Auto Threshold setting.
  returned: changed
  type: bool
  sample: no
state:
  description: The new state of the vector.
  returned: changed
  type: str
  sample: mitigate
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.six import iteritems

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.common import flatten_boolean
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import flatten_boolean


NETWORK_SECURITY_VECTORS = [
    'ext-hdr-too-large',             # IPv6 extension header too large
    'hop-cnt-low',                   # IPv6 hop count <= <tunable>
    'host-unreachable',              # Host Unreachable
    'icmp-frag',                     # ICMP Fragment
    'icmpv4-flood',                  # ICMPv4 flood
    'icmpv6-flood',                  # ICMPv6 flood
    'ip-frag-flood',                 # IP Fragment Flood
    'ip-low-ttl',                    # TTL <= <tunable>
    'ip-opt-frames',                 # IP Option Frames
    'ipv6-ext-hdr-frames',           # IPv6 Extended Header Frames
    'ipv6-frag-flood',               # IPv6 Fragment Flood
    'opt-present-with-illegal-len',  # Option Present With Illegal Length
    'sweep',                         # Sweep
    'tcp-bad-urg',                   # TCP Flags-Bad URG
    'tcp-half-open',                 # TCP Half Open
    'tcp-opt-overruns-tcp-hdr',      # TCP Option Overruns TCP Header
    'tcp-psh-flood',                 # TCP PUSH Flood
    'tcp-rst-flood',                 # TCP RST Flood
    'tcp-syn-flood',                 # TCP SYN Flood
    'tcp-syn-oversize',              # TCP SYN Oversize
    'tcp-synack-flood',              # TCP SYN ACK Flood
    'tcp-window-size',               # TCP Window Size
    'tidcmp',                        # TIDCMP
    'too-many-ext-hdrs',             # Too Many Extension Headers
    'udp-flood',                     # UDP Flood
    'unk-tcp-opt-type',              # Unknown TCP Option Type
]

PROTOCOL_SIP_VECTORS = [
    'ack',            # SIP ACK Method
    'bye',            # SIP BYE Method
    'cancel',         # SIP CANCEL Method
    'invite',         # SIP INVITE Method
    'message',        # SIP MESSAGE Method
    'notify',         # SIP NOTIFY Method
    'options',        # SIP OPTIONS Method
    'other',          # SIP OTHER Method
    'prack',          # SIP PRACK Method
    'publish',        # SIP PUBLISH Method
    'register',       # SIP REGISTER Method
    'sip-malformed',  # sip-malformed
    'subscribe',      # SIP SUBSCRIBE Method
    'uri-limit',      # uri-limit
]

PROTOCOL_DNS_VECTORS = [
    'a',              # DNS A Query
    'aaaa',           # DNS AAAA Query
    'any',            # DNS ANY Query
    'axfr',           # DNS AXFR Query
    'cname',          # DNS CNAME Query
    'dns-malformed',  # dns-malformed
    'ixfr',           # DNS IXFR Query
    'mx',             # DNS MX Query
    'ns',             # DNS NS Query
    'other',          # DNS OTHER Query
    'ptr',            # DNS PTR Query
    'qdcount',        # DNS QDCOUNT LIMIT
    'soa',            # DNS SOA Query
    'srv',            # DNS SRV Query
    'txt',            # DNS TXT Query
]


class Parameters(AnsibleF5Parameters):
    api_map = {
        'allowAdvertisement': 'allow_advertisement',
        'autoBlacklisting': 'auto_blacklist',

        # "autoThreshold": "disabled",
        # This is a deprecated parameter in 13.1.0. Use threshold_mode instead

        'badActor': 'bad_actor_detection',
        'blacklistCategory': 'blacklist_category',
        'blacklistDetectionSeconds': 'blacklist_detection_seconds',
        'blacklistDuration': 'blacklist_duration',
        'ceiling': 'attack_ceiling',
        # "enforce": "enabled",
        'floor': 'attack_floor',
        'perSourceIpDetectionPps': 'per_source_ip_detection_threshold',
        'perSourceIpLimitPps': 'per_source_ip_mitigation_threshold',
        'rateIncrease': 'detection_threshold_percent',
        'rateLimit': 'mitigation_threshold_eps',
        'rateThreshold': 'detection_threshold_eps',
        'simulateAutoThreshold': 'simulate_auto_threshold',
        'thresholdMode': 'threshold_mode',

        # device-config specific settings
        'scrubbingDetectionSeconds': 'sustained_attack_detection_time',
        'scrubbingDuration': 'category_detection_time',
        'perDstIpDetectionPps': 'per_dest_ip_detection_threshold',
        'perDstIpLimitPps': 'per_dest_ip_mitigation_threshold',

        # The following are not enabled for device-config because I
        # do not know what parameters in TMUI they map to. Additionally,
        # they do not appear to have any "help" documentation available
        # in ``tmsh help security dos device-config``.
        #
        # "allowUpstreamScrubbing": "disabled",
        # "attackedDst": "disabled",
        # "autoScrubbing": "disabled",
        'defaultInternalRateLimit': 'mitigation_threshold_eps',
        'detectionThresholdPercent': 'detection_threshold_percent',
        'detectionThresholdPps': 'detection_threshold_eps',
    }

    api_attributes = [
        'allowAdvertisement',
        'autoBlacklisting',
        'autoThreshold',
        'badActor',
        'blacklistCategory',
        'blacklistDetectionSeconds',
        'blacklistDuration',
        'ceiling',
        'enforce',
        'floor',
        'perSourceIpDetectionPps',
        'perSourceIpLimitPps',
        'rateIncrease',
        'rateLimit',
        'rateThreshold',
        'simulateAutoThreshold',
        'state',
        'thresholdMode',

        # device-config specific
        'scrubbingDetectionSeconds',
        'scrubbingDuration',
        'perDstIpDetectionPps',
        'perDstIpLimitPps',
        'defaultInternalRateLimit',
        'detectionThresholdPercent',
        'detectionThresholdPps',

        # Attributes on the DoS profiles that hold the different vectors
        #
        # Each of these attributes is a list of dictionaries. Each dictionary
        # contains the settings that affect the way the vector works.
        #
        # The vectors appear to all have the same attributes even if those
        # attributes are not used. There may be cases where this is not true,
        # however, and for those vectors we should either include specific
        # error detection, or pass the unfiltered values through to mcpd and
        # handle any unintuitive error messages that mcpd returns.
        'dosDeviceVector',
        'dnsQueryVector',
        'networkAttackVector',
        'sipAttackVector',
    ]

    returnables = [
        'allow_advertisement',
        'auto_blacklist',
        'bad_actor_detection',
        'blacklist_detection_seconds',
        'blacklist_duration',
        'attack_ceiling',
        'attack_floor',
        'blacklist_category',
        'per_source_ip_detection_threshold',
        'per_source_ip_mitigation_threshold',
        'detection_threshold_percent',
        'detection_threshold_eps',
        'mitigation_threshold_eps',
        'threshold_mode',
        'simulate_auto_threshold',
        'state',
    ]

    updatables = [
        'allow_advertisement',
        'auto_blacklist',
        'bad_actor_detection',
        'blacklist_detection_seconds',
        'blacklist_duration',
        'attack_ceiling',
        'attack_floor',
        'blacklist_category',
        'per_source_ip_detection_threshold',
        'per_source_ip_mitigation_threshold',
        'detection_threshold_percent',
        'detection_threshold_eps',
        'mitigation_threshold_eps',
        'threshold_mode',
        'simulate_auto_threshold',
        'state',
    ]

    @property
    def allow_advertisement(self):
        return flatten_boolean(self._values['allow_advertisement'])

    @property
    def auto_blacklist(self):
        return flatten_boolean(self._values['auto_blacklist'])

    @property
    def simulate_auto_threshold(self):
        return flatten_boolean(self._values['simulate_auto_threshold'])

    @property
    def bad_actor_detection(self):
        return flatten_boolean(self._values['bad_actor_detection'])

    @property
    def detection_threshold_percent(self):
        if self._values['detection_threshold_percent'] in [None, "infinite"]:
            return self._values['detection_threshold_percent']
        return int(self._values['detection_threshold_percent'])

    @property
    def per_source_ip_mitigation_threshold(self):
        if self._values['per_source_ip_mitigation_threshold'] in [None, "infinite"]:
            return self._values['per_source_ip_mitigation_threshold']
        return int(self._values['per_source_ip_mitigation_threshold'])

    @property
    def per_dest_ip_mitigation_threshold(self):
        if self._values['per_dest_ip_mitigation_threshold'] in [None, "infinite"]:
            return self._values['per_dest_ip_mitigation_threshold']
        return int(self._values['per_dest_ip_mitigation_threshold'])

    @property
    def mitigation_threshold_eps(self):
        if self._values['mitigation_threshold_eps'] in [None, "infinite"]:
            return self._values['mitigation_threshold_eps']
        return int(self._values['mitigation_threshold_eps'])

    @property
    def detection_threshold_eps(self):
        if self._values['detection_threshold_eps'] in [None, "infinite"]:
            return self._values['detection_threshold_eps']
        return int(self._values['detection_threshold_eps'])

    @property
    def attack_ceiling(self):
        if self._values['attack_ceiling'] in [None, "infinite"]:
            return self._values['attack_ceiling']
        return int(self._values['attack_ceiling'])

    @property
    def blacklist_category(self):
        if self._values['blacklist_category'] is None:
            return None
        return fq_name(self.partition, self._values['blacklist_category'])


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    pass


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
    def allow_advertisement(self):
        if self._values['allow_advertisement'] is None:
            return None
        if self._values['allow_advertisement'] == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def auto_blacklist(self):
        if self._values['auto_blacklist'] is None:
            return None
        if self._values['auto_blacklist'] == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def simulate_auto_threshold(self):
        if self._values['simulate_auto_threshold'] is None:
            return None
        if self._values['simulate_auto_threshold'] == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def bad_actor_detection(self):
        if self._values['bad_actor_detection'] is None:
            return None
        if self._values['bad_actor_detection'] == 'yes':
            return 'enabled'
        return 'disabled'


class ReportableChanges(Changes):
    @property
    def allow_advertisement(self):
        return flatten_boolean(self._values['allow_advertisement'])

    @property
    def auto_blacklist(self):
        return flatten_boolean(self._values['auto_blacklist'])

    @property
    def simulate_auto_threshold(self):
        return flatten_boolean(self._values['simulate_auto_threshold'])

    @property
    def bad_actor_detection(self):
        return flatten_boolean(self._values['bad_actor_detection'])


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
        want = getattr(self.want, param)
        try:
            have = getattr(self.have, param)
            if want != have:
                return want
        except AttributeError:
            return want


class BaseManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)

        # A list of all the vectors queried from the API when reading current info
        # from the device. This is used when updating the API as the value that needs
        # to be updated is a list of vectors and PATCHing a list would override any
        # default settings.
        self.vectors = dict()

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

    def exec_module(self):
        result = dict()

        changed = self.present()

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        return result

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def present(self):
        return self.update()

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def format_vectors(self, vectors):
        result = None
        for x in vectors:
            vector = ApiParameters(params=x)
            self.vectors[vector.name] = x
            if vector.name == self.want.name:
                result = vector
        if not result:
            return ApiParameters()
        return result

    def _update(self, vtype):
        self.have = self.format_vectors(self.read_current_from_device())
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True

        # A disabled vector does not appear in the list of existing vectors
        if self.want.state == 'disabled':
            if self.want.profile == 'device-config' and self.have.state == 'disabled':
                return False
            # For non-device-config
            if self.want.name not in self.vectors:
                return False

        # At this point we know the existing vector is not disabled, so we need
        # to change it in some way.
        #
        # First, if we see that the vector is in the current list of vectors,
        # we are going to update it
        changes = dict(self.changes.api_params())
        if self.want.name in self.vectors:
            self.vectors[self.want.name].update(changes)
        else:
            # else, we are going to add it to the list of vectors
            self.vectors[self.want.name] = changes

        # Since the name attribute is not a parameter tracked in the Parameter
        # classes, we will add the name to the list of attributes so that when
        # we update the API, it creates the correct vector
        self.vectors[self.want.name].update({'name': self.want.name})

        # Finally, the disabled state forces us to remove the vector from the
        # list. However, items are only removed from the list if the profile
        # being configured is not a device-config
        if self.want.state == 'disabled':
            if self.want.profile != 'device-config':
                del self.vectors[self.want.name]

        # All of the vectors must be re-assembled into a list of dictionaries
        # so that when we PATCH the API endpoint, the vectors list is filled
        # correctly.
        #
        # There are **not** individual API endpoints for the individual vectors.
        # Instead, the endpoint includes a list of vectors that is part of the
        # DoS profile
        result = [v for k, v in iteritems(self.vectors)]

        self.changes = Changes(params={vtype: result})
        self.update_on_device()
        return True


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.kwargs = kwargs

    def exec_module(self):
        if self.module.params['profile'] == 'device-config':
            manager = self.get_manager('v1')
        elif self.module.params['name'] in NETWORK_SECURITY_VECTORS:
            manager = self.get_manager('v2')
        elif self.module.params['name'] in PROTOCOL_DNS_VECTORS:
            manager = self.get_manager('v3')
        elif self.module.params['name'] in PROTOCOL_SIP_VECTORS:
            manager = self.get_manager('v4')
        else:
            raise F5ModuleError(
                "Unknown vector type specified."
            )
        return manager.exec_module()

    def get_manager(self, type):
        if type == 'v1':
            return DeviceConfigManager(**self.kwargs)
        elif type == 'v2':
            return NetworkSecurityManager(**self.kwargs)
        elif type == 'v3':
            return ProtocolDnsManager(**self.kwargs)
        elif type == 'v4':
            return ProtocolSipManager(**self.kwargs)


class DeviceConfigManager(BaseManager):
    """Manages AFM DoS Device Configuration settings.

    DeviceConfiguration is a special type of profile that is specific to the
    BIG-IP device's management interface; not the data plane interfaces.

    There are many similar vectors that can be managed here. This configuration
    is a super-set of the base DoS profile vector configuration and includes
    several attributes per-vector that are not found in the DoS profile configuration.
    These include,

      * allowUpstreamScrubbing
      * attackedDst
      * autoScrubbing
      * defaultInternalRateLimit
      * detectionThresholdPercent
      * detectionThresholdPps
      * perDstIpDetectionPps
      * perDstIpLimitPps
      * scrubbingDetectionSeconds
      * scrubbingDuration
    """
    def __init__(self, *args, **kwargs):
        super(DeviceConfigManager, self).__init__(**kwargs)
        self.want = ModuleParameters(params=self.module.params)
        self.have = ApiParameters()
        self.changes = UsableChanges()

    def update(self):
        name = self.normalize_names_in_device_config(self.want.name)

        self.want.update({'name': name})

        return self._update('dosDeviceVector')

    def normalize_names_in_device_config(self, name):
        # Overwrite specific names because they do not align with DoS Profile names
        #
        # The following names (on the right) differ from the functionally equivalent
        # names (on the left) found in DoS Profiles. This seems like a bug to me,
        # but I do not expect it to be fixed, so this works around it in the meantime.
        name_map = {
            'hop-cnt-low': 'hop-cnt-leq-one',
            'ip-low-ttl': 'ttl-leq-one',
        }

        # Attempt to normalize, else just return the name. This handles the default
        # case where the name is actually correct and would not be found in the
        # ``name_map`` above.
        result = name_map.get(name, name)
        return result

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/security/dos/device-config/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name('Common', 'dos-device-config')
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

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/security/dos/device-config/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name('Common', 'dos-device-config')
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
        result = response.get('dosDeviceVector', [])
        return result


class NetworkSecurityManager(BaseManager):
    """Manages AFM DoS Profile Network Security settings.

    Network Security settings are a sub-collection attached to each profile.

    There are many similar vectors that can be managed here. This configuration
    is a sub-set of the device-config DoS vector configuration and excludes
    several attributes per-vector that are found in the device-config configuration.
    These include,

      * rateIncrease
      * rateLimit
      * rateThreshold
    """
    def __init__(self, *args, **kwargs):
        super(NetworkSecurityManager, self).__init__(**kwargs)
        self.want = ModuleParameters(params=self.module.params)
        self.have = ApiParameters()
        self.changes = UsableChanges()

    def update(self):
        return self._update('networkAttackVector')

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/security/dos/profile/{2}/dos-network/{3}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.profile),
            self.want.profile
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

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/security/dos/profile/{2}/dos-network/{3}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.profile),
            self.want.profile
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
        return response.get('networkAttackVector', [])


class ProtocolDnsManager(BaseManager):
    """Manages AFM DoS Profile Protocol DNS settings.

    Protocol DNS settings are a sub-collection attached to each profile.

    There are many similar vectors that can be managed here. This configuration
    is a sub-set of the device-config DoS vector configuration and excludes
    several attributes per-vector that are found in the device-config configuration.
    These include,

      * rateIncrease
      * rateLimit
      * rateThreshold
    """
    def __init__(self, *args, **kwargs):
        super(ProtocolDnsManager, self).__init__(**kwargs)
        self.want = ModuleParameters(params=self.module.params)
        self.have = ApiParameters()
        self.changes = UsableChanges()

    def update(self):
        return self._update('dnsQueryVector')

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/security/dos/profile/{2}/protocol-dns/{3}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.profile),
            self.want.profile
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

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/security/dos/profile/{2}/protocol-dns/{3}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.profile),
            self.want.profile
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
        return response.get('dnsQueryVector', [])


class ProtocolSipManager(BaseManager):
    """Manages AFM DoS Profile Protocol SIP settings.

    Protocol SIP settings are a sub-collection attached to each profile.

    There are many similar vectors that can be managed here. This configuration
    is a sub-set of the device-config DoS vector configuration and excludes
    several attributes per-vector that are found in the device-config configuration.
    These include,

      * rateIncrease
      * rateLimit
      * rateThreshold
    """
    def __init__(self, *args, **kwargs):
        super(ProtocolSipManager, self).__init__(**kwargs)
        self.want = ModuleParameters(params=self.module.params)
        self.have = ApiParameters()
        self.changes = UsableChanges()

    def update(self):
        return self._update('sipAttackVector')

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/security/dos/profile/{2}/protocol-sip/{3}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.profile),
            self.want.profile
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

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/security/dos/profile/{2}/protocol-sip/{3}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.profile),
            self.want.profile
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
        return response.get('sipAttackVector', [])


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(
                required=True,
                choices=[
                    'ext-hdr-too-large',
                    'hop-cnt-low',
                    'host-unreachable',
                    'icmp-frag',
                    'icmpv4-flood',
                    'icmpv6-flood',
                    'ip-frag-flood',
                    'ip-low-ttl',
                    'ip-opt-frames',
                    'ipv6-frag-flood',
                    'opt-present-with-illegal-len',
                    'sweep',
                    'tcp-bad-urg',
                    'tcp-half-open',
                    'tcp-opt-overruns-tcp-hdr',
                    'tcp-psh-flood',
                    'tcp-rst-flood',
                    'tcp-syn-flood',
                    'tcp-syn-oversize',
                    'tcp-synack-flood',
                    'tcp-window-size',
                    'tidcmp',
                    'too-many-ext-hdrs',
                    'udp-flood',
                    'unk-tcp-opt-type',
                    'a',
                    'aaaa',
                    'any',
                    'axfr',
                    'cname',
                    'dns-malformed',
                    'ixfr',
                    'mx',
                    'ns',
                    'other',
                    'ptr',
                    'qdcount',
                    'soa',
                    'srv',
                    'txt',
                    'ack',
                    'bye',
                    'cancel',
                    'invite',
                    'message',
                    'notify',
                    'options',
                    'other',
                    'prack',
                    'publish',
                    'register',
                    'sip-malformed',
                    'subscribe',
                    'uri-limit',
                ]
            ),
            profile=dict(required=True),
            allow_advertisement=dict(type='bool'),
            auto_blacklist=dict(type='bool'),
            simulate_auto_threshold=dict(type='bool'),
            bad_actor_detection=dict(type='bool'),
            blacklist_detection_seconds=dict(type='int'),
            blacklist_duration=dict(type='int'),
            attack_ceiling=dict(),
            attack_floor=dict(),
            per_source_ip_detection_threshold=dict(),
            per_source_ip_mitigation_threshold=dict(),
            # sustained_attack_detection_time=dict(),
            # category_detection_time=dict(),
            # per_dest_ip_detection_threshold=dict(),
            # per_dest_ip_mitigation_threshold=dict(),

            detection_threshold_percent=dict(
                aliases=['rate_increase']
            ),
            detection_threshold_eps=dict(
                aliases=['rate_threshold']
            ),
            mitigation_threshold_eps=dict(
                aliases=['rate_limit']
            ),
            threshold_mode=dict(
                choices=['manual', 'stress-based-mitigation', 'fully-automatic']
            ),
            state=dict(
                choices=['mitigate', 'detect-only', 'learn-only', 'disabled'],
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
