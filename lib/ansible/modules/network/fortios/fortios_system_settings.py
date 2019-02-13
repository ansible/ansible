#!/usr/bin/python
from __future__ import (absolute_import, division, print_function)
# Copyright 2019 Fortinet, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# the lib use python logging can get it if the following is set in your
# Ansible config.

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fortios_system_settings
short_description: Configure VDOM settings in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure system feature and settings category.
      Examples includes all options and need to be adjusted to datasources before usage.
      Tested with FOS v6.0.2
version_added: "2.8"
author:
    - Miguel Angel Munoz (@mamunozgonzalez)
    - Nicolas Thomas (@thomnico)
notes:
    - Requires fortiosapi library developed by Fortinet
    - Run as a local_action in your playbook
requirements:
    - fortiosapi>=0.9.8
options:
    host:
       description:
            - FortiOS or FortiGate ip adress.
       required: true
    username:
        description:
            - FortiOS or FortiGate username.
        required: true
    password:
        description:
            - FortiOS or FortiGate password.
        default: ""
    vdom:
        description:
            - Virtual domain, among those defined previously. A vdom is a
              virtual instance of the FortiGate that can be configured and
              used as a different unit.
        default: root
    https:
        description:
            - Indicates if the requests towards FortiGate must use HTTPS
              protocol
        type: bool
        default: true
    system_settings:
        description:
            - Configure VDOM settings.
        default: null
        suboptions:
            allow-subnet-overlap:
                description:
                    - Enable/disable allowing interface subnets to use overlapping IP addresses.
                choices:
                    - enable
                    - disable
            asymroute:
                description:
                    - Enable/disable IPv4 asymmetric routing.
                choices:
                    - enable
                    - disable
            asymroute-icmp:
                description:
                    - Enable/disable ICMP asymmetric routing.
                choices:
                    - enable
                    - disable
            asymroute6:
                description:
                    - Enable/disable asymmetric IPv6 routing.
                choices:
                    - enable
                    - disable
            asymroute6-icmp:
                description:
                    - Enable/disable asymmetric ICMPv6 routing.
                choices:
                    - enable
                    - disable
            bfd:
                description:
                    - Enable/disable Bi-directional Forwarding Detection (BFD) on all interfaces.
                choices:
                    - enable
                    - disable
            bfd-desired-min-tx:
                description:
                    - BFD desired minimal transmit interval (1 - 100000 ms, default = 50).
            bfd-detect-mult:
                description:
                    - BFD detection multiplier (1 - 50, default = 3).
            bfd-dont-enforce-src-port:
                description:
                    - Enable to not enforce verifying the source port of BFD Packets.
                choices:
                    - enable
                    - disable
            bfd-required-min-rx:
                description:
                    - BFD required minimal receive interval (1 - 100000 ms, default = 50).
            block-land-attack:
                description:
                    - Enable/disable blocking of land attacks.
                choices:
                    - disable
                    - enable
            central-nat:
                description:
                    - Enable/disable central NAT.
                choices:
                    - enable
                    - disable
            comments:
                description:
                    - VDOM comments.
            compliance-check:
                description:
                    - Enable/disable PCI DSS compliance checking.
                choices:
                    - enable
                    - disable
            default-voip-alg-mode:
                description:
                    - Configure how the FortiGate handles VoIP traffic when a policy that accepts the traffic doesn't include a VoIP profile.
                choices:
                    - proxy-based
                    - kernel-helper-based
            deny-tcp-with-icmp:
                description:
                    - Enable/disable denying TCP by sending an ICMP communication prohibited packet.
                choices:
                    - enable
                    - disable
            device:
                description:
                    - Interface to use for management access for NAT mode. Source system.interface.name.
            dhcp-proxy:
                description:
                    - Enable/disable the DHCP Proxy.
                choices:
                    - enable
                    - disable
            dhcp-server-ip:
                description:
                    - DHCP Server IPv4 address.
            dhcp6-server-ip:
                description:
                    - DHCPv6 server IPv6 address.
            discovered-device-timeout:
                description:
                    - Timeout for discovered devices (1 - 365 days, default = 28).
            ecmp-max-paths:
                description:
                    - Maximum number of Equal Cost Multi-Path (ECMP) next-hops. Set to 1 to disable ECMP routing (1 - 100, default = 10).
            email-portal-check-dns:
                description:
                    - Enable/disable using DNS to validate email addresses collected by a captive portal.
                choices:
                    - disable
                    - enable
            firewall-session-dirty:
                description:
                    - Select how to manage sessions affected by firewall policy configuration changes.
                choices:
                    - check-all
                    - check-new
                    - check-policy-option
            fw-session-hairpin:
                description:
                    - Enable/disable checking for a matching policy each time hairpin traffic goes through the FortiGate.
                choices:
                    - enable
                    - disable
            gateway:
                description:
                    - Transparent mode IPv4 default gateway IP address.
            gateway6:
                description:
                    - Transparent mode IPv4 default gateway IP address.
            gui-advanced-policy:
                description:
                    - Enable/disable advanced policy configuration on the GUI.
                choices:
                    - enable
                    - disable
            gui-allow-unnamed-policy:
                description:
                    - Enable/disable the requirement for policy naming on the GUI.
                choices:
                    - enable
                    - disable
            gui-antivirus:
                description:
                    - Enable/disable AntiVirus on the GUI.
                choices:
                    - enable
                    - disable
            gui-ap-profile:
                description:
                    - Enable/disable FortiAP profiles on the GUI.
                choices:
                    - enable
                    - disable
            gui-application-control:
                description:
                    - Enable/disable application control on the GUI.
                choices:
                    - enable
                    - disable
            gui-default-policy-columns:
                description:
                    - Default columns to display for policy lists on GUI.
                suboptions:
                    name:
                        description:
                            - Select column name.
                        required: true
            gui-dhcp-advanced:
                description:
                    - Enable/disable advanced DHCP options on the GUI.
                choices:
                    - enable
                    - disable
            gui-dlp:
                description:
                    - Enable/disable DLP on the GUI.
                choices:
                    - enable
                    - disable
            gui-dns-database:
                description:
                    - Enable/disable DNS database settings on the GUI.
                choices:
                    - enable
                    - disable
            gui-dnsfilter:
                description:
                    - Enable/disable DNS Filtering on the GUI.
                choices:
                    - enable
                    - disable
            gui-domain-ip-reputation:
                description:
                    - Enable/disable Domain and IP Reputation on the GUI.
                choices:
                    - enable
                    - disable
            gui-dos-policy:
                description:
                    - Enable/disable DoS policies on the GUI.
                choices:
                    - enable
                    - disable
            gui-dynamic-profile-display:
                description:
                    - Enable/disable RADIUS Single Sign On (RSSO) on the GUI.
                choices:
                    - enable
                    - disable
            gui-dynamic-routing:
                description:
                    - Enable/disable dynamic routing on the GUI.
                choices:
                    - enable
                    - disable
            gui-email-collection:
                description:
                    - Enable/disable email collection on the GUI.
                choices:
                    - enable
                    - disable
            gui-endpoint-control:
                description:
                    - Enable/disable endpoint control on the GUI.
                choices:
                    - enable
                    - disable
            gui-endpoint-control-advanced:
                description:
                    - Enable/disable advanced endpoint control options on the GUI.
                choices:
                    - enable
                    - disable
            gui-explicit-proxy:
                description:
                    - Enable/disable the explicit proxy on the GUI.
                choices:
                    - enable
                    - disable
            gui-fortiap-split-tunneling:
                description:
                    - Enable/disable FortiAP split tunneling on the GUI.
                choices:
                    - enable
                    - disable
            gui-fortiextender-controller:
                description:
                    - Enable/disable FortiExtender on the GUI.
                choices:
                    - enable
                    - disable
            gui-icap:
                description:
                    - Enable/disable ICAP on the GUI.
                choices:
                    - enable
                    - disable
            gui-implicit-policy:
                description:
                    - Enable/disable implicit firewall policies on the GUI.
                choices:
                    - enable
                    - disable
            gui-ips:
                description:
                    - Enable/disable IPS on the GUI.
                choices:
                    - enable
                    - disable
            gui-load-balance:
                description:
                    - Enable/disable server load balancing on the GUI.
                choices:
                    - enable
                    - disable
            gui-local-in-policy:
                description:
                    - Enable/disable Local-In policies on the GUI.
                choices:
                    - enable
                    - disable
            gui-local-reports:
                description:
                    - Enable/disable local reports on the GUI.
                choices:
                    - enable
                    - disable
            gui-multicast-policy:
                description:
                    - Enable/disable multicast firewall policies on the GUI.
                choices:
                    - enable
                    - disable
            gui-multiple-interface-policy:
                description:
                    - Enable/disable adding multiple interfaces to a policy on the GUI.
                choices:
                    - enable
                    - disable
            gui-multiple-utm-profiles:
                description:
                    - Enable/disable multiple UTM profiles on the GUI.
                choices:
                    - enable
                    - disable
            gui-nat46-64:
                description:
                    - Enable/disable NAT46 and NAT64 settings on the GUI.
                choices:
                    - enable
                    - disable
            gui-object-colors:
                description:
                    - Enable/disable object colors on the GUI.
                choices:
                    - enable
                    - disable
            gui-policy-based-ipsec:
                description:
                    - Enable/disable policy-based IPsec VPN on the GUI.
                choices:
                    - enable
                    - disable
            gui-policy-learning:
                description:
                    - Enable/disable firewall policy learning mode on the GUI.
                choices:
                    - enable
                    - disable
            gui-replacement-message-groups:
                description:
                    - Enable/disable replacement message groups on the GUI.
                choices:
                    - enable
                    - disable
            gui-spamfilter:
                description:
                    - Enable/disable Antispam on the GUI.
                choices:
                    - enable
                    - disable
            gui-sslvpn-personal-bookmarks:
                description:
                    - Enable/disable SSL-VPN personal bookmark management on the GUI.
                choices:
                    - enable
                    - disable
            gui-sslvpn-realms:
                description:
                    - Enable/disable SSL-VPN realms on the GUI.
                choices:
                    - enable
                    - disable
            gui-switch-controller:
                description:
                    - Enable/disable the switch controller on the GUI.
                choices:
                    - enable
                    - disable
            gui-threat-weight:
                description:
                    - Enable/disable threat weight on the GUI.
                choices:
                    - enable
                    - disable
            gui-traffic-shaping:
                description:
                    - Enable/disable traffic shaping on the GUI.
                choices:
                    - enable
                    - disable
            gui-voip-profile:
                description:
                    - Enable/disable VoIP profiles on the GUI.
                choices:
                    - enable
                    - disable
            gui-vpn:
                description:
                    - Enable/disable VPN tunnels on the GUI.
                choices:
                    - enable
                    - disable
            gui-waf-profile:
                description:
                    - Enable/disable Web Application Firewall on the GUI.
                choices:
                    - enable
                    - disable
            gui-wan-load-balancing:
                description:
                    - Enable/disable SD-WAN on the GUI.
                choices:
                    - enable
                    - disable
            gui-wanopt-cache:
                description:
                    - Enable/disable WAN Optimization and Web Caching on the GUI.
                choices:
                    - enable
                    - disable
            gui-webfilter:
                description:
                    - Enable/disable Web filtering on the GUI.
                choices:
                    - enable
                    - disable
            gui-webfilter-advanced:
                description:
                    - Enable/disable advanced web filtering on the GUI.
                choices:
                    - enable
                    - disable
            gui-wireless-controller:
                description:
                    - Enable/disable the wireless controller on the GUI.
                choices:
                    - enable
                    - disable
            http-external-dest:
                description:
                    - Offload HTTP traffic to FortiWeb or FortiCache.
                choices:
                    - fortiweb
                    - forticache
            ike-dn-format:
                description:
                    - Configure IKE ASN.1 Distinguished Name format conventions.
                choices:
                    - with-space
                    - no-space
            ike-quick-crash-detect:
                description:
                    - Enable/disable IKE quick crash detection (RFC 6290).
                choices:
                    - enable
                    - disable
            ike-session-resume:
                description:
                    - Enable/disable IKEv2 session resumption (RFC 5723).
                choices:
                    - enable
                    - disable
            implicit-allow-dns:
                description:
                    - Enable/disable implicitly allowing DNS traffic.
                choices:
                    - enable
                    - disable
            inspection-mode:
                description:
                    - Inspection mode (proxy-based or flow-based).
                choices:
                    - proxy
                    - flow
            ip:
                description:
                    - IP address and netmask.
            ip6:
                description:
                    - IPv6 address prefix for NAT mode.
            link-down-access:
                description:
                    - Enable/disable link down access traffic.
                choices:
                    - enable
                    - disable
            lldp-transmission:
                description:
                    - Enable/disable Link Layer Discovery Protocol (LLDP) for this VDOM or apply global settings to this VDOM.
                choices:
                    - enable
                    - disable
                    - global
            mac-ttl:
                description:
                    - Duration of MAC addresses in Transparent mode (300 - 8640000 sec, default = 300).
            manageip:
                description:
                    - Transparent mode IPv4 management IP address and netmask.
            manageip6:
                description:
                    - Transparent mode IPv6 management IP address and netmask.
            multicast-forward:
                description:
                    - Enable/disable multicast forwarding.
                choices:
                    - enable
                    - disable
            multicast-skip-policy:
                description:
                    - Enable/disable allowing multicast traffic through the FortiGate without a policy check.
                choices:
                    - enable
                    - disable
            multicast-ttl-notchange:
                description:
                    - Enable/disable preventing the FortiGate from changing the TTL for forwarded multicast packets.
                choices:
                    - enable
                    - disable
            ngfw-mode:
                description:
                    - Next Generation Firewall (NGFW) mode.
                choices:
                    - profile-based
                    - policy-based
            opmode:
                description:
                    - Firewall operation mode (NAT or Transparent).
                choices:
                    - nat
                    - transparent
            prp-trailer-action:
                description:
                    - Enable/disable action to take on PRP trailer.
                choices:
                    - enable
                    - disable
            sccp-port:
                description:
                    - TCP port the SCCP proxy monitors for SCCP traffic (0 - 65535, default = 2000).
            ses-denied-traffic:
                description:
                    - Enable/disable including denied session in the session table.
                choices:
                    - enable
                    - disable
            sip-helper:
                description:
                    - Enable/disable the SIP session helper to process SIP sessions unless SIP sessions are accepted by the SIP application layer gateway
                       (ALG).
                choices:
                    - enable
                    - disable
            sip-nat-trace:
                description:
                    - Enable/disable recording the original SIP source IP address when NAT is used.
                choices:
                    - enable
                    - disable
            sip-ssl-port:
                description:
                    - TCP port the SIP proxy monitors for SIP SSL/TLS traffic (0 - 65535, default = 5061).
            sip-tcp-port:
                description:
                    - TCP port the SIP proxy monitors for SIP traffic (0 - 65535, default = 5060).
            sip-udp-port:
                description:
                    - UDP port the SIP proxy monitors for SIP traffic (0 - 65535, default = 5060).
            snat-hairpin-traffic:
                description:
                    - Enable/disable source NAT (SNAT) for hairpin traffic.
                choices:
                    - enable
                    - disable
            ssl-ssh-profile:
                description:
                    - Profile for SSL/SSH inspection. Source firewall.ssl-ssh-profile.name.
            status:
                description:
                    - Enable/disable this VDOM.
                choices:
                    - enable
                    - disable
            strict-src-check:
                description:
                    - Enable/disable strict source verification.
                choices:
                    - enable
                    - disable
            tcp-session-without-syn:
                description:
                    - Enable/disable allowing TCP session without SYN flags.
                choices:
                    - enable
                    - disable
            utf8-spam-tagging:
                description:
                    - Enable/disable converting antispam tags to UTF-8 for better non-ASCII character support.
                choices:
                    - enable
                    - disable
            v4-ecmp-mode:
                description:
                    - IPv4 Equal-cost multi-path (ECMP) routing and load balancing mode.
                choices:
                    - source-ip-based
                    - weight-based
                    - usage-based
                    - source-dest-ip-based
            vpn-stats-log:
                description:
                    - Enable/disable periodic VPN log statistics for one or more types of VPN. Separate names with a space.
                choices:
                    - ipsec
                    - pptp
                    - l2tp
                    - ssl
            vpn-stats-period:
                description:
                    - Period to send VPN log statistics (60 - 86400 sec).
            wccp-cache-engine:
                description:
                    - Enable/disable WCCP cache engine.
                choices:
                    - enable
                    - disable
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure VDOM settings.
    fortios_system_settings:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      system_settings:
        allow-subnet-overlap: "enable"
        asymroute: "enable"
        asymroute-icmp: "enable"
        asymroute6: "enable"
        asymroute6-icmp: "enable"
        bfd: "enable"
        bfd-desired-min-tx: "9"
        bfd-detect-mult: "10"
        bfd-dont-enforce-src-port: "enable"
        bfd-required-min-rx: "12"
        block-land-attack: "disable"
        central-nat: "enable"
        comments: "<your_own_value>"
        compliance-check: "enable"
        default-voip-alg-mode: "proxy-based"
        deny-tcp-with-icmp: "enable"
        device: "<your_own_value> (source system.interface.name)"
        dhcp-proxy: "enable"
        dhcp-server-ip: "<your_own_value>"
        dhcp6-server-ip: "<your_own_value>"
        discovered-device-timeout: "23"
        ecmp-max-paths: "24"
        email-portal-check-dns: "disable"
        firewall-session-dirty: "check-all"
        fw-session-hairpin: "enable"
        gateway: "<your_own_value>"
        gateway6: "<your_own_value>"
        gui-advanced-policy: "enable"
        gui-allow-unnamed-policy: "enable"
        gui-antivirus: "enable"
        gui-ap-profile: "enable"
        gui-application-control: "enable"
        gui-default-policy-columns:
         -
            name: "default_name_36"
        gui-dhcp-advanced: "enable"
        gui-dlp: "enable"
        gui-dns-database: "enable"
        gui-dnsfilter: "enable"
        gui-domain-ip-reputation: "enable"
        gui-dos-policy: "enable"
        gui-dynamic-profile-display: "enable"
        gui-dynamic-routing: "enable"
        gui-email-collection: "enable"
        gui-endpoint-control: "enable"
        gui-endpoint-control-advanced: "enable"
        gui-explicit-proxy: "enable"
        gui-fortiap-split-tunneling: "enable"
        gui-fortiextender-controller: "enable"
        gui-icap: "enable"
        gui-implicit-policy: "enable"
        gui-ips: "enable"
        gui-load-balance: "enable"
        gui-local-in-policy: "enable"
        gui-local-reports: "enable"
        gui-multicast-policy: "enable"
        gui-multiple-interface-policy: "enable"
        gui-multiple-utm-profiles: "enable"
        gui-nat46-64: "enable"
        gui-object-colors: "enable"
        gui-policy-based-ipsec: "enable"
        gui-policy-learning: "enable"
        gui-replacement-message-groups: "enable"
        gui-spamfilter: "enable"
        gui-sslvpn-personal-bookmarks: "enable"
        gui-sslvpn-realms: "enable"
        gui-switch-controller: "enable"
        gui-threat-weight: "enable"
        gui-traffic-shaping: "enable"
        gui-voip-profile: "enable"
        gui-vpn: "enable"
        gui-waf-profile: "enable"
        gui-wan-load-balancing: "enable"
        gui-wanopt-cache: "enable"
        gui-webfilter: "enable"
        gui-webfilter-advanced: "enable"
        gui-wireless-controller: "enable"
        http-external-dest: "fortiweb"
        ike-dn-format: "with-space"
        ike-quick-crash-detect: "enable"
        ike-session-resume: "enable"
        implicit-allow-dns: "enable"
        inspection-mode: "proxy"
        ip: "<your_own_value>"
        ip6: "<your_own_value>"
        link-down-access: "enable"
        lldp-transmission: "enable"
        mac-ttl: "89"
        manageip: "<your_own_value>"
        manageip6: "<your_own_value>"
        multicast-forward: "enable"
        multicast-skip-policy: "enable"
        multicast-ttl-notchange: "enable"
        ngfw-mode: "profile-based"
        opmode: "nat"
        prp-trailer-action: "enable"
        sccp-port: "98"
        ses-denied-traffic: "enable"
        sip-helper: "enable"
        sip-nat-trace: "enable"
        sip-ssl-port: "102"
        sip-tcp-port: "103"
        sip-udp-port: "104"
        snat-hairpin-traffic: "enable"
        ssl-ssh-profile: "<your_own_value> (source firewall.ssl-ssh-profile.name)"
        status: "enable"
        strict-src-check: "enable"
        tcp-session-without-syn: "enable"
        utf8-spam-tagging: "enable"
        v4-ecmp-mode: "source-ip-based"
        vpn-stats-log: "ipsec"
        vpn-stats-period: "113"
        wccp-cache-engine: "enable"
'''

RETURN = '''
build:
  description: Build number of the fortigate image
  returned: always
  type: str
  sample: '1547'
http_method:
  description: Last method used to provision the content into FortiGate
  returned: always
  type: str
  sample: 'PUT'
http_status:
  description: Last result given by FortiGate on last operation applied
  returned: always
  type: str
  sample: "200"
mkey:
  description: Master key (id) used in the last call to FortiGate
  returned: success
  type: str
  sample: "id"
name:
  description: Name of the table used to fulfill the request
  returned: always
  type: str
  sample: "urlfilter"
path:
  description: Path of the table used to fulfill the request
  returned: always
  type: str
  sample: "webfilter"
revision:
  description: Internal revision number
  returned: always
  type: str
  sample: "17.0.2.10658"
serial:
  description: Serial number of the unit
  returned: always
  type: str
  sample: "FGVMEVYYQT3AB5352"
status:
  description: Indication of the operation's result
  returned: always
  type: str
  sample: "success"
vdom:
  description: Virtual domain used
  returned: always
  type: str
  sample: "root"
version:
  description: Version of the FortiGate
  returned: always
  type: str
  sample: "v5.6.3"

'''

from ansible.module_utils.basic import AnsibleModule

fos = None


def login(data):
    host = data['host']
    username = data['username']
    password = data['password']

    fos.debug('on')
    if 'https' in data and not data['https']:
        fos.https('off')
    else:
        fos.https('on')

    fos.login(host, username, password)


def filter_system_settings_data(json):
    option_list = ['allow-subnet-overlap', 'asymroute', 'asymroute-icmp',
                   'asymroute6', 'asymroute6-icmp', 'bfd',
                   'bfd-desired-min-tx', 'bfd-detect-mult', 'bfd-dont-enforce-src-port',
                   'bfd-required-min-rx', 'block-land-attack', 'central-nat',
                   'comments', 'compliance-check', 'default-voip-alg-mode',
                   'deny-tcp-with-icmp', 'device', 'dhcp-proxy',
                   'dhcp-server-ip', 'dhcp6-server-ip', 'discovered-device-timeout',
                   'ecmp-max-paths', 'email-portal-check-dns', 'firewall-session-dirty',
                   'fw-session-hairpin', 'gateway', 'gateway6',
                   'gui-advanced-policy', 'gui-allow-unnamed-policy', 'gui-antivirus',
                   'gui-ap-profile', 'gui-application-control', 'gui-default-policy-columns',
                   'gui-dhcp-advanced', 'gui-dlp', 'gui-dns-database',
                   'gui-dnsfilter', 'gui-domain-ip-reputation', 'gui-dos-policy',
                   'gui-dynamic-profile-display', 'gui-dynamic-routing', 'gui-email-collection',
                   'gui-endpoint-control', 'gui-endpoint-control-advanced', 'gui-explicit-proxy',
                   'gui-fortiap-split-tunneling', 'gui-fortiextender-controller', 'gui-icap',
                   'gui-implicit-policy', 'gui-ips', 'gui-load-balance',
                   'gui-local-in-policy', 'gui-local-reports', 'gui-multicast-policy',
                   'gui-multiple-interface-policy', 'gui-multiple-utm-profiles', 'gui-nat46-64',
                   'gui-object-colors', 'gui-policy-based-ipsec', 'gui-policy-learning',
                   'gui-replacement-message-groups', 'gui-spamfilter', 'gui-sslvpn-personal-bookmarks',
                   'gui-sslvpn-realms', 'gui-switch-controller', 'gui-threat-weight',
                   'gui-traffic-shaping', 'gui-voip-profile', 'gui-vpn',
                   'gui-waf-profile', 'gui-wan-load-balancing', 'gui-wanopt-cache',
                   'gui-webfilter', 'gui-webfilter-advanced', 'gui-wireless-controller',
                   'http-external-dest', 'ike-dn-format', 'ike-quick-crash-detect',
                   'ike-session-resume', 'implicit-allow-dns', 'inspection-mode',
                   'ip', 'ip6', 'link-down-access',
                   'lldp-transmission', 'mac-ttl', 'manageip',
                   'manageip6', 'multicast-forward', 'multicast-skip-policy',
                   'multicast-ttl-notchange', 'ngfw-mode', 'opmode',
                   'prp-trailer-action', 'sccp-port', 'ses-denied-traffic',
                   'sip-helper', 'sip-nat-trace', 'sip-ssl-port',
                   'sip-tcp-port', 'sip-udp-port', 'snat-hairpin-traffic',
                   'ssl-ssh-profile', 'status', 'strict-src-check',
                   'tcp-session-without-syn', 'utf8-spam-tagging', 'v4-ecmp-mode',
                   'vpn-stats-log', 'vpn-stats-period', 'wccp-cache-engine']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def system_settings(data, fos):
    vdom = data['vdom']
    system_settings_data = data['system_settings']
    filtered_data = filter_system_settings_data(system_settings_data)
    return fos.set('system',
                   'settings',
                   data=filtered_data,
                   vdom=vdom)


def fortios_system(data, fos):
    login(data)

    methodlist = ['system_settings']
    for method in methodlist:
        if data[method]:
            resp = eval(method)(data, fos)
            break

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "system_settings": {
            "required": False, "type": "dict",
            "options": {
                "allow-subnet-overlap": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "asymroute": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "asymroute-icmp": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "asymroute6": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "asymroute6-icmp": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "bfd": {"required": False, "type": "str",
                        "choices": ["enable", "disable"]},
                "bfd-desired-min-tx": {"required": False, "type": "int"},
                "bfd-detect-mult": {"required": False, "type": "int"},
                "bfd-dont-enforce-src-port": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                "bfd-required-min-rx": {"required": False, "type": "int"},
                "block-land-attack": {"required": False, "type": "str",
                                      "choices": ["disable", "enable"]},
                "central-nat": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "comments": {"required": False, "type": "str"},
                "compliance-check": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "default-voip-alg-mode": {"required": False, "type": "str",
                                          "choices": ["proxy-based", "kernel-helper-based"]},
                "deny-tcp-with-icmp": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "device": {"required": False, "type": "str"},
                "dhcp-proxy": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "dhcp-server-ip": {"required": False, "type": "str"},
                "dhcp6-server-ip": {"required": False, "type": "str"},
                "discovered-device-timeout": {"required": False, "type": "int"},
                "ecmp-max-paths": {"required": False, "type": "int"},
                "email-portal-check-dns": {"required": False, "type": "str",
                                           "choices": ["disable", "enable"]},
                "firewall-session-dirty": {"required": False, "type": "str",
                                           "choices": ["check-all", "check-new", "check-policy-option"]},
                "fw-session-hairpin": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "gateway": {"required": False, "type": "str"},
                "gateway6": {"required": False, "type": "str"},
                "gui-advanced-policy": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "gui-allow-unnamed-policy": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                "gui-antivirus": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "gui-ap-profile": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "gui-application-control": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                "gui-default-policy-columns": {"required": False, "type": "list",
                                               "options": {
                                                   "name": {"required": True, "type": "str"}
                                               }},
                "gui-dhcp-advanced": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "gui-dlp": {"required": False, "type": "str",
                            "choices": ["enable", "disable"]},
                "gui-dns-database": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "gui-dnsfilter": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "gui-domain-ip-reputation": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                "gui-dos-policy": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "gui-dynamic-profile-display": {"required": False, "type": "str",
                                                "choices": ["enable", "disable"]},
                "gui-dynamic-routing": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "gui-email-collection": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "gui-endpoint-control": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "gui-endpoint-control-advanced": {"required": False, "type": "str",
                                                  "choices": ["enable", "disable"]},
                "gui-explicit-proxy": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "gui-fortiap-split-tunneling": {"required": False, "type": "str",
                                                "choices": ["enable", "disable"]},
                "gui-fortiextender-controller": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]},
                "gui-icap": {"required": False, "type": "str",
                             "choices": ["enable", "disable"]},
                "gui-implicit-policy": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "gui-ips": {"required": False, "type": "str",
                            "choices": ["enable", "disable"]},
                "gui-load-balance": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "gui-local-in-policy": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "gui-local-reports": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "gui-multicast-policy": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "gui-multiple-interface-policy": {"required": False, "type": "str",
                                                  "choices": ["enable", "disable"]},
                "gui-multiple-utm-profiles": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                "gui-nat46-64": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "gui-object-colors": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "gui-policy-based-ipsec": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "gui-policy-learning": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "gui-replacement-message-groups": {"required": False, "type": "str",
                                                   "choices": ["enable", "disable"]},
                "gui-spamfilter": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "gui-sslvpn-personal-bookmarks": {"required": False, "type": "str",
                                                  "choices": ["enable", "disable"]},
                "gui-sslvpn-realms": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "gui-switch-controller": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "gui-threat-weight": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "gui-traffic-shaping": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "gui-voip-profile": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "gui-vpn": {"required": False, "type": "str",
                            "choices": ["enable", "disable"]},
                "gui-waf-profile": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "gui-wan-load-balancing": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "gui-wanopt-cache": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "gui-webfilter": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "gui-webfilter-advanced": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "gui-wireless-controller": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                "http-external-dest": {"required": False, "type": "str",
                                       "choices": ["fortiweb", "forticache"]},
                "ike-dn-format": {"required": False, "type": "str",
                                  "choices": ["with-space", "no-space"]},
                "ike-quick-crash-detect": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "ike-session-resume": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "implicit-allow-dns": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "inspection-mode": {"required": False, "type": "str",
                                    "choices": ["proxy", "flow"]},
                "ip": {"required": False, "type": "str"},
                "ip6": {"required": False, "type": "str"},
                "link-down-access": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "lldp-transmission": {"required": False, "type": "str",
                                      "choices": ["enable", "disable", "global"]},
                "mac-ttl": {"required": False, "type": "int"},
                "manageip": {"required": False, "type": "str"},
                "manageip6": {"required": False, "type": "str"},
                "multicast-forward": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "multicast-skip-policy": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "multicast-ttl-notchange": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                "ngfw-mode": {"required": False, "type": "str",
                              "choices": ["profile-based", "policy-based"]},
                "opmode": {"required": False, "type": "str",
                           "choices": ["nat", "transparent"]},
                "prp-trailer-action": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "sccp-port": {"required": False, "type": "int"},
                "ses-denied-traffic": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "sip-helper": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "sip-nat-trace": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "sip-ssl-port": {"required": False, "type": "int"},
                "sip-tcp-port": {"required": False, "type": "int"},
                "sip-udp-port": {"required": False, "type": "int"},
                "snat-hairpin-traffic": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "ssl-ssh-profile": {"required": False, "type": "str"},
                "status": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "strict-src-check": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "tcp-session-without-syn": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                "utf8-spam-tagging": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "v4-ecmp-mode": {"required": False, "type": "str",
                                 "choices": ["source-ip-based", "weight-based", "usage-based",
                                             "source-dest-ip-based"]},
                "vpn-stats-log": {"required": False, "type": "str",
                                  "choices": ["ipsec", "pptp", "l2tp",
                                              "ssl"]},
                "vpn-stats-period": {"required": False, "type": "int"},
                "wccp-cache-engine": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]}

            }
        }
    }

    module = AnsibleModule(argument_spec=fields,
                           supports_check_mode=False)
    try:
        from fortiosapi import FortiOSAPI
    except ImportError:
        module.fail_json(msg="fortiosapi module is required")

    global fos
    fos = FortiOSAPI()

    is_error, has_changed, result = fortios_system(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
