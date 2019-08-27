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

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fortios_system_settings
short_description: Configure VDOM settings in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify system feature and settings category.
      Examples include all parameters and values need to be adjusted to datasources before usage.
      Tested with FOS v6.0.5
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
            - FortiOS or FortiGate IP address.
        type: str
        required: false
    username:
        description:
            - FortiOS or FortiGate username.
        type: str
        required: false
    password:
        description:
            - FortiOS or FortiGate password.
        type: str
        default: ""
    vdom:
        description:
            - Virtual domain, among those defined previously. A vdom is a
              virtual instance of the FortiGate that can be configured and
              used as a different unit.
        type: str
        default: root
    https:
        description:
            - Indicates if the requests towards FortiGate must use HTTPS protocol.
        type: bool
        default: true
    ssl_verify:
        description:
            - Ensures FortiGate certificate must be verified by a proper CA.
        type: bool
        default: true
        version_added: 2.9
    system_settings:
        description:
            - Configure VDOM settings.
        default: null
        type: dict
        suboptions:
            allow_linkdown_path:
                description:
                    - Enable/disable link down path.
                type: str
                choices:
                    - enable
                    - disable
            allow_subnet_overlap:
                description:
                    - Enable/disable allowing interface subnets to use overlapping IP addresses.
                type: str
                choices:
                    - enable
                    - disable
            asymroute:
                description:
                    - Enable/disable IPv4 asymmetric routing.
                type: str
                choices:
                    - enable
                    - disable
            asymroute_icmp:
                description:
                    - Enable/disable ICMP asymmetric routing.
                type: str
                choices:
                    - enable
                    - disable
            asymroute6:
                description:
                    - Enable/disable asymmetric IPv6 routing.
                type: str
                choices:
                    - enable
                    - disable
            asymroute6_icmp:
                description:
                    - Enable/disable asymmetric ICMPv6 routing.
                type: str
                choices:
                    - enable
                    - disable
            bfd:
                description:
                    - Enable/disable Bi-directional Forwarding Detection (BFD) on all interfaces.
                type: str
                choices:
                    - enable
                    - disable
            bfd_desired_min_tx:
                description:
                    - BFD desired minimal transmit interval (1 - 100000 ms).
                type: int
            bfd_detect_mult:
                description:
                    - BFD detection multiplier (1 - 50).
                type: int
            bfd_dont_enforce_src_port:
                description:
                    - Enable to not enforce verifying the source port of BFD Packets.
                type: str
                choices:
                    - enable
                    - disable
            bfd_required_min_rx:
                description:
                    - BFD required minimal receive interval (1 - 100000 ms).
                type: int
            block_land_attack:
                description:
                    - Enable/disable blocking of land attacks.
                type: str
                choices:
                    - disable
                    - enable
            central_nat:
                description:
                    - Enable/disable central NAT.
                type: str
                choices:
                    - enable
                    - disable
            comments:
                description:
                    - VDOM comments.
                type: str
            compliance_check:
                description:
                    - Enable/disable PCI DSS compliance checking.
                type: str
                choices:
                    - enable
                    - disable
            default_voip_alg_mode:
                description:
                    - Configure how the FortiGate handles VoIP traffic when a policy that accepts the traffic doesn't include a VoIP profile.
                type: str
                choices:
                    - proxy-based
                    - kernel-helper-based
            deny_tcp_with_icmp:
                description:
                    - Enable/disable denying TCP by sending an ICMP communication prohibited packet.
                type: str
                choices:
                    - enable
                    - disable
            device:
                description:
                    - Interface to use for management access for NAT mode. Source system.interface.name.
                type: str
            dhcp_proxy:
                description:
                    - Enable/disable the DHCP Proxy.
                type: str
                choices:
                    - enable
                    - disable
            dhcp_server_ip:
                description:
                    - DHCP Server IPv4 address.
                type: str
            dhcp6_server_ip:
                description:
                    - DHCPv6 server IPv6 address.
                type: str
            discovered_device_timeout:
                description:
                    - Timeout for discovered devices (1 - 365 days).
                type: int
            ecmp_max_paths:
                description:
                    - Maximum number of Equal Cost Multi-Path (ECMP) next-hops. Set to 1 to disable ECMP routing (1 - 100).
                type: int
            email_portal_check_dns:
                description:
                    - Enable/disable using DNS to validate email addresses collected by a captive portal.
                type: str
                choices:
                    - disable
                    - enable
            firewall_session_dirty:
                description:
                    - Select how to manage sessions affected by firewall policy configuration changes.
                type: str
                choices:
                    - check-all
                    - check-new
                    - check-policy-option
            fw_session_hairpin:
                description:
                    - Enable/disable checking for a matching policy each time hairpin traffic goes through the FortiGate.
                type: str
                choices:
                    - enable
                    - disable
            gateway:
                description:
                    - Transparent mode IPv4 default gateway IP address.
                type: str
            gateway6:
                description:
                    - Transparent mode IPv4 default gateway IP address.
                type: str
            gui_advanced_policy:
                description:
                    - Enable/disable advanced policy configuration on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_allow_unnamed_policy:
                description:
                    - Enable/disable the requirement for policy naming on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_antivirus:
                description:
                    - Enable/disable AntiVirus on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_ap_profile:
                description:
                    - Enable/disable FortiAP profiles on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_application_control:
                description:
                    - Enable/disable application control on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_default_policy_columns:
                description:
                    - Default columns to display for policy lists on GUI.
                type: list
                suboptions:
                    name:
                        description:
                            - Select column name.
                        required: true
                        type: str
            gui_dhcp_advanced:
                description:
                    - Enable/disable advanced DHCP options on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_dlp:
                description:
                    - Enable/disable DLP on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_dns_database:
                description:
                    - Enable/disable DNS database settings on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_dnsfilter:
                description:
                    - Enable/disable DNS Filtering on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_domain_ip_reputation:
                description:
                    - Enable/disable Domain and IP Reputation on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_dos_policy:
                description:
                    - Enable/disable DoS policies on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_dynamic_profile_display:
                description:
                    - Enable/disable RADIUS Single Sign On (RSSO) on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_dynamic_routing:
                description:
                    - Enable/disable dynamic routing on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_email_collection:
                description:
                    - Enable/disable email collection on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_endpoint_control:
                description:
                    - Enable/disable endpoint control on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_endpoint_control_advanced:
                description:
                    - Enable/disable advanced endpoint control options on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_explicit_proxy:
                description:
                    - Enable/disable the explicit proxy on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_fortiap_split_tunneling:
                description:
                    - Enable/disable FortiAP split tunneling on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_fortiextender_controller:
                description:
                    - Enable/disable FortiExtender on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_icap:
                description:
                    - Enable/disable ICAP on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_implicit_policy:
                description:
                    - Enable/disable implicit firewall policies on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_ips:
                description:
                    - Enable/disable IPS on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_load_balance:
                description:
                    - Enable/disable server load balancing on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_local_in_policy:
                description:
                    - Enable/disable Local-In policies on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_local_reports:
                description:
                    - Enable/disable local reports on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_multicast_policy:
                description:
                    - Enable/disable multicast firewall policies on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_multiple_interface_policy:
                description:
                    - Enable/disable adding multiple interfaces to a policy on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_multiple_utm_profiles:
                description:
                    - Enable/disable multiple UTM profiles on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_nat46_64:
                description:
                    - Enable/disable NAT46 and NAT64 settings on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_object_colors:
                description:
                    - Enable/disable object colors on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_policy_based_ipsec:
                description:
                    - Enable/disable policy-based IPsec VPN on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_policy_learning:
                description:
                    - Enable/disable firewall policy learning mode on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_replacement_message_groups:
                description:
                    - Enable/disable replacement message groups on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_spamfilter:
                description:
                    - Enable/disable Antispam on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_sslvpn_personal_bookmarks:
                description:
                    - Enable/disable SSL-VPN personal bookmark management on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_sslvpn_realms:
                description:
                    - Enable/disable SSL-VPN realms on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_switch_controller:
                description:
                    - Enable/disable the switch controller on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_threat_weight:
                description:
                    - Enable/disable threat weight on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_traffic_shaping:
                description:
                    - Enable/disable traffic shaping on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_voip_profile:
                description:
                    - Enable/disable VoIP profiles on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_vpn:
                description:
                    - Enable/disable VPN tunnels on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_waf_profile:
                description:
                    - Enable/disable Web Application Firewall on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_wan_load_balancing:
                description:
                    - Enable/disable SD-WAN on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_wanopt_cache:
                description:
                    - Enable/disable WAN Optimization and Web Caching on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_webfilter:
                description:
                    - Enable/disable Web filtering on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_webfilter_advanced:
                description:
                    - Enable/disable advanced web filtering on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            gui_wireless_controller:
                description:
                    - Enable/disable the wireless controller on the GUI.
                type: str
                choices:
                    - enable
                    - disable
            http_external_dest:
                description:
                    - Offload HTTP traffic to FortiWeb or FortiCache.
                type: str
                choices:
                    - fortiweb
                    - forticache
            ike_dn_format:
                description:
                    - Configure IKE ASN.1 Distinguished Name format conventions.
                type: str
                choices:
                    - with-space
                    - no-space
            ike_quick_crash_detect:
                description:
                    - Enable/disable IKE quick crash detection (RFC 6290).
                type: str
                choices:
                    - enable
                    - disable
            ike_session_resume:
                description:
                    - Enable/disable IKEv2 session resumption (RFC 5723).
                type: str
                choices:
                    - enable
                    - disable
            implicit_allow_dns:
                description:
                    - Enable/disable implicitly allowing DNS traffic.
                type: str
                choices:
                    - enable
                    - disable
            inspection_mode:
                description:
                    - Inspection mode (proxy-based or flow-based).
                type: str
                choices:
                    - proxy
                    - flow
            ip:
                description:
                    - IP address and netmask.
                type: str
            ip6:
                description:
                    - IPv6 address prefix for NAT mode.
                type: str
            link_down_access:
                description:
                    - Enable/disable link down access traffic.
                type: str
                choices:
                    - enable
                    - disable
            lldp_transmission:
                description:
                    - Enable/disable Link Layer Discovery Protocol (LLDP) for this VDOM or apply global settings to this VDOM.
                type: str
                choices:
                    - enable
                    - disable
                    - global
            mac_ttl:
                description:
                    - Duration of MAC addresses in Transparent mode (300 - 8640000 sec).
                type: int
            manageip:
                description:
                    - Transparent mode IPv4 management IP address and netmask.
                type: str
            manageip6:
                description:
                    - Transparent mode IPv6 management IP address and netmask.
                type: str
            multicast_forward:
                description:
                    - Enable/disable multicast forwarding.
                type: str
                choices:
                    - enable
                    - disable
            multicast_skip_policy:
                description:
                    - Enable/disable allowing multicast traffic through the FortiGate without a policy check.
                type: str
                choices:
                    - enable
                    - disable
            multicast_ttl_notchange:
                description:
                    - Enable/disable preventing the FortiGate from changing the TTL for forwarded multicast packets.
                type: str
                choices:
                    - enable
                    - disable
            ngfw_mode:
                description:
                    - Next Generation Firewall (NGFW) mode.
                type: str
                choices:
                    - profile-based
                    - policy-based
            opmode:
                description:
                    - Firewall operation mode (NAT or Transparent).
                type: str
                choices:
                    - nat
                    - transparent
            prp_trailer_action:
                description:
                    - Enable/disable action to take on PRP trailer.
                type: str
                choices:
                    - enable
                    - disable
            sccp_port:
                description:
                    - TCP port the SCCP proxy monitors for SCCP traffic (0 - 65535).
                type: int
            ses_denied_traffic:
                description:
                    - Enable/disable including denied session in the session table.
                type: str
                choices:
                    - enable
                    - disable
            sip_helper:
                description:
                    - Enable/disable the SIP session helper to process SIP sessions unless SIP sessions are accepted by the SIP application layer gateway
                       (ALG).
                type: str
                choices:
                    - enable
                    - disable
            sip_nat_trace:
                description:
                    - Enable/disable recording the original SIP source IP address when NAT is used.
                type: str
                choices:
                    - enable
                    - disable
            sip_ssl_port:
                description:
                    - TCP port the SIP proxy monitors for SIP SSL/TLS traffic (0 - 65535).
                type: int
            sip_tcp_port:
                description:
                    - TCP port the SIP proxy monitors for SIP traffic (0 - 65535).
                type: int
            sip_udp_port:
                description:
                    - UDP port the SIP proxy monitors for SIP traffic (0 - 65535).
                type: int
            snat_hairpin_traffic:
                description:
                    - Enable/disable source NAT (SNAT) for hairpin traffic.
                type: str
                choices:
                    - enable
                    - disable
            ssl_ssh_profile:
                description:
                    - Profile for SSL/SSH inspection. Source firewall.ssl-ssh-profile.name.
                type: str
            status:
                description:
                    - Enable/disable this VDOM.
                type: str
                choices:
                    - enable
                    - disable
            strict_src_check:
                description:
                    - Enable/disable strict source verification.
                type: str
                choices:
                    - enable
                    - disable
            tcp_session_without_syn:
                description:
                    - Enable/disable allowing TCP session without SYN flags.
                type: str
                choices:
                    - enable
                    - disable
            utf8_spam_tagging:
                description:
                    - Enable/disable converting antispam tags to UTF-8 for better non-ASCII character support.
                type: str
                choices:
                    - enable
                    - disable
            v4_ecmp_mode:
                description:
                    - IPv4 Equal-cost multi-path (ECMP) routing and load balancing mode.
                type: str
                choices:
                    - source-ip-based
                    - weight-based
                    - usage-based
                    - source-dest-ip-based
            vpn_stats_log:
                description:
                    - Enable/disable periodic VPN log statistics for one or more types of VPN. Separate names with a space.
                type: str
                choices:
                    - ipsec
                    - pptp
                    - l2tp
                    - ssl
            vpn_stats_period:
                description:
                    - Period to send VPN log statistics (60 - 86400 sec).
                type: int
            wccp_cache_engine:
                description:
                    - Enable/disable WCCP cache engine.
                type: str
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
   ssl_verify: "False"
  tasks:
  - name: Configure VDOM settings.
    fortios_system_settings:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      system_settings:
        allow_linkdown_path: "enable"
        allow_subnet_overlap: "enable"
        asymroute: "enable"
        asymroute_icmp: "enable"
        asymroute6: "enable"
        asymroute6_icmp: "enable"
        bfd: "enable"
        bfd_desired_min_tx: "10"
        bfd_detect_mult: "11"
        bfd_dont_enforce_src_port: "enable"
        bfd_required_min_rx: "13"
        block_land_attack: "disable"
        central_nat: "enable"
        comments: "<your_own_value>"
        compliance_check: "enable"
        default_voip_alg_mode: "proxy-based"
        deny_tcp_with_icmp: "enable"
        device: "<your_own_value> (source system.interface.name)"
        dhcp_proxy: "enable"
        dhcp_server_ip: "<your_own_value>"
        dhcp6_server_ip: "<your_own_value>"
        discovered_device_timeout: "24"
        ecmp_max_paths: "25"
        email_portal_check_dns: "disable"
        firewall_session_dirty: "check-all"
        fw_session_hairpin: "enable"
        gateway: "<your_own_value>"
        gateway6: "<your_own_value>"
        gui_advanced_policy: "enable"
        gui_allow_unnamed_policy: "enable"
        gui_antivirus: "enable"
        gui_ap_profile: "enable"
        gui_application_control: "enable"
        gui_default_policy_columns:
         -
            name: "default_name_37"
        gui_dhcp_advanced: "enable"
        gui_dlp: "enable"
        gui_dns_database: "enable"
        gui_dnsfilter: "enable"
        gui_domain_ip_reputation: "enable"
        gui_dos_policy: "enable"
        gui_dynamic_profile_display: "enable"
        gui_dynamic_routing: "enable"
        gui_email_collection: "enable"
        gui_endpoint_control: "enable"
        gui_endpoint_control_advanced: "enable"
        gui_explicit_proxy: "enable"
        gui_fortiap_split_tunneling: "enable"
        gui_fortiextender_controller: "enable"
        gui_icap: "enable"
        gui_implicit_policy: "enable"
        gui_ips: "enable"
        gui_load_balance: "enable"
        gui_local_in_policy: "enable"
        gui_local_reports: "enable"
        gui_multicast_policy: "enable"
        gui_multiple_interface_policy: "enable"
        gui_multiple_utm_profiles: "enable"
        gui_nat46_64: "enable"
        gui_object_colors: "enable"
        gui_policy_based_ipsec: "enable"
        gui_policy_learning: "enable"
        gui_replacement_message_groups: "enable"
        gui_spamfilter: "enable"
        gui_sslvpn_personal_bookmarks: "enable"
        gui_sslvpn_realms: "enable"
        gui_switch_controller: "enable"
        gui_threat_weight: "enable"
        gui_traffic_shaping: "enable"
        gui_voip_profile: "enable"
        gui_vpn: "enable"
        gui_waf_profile: "enable"
        gui_wan_load_balancing: "enable"
        gui_wanopt_cache: "enable"
        gui_webfilter: "enable"
        gui_webfilter_advanced: "enable"
        gui_wireless_controller: "enable"
        http_external_dest: "fortiweb"
        ike_dn_format: "with-space"
        ike_quick_crash_detect: "enable"
        ike_session_resume: "enable"
        implicit_allow_dns: "enable"
        inspection_mode: "proxy"
        ip: "<your_own_value>"
        ip6: "<your_own_value>"
        link_down_access: "enable"
        lldp_transmission: "enable"
        mac_ttl: "90"
        manageip: "<your_own_value>"
        manageip6: "<your_own_value>"
        multicast_forward: "enable"
        multicast_skip_policy: "enable"
        multicast_ttl_notchange: "enable"
        ngfw_mode: "profile-based"
        opmode: "nat"
        prp_trailer_action: "enable"
        sccp_port: "99"
        ses_denied_traffic: "enable"
        sip_helper: "enable"
        sip_nat_trace: "enable"
        sip_ssl_port: "103"
        sip_tcp_port: "104"
        sip_udp_port: "105"
        snat_hairpin_traffic: "enable"
        ssl_ssh_profile: "<your_own_value> (source firewall.ssl-ssh-profile.name)"
        status: "enable"
        strict_src_check: "enable"
        tcp_session_without_syn: "enable"
        utf8_spam_tagging: "enable"
        v4_ecmp_mode: "source-ip-based"
        vpn_stats_log: "ipsec"
        vpn_stats_period: "114"
        wccp_cache_engine: "enable"
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
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.fortios.fortios import FortiOSHandler
from ansible.module_utils.network.fortimanager.common import FAIL_SOCKET_MSG


def login(data, fos):
    host = data['host']
    username = data['username']
    password = data['password']
    ssl_verify = data['ssl_verify']

    fos.debug('on')
    if 'https' in data and not data['https']:
        fos.https('off')
    else:
        fos.https('on')

    fos.login(host, username, password, verify=ssl_verify)


def filter_system_settings_data(json):
    option_list = ['allow_linkdown_path', 'allow_subnet_overlap', 'asymroute',
                   'asymroute_icmp', 'asymroute6', 'asymroute6_icmp',
                   'bfd', 'bfd_desired_min_tx', 'bfd_detect_mult',
                   'bfd_dont_enforce_src_port', 'bfd_required_min_rx', 'block_land_attack',
                   'central_nat', 'comments', 'compliance_check',
                   'default_voip_alg_mode', 'deny_tcp_with_icmp', 'device',
                   'dhcp_proxy', 'dhcp_server_ip', 'dhcp6_server_ip',
                   'discovered_device_timeout', 'ecmp_max_paths', 'email_portal_check_dns',
                   'firewall_session_dirty', 'fw_session_hairpin', 'gateway',
                   'gateway6', 'gui_advanced_policy', 'gui_allow_unnamed_policy',
                   'gui_antivirus', 'gui_ap_profile', 'gui_application_control',
                   'gui_default_policy_columns', 'gui_dhcp_advanced', 'gui_dlp',
                   'gui_dns_database', 'gui_dnsfilter', 'gui_domain_ip_reputation',
                   'gui_dos_policy', 'gui_dynamic_profile_display', 'gui_dynamic_routing',
                   'gui_email_collection', 'gui_endpoint_control', 'gui_endpoint_control_advanced',
                   'gui_explicit_proxy', 'gui_fortiap_split_tunneling', 'gui_fortiextender_controller',
                   'gui_icap', 'gui_implicit_policy', 'gui_ips',
                   'gui_load_balance', 'gui_local_in_policy', 'gui_local_reports',
                   'gui_multicast_policy', 'gui_multiple_interface_policy', 'gui_multiple_utm_profiles',
                   'gui_nat46_64', 'gui_object_colors', 'gui_policy_based_ipsec',
                   'gui_policy_learning', 'gui_replacement_message_groups', 'gui_spamfilter',
                   'gui_sslvpn_personal_bookmarks', 'gui_sslvpn_realms', 'gui_switch_controller',
                   'gui_threat_weight', 'gui_traffic_shaping', 'gui_voip_profile',
                   'gui_vpn', 'gui_waf_profile', 'gui_wan_load_balancing',
                   'gui_wanopt_cache', 'gui_webfilter', 'gui_webfilter_advanced',
                   'gui_wireless_controller', 'http_external_dest', 'ike_dn_format',
                   'ike_quick_crash_detect', 'ike_session_resume', 'implicit_allow_dns',
                   'inspection_mode', 'ip', 'ip6',
                   'link_down_access', 'lldp_transmission', 'mac_ttl',
                   'manageip', 'manageip6', 'multicast_forward',
                   'multicast_skip_policy', 'multicast_ttl_notchange', 'ngfw_mode',
                   'opmode', 'prp_trailer_action', 'sccp_port',
                   'ses_denied_traffic', 'sip_helper', 'sip_nat_trace',
                   'sip_ssl_port', 'sip_tcp_port', 'sip_udp_port',
                   'snat_hairpin_traffic', 'ssl_ssh_profile', 'status',
                   'strict_src_check', 'tcp_session_without_syn', 'utf8_spam_tagging',
                   'v4_ecmp_mode', 'vpn_stats_log', 'vpn_stats_period',
                   'wccp_cache_engine']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def underscore_to_hyphen(data):
    if isinstance(data, list):
        for elem in data:
            elem = underscore_to_hyphen(elem)
    elif isinstance(data, dict):
        new_data = {}
        for k, v in data.items():
            new_data[k.replace('_', '-')] = underscore_to_hyphen(v)
        data = new_data

    return data


def system_settings(data, fos):
    vdom = data['vdom']
    system_settings_data = data['system_settings']
    filtered_data = underscore_to_hyphen(filter_system_settings_data(system_settings_data))

    return fos.set('system',
                   'settings',
                   data=filtered_data,
                   vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_system(data, fos):

    if data['system_settings']:
        resp = system_settings(data, fos)

    return not is_successful_status(resp), \
        resp['status'] == "success", \
        resp


def main():
    fields = {
        "host": {"required": False, "type": "str"},
        "username": {"required": False, "type": "str"},
        "password": {"required": False, "type": "str", "default": "", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "ssl_verify": {"required": False, "type": "bool", "default": True},
        "system_settings": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "allow_linkdown_path": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "allow_subnet_overlap": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "asymroute": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "asymroute_icmp": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "asymroute6": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "asymroute6_icmp": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "bfd": {"required": False, "type": "str",
                        "choices": ["enable", "disable"]},
                "bfd_desired_min_tx": {"required": False, "type": "int"},
                "bfd_detect_mult": {"required": False, "type": "int"},
                "bfd_dont_enforce_src_port": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                "bfd_required_min_rx": {"required": False, "type": "int"},
                "block_land_attack": {"required": False, "type": "str",
                                      "choices": ["disable", "enable"]},
                "central_nat": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "comments": {"required": False, "type": "str"},
                "compliance_check": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "default_voip_alg_mode": {"required": False, "type": "str",
                                          "choices": ["proxy-based", "kernel-helper-based"]},
                "deny_tcp_with_icmp": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "device": {"required": False, "type": "str"},
                "dhcp_proxy": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "dhcp_server_ip": {"required": False, "type": "str"},
                "dhcp6_server_ip": {"required": False, "type": "str"},
                "discovered_device_timeout": {"required": False, "type": "int"},
                "ecmp_max_paths": {"required": False, "type": "int"},
                "email_portal_check_dns": {"required": False, "type": "str",
                                           "choices": ["disable", "enable"]},
                "firewall_session_dirty": {"required": False, "type": "str",
                                           "choices": ["check-all", "check-new", "check-policy-option"]},
                "fw_session_hairpin": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "gateway": {"required": False, "type": "str"},
                "gateway6": {"required": False, "type": "str"},
                "gui_advanced_policy": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "gui_allow_unnamed_policy": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                "gui_antivirus": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "gui_ap_profile": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "gui_application_control": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                "gui_default_policy_columns": {"required": False, "type": "list",
                                               "options": {
                                                   "name": {"required": True, "type": "str"}
                                               }},
                "gui_dhcp_advanced": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "gui_dlp": {"required": False, "type": "str",
                            "choices": ["enable", "disable"]},
                "gui_dns_database": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "gui_dnsfilter": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "gui_domain_ip_reputation": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                "gui_dos_policy": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "gui_dynamic_profile_display": {"required": False, "type": "str",
                                                "choices": ["enable", "disable"]},
                "gui_dynamic_routing": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "gui_email_collection": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "gui_endpoint_control": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "gui_endpoint_control_advanced": {"required": False, "type": "str",
                                                  "choices": ["enable", "disable"]},
                "gui_explicit_proxy": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "gui_fortiap_split_tunneling": {"required": False, "type": "str",
                                                "choices": ["enable", "disable"]},
                "gui_fortiextender_controller": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]},
                "gui_icap": {"required": False, "type": "str",
                             "choices": ["enable", "disable"]},
                "gui_implicit_policy": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "gui_ips": {"required": False, "type": "str",
                            "choices": ["enable", "disable"]},
                "gui_load_balance": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "gui_local_in_policy": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "gui_local_reports": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "gui_multicast_policy": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "gui_multiple_interface_policy": {"required": False, "type": "str",
                                                  "choices": ["enable", "disable"]},
                "gui_multiple_utm_profiles": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                "gui_nat46_64": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "gui_object_colors": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "gui_policy_based_ipsec": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "gui_policy_learning": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "gui_replacement_message_groups": {"required": False, "type": "str",
                                                   "choices": ["enable", "disable"]},
                "gui_spamfilter": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "gui_sslvpn_personal_bookmarks": {"required": False, "type": "str",
                                                  "choices": ["enable", "disable"]},
                "gui_sslvpn_realms": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "gui_switch_controller": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "gui_threat_weight": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "gui_traffic_shaping": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "gui_voip_profile": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "gui_vpn": {"required": False, "type": "str",
                            "choices": ["enable", "disable"]},
                "gui_waf_profile": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "gui_wan_load_balancing": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "gui_wanopt_cache": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "gui_webfilter": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "gui_webfilter_advanced": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "gui_wireless_controller": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                "http_external_dest": {"required": False, "type": "str",
                                       "choices": ["fortiweb", "forticache"]},
                "ike_dn_format": {"required": False, "type": "str",
                                  "choices": ["with-space", "no-space"]},
                "ike_quick_crash_detect": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "ike_session_resume": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "implicit_allow_dns": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "inspection_mode": {"required": False, "type": "str",
                                    "choices": ["proxy", "flow"]},
                "ip": {"required": False, "type": "str"},
                "ip6": {"required": False, "type": "str"},
                "link_down_access": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "lldp_transmission": {"required": False, "type": "str",
                                      "choices": ["enable", "disable", "global"]},
                "mac_ttl": {"required": False, "type": "int"},
                "manageip": {"required": False, "type": "str"},
                "manageip6": {"required": False, "type": "str"},
                "multicast_forward": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "multicast_skip_policy": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "multicast_ttl_notchange": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                "ngfw_mode": {"required": False, "type": "str",
                              "choices": ["profile-based", "policy-based"]},
                "opmode": {"required": False, "type": "str",
                           "choices": ["nat", "transparent"]},
                "prp_trailer_action": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "sccp_port": {"required": False, "type": "int"},
                "ses_denied_traffic": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "sip_helper": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "sip_nat_trace": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "sip_ssl_port": {"required": False, "type": "int"},
                "sip_tcp_port": {"required": False, "type": "int"},
                "sip_udp_port": {"required": False, "type": "int"},
                "snat_hairpin_traffic": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "ssl_ssh_profile": {"required": False, "type": "str"},
                "status": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "strict_src_check": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "tcp_session_without_syn": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                "utf8_spam_tagging": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "v4_ecmp_mode": {"required": False, "type": "str",
                                 "choices": ["source-ip-based", "weight-based", "usage-based",
                                             "source-dest-ip-based"]},
                "vpn_stats_log": {"required": False, "type": "str",
                                  "choices": ["ipsec", "pptp", "l2tp",
                                              "ssl"]},
                "vpn_stats_period": {"required": False, "type": "int"},
                "wccp_cache_engine": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]}

            }
        }
    }

    module = AnsibleModule(argument_spec=fields,
                           supports_check_mode=False)

    # legacy_mode refers to using fortiosapi instead of HTTPAPI
    legacy_mode = 'host' in module.params and module.params['host'] is not None and \
                  'username' in module.params and module.params['username'] is not None and \
                  'password' in module.params and module.params['password'] is not None

    if not legacy_mode:
        if module._socket_path:
            connection = Connection(module._socket_path)
            fos = FortiOSHandler(connection)

            is_error, has_changed, result = fortios_system(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_system(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
