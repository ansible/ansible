#!/usr/bin/python
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
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
version_added: "2.6"
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: Manages FortiManager Firewall Policies IPv4
description:
  -  Manages FortiManager Firewall Policies IPv4

options:
  adom:
    description:
      - The ADOM the configuration should belong to.
    required: true
  host:
    description:
      - The FortiManager's Address.
    required: true
  username:
    description:
      - The username to log into the FortiManager
    required: true
  password:
    description:
      - The password associated with the username account.
    required: false
  package_name:
    description:
      - The policy package you want to modify
    required: true
  mode:
    description:
      - The mode for the operation
    required: false
    default: add
    choices: ["set", "add", "delete"]

  action:
    description:
      - Policy action (allow/deny/ipsec).
    required: false
  app_category:
    description:
      - Application category ID list.
    required: false
  application:
    description:
      - Application ID list.
    required: false
  application_list:
    description:
      - Application list.
    required: false
  auth_cert:
    description:
      - HTTPS server certificate for policy authentication.
    required: false
  auth_path:
    description:
      - Enable/disable authentication-based routing.
    required: false
    default: "0"
  auth_redirect_addr:
    description:
      - HTTP-to-HTTPS redirect address for firewall authentication.
    required: false
  auto_asic_offload:
    description:
      - Enable/disable offloading security profile processing to CP processors.
    required: false
    default: 1
  av_profile:
    description:
      - Antivirus profile.
    required: false
  block_notification:
    description:
      - Enable/disable block notification.
    required: false
    default: "0"
  captive_portal_exempt:
    description:
      - Enable to exempt some users from the captive portal.
    required: false
    default: "0"
  capture_packet:
    description:
      - Enable/disable capture packets.
    required: false
    default: "0"
  casi_profile:
    description:
      - CASI Profile.
    required: false
  comments:
    description:
      - Comment.
    required: false
  custom_log_fields:
    description:
      - Log field index numbers to append custom log fields to log messages for this policy.
    required: false
  delay_tcp_npu_session:
    description:
      - Enable TCP NPU session delay to guarantee packet order of 3-way handshake.
    required: false
    default: "0"
  devices:
    description:
      - Names of devices or device groups that can be matched by the policy.
    required: false
  diffserv_forward:
    description:
      - Enable to change packet's DiffServ values to the specified diffservcode-forward value.
    required: false
    default: "0"
  diffserv_reverse:
    description:
      - Enable to change packet's reverse (reply) DiffServ values to the specified diffservcode-rev value.
    required: false
    default: "0"
  diffservcode_forward:
    description:
      - Change packet's DiffServ to this value.
    required: false
    default: "000000"
  diffservcode_rev:
    description:
      - Change packet's reverse (reply) DiffServ to this value.
    required: false
    default: "000000"
  disclaimer:
    description:
      - Enable/disable user authentication disclaimer.
    required: false
    default: "0"
  dlp_sensor:
    description:
      - DLP sensor.
    required: false
  dnsfilter_profile:
    description:
      - DNS filter profile.
    required: false
  dsri:
    description:
      - Enable DSRI to ignore HTTP server responses.
    required: false
    default: "0"
  dstaddr:
    description:
      - Destination address and address group names.
    required: false
  dstaddr_negate:
    description:
      - When enabled dstaddr specifies what the destination address must NOT be.
    required: false
    default: "0"
  dstintf:
    description:
      - Outgoing (egress) interface.
    required: false
  firewall_session_dirty:
    description:
      - How to handle sessions if the configuration of this firewall policy changes.
    required: false
    default: "0"
  fixedport:
    description:
      - Enable to prevent source NAT from changing a session's source port.
    required: false
    default: "0"
  fsso:
    description:
      - Enable/disable Fortinet Single Sign-On.
    required: false
    default: "0"
  fsso_agent_for_ntlm:
    description:
      - FSSO agent to use for NTLM authentication.
    required: false
  global_label:
    description:
      - Label for the policy that appears when the GUI is in Global View mode.
    required: false
  groups:
    description:
      - Names of user groups that can authenticate with this policy.
    required: false
  gtp_profile:
    description:
      - GTP profile.
    required: false
  icap_profile:
    description:
      - ICAP profile.
    required: false
  identity_based_route:
    description:
      - Name of identity-based routing rule.
    required: false
  inbound:
    description:
      - Policy-based IPsec VPN only traffic from the remote network can initiate a VPN.
    required: false
    default: "0"
  internet_service:
    description:
      - Enable/disable use of Internet Services for this policy. If enabled, destination address/service not used.
    required: false
    default: "0"
  internet_service_custom:
    description:
      - Custom Internet Service Name.
    required: false
  internet_service_id:
    description:
      - Internet Service ID.
    required: false
  internet_service_negate:
    description:
      - When enabled internet-service specifies what the service must NOT be.
    required: false
    default: "0"
  ippool:
    description:
      - Enable to use IP Pools for source NAT.
    required: false
    default: "0"
  ips_sensor:
    description:
      - IPS sensor.
    required: false
  label:
    description:
      - Label for the policy that appears when the GUI is in Section View mode.
    required: false
  learning_mode:
    description:
      - Enable to allow everything, but log all of the meaningful data. A learning report will be generated.
    required: false
    default: "0"
  logtraffic:
    description:
      - Enable or disable logging. Log all sessions or security profile sessions.
    required: false
  logtraffic_start:
    description:
      - Record logs when a session starts and ends.
    required: false
    default: "0"
  match_vip:
    description:
      - Enable to match packets that have had their destination addresses changed by a VIP.
    required: false
    default: "0"
  mms_profile:
    description:
      - mms profile
    required: false
  name:
    description:
      - Policy name.
    required: false
  nat:
    description:
      - Enable/disable source NAT.
    choices: ['enable','disable']
    required: false
    default: disable
  natinbound:
    description:
      - Policy-based IPsec VPN apply destination NAT to inbound traffic.
    required: false
    default: "0"
  natip:
    description:
      - Policy-based IPsec VPN source NAT IP address for outgoing traffic.
    required: false
    default: ["0.0.0.0", "0.0.0.0"]
  natoutbound:
    description:
      - Policy-based IPsec VPN apply source NAT to outbound traffic.
    required: false
    default: "0"
  ntlm:
    description:
      - Enable/disable NTLM authentication.
    required: false
    default: "0"
  ntlm_enabled_browsers:
    description:
      - HTTP-User-Agent value of supported browsers.
    required: false
  ntlm_guest:
    description:
      - Enable/disable NTLM guest user access.
    required: false
    default: "0"
  outbound:
    description:
      - Policy-based IPsec VPN only traffic from the internal network can initiate a VPN.
    required: false
    default: "0"
  per_ip_shaper:
    description:
      - Per-IP traffic shaper.
    required: false
  permit_any_host:
    description:
      - Accept UDP packets from any host.
    required: false
    default: "0"
  permit_stun_host:
    description:
      - Accept UDP packets from any Session Traversal Utilities for NAT (STUN) host.
    required: false
    default: "0"
  policyid:
    description:
      - Policy ID.
    required: false
    default: -1
  poolname:
    description:
      - IP Pool names.
    required: false
  profile_group:
    description:
      - profile group
    required: false
  profile_protocol_options:
    description:
      - Profile protocol options.
    required: false
  profile_type:
    description:
      - Determine whether the firewall policy allows security profile groups.
    required: false
    default: "0"
  radius_mac_auth_bypass:
    description:
      - Enable MAC authentication bypass. The bypassed MAC address must be received from RADIUS server.
    required: false
    default: "0"
  redirect_url:
    description:
      - URL users are directed to after seeing and accepting the disclaimer or authenticating.
    required: false
  replacemsg_override_group:
    description:
      - Override the default replacement message group for this policy.
    required: false
    default: "0"
  rsso:
    description:
      - Enable/disable RADIUS single sign-on (RSSO).
    required: false
    default: "0"
  rtp_addr:
    description:
      - Address names if this is an RTP NAT policy.
    required: false
  rtp_nat:
    description:
      - Enable Real Time Protocol (RTP) NAT.
    required: false
    default: "0"
  scan_botnet_connections:
    description:
      - Block or monitor connections to Botnet servers or disable Botnet scanning.
    required: false
    default: "0"
  schedule:
    description:
      - Schedule name.
    required: false
    default: always
  schedule_timeout:
    description:
      - Enable to force current sessions to end when the schedule object times out. Disable allows them to end from inactivity.
    required: false
    default: "0"
  send_deny_packet:
    description:
      - Enable to send a reply when a session is denied or blocked by a firewall policy.
    required: false
    default: "0"
  service:
    description:
      - Service and service group names.
    required: false
  service_negate:
    description:
      - When enabled service specifies what the service must NOT be.
    required: false
    default: "0"
  session_ttl:
    description:
      - Session TTL in seconds for sessions accepted by this policy. 0 means use the system default session TTL.
    required: false
    default: "0"
  spamfilter_profile:
    description:
      - Spam filter profile.
    required: false
    default: "0"
  srcaddr:
    description:
      - Source address and address group names.
    required: false
  srcaddr_negate:
    description:
      - When enabled srcaddr specifies what the source address must NOT be.
    required: false
    default: "0"
  srcintf:
    description:
      - Incoming (ingress) interface.
    required: false
  ssl_mirror:
    description:
      - Enable to copy decrypted SSL traffic to a FortiGate interface (called SSL mirroring).
    required: false
    default: "0"
  ssl_mirror_intf:
    description:
      - SSL mirror interface name.
    required: false
  ssl_ssh_profile:
    description:
      - SSL SSH Profile.
    required: false
  status:
    description:
      - Enable or disable this policy.
    required: false
    default: 1
  tags:
    description:
      - Names of object-tags applied to this policy.
    required: false
  tcp_mss_receiver:
    description:
      - Receiver TCP maximum segment size (MSS).
    required: false
    default: "0"
  tcp_mss_sender:
    description:
      - Sender TCP maximum segment size (MSS).
    required: false
    default: "0"
  timeout_send_rst:
    description:
      - Enable/disable sending RST packets when TCP sessions expire.
    required: false
    default: "0"
  traffic_shaper:
    description:
      - Traffic shaper.
    required: false
  traffic_shaper_reverse:
    description:
      - Reverse traffic shaper.
    required: false
  url_category:
    description:
      - URL category ID list.
    required: false
  users:
    description:
      - Names of individual users that can authenticate with this policy.
    required: false
  utm_status:
    description:
      - Enable to add one or more security profiles (AV, IPS, etc.) to the firewall policy.
    required: false
    default: "0"
  vlan_cos_fwd:
    description:
      - VLAN forward direction user priority 255 passthrough, 0 lowest, 7 highest.
    required: false
    default: 255
  vlan_cos_rev:
    description:
      - VLAN reverse direction user priority 255 passthrough, 0 lowest, 7 highest..
    required: false
    default: 255
  voip_profile:
    description:
      - VoIP profile.
    required: false
  vpn_dst_node:
    description:
      - NO DESCRIPTION PARSED ENTER MANUALLY
    required: false
  vpn_src_node:
    description:
      - NO DESCRIPTION PARSED ENTER MANUALLY
    required: false
  vpntunnel:
    description:
      - Policy-based IPsec VPN name of the IPsec VPN Phase 1.
    required: false
  waf_profile:
    description:
      - Web application firewall profile.
    required: false
  wanopt:
    description:
      - Enable/disable WAN optimization.
    required: false
    default: "0"
  wanopt_detection:
    description:
      - WAN optimization auto-detection mode.
    required: false
    default: 1
  wanopt_passive_opt:
    description:
      - WAN optimization passive mode options. This option decides what IP address will be used to connect server.
    required: false
    default: "0"
  wanopt_peer:
    description:
      - WAN optimization peer.
    required: false
  wanopt_profile:
    description:
      - WAN optimization profile.
    required: false
  wccp:
    description:
      - Enable/disable forwarding traffic matching this policy to a configured WCCP server.
    required: false
    default: "0"
  webcache:
    description:
      - Enable/disable web cache.
    required: false
    default: "0"
  webcache_https:
    description:
      - Enable/disable web cache for HTTPS.
    required: false
    default: "0"
  webfilter_profile:
    description:
      - Web filter profile.
    required: false
  wsso:
    description:
      - Enable/disable WiFi Single Sign On (WSSO).
    required: false
    default: 1

'''

EXAMPLES = '''
- name: ADD VERY BASIC IPV4 POLICY WITH NO NAT (WIDE OPEN)
  fmgr_fwpol_ipv4:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    adom: "ansible"
    package_name: "default"
    name: "Basic_IPv4_Policy"
    action: "accept"
    dstaddr: "all"
    srcaddr: "all"
    dstintf: "any"
    srcintf: "any"
    logtraffic: "utm"
'''

RETURN = """
api_result:
  description: full API response, includes status code and message
  returned: always
  type: string
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.network.fortimanager.fortimanager import AnsibleFortiManager

# check for pyFMG lib
try:
    from pyFMG.fortimgr import FortiManager
    HAS_PYFMGR = True
except ImportError:
    HAS_PYFMGR = False


def parse_csv_str_to_list(input_string):
    """
    This function will take a comma seperated string and turn it into a list, removing any spaces next the commas
    that it finds. This is useful for using csv input from ansible parameters and transforming to API requirements.
    """
    if input_string is not None:
        inputs = input_string
        inputs = inputs.replace(", ", ",")
        inputs = inputs.replace(" ,", ",")
        input = []
        for obj in inputs.split(","):
            input.append(obj)
        return input
    else:
        return None


def fmgr_fwpol_ipv4(fmg, paramgram):
    """
    This method sets a fmgr_firewall_policy for ipv4. Note that not all parameters are built in yet!
    Right now it only supports profile groups and basic NAT.
    This method will be constantly evolving until we address every single use case for all of the parameters
    or we decide to cut down on the parameters we can use.
    """
    # TODO:
    # Continue to add parameters from the massive list to the datagram as time goes on, to test these.

    if paramgram["mode"] in ['set', 'add']:
        url = '/pm/config/adom/{adom}/pkg/{pkg}/firewall/policy'.format(adom=paramgram["adom"],
                                                                        pkg=paramgram["package_name"])
        # BEGIN CREATING THE DATAGRAM PARAMETERS
        datagram = {
            # BASIC PARAMETERS
            "name": paramgram["name"],
            "action": paramgram["action"],
            "logtraffic": paramgram["logtraffic"],
            "schedule": paramgram["schedule"],
            "nat": paramgram["nat"],

            # LIST PARAMETERS
            "srcaddr": parse_csv_str_to_list(paramgram["srcaddr"]),
            "dstaddr": parse_csv_str_to_list(paramgram["dstaddr"]),
            "srcintf": parse_csv_str_to_list(paramgram["srcintf"]),
            "dstintf": parse_csv_str_to_list(paramgram["dstintf"]),
            "service": parse_csv_str_to_list(paramgram["service"]),
            "users": parse_csv_str_to_list(paramgram["users"]),

            # ADD PROFILE GENERAL PARAMS

            "profile-type": paramgram["profile-type"],
            "profile-group": paramgram["profile-group"],
            # ADD SECURITY PROFILES
            "dlp-sensor": paramgram["dlp-sensor"],
            "ips-sensor": paramgram["ips-sensor"],
            "av-profile": paramgram["av-profile"],
            "dnsfilter-profile": paramgram["dnsfilter-profile"],
            "gtp-profile": paramgram["gtp-profile"],
            "icap-profile": paramgram["icap-profile"],
            "mms-profile": paramgram["mms-profile"],
            "ssl-ssh-profile": paramgram["ssl-ssh-profile"],
            "voip-profile": paramgram["voip-profile"],
            "waf-profile": paramgram["waf-profile"],
            "wanopt-profile": paramgram["wanopt-profile"],
            "webfilter-profile": paramgram["webfilter-profile"],
            # TODO:
            # CASI IS BROKEN IN THIS VERSION? SAME WITH SPAMFILTER?!
            # "casi-profile": paramgram["casi-profile"],
            # "spamfilter-profile": paramgram["spamfilter-profile"],
            # "profile-protocol-options": paramgram["profile-protocol-options"],
        }

        # IF ANY SECURITY PROFILES ARE DEFINED, WE HAVE TO CHANGE THE PROFILE-TYPE TO "SINGLE"
        if any([datagram["dlp-sensor"], datagram["ips-sensor"], datagram["av-profile"], datagram["dnsfilter-profile"],
                datagram["gtp-profile"], datagram["icap-profile"], datagram["mms-profile"], datagram["ssl-ssh-profile"],
                datagram["voip-profile"], datagram["waf-profile"], datagram["wanopt-profile"],
                datagram["webfilter-profile"]
                ]):
            datagram["profile-type"] = 1

        # IF A PROFILE GROUP IS DEFINED, WE HAVE TO CHANGE THE TYPE TO 2
        if datagram["profile-group"]:
            datagram["profile-type"] = 2

    # IF MODE IS DELETE THEN...
    if paramgram["mode"] == "delete":
        # WE NEED TO GET THE POLICY ID FROM THE NAME OF THE POLICY
        url = '/pm/config/adom/{adom}/pkg/{pkg}/firewall' \
              '/policy/'.format(adom=paramgram["adom"],
                                pkg=paramgram["package_name"])

        datagram = {
            "filter": ["name", "==", paramgram["name"]]
        }

        response = fmg.get(url, datagram)
        try:
            if response[1][0]["policyid"]:
                policy_id = response[1][0]["policyid"]
                datagram = {
                    "policyid": policy_id
                }
                url = '/pm/config/adom/{adom}/pkg/{pkg}/firewall' \
                      '/policy/{policyid}'.format(adom=paramgram["adom"],
                                                  pkg=paramgram["package_name"],
                                                  policyid=policy_id)
                response = fmg.delete(url, datagram)
                return response
        except:
            pass

        # IF POLICY ID WASN'T FOUND, THEN JUST RETURN THE GET
        return response

    if paramgram["mode"] == "set":
        response = fmg.set(url, datagram)
        # IF MODE = ADD  -- USE THE 'ADD' API CALL MODE
    if paramgram["mode"] == "add":
        response = fmg.add(url, datagram)

    # TODO:
    # FIX THE DELETE FUNCTIONS!
    # if paramgram["mode"] == "delete":
    #     response = fmg.delete(url, datagram)
    #     return response

    return response


def main():
    argument_spec = dict(
        adom=dict(required=False, type="str"),
        host=dict(required=True, type="str"),
        password=dict(fallback=(env_fallback, ["ANSIBLE_NET_PASSWORD"]), no_log=True),
        username=dict(fallback=(env_fallback, ["ANSIBLE_NET_USERNAME"]), no_log=True),
        package_name=dict(required=True, type="str"),
        mode=dict(required=False, type="str", default="add", choices=["set", "add", "delete"]),

        action=dict(required=False, type="str"),
        app_category=dict(required=False, type="str"),
        application=dict(required=False, type="str"),
        application_list=dict(required=False, type="str"),
        auth_cert=dict(required=False, type="str"),
        auth_path=dict(required=False, type="str", default="0"),
        auth_redirect_addr=dict(required=False, type="str"),
        auto_asic_offload=dict(required=False, type="str", default="1"),
        av_profile=dict(required=False, type="str"),
        block_notification=dict(required=False, type="str", default="0"),
        captive_portal_exempt=dict(required=False, type="str", default="0"),
        capture_packet=dict(required=False, type="str", default="0"),
        casi_profile=dict(required=False, type="str"),
        comments=dict(required=False, type="str"),
        custom_log_fields=dict(required=False, type="str"),
        delay_tcp_npu_session=dict(required=False, type="str", default="0"),
        devices=dict(required=False, type="str"),
        diffserv_forward=dict(required=False, type="str", default="0"),
        diffserv_reverse=dict(required=False, type="str", default="0"),
        diffservcode_forward=dict(required=False, type="str", default="000000"),
        diffservcode_rev=dict(required=False, type="str", default="000000"),
        disclaimer=dict(required=False, type="str", default="0"),
        dlp_sensor=dict(required=False, type="str"),
        dnsfilter_profile=dict(required=False, type="str"),
        dsri=dict(required=False, type="str", default="0"),
        dstaddr=dict(required=False, type="str"),
        dstaddr_negate=dict(required=False, type="str", default="0"),
        dstintf=dict(required=False, type="str"),
        firewall_session_dirty=dict(required=False, type="str", default="0"),
        fixedport=dict(required=False, type="str", default="0"),
        fsso=dict(required=False, type="str", default="0"),
        fsso_agent_for_ntlm=dict(required=False, type="str"),
        global_label=dict(required=False, type="str"),
        groups=dict(required=False, type="str"),
        gtp_profile=dict(required=False, type="str"),
        icap_profile=dict(required=False, type="str"),
        identity_based_route=dict(required=False, type="str"),
        inbound=dict(required=False, type="str", default="0"),
        internet_service=dict(required=False, type="str", default="0"),
        internet_service_custom=dict(required=False, type="str"),
        internet_service_id=dict(required=False, type="str"),
        internet_service_negate=dict(required=False, type="str", default="0"),
        ippool=dict(required=False, type="str", default="0"),
        ips_sensor=dict(required=False, type="str"),
        label=dict(required=False, type="str"),
        learning_mode=dict(required=False, type="str", default="0"),
        logtraffic=dict(required=False, type="str"),
        logtraffic_start=dict(required=False, type="str", default="0"),
        match_vip=dict(required=False, type="str", default="0"),
        mms_profile=dict(required=False, type="str"),
        name=dict(required=True, type="str"),
        nat=dict(required=False, type="str", choices=["enable", "disable"], default="disable"),
        natinbound=dict(required=False, type="str", default="0"),
        natip=dict(required=False, type="list", default=["0.0.0.0", "0.0.0.0"]),
        natoutbound=dict(required=False, type="str", default="0"),
        ntlm=dict(required=False, type="str", default="0"),
        ntlm_enabled_browsers=dict(required=False, type="str"),
        ntlm_guest=dict(required=False, type="str", default="0"),
        outbound=dict(required=False, type="str", default="0"),
        per_ip_shaper=dict(required=False, type="str"),
        permit_any_host=dict(required=False, type="str", default="0"),
        permit_stun_host=dict(required=False, type="str", default="0"),
        policyid=dict(required=False, type="int", default=-1),
        poolname=dict(required=False, type="str"),
        profile_group=dict(required=False, type="str"),
        profile_protocol_options=dict(required=False, type="str"),
        profile_type=dict(required=False, type="int", default="0"),
        radius_mac_auth_bypass=dict(required=False, type="str", default="0"),
        redirect_url=dict(required=False, type="str"),
        replacemsg_override_group=dict(required=False, type="str", default="0"),
        rsso=dict(required=False, type="str", default="0"),
        rtp_addr=dict(required=False, type="str"),
        rtp_nat=dict(required=False, type="str", default="0"),
        scan_botnet_connections=dict(required=False, type="str", default="0"),
        schedule=dict(required=False, type="str", default="always"),
        schedule_timeout=dict(required=False, type="str", default="0"),
        send_deny_packet=dict(required=False, type="str", default="0"),
        service=dict(required=False, type="str"),
        service_negate=dict(required=False, type="str", default="0"),
        session_ttl=dict(required=False, type="int", default="0"),
        spamfilter_profile=dict(required=False, type="str", default="0"),
        srcaddr=dict(required=False, type="str"),
        srcaddr_negate=dict(required=False, type="str", default="0"),
        srcintf=dict(required=False, type="str"),
        ssl_mirror=dict(required=False, type="str", default="0"),
        ssl_mirror_intf=dict(required=False, type="str"),
        ssl_ssh_profile=dict(required=False, type="str"),
        status=dict(required=False, type="str", default="1"),
        tags=dict(required=False, type="str"),
        tcp_mss_receiver=dict(required=False, type="int", default="0"),
        tcp_mss_sender=dict(required=False, type="int", default="0"),
        timeout_send_rst=dict(required=False, type="str", default="0"),
        traffic_shaper=dict(required=False, type="str"),
        traffic_shaper_reverse=dict(required=False, type="str"),
        url_category=dict(required=False, type="str"),
        users=dict(required=False, type="str"),
        utm_status=dict(required=False, type="str", default="0"),
        vlan_cos_fwd=dict(required=False, type="int", default=255),
        vlan_cos_rev=dict(required=False, type="int", default=255),
        voip_profile=dict(required=False, type="str"),
        vpn_dst_node=dict(required=False, type="str"),
        vpn_src_node=dict(required=False, type="str"),
        vpntunnel=dict(required=False, type="str"),
        waf_profile=dict(required=False, type="str"),
        wanopt=dict(required=False, type="str", default="0"),
        wanopt_detection=dict(required=False, type="str", default="1"),
        wanopt_passive_opt=dict(required=False, type="str", default="0"),
        wanopt_peer=dict(required=False, type="str"),
        wanopt_profile=dict(required=False, type="str"),
        wccp=dict(required=False, type="str", default="0"),
        webcache=dict(required=False, type="str", default="0"),
        webcache_https=dict(required=False, type="str", default="0"),
        webfilter_profile=dict(required=False, type="str"),
        wsso=dict(required=False, type="str", default="1"),

    )
    module = AnsibleModule(argument_spec, supports_check_mode=True, )

    # MODULE DATAGRAM
    paramgram = {
        "adom": module.params["adom"],
        "package_name": module.params["package_name"],
        "mode": module.params["mode"],
        "action": module.params["action"],
        "app-category": module.params["app_category"],
        "application": module.params["application"],
        "application-list": module.params["application_list"],
        "auth-cert": module.params["auth_cert"],
        "auth-path": module.params["auth_path"],
        "auth-redirect-addr": module.params["auth_redirect_addr"],
        "auto-asic-offload": module.params["auto_asic_offload"],
        "av-profile": module.params["av_profile"],
        "block-notification": module.params["block_notification"],
        "captive-portal-exempt": module.params["captive_portal_exempt"],
        "capture-packet": module.params["capture_packet"],
        "casi-profile": module.params["casi_profile"],
        "comments": module.params["comments"],
        "custom-log-fields": module.params["custom_log_fields"],
        "delay-tcp-npu-session": module.params["delay_tcp_npu_session"],
        "devices": module.params["devices"],
        "diffserv-forward": module.params["diffserv_forward"],
        "diffserv-reverse": module.params["diffserv_reverse"],
        "diffservcode-forward": module.params["diffservcode_forward"],
        "diffservcode-rev": module.params["diffservcode_rev"],
        "disclaimer": module.params["disclaimer"],
        "dlp-sensor": module.params["dlp_sensor"],
        "dnsfilter-profile": module.params["dnsfilter_profile"],
        "dsri": module.params["dsri"],
        "dstaddr": module.params["dstaddr"],
        "dstaddr-negate": module.params["dstaddr_negate"],
        "dstintf": module.params["dstintf"],
        "firewall-session-dirty": module.params["firewall_session_dirty"],
        "fixedport": module.params["fixedport"],
        "fsso": module.params["fsso"],
        "fsso-agent-for-ntlm": module.params["fsso_agent_for_ntlm"],
        "global-label": module.params["global_label"],
        "groups": module.params["groups"],
        "gtp-profile": module.params["gtp_profile"],
        "icap-profile": module.params["icap_profile"],
        "identity-based-route": module.params["identity_based_route"],
        "inbound": module.params["inbound"],
        "internet-service": module.params["internet_service"],
        "internet-service-custom": module.params["internet_service_custom"],
        "internet-service-id": module.params["internet_service_id"],
        "internet-service-negate": module.params["internet_service_negate"],
        "ippool": module.params["ippool"],
        "ips-sensor": module.params["ips_sensor"],
        "label": module.params["label"],
        "learning-mode": module.params["learning_mode"],
        "logtraffic": module.params["logtraffic"],
        "logtraffic-start": module.params["logtraffic_start"],
        "match-vip": module.params["match_vip"],
        "mms-profile": module.params["mms_profile"],
        "name": module.params["name"],
        "nat": module.params["nat"],
        "natinbound": module.params["natinbound"],
        "natip": module.params["natip"],
        "natoutbound": module.params["natoutbound"],
        "ntlm": module.params["ntlm"],
        "ntlm-enabled-browsers": module.params["ntlm_enabled_browsers"],
        "ntlm-guest": module.params["ntlm_guest"],
        "outbound": module.params["outbound"],
        "per-ip-shaper": module.params["per_ip_shaper"],
        "permit-any-host": module.params["permit_any_host"],
        "permit-stun-host": module.params["permit_stun_host"],
        "policyid": module.params["policyid"],
        "poolname": module.params["poolname"],
        "profile-group": module.params["profile_group"],
        "profile-protocol-options": module.params["profile_protocol_options"],
        "profile-type": module.params["profile_type"],
        "radius-mac-auth-bypass": module.params["radius_mac_auth_bypass"],
        "redirect-url": module.params["redirect_url"],
        "replacemsg-override-group": module.params["replacemsg_override_group"],
        "rsso": module.params["rsso"],
        "rtp-addr": module.params["rtp_addr"],
        "rtp-nat": module.params["rtp_nat"],
        "scan-botnet-connections": module.params["scan_botnet_connections"],
        "schedule": module.params["schedule"],
        "schedule-timeout": module.params["schedule_timeout"],
        "send-deny-packet": module.params["send_deny_packet"],
        "service": module.params["service"],
        "service-negate": module.params["service_negate"],
        "session-ttl": module.params["session_ttl"],
        "spamfilter-profile": module.params["spamfilter_profile"],
        "srcaddr": module.params["srcaddr"],
        "srcaddr-negate": module.params["srcaddr_negate"],
        "srcintf": module.params["srcintf"],
        "ssl-mirror": module.params["ssl_mirror"],
        "ssl-mirror-intf": module.params["ssl_mirror_intf"],
        "ssl-ssh-profile": module.params["ssl_ssh_profile"],
        "status": module.params["status"],
        "tags": module.params["tags"],
        "tcp-mss-receiver": module.params["tcp_mss_receiver"],
        "tcp-mss-sender": module.params["tcp_mss_sender"],
        "timeout-send-rst": module.params["timeout_send_rst"],
        "traffic-shaper": module.params["traffic_shaper"],
        "traffic-shaper-reverse": module.params["traffic_shaper_reverse"],
        "url-category": module.params["url_category"],
        "users": module.params["users"],
        "utm-status": module.params["utm_status"],
        "vlan-cos-fwd": module.params["vlan_cos_fwd"],
        "vlan-cos-rev": module.params["vlan_cos_rev"],
        "voip-profile": module.params["voip_profile"],
        "vpn_dst_node": module.params["vpn_dst_node"],
        "vpn_src_node": module.params["vpn_src_node"],
        "vpntunnel": module.params["vpntunnel"],
        "waf-profile": module.params["waf_profile"],
        "wanopt": module.params["wanopt"],
        "wanopt-detection": module.params["wanopt_detection"],
        "wanopt-passive-opt": module.params["wanopt_passive_opt"],
        "wanopt-peer": module.params["wanopt_peer"],
        "wanopt-profile": module.params["wanopt_profile"],
        "wccp": module.params["wccp"],
        "webcache": module.params["webcache"],
        "webcache-https": module.params["webcache_https"],
        "webfilter-profile": module.params["webfilter_profile"],
        "wsso": module.params["wsso"],

    }

    # CHECK IF THE HOST/USERNAME/PW EXISTS, AND IF IT DOES, LOGIN.
    host = module.params["host"]
    password = module.params["password"]
    username = module.params["username"]
    if host is None or username is None:
        module.fail_json(msg="Host and username are required")

    # CHECK IF LOGIN FAILED
    fmg = AnsibleFortiManager(module, module.params["host"], module.params["username"], module.params["password"])
    response = fmg.login()

    if "FortiManager instance connnected" not in str(response):
        module.fail_json(msg="Connection to FortiManager Failed")
    else:
        # START SESSION LOGIC
        # IF THE BASIC PARAMETERS NEEDED ARE PRESENT THEN TRY TO CREATE THE POLICY
        if (all([paramgram["action"], paramgram["srcaddr"], paramgram["dstaddr"]]))\
                or (paramgram["mode"] == "delete" and paramgram["name"] is not None):
            results = fmgr_fwpol_ipv4(fmg, paramgram)
            if results[0] == -9998:
                module.exit_json(msg="POLICY ALREADY EXISTS", **results[1])
            elif results[0] != 0 and results[0] not in [-9998]:
                module.fail_json(msg="POLICY UPDATE FAILED", **results[1])
            elif results[0] == 0:
                module.exit_json(msg="POLICY CREATED", **results[1])

    # LOG OUT OF FMGR!
    fmg.logout()

    # return module.exit_json(**results[1])
    # return module.exit_json(msg="debug end", **paramgram)


if __name__ == "__main__":
    main()
