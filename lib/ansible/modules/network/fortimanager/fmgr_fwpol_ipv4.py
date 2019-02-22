#!/usr/bin/python
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fmgr_fwpol_ipv4
version_added: "2.8"
notes:
    - Full Documentation at U(https://ftnt-ansible-docs.readthedocs.io/en/latest/).
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: Allows the add/delete of Firewall Policies on Packages in FortiManager.
description:
  -  Allows the add/delete of Firewall Policies on Packages in FortiManager.

options:
  adom:
    description:
      - The ADOM the configuration should belong to.
    required: false
    default: root

  mode:
    description:
      - Sets one of three modes for managing the object.
      - Allows use of soft-adds instead of overwriting existing values
    choices: ['add', 'set', 'delete', 'update']
    required: false
    default: add

  package_name:
    description:
      - The policy package you want to modify
    required: false
    default: "default"

  wsso:
    description:
      - Enable/disable WiFi Single Sign On (WSSO).
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  webfilter_profile:
    description:
      - Name of an existing Web filter profile.
    required: false

  webcache_https:
    description:
      - Enable/disable web cache for HTTPS.
      - choice | disable | Disable web cache for HTTPS.
      - choice | enable | Enable web cache for HTTPS.
    required: false
    choices: ["disable", "enable"]

  webcache:
    description:
      - Enable/disable web cache.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  wccp:
    description:
      - Enable/disable forwarding traffic matching this policy to a configured WCCP server.
      - choice | disable | Disable WCCP setting.
      - choice | enable | Enable WCCP setting.
    required: false
    choices: ["disable", "enable"]

  wanopt_profile:
    description:
      - WAN optimization profile.
    required: false

  wanopt_peer:
    description:
      - WAN optimization peer.
    required: false

  wanopt_passive_opt:
    description:
      - WAN optimization passive mode options. This option decides what IP address will be used to connect server.
      - choice | default | Allow client side WAN opt peer to decide.
      - choice | transparent | Use address of client to connect to server.
      - choice | non-transparent | Use local FortiGate address to connect to server.
    required: false
    choices: ["default", "transparent", "non-transparent"]

  wanopt_detection:
    description:
      - WAN optimization auto-detection mode.
      - choice | active | Active WAN optimization peer auto-detection.
      - choice | passive | Passive WAN optimization peer auto-detection.
      - choice | off | Turn off WAN optimization peer auto-detection.
    required: false
    choices: ["active", "passive", "off"]

  wanopt:
    description:
      - Enable/disable WAN optimization.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  waf_profile:
    description:
      - Name of an existing Web application firewall profile.
    required: false

  vpntunnel:
    description:
      - Policy-based IPsec VPN |  name of the IPsec VPN Phase 1.
    required: false

  voip_profile:
    description:
      - Name of an existing VoIP profile.
    required: false

  vlan_filter:
    description:
      - Set VLAN filters.
    required: false

  vlan_cos_rev:
    description:
      - VLAN reverse direction user priority | 255 passthrough, 0 lowest, 7 highest..
    required: false

  vlan_cos_fwd:
    description:
      - VLAN forward direction user priority | 255 passthrough, 0 lowest, 7 highest.
    required: false

  utm_status:
    description:
      - Enable to add one or more security profiles (AV, IPS, etc.) to the firewall policy.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  users:
    description:
      - Names of individual users that can authenticate with this policy.
    required: false

  url_category:
    description:
      - URL category ID list.
    required: false

  traffic_shaper_reverse:
    description:
      - Reverse traffic shaper.
    required: false

  traffic_shaper:
    description:
      - Traffic shaper.
    required: false

  timeout_send_rst:
    description:
      - Enable/disable sending RST packets when TCP sessions expire.
      - choice | disable | Disable sending of RST packet upon TCP session expiration.
      - choice | enable | Enable sending of RST packet upon TCP session expiration.
    required: false
    choices: ["disable", "enable"]

  tcp_session_without_syn:
    description:
      - Enable/disable creation of TCP session without SYN flag.
      - choice | all | Enable TCP session without SYN.
      - choice | data-only | Enable TCP session data only.
      - choice | disable | Disable TCP session without SYN.
    required: false
    choices: ["all", "data-only", "disable"]

  tcp_mss_sender:
    description:
      - Sender TCP maximum segment size (MSS).
    required: false

  tcp_mss_receiver:
    description:
      - Receiver TCP maximum segment size (MSS).
    required: false

  status:
    description:
      - Enable or disable this policy.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  ssl_ssh_profile:
    description:
      - Name of an existing SSL SSH profile.
    required: false

  ssl_mirror_intf:
    description:
      - SSL mirror interface name.
    required: false

  ssl_mirror:
    description:
      - Enable to copy decrypted SSL traffic to a FortiGate interface (called SSL mirroring).
      - choice | disable | Disable SSL mirror.
      - choice | enable | Enable SSL mirror.
    required: false
    choices: ["disable", "enable"]

  ssh_filter_profile:
    description:
      - Name of an existing SSH filter profile.
    required: false

  srcintf:
    description:
      - Incoming (ingress) interface.
    required: false

  srcaddr_negate:
    description:
      - When enabled srcaddr specifies what the source address must NOT be.
      - choice | disable | Disable source address negate.
      - choice | enable | Enable source address negate.
    required: false
    choices: ["disable", "enable"]

  srcaddr:
    description:
      - Source address and address group names.
    required: false

  spamfilter_profile:
    description:
      - Name of an existing Spam filter profile.
    required: false

  session_ttl:
    description:
      - TTL in seconds for sessions accepted by this policy (0 means use the system default session TTL).
    required: false

  service_negate:
    description:
      - When enabled service specifies what the service must NOT be.
      - choice | disable | Disable negated service match.
      - choice | enable | Enable negated service match.
    required: false
    choices: ["disable", "enable"]

  service:
    description:
      - Service and service group names.
    required: false

  send_deny_packet:
    description:
      - Enable to send a reply when a session is denied or blocked by a firewall policy.
      - choice | disable | Disable deny-packet sending.
      - choice | enable | Enable deny-packet sending.
    required: false
    choices: ["disable", "enable"]

  schedule_timeout:
    description:
      - Enable to force current sessions to end when the schedule object times out.
      - choice | disable | Disable schedule timeout.
      - choice | enable | Enable schedule timeout.
    required: false
    choices: ["disable", "enable"]

  schedule:
    description:
      - Schedule name.
    required: false

  scan_botnet_connections:
    description:
      - Block or monitor connections to Botnet servers or disable Botnet scanning.
      - choice | disable | Do not scan connections to botnet servers.
      - choice | block | Block connections to botnet servers.
      - choice | monitor | Log connections to botnet servers.
    required: false
    choices: ["disable", "block", "monitor"]

  rtp_nat:
    description:
      - Enable Real Time Protocol (RTP) NAT.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  rtp_addr:
    description:
      - Address names if this is an RTP NAT policy.
    required: false

  rsso:
    description:
      - Enable/disable RADIUS single sign-on (RSSO).
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  replacemsg_override_group:
    description:
      - Override the default replacement message group for this policy.
    required: false

  redirect_url:
    description:
      - URL users are directed to after seeing and accepting the disclaimer or authenticating.
    required: false

  radius_mac_auth_bypass:
    description:
      - Enable MAC authentication bypass. The bypassed MAC address must be received from RADIUS server.
      - choice | disable | Disable MAC authentication bypass.
      - choice | enable | Enable MAC authentication bypass.
    required: false
    choices: ["disable", "enable"]

  profile_type:
    description:
      - Determine whether the firewall policy allows security profile groups or single profiles only.
      - choice | single | Do not allow security profile groups.
      - choice | group | Allow security profile groups.
    required: false
    choices: ["single", "group"]

  profile_protocol_options:
    description:
      - Name of an existing Protocol options profile.
    required: false

  profile_group:
    description:
      - Name of profile group.
    required: false

  poolname:
    description:
      - IP Pool names.
    required: false

  policyid:
    description:
      - Policy ID.
    required: false

  permit_stun_host:
    description:
      - Accept UDP packets from any Session Traversal Utilities for NAT (STUN) host.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  permit_any_host:
    description:
      - Accept UDP packets from any host.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  per_ip_shaper:
    description:
      - Per-IP traffic shaper.
    required: false

  outbound:
    description:
      - Policy-based IPsec VPN |  only traffic from the internal network can initiate a VPN.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  ntlm_guest:
    description:
      - Enable/disable NTLM guest user access.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  ntlm_enabled_browsers:
    description:
      - HTTP-User-Agent value of supported browsers.
    required: false

  ntlm:
    description:
      - Enable/disable NTLM authentication.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  np_acceleration:
    description:
      - Enable/disable UTM Network Processor acceleration.
      - choice | disable | Disable UTM Network Processor acceleration.
      - choice | enable | Enable UTM Network Processor acceleration.
    required: false
    choices: ["disable", "enable"]

  natoutbound:
    description:
      - Policy-based IPsec VPN |  apply source NAT to outbound traffic.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  natip:
    description:
      - Policy-based IPsec VPN |  source NAT IP address for outgoing traffic.
    required: false

  natinbound:
    description:
      - Policy-based IPsec VPN |  apply destination NAT to inbound traffic.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  nat:
    description:
      - Enable/disable source NAT.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  name:
    description:
      - Policy name.
    required: false

  mms_profile:
    description:
      - Name of an existing MMS profile.
    required: false

  match_vip:
    description:
      - Enable to match packets that have had their destination addresses changed by a VIP.
      - choice | disable | Do not match DNATed packet.
      - choice | enable | Match DNATed packet.
    required: false
    choices: ["disable", "enable"]

  logtraffic_start:
    description:
      - Record logs when a session starts and ends.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  logtraffic:
    description:
      - Enable or disable logging. Log all sessions or security profile sessions.
      - choice | disable | Disable all logging for this policy.
      - choice | all | Log all sessions accepted or denied by this policy.
      - choice | utm | Log traffic that has a security profile applied to it.
    required: false
    choices: ["disable", "all", "utm"]

  learning_mode:
    description:
      - Enable to allow everything, but log all of the meaningful data for security information gathering.
      - choice | disable | Disable learning mode in firewall policy.
      - choice | enable | Enable learning mode in firewall policy.
    required: false
    choices: ["disable", "enable"]

  label:
    description:
      - Label for the policy that appears when the GUI is in Section View mode.
    required: false

  ips_sensor:
    description:
      - Name of an existing IPS sensor.
    required: false

  ippool:
    description:
      - Enable to use IP Pools for source NAT.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  internet_service_src_negate:
    description:
      - When enabled internet-service-src specifies what the service must NOT be.
      - choice | disable | Disable negated Internet Service source match.
      - choice | enable | Enable negated Internet Service source match.
    required: false
    choices: ["disable", "enable"]

  internet_service_src_id:
    description:
      - Internet Service source ID.
    required: false

  internet_service_src_custom:
    description:
      - Custom Internet Service source name.
    required: false

  internet_service_src:
    description:
      - Enable/disable use of Internet Services in source for this policy. If enabled, source address is not used.
      - choice | disable | Disable use of Internet Services source in policy.
      - choice | enable | Enable use of Internet Services source in policy.
    required: false
    choices: ["disable", "enable"]

  internet_service_negate:
    description:
      - When enabled internet-service specifies what the service must NOT be.
      - choice | disable | Disable negated Internet Service match.
      - choice | enable | Enable negated Internet Service match.
    required: false
    choices: ["disable", "enable"]

  internet_service_id:
    description:
      - Internet Service ID.
    required: false

  internet_service_custom:
    description:
      - Custom Internet Service name.
    required: false

  internet_service:
    description:
      - Enable/disable use of Internet Services for this policy. If enabled, dstaddr and service are not used.
      - choice | disable | Disable use of Internet Services in policy.
      - choice | enable | Enable use of Internet Services in policy.
    required: false
    choices: ["disable", "enable"]

  inbound:
    description:
      - Policy-based IPsec VPN |  only traffic from the remote network can initiate a VPN.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  identity_based_route:
    description:
      - Name of identity-based routing rule.
    required: false

  icap_profile:
    description:
      - Name of an existing ICAP profile.
    required: false

  gtp_profile:
    description:
      - GTP profile.
    required: false

  groups:
    description:
      - Names of user groups that can authenticate with this policy.
    required: false

  global_label:
    description:
      - Label for the policy that appears when the GUI is in Global View mode.
    required: false

  fsso_agent_for_ntlm:
    description:
      - FSSO agent to use for NTLM authentication.
    required: false

  fsso:
    description:
      - Enable/disable Fortinet Single Sign-On.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  fixedport:
    description:
      - Enable to prevent source NAT from changing a session's source port.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  firewall_session_dirty:
    description:
      - How to handle sessions if the configuration of this firewall policy changes.
      - choice | check-all | Flush all current sessions accepted by this policy.
      - choice | check-new | Continue to allow sessions already accepted by this policy.
    required: false
    choices: ["check-all", "check-new"]

  dstintf:
    description:
      - Outgoing (egress) interface.
    required: false

  dstaddr_negate:
    description:
      - When enabled dstaddr specifies what the destination address must NOT be.
      - choice | disable | Disable destination address negate.
      - choice | enable | Enable destination address negate.
    required: false
    choices: ["disable", "enable"]

  dstaddr:
    description:
      - Destination address and address group names.
    required: false

  dsri:
    description:
      - Enable DSRI to ignore HTTP server responses.
      - choice | disable | Disable DSRI.
      - choice | enable | Enable DSRI.
    required: false
    choices: ["disable", "enable"]

  dscp_value:
    description:
      - DSCP value.
    required: false

  dscp_negate:
    description:
      - Enable negated DSCP match.
      - choice | disable | Disable DSCP negate.
      - choice | enable | Enable DSCP negate.
    required: false
    choices: ["disable", "enable"]

  dscp_match:
    description:
      - Enable DSCP check.
      - choice | disable | Disable DSCP check.
      - choice | enable | Enable DSCP check.
    required: false
    choices: ["disable", "enable"]

  dnsfilter_profile:
    description:
      - Name of an existing DNS filter profile.
    required: false

  dlp_sensor:
    description:
      - Name of an existing DLP sensor.
    required: false

  disclaimer:
    description:
      - Enable/disable user authentication disclaimer.
      - choice | disable | Disable user authentication disclaimer.
      - choice | enable | Enable user authentication disclaimer.
    required: false
    choices: ["disable", "enable"]

  diffservcode_rev:
    description:
      - Change packet's reverse (reply) DiffServ to this value.
    required: false

  diffservcode_forward:
    description:
      - Change packet's DiffServ to this value.
    required: false

  diffserv_reverse:
    description:
      - Enable to change packet's reverse (reply) DiffServ values to the specified diffservcode-rev value.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  diffserv_forward:
    description:
      - Enable to change packet's DiffServ values to the specified diffservcode-forward value.
      - choice | disable | Disable WAN optimization.
      - choice | enable | Enable WAN optimization.
    required: false
    choices: ["disable", "enable"]

  devices:
    description:
      - Names of devices or device groups that can be matched by the policy.
    required: false

  delay_tcp_npu_session:
    description:
      - Enable TCP NPU session delay to guarantee packet order of 3-way handshake.
      - choice | disable | Disable TCP NPU session delay in order to guarantee packet order of 3-way handshake.
      - choice | enable | Enable TCP NPU session delay in order to guarantee packet order of 3-way handshake.
    required: false
    choices: ["disable", "enable"]

  custom_log_fields:
    description:
      - Custom fields to append to log messages for this policy.
    required: false

  comments:
    description:
      - Comment.
    required: false

  capture_packet:
    description:
      - Enable/disable capture packets.
      - choice | disable | Disable capture packets.
      - choice | enable | Enable capture packets.
    required: false
    choices: ["disable", "enable"]

  captive_portal_exempt:
    description:
      - Enable to exempt some users from the captive portal.
      - choice | disable | Disable exemption of captive portal.
      - choice | enable | Enable exemption of captive portal.
    required: false
    choices: ["disable", "enable"]

  block_notification:
    description:
      - Enable/disable block notification.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  av_profile:
    description:
      - Name of an existing Antivirus profile.
    required: false

  auto_asic_offload:
    description:
      - Enable/disable offloading security profile processing to CP processors.
      - choice | disable | Disable ASIC offloading.
      - choice | enable | Enable auto ASIC offloading.
    required: false
    choices: ["disable", "enable"]

  auth_redirect_addr:
    description:
      - HTTP-to-HTTPS redirect address for firewall authentication.
    required: false

  auth_path:
    description:
      - Enable/disable authentication-based routing.
      - choice | disable | Disable authentication-based routing.
      - choice | enable | Enable authentication-based routing.
    required: false
    choices: ["disable", "enable"]

  auth_cert:
    description:
      - HTTPS server certificate for policy authentication.
    required: false

  application_list:
    description:
      - Name of an existing Application list.
    required: false

  application:
    description:
      - Application ID list.
    required: false

  app_group:
    description:
      - Application group names.
    required: false

  app_category:
    description:
      - Application category ID list.
    required: false

  action:
    description:
      - Policy action (allow/deny/ipsec).
      - choice | deny | Blocks sessions that match the firewall policy.
      - choice | accept | Allows session that match the firewall policy.
      - choice | ipsec | Firewall policy becomes a policy-based IPsec VPN policy.
    required: false
    choices: ["deny", "accept", "ipsec"]

  vpn_dst_node:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED. This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
    required: false

  vpn_dst_node_host:
    description:
      - VPN Destination Node Host.
    required: false

  vpn_dst_node_seq:
    description:
      - VPN Destination Node Seq.
    required: false

  vpn_dst_node_subnet:
    description:
      - VPN Destination Node Seq.
    required: false

  vpn_src_node:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED. This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
    required: false

  vpn_src_node_host:
    description:
      - VPN Source Node Host.
    required: false

  vpn_src_node_seq:
    description:
      - VPN Source Node Seq.
    required: false

  vpn_src_node_subnet:
    description:
      - VPN Source Node.
    required: false


'''

EXAMPLES = '''
- name: ADD VERY BASIC IPV4 POLICY WITH NO NAT (WIDE OPEN)
  fmgr_fwpol_ipv4:
    mode: "set"
    adom: "ansible"
    package_name: "default"
    name: "Basic_IPv4_Policy"
    comments: "Created by Ansible"
    action: "accept"
    dstaddr: "all"
    srcaddr: "all"
    dstintf: "any"
    srcintf: "any"
    logtraffic: "utm"
    service: "ALL"
    schedule: "always"

- name: ADD VERY BASIC IPV4 POLICY WITH NAT AND MULTIPLE ENTRIES
  fmgr_fwpol_ipv4:
    mode: "set"
    adom: "ansible"
    package_name: "default"
    name: "Basic_IPv4_Policy_2"
    comments: "Created by Ansible"
    action: "accept"
    dstaddr: "google-play"
    srcaddr: "all"
    dstintf: "any"
    srcintf: "any"
    logtraffic: "utm"
    service: "HTTP, HTTPS"
    schedule: "always"
    nat: "enable"
    users: "karen, kevin"

- name: ADD VERY BASIC IPV4 POLICY WITH NAT AND MULTIPLE ENTRIES AND SEC PROFILES
  fmgr_fwpol_ipv4:
    mode: "set"
    adom: "ansible"
    package_name: "default"
    name: "Basic_IPv4_Policy_3"
    comments: "Created by Ansible"
    action: "accept"
    dstaddr: "google-play, autoupdate.opera.com"
    srcaddr: "corp_internal"
    dstintf: "zone_wan1, zone_wan2"
    srcintf: "zone_int1"
    logtraffic: "utm"
    service: "HTTP, HTTPS"
    schedule: "always"
    nat: "enable"
    users: "karen, kevin"
    av_profile: "sniffer-profile"
    ips_sensor: "default"

'''

RETURN = """
api_result:
  description: full API response, includes status code and message
  returned: always
  type: str
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.fortimanager.fortimanager import FortiManagerHandler
from ansible.module_utils.network.fortimanager.common import FMGBaseException
from ansible.module_utils.network.fortimanager.common import FMGRCommon
from ansible.module_utils.network.fortimanager.common import FMGRMethods
from ansible.module_utils.network.fortimanager.common import DEFAULT_RESULT_OBJ
from ansible.module_utils.network.fortimanager.common import FAIL_SOCKET_MSG
from ansible.module_utils.network.fortimanager.common import prepare_dict
from ansible.module_utils.network.fortimanager.common import scrub_dict


def fmgr_firewall_policy_modify(fmgr, paramgram):
    """
    fmgr_firewall_policy -- Add/Set/Deletes Firewall Policy Objects defined in the "paramgram"

    :param fmgr: The fmgr object instance from fmgr_utils.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict

    :return: The response from the FortiManager
    :rtype: dict
    """

    mode = paramgram["mode"]
    adom = paramgram["adom"]
    # INIT A BASIC OBJECTS
    response = DEFAULT_RESULT_OBJ
    url = ""
    datagram = {}

    # EVAL THE MODE PARAMETER FOR SET OR ADD
    if mode in ['set', 'add', 'update']:
        url = '/pm/config/adom/{adom}/pkg/{pkg}/firewall/policy'.format(adom=adom, pkg=paramgram["package_name"])
        datagram = scrub_dict((prepare_dict(paramgram)))
        del datagram["package_name"]
        datagram = fmgr._tools.split_comma_strings_into_lists(datagram)

    # EVAL THE MODE PARAMETER FOR DELETE
    elif mode == "delete":
        url = '/pm/config/adom/{adom}/pkg/{pkg}/firewall' \
              '/policy/{policyid}'.format(adom=paramgram["adom"],
                                          pkg=paramgram["package_name"],
                                          policyid=paramgram["policyid"])
        datagram = {
            "policyid": paramgram["policyid"]
        }

    response = fmgr.process_request(url, datagram, paramgram["mode"])
    return response


#############
# END METHODS
#############


def main():
    argument_spec = dict(
        adom=dict(type="str", default="root"),
        mode=dict(choices=["add", "set", "delete", "update"], type="str", default="add"),
        package_name=dict(type="str", required=False, default="default"),

        wsso=dict(required=False, type="str", choices=["disable", "enable"]),
        webfilter_profile=dict(required=False, type="str"),
        webcache_https=dict(required=False, type="str", choices=["disable", "enable"]),
        webcache=dict(required=False, type="str", choices=["disable", "enable"]),
        wccp=dict(required=False, type="str", choices=["disable", "enable"]),
        wanopt_profile=dict(required=False, type="str"),
        wanopt_peer=dict(required=False, type="str"),
        wanopt_passive_opt=dict(required=False, type="str", choices=["default", "transparent", "non-transparent"]),
        wanopt_detection=dict(required=False, type="str", choices=["active", "passive", "off"]),
        wanopt=dict(required=False, type="str", choices=["disable", "enable"]),
        waf_profile=dict(required=False, type="str"),
        vpntunnel=dict(required=False, type="str"),
        voip_profile=dict(required=False, type="str"),
        vlan_filter=dict(required=False, type="str"),
        vlan_cos_rev=dict(required=False, type="int"),
        vlan_cos_fwd=dict(required=False, type="int"),
        utm_status=dict(required=False, type="str", choices=["disable", "enable"]),
        users=dict(required=False, type="str"),
        url_category=dict(required=False, type="str"),
        traffic_shaper_reverse=dict(required=False, type="str"),
        traffic_shaper=dict(required=False, type="str"),
        timeout_send_rst=dict(required=False, type="str", choices=["disable", "enable"]),
        tcp_session_without_syn=dict(required=False, type="str", choices=["all", "data-only", "disable"]),
        tcp_mss_sender=dict(required=False, type="int"),
        tcp_mss_receiver=dict(required=False, type="int"),
        status=dict(required=False, type="str", choices=["disable", "enable"]),
        ssl_ssh_profile=dict(required=False, type="str"),
        ssl_mirror_intf=dict(required=False, type="str"),
        ssl_mirror=dict(required=False, type="str", choices=["disable", "enable"]),
        ssh_filter_profile=dict(required=False, type="str"),
        srcintf=dict(required=False, type="str"),
        srcaddr_negate=dict(required=False, type="str", choices=["disable", "enable"]),
        srcaddr=dict(required=False, type="str"),
        spamfilter_profile=dict(required=False, type="str"),
        session_ttl=dict(required=False, type="int"),
        service_negate=dict(required=False, type="str", choices=["disable", "enable"]),
        service=dict(required=False, type="str"),
        send_deny_packet=dict(required=False, type="str", choices=["disable", "enable"]),
        schedule_timeout=dict(required=False, type="str", choices=["disable", "enable"]),
        schedule=dict(required=False, type="str"),
        scan_botnet_connections=dict(required=False, type="str", choices=["disable", "block", "monitor"]),
        rtp_nat=dict(required=False, type="str", choices=["disable", "enable"]),
        rtp_addr=dict(required=False, type="str"),
        rsso=dict(required=False, type="str", choices=["disable", "enable"]),
        replacemsg_override_group=dict(required=False, type="str"),
        redirect_url=dict(required=False, type="str"),
        radius_mac_auth_bypass=dict(required=False, type="str", choices=["disable", "enable"]),
        profile_type=dict(required=False, type="str", choices=["single", "group"]),
        profile_protocol_options=dict(required=False, type="str"),
        profile_group=dict(required=False, type="str"),
        poolname=dict(required=False, type="str"),
        policyid=dict(required=False, type="str"),
        permit_stun_host=dict(required=False, type="str", choices=["disable", "enable"]),
        permit_any_host=dict(required=False, type="str", choices=["disable", "enable"]),
        per_ip_shaper=dict(required=False, type="str"),
        outbound=dict(required=False, type="str", choices=["disable", "enable"]),
        ntlm_guest=dict(required=False, type="str", choices=["disable", "enable"]),
        ntlm_enabled_browsers=dict(required=False, type="str"),
        ntlm=dict(required=False, type="str", choices=["disable", "enable"]),
        np_acceleration=dict(required=False, type="str", choices=["disable", "enable"]),
        natoutbound=dict(required=False, type="str", choices=["disable", "enable"]),
        natip=dict(required=False, type="str"),
        natinbound=dict(required=False, type="str", choices=["disable", "enable"]),
        nat=dict(required=False, type="str", choices=["disable", "enable"]),
        name=dict(required=False, type="str"),
        mms_profile=dict(required=False, type="str"),
        match_vip=dict(required=False, type="str", choices=["disable", "enable"]),
        logtraffic_start=dict(required=False, type="str", choices=["disable", "enable"]),
        logtraffic=dict(required=False, type="str", choices=["disable", "all", "utm"]),
        learning_mode=dict(required=False, type="str", choices=["disable", "enable"]),
        label=dict(required=False, type="str"),
        ips_sensor=dict(required=False, type="str"),
        ippool=dict(required=False, type="str", choices=["disable", "enable"]),
        internet_service_src_negate=dict(required=False, type="str", choices=["disable", "enable"]),
        internet_service_src_id=dict(required=False, type="str"),
        internet_service_src_custom=dict(required=False, type="str"),
        internet_service_src=dict(required=False, type="str", choices=["disable", "enable"]),
        internet_service_negate=dict(required=False, type="str", choices=["disable", "enable"]),
        internet_service_id=dict(required=False, type="str"),
        internet_service_custom=dict(required=False, type="str"),
        internet_service=dict(required=False, type="str", choices=["disable", "enable"]),
        inbound=dict(required=False, type="str", choices=["disable", "enable"]),
        identity_based_route=dict(required=False, type="str"),
        icap_profile=dict(required=False, type="str"),
        gtp_profile=dict(required=False, type="str"),
        groups=dict(required=False, type="str"),
        global_label=dict(required=False, type="str"),
        fsso_agent_for_ntlm=dict(required=False, type="str"),
        fsso=dict(required=False, type="str", choices=["disable", "enable"]),
        fixedport=dict(required=False, type="str", choices=["disable", "enable"]),
        firewall_session_dirty=dict(required=False, type="str", choices=["check-all", "check-new"]),
        dstintf=dict(required=False, type="str"),
        dstaddr_negate=dict(required=False, type="str", choices=["disable", "enable"]),
        dstaddr=dict(required=False, type="str"),
        dsri=dict(required=False, type="str", choices=["disable", "enable"]),
        dscp_value=dict(required=False, type="str"),
        dscp_negate=dict(required=False, type="str", choices=["disable", "enable"]),
        dscp_match=dict(required=False, type="str", choices=["disable", "enable"]),
        dnsfilter_profile=dict(required=False, type="str"),
        dlp_sensor=dict(required=False, type="str"),
        disclaimer=dict(required=False, type="str", choices=["disable", "enable"]),
        diffservcode_rev=dict(required=False, type="str"),
        diffservcode_forward=dict(required=False, type="str"),
        diffserv_reverse=dict(required=False, type="str", choices=["disable", "enable"]),
        diffserv_forward=dict(required=False, type="str", choices=["disable", "enable"]),
        devices=dict(required=False, type="str"),
        delay_tcp_npu_session=dict(required=False, type="str", choices=["disable", "enable"]),
        custom_log_fields=dict(required=False, type="str"),
        comments=dict(required=False, type="str"),
        capture_packet=dict(required=False, type="str", choices=["disable", "enable"]),
        captive_portal_exempt=dict(required=False, type="str", choices=["disable", "enable"]),
        block_notification=dict(required=False, type="str", choices=["disable", "enable"]),
        av_profile=dict(required=False, type="str"),
        auto_asic_offload=dict(required=False, type="str", choices=["disable", "enable"]),
        auth_redirect_addr=dict(required=False, type="str"),
        auth_path=dict(required=False, type="str", choices=["disable", "enable"]),
        auth_cert=dict(required=False, type="str"),
        application_list=dict(required=False, type="str"),
        application=dict(required=False, type="str"),
        app_group=dict(required=False, type="str"),
        app_category=dict(required=False, type="str"),
        action=dict(required=False, type="str", choices=["deny", "accept", "ipsec"]),
        vpn_dst_node=dict(required=False, type="list"),
        vpn_dst_node_host=dict(required=False, type="str"),
        vpn_dst_node_seq=dict(required=False, type="str"),
        vpn_dst_node_subnet=dict(required=False, type="str"),
        vpn_src_node=dict(required=False, type="list"),
        vpn_src_node_host=dict(required=False, type="str"),
        vpn_src_node_seq=dict(required=False, type="str"),
        vpn_src_node_subnet=dict(required=False, type="str"),

    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False, )
    # MODULE PARAMGRAM
    paramgram = {
        "mode": module.params["mode"],
        "adom": module.params["adom"],
        "package_name": module.params["package_name"],
        "wsso": module.params["wsso"],
        "webfilter-profile": module.params["webfilter_profile"],
        "webcache-https": module.params["webcache_https"],
        "webcache": module.params["webcache"],
        "wccp": module.params["wccp"],
        "wanopt-profile": module.params["wanopt_profile"],
        "wanopt-peer": module.params["wanopt_peer"],
        "wanopt-passive-opt": module.params["wanopt_passive_opt"],
        "wanopt-detection": module.params["wanopt_detection"],
        "wanopt": module.params["wanopt"],
        "waf-profile": module.params["waf_profile"],
        "vpntunnel": module.params["vpntunnel"],
        "voip-profile": module.params["voip_profile"],
        "vlan-filter": module.params["vlan_filter"],
        "vlan-cos-rev": module.params["vlan_cos_rev"],
        "vlan-cos-fwd": module.params["vlan_cos_fwd"],
        "utm-status": module.params["utm_status"],
        "users": module.params["users"],
        "url-category": module.params["url_category"],
        "traffic-shaper-reverse": module.params["traffic_shaper_reverse"],
        "traffic-shaper": module.params["traffic_shaper"],
        "timeout-send-rst": module.params["timeout_send_rst"],
        "tcp-session-without-syn": module.params["tcp_session_without_syn"],
        "tcp-mss-sender": module.params["tcp_mss_sender"],
        "tcp-mss-receiver": module.params["tcp_mss_receiver"],
        "status": module.params["status"],
        "ssl-ssh-profile": module.params["ssl_ssh_profile"],
        "ssl-mirror-intf": module.params["ssl_mirror_intf"],
        "ssl-mirror": module.params["ssl_mirror"],
        "ssh-filter-profile": module.params["ssh_filter_profile"],
        "srcintf": module.params["srcintf"],
        "srcaddr-negate": module.params["srcaddr_negate"],
        "srcaddr": module.params["srcaddr"],
        "spamfilter-profile": module.params["spamfilter_profile"],
        "session-ttl": module.params["session_ttl"],
        "service-negate": module.params["service_negate"],
        "service": module.params["service"],
        "send-deny-packet": module.params["send_deny_packet"],
        "schedule-timeout": module.params["schedule_timeout"],
        "schedule": module.params["schedule"],
        "scan-botnet-connections": module.params["scan_botnet_connections"],
        "rtp-nat": module.params["rtp_nat"],
        "rtp-addr": module.params["rtp_addr"],
        "rsso": module.params["rsso"],
        "replacemsg-override-group": module.params["replacemsg_override_group"],
        "redirect-url": module.params["redirect_url"],
        "radius-mac-auth-bypass": module.params["radius_mac_auth_bypass"],
        "profile-type": module.params["profile_type"],
        "profile-protocol-options": module.params["profile_protocol_options"],
        "profile-group": module.params["profile_group"],
        "poolname": module.params["poolname"],
        "policyid": module.params["policyid"],
        "permit-stun-host": module.params["permit_stun_host"],
        "permit-any-host": module.params["permit_any_host"],
        "per-ip-shaper": module.params["per_ip_shaper"],
        "outbound": module.params["outbound"],
        "ntlm-guest": module.params["ntlm_guest"],
        "ntlm-enabled-browsers": module.params["ntlm_enabled_browsers"],
        "ntlm": module.params["ntlm"],
        "np-acceleration": module.params["np_acceleration"],
        "natoutbound": module.params["natoutbound"],
        "natip": module.params["natip"],
        "natinbound": module.params["natinbound"],
        "nat": module.params["nat"],
        "name": module.params["name"],
        "mms-profile": module.params["mms_profile"],
        "match-vip": module.params["match_vip"],
        "logtraffic-start": module.params["logtraffic_start"],
        "logtraffic": module.params["logtraffic"],
        "learning-mode": module.params["learning_mode"],
        "label": module.params["label"],
        "ips-sensor": module.params["ips_sensor"],
        "ippool": module.params["ippool"],
        "internet-service-src-negate": module.params["internet_service_src_negate"],
        "internet-service-src-id": module.params["internet_service_src_id"],
        "internet-service-src-custom": module.params["internet_service_src_custom"],
        "internet-service-src": module.params["internet_service_src"],
        "internet-service-negate": module.params["internet_service_negate"],
        "internet-service-id": module.params["internet_service_id"],
        "internet-service-custom": module.params["internet_service_custom"],
        "internet-service": module.params["internet_service"],
        "inbound": module.params["inbound"],
        "identity-based-route": module.params["identity_based_route"],
        "icap-profile": module.params["icap_profile"],
        "gtp-profile": module.params["gtp_profile"],
        "groups": module.params["groups"],
        "global-label": module.params["global_label"],
        "fsso-agent-for-ntlm": module.params["fsso_agent_for_ntlm"],
        "fsso": module.params["fsso"],
        "fixedport": module.params["fixedport"],
        "firewall-session-dirty": module.params["firewall_session_dirty"],
        "dstintf": module.params["dstintf"],
        "dstaddr-negate": module.params["dstaddr_negate"],
        "dstaddr": module.params["dstaddr"],
        "dsri": module.params["dsri"],
        "dscp-value": module.params["dscp_value"],
        "dscp-negate": module.params["dscp_negate"],
        "dscp-match": module.params["dscp_match"],
        "dnsfilter-profile": module.params["dnsfilter_profile"],
        "dlp-sensor": module.params["dlp_sensor"],
        "disclaimer": module.params["disclaimer"],
        "diffservcode-rev": module.params["diffservcode_rev"],
        "diffservcode-forward": module.params["diffservcode_forward"],
        "diffserv-reverse": module.params["diffserv_reverse"],
        "diffserv-forward": module.params["diffserv_forward"],
        "devices": module.params["devices"],
        "delay-tcp-npu-session": module.params["delay_tcp_npu_session"],
        "custom-log-fields": module.params["custom_log_fields"],
        "comments": module.params["comments"],
        "capture-packet": module.params["capture_packet"],
        "captive-portal-exempt": module.params["captive_portal_exempt"],
        "block-notification": module.params["block_notification"],
        "av-profile": module.params["av_profile"],
        "auto-asic-offload": module.params["auto_asic_offload"],
        "auth-redirect-addr": module.params["auth_redirect_addr"],
        "auth-path": module.params["auth_path"],
        "auth-cert": module.params["auth_cert"],
        "application-list": module.params["application_list"],
        "application": module.params["application"],
        "app-group": module.params["app_group"],
        "app-category": module.params["app_category"],
        "action": module.params["action"],
        "vpn_dst_node": {
            "host": module.params["vpn_dst_node_host"],
            "seq": module.params["vpn_dst_node_seq"],
            "subnet": module.params["vpn_dst_node_subnet"],
        },
        "vpn_src_node": {
            "host": module.params["vpn_src_node_host"],
            "seq": module.params["vpn_src_node_seq"],
            "subnet": module.params["vpn_src_node_subnet"],
        }
    }
    module.paramgram = paramgram
    fmgr = None
    if module._socket_path:
        connection = Connection(module._socket_path)
        fmgr = FortiManagerHandler(connection, module)
        fmgr.tools = FMGRCommon()
    else:
        module.fail_json(**FAIL_SOCKET_MSG)

    list_overrides = ['vpn_dst_node', 'vpn_src_node']
    paramgram = fmgr.tools.paramgram_child_list_override(list_overrides=list_overrides,
                                                         paramgram=paramgram, module=module)

    # BEGIN MODULE-SPECIFIC LOGIC -- THINGS NEED TO HAPPEN DEPENDING ON THE ENDPOINT AND OPERATION
    results = DEFAULT_RESULT_OBJ
    try:
        if paramgram["mode"] == "delete":
            # WE NEED TO GET THE POLICY ID FROM THE NAME OF THE POLICY TO DELETE IT
            url = '/pm/config/adom/{adom}/pkg/{pkg}/firewall' \
                  '/policy/'.format(adom=paramgram["adom"],
                                    pkg=paramgram["package_name"])
            datagram = {
                "filter": ["name", "==", paramgram["name"]]
            }
            response = fmgr.process_request(url, datagram, FMGRMethods.GET)
            try:
                if response[1][0]["policyid"]:
                    policy_id = response[1][0]["policyid"]
                    paramgram["policyid"] = policy_id
            except BaseException:
                fmgr.return_response(module=module, results=response, good_codes=[0, ], stop_on_success=True,
                                     ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram),
                                     msg="Couldn't find policy ID number for policy name specified.")
    except Exception as err:
        raise FMGBaseException(err)

    try:
        results = fmgr_firewall_policy_modify(fmgr, paramgram)
        fmgr.govern_response(module=module, results=results, good_codes=[0, -9998],
                             ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))
    except Exception as err:
        raise FMGBaseException(err)

    return module.exit_json(**results[1])


if __name__ == "__main__":
    main()
