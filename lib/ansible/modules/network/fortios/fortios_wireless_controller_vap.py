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
module: fortios_wireless_controller_vap
short_description: Configure Virtual Access Points (VAPs) in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify wireless_controller feature and vap category.
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
    state:
        description:
            - Indicates whether to create or remove the object.
              This attribute was present already in previous version in a deeper level.
              It has been moved out to this outer level.
        type: str
        required: false
        choices:
            - present
            - absent
        version_added: 2.9
    wireless_controller_vap:
        description:
            - Configure Virtual Access Points (VAPs).
        default: null
        type: dict
        suboptions:
            state:
                description:
                    - B(Deprecated)
                    - Starting with Ansible 2.9 we recommend using the top-level 'state' parameter.
                    - HORIZONTALLINE
                    - Indicates whether to create or remove the object.
                type: str
                required: false
                choices:
                    - present
                    - absent
            acct_interim_interval:
                description:
                    - WiFi RADIUS accounting interim interval (60 - 86400 sec).
                type: int
            alias:
                description:
                    - Alias.
                type: str
            auth:
                description:
                    - Authentication protocol.
                type: str
                choices:
                    - psk
                    - radius
                    - usergroup
            broadcast_ssid:
                description:
                    - Enable/disable broadcasting the SSID .
                type: str
                choices:
                    - enable
                    - disable
            broadcast_suppression:
                description:
                    - Optional suppression of broadcast messages. For example, you can keep DHCP messages, ARP broadcasts, and so on off of the wireless
                       network.
                type: str
                choices:
                    - dhcp-up
                    - dhcp-down
                    - dhcp-starvation
                    - arp-known
                    - arp-unknown
                    - arp-reply
                    - arp-poison
                    - arp-proxy
                    - netbios-ns
                    - netbios-ds
                    - ipv6
                    - all-other-mc
                    - all-other-bc
            captive_portal_ac_name:
                description:
                    - Local-bridging captive portal ac-name.
                type: str
            captive_portal_macauth_radius_secret:
                description:
                    - Secret key to access the macauth RADIUS server.
                type: str
            captive_portal_macauth_radius_server:
                description:
                    - Captive portal external RADIUS server domain name or IP address.
                type: str
            captive_portal_radius_secret:
                description:
                    - Secret key to access the RADIUS server.
                type: str
            captive_portal_radius_server:
                description:
                    - Captive portal RADIUS server domain name or IP address.
                type: str
            captive_portal_session_timeout_interval:
                description:
                    - Session timeout interval (0 - 864000 sec).
                type: int
            dhcp_lease_time:
                description:
                    - DHCP lease time in seconds for NAT IP address.
                type: int
            dhcp_option82_circuit_id_insertion:
                description:
                    - Enable/disable DHCP option 82 circuit-id insert .
                type: str
                choices:
                    - style-1
                    - style-2
                    - disable
            dhcp_option82_insertion:
                description:
                    - Enable/disable DHCP option 82 insert .
                type: str
                choices:
                    - enable
                    - disable
            dhcp_option82_remote_id_insertion:
                description:
                    - Enable/disable DHCP option 82 remote-id insert .
                type: str
                choices:
                    - style-1
                    - disable
            dynamic_vlan:
                description:
                    - Enable/disable dynamic VLAN assignment.
                type: str
                choices:
                    - enable
                    - disable
            eap_reauth:
                description:
                    - Enable/disable EAP re-authentication for WPA-Enterprise security.
                type: str
                choices:
                    - enable
                    - disable
            eap_reauth_intv:
                description:
                    - EAP re-authentication interval (1800 - 864000 sec).
                type: int
            eapol_key_retries:
                description:
                    - Enable/disable retransmission of EAPOL-Key frames (message 3/4 and group message 1/2) .
                type: str
                choices:
                    - disable
                    - enable
            encrypt:
                description:
                    - Encryption protocol to use (only available when security is set to a WPA type).
                type: str
                choices:
                    - TKIP
                    - AES
                    - TKIP-AES
            external_fast_roaming:
                description:
                    - Enable/disable fast roaming or pre-authentication with external APs not managed by the FortiGate .
                type: str
                choices:
                    - enable
                    - disable
            external_logout:
                description:
                    - URL of external authentication logout server.
                type: str
            external_web:
                description:
                    - URL of external authentication web server.
                type: str
            fast_bss_transition:
                description:
                    - Enable/disable 802.11r Fast BSS Transition (FT) .
                type: str
                choices:
                    - disable
                    - enable
            fast_roaming:
                description:
                    - Enable/disable fast-roaming, or pre-authentication, where supported by clients .
                type: str
                choices:
                    - enable
                    - disable
            ft_mobility_domain:
                description:
                    - Mobility domain identifier in FT (1 - 65535).
                type: int
            ft_over_ds:
                description:
                    - Enable/disable FT over the Distribution System (DS).
                type: str
                choices:
                    - disable
                    - enable
            ft_r0_key_lifetime:
                description:
                    - Lifetime of the PMK-R0 key in FT, 1-65535 minutes.
                type: int
            gtk_rekey:
                description:
                    - Enable/disable GTK rekey for WPA security.
                type: str
                choices:
                    - enable
                    - disable
            gtk_rekey_intv:
                description:
                    - GTK rekey interval (1800 - 864000 sec).
                type: int
            hotspot20_profile:
                description:
                    - Hotspot 2.0 profile name.
                type: str
            intra_vap_privacy:
                description:
                    - Enable/disable blocking communication between clients on the same SSID (called intra-SSID privacy) .
                type: str
                choices:
                    - enable
                    - disable
            ip:
                description:
                    - IP address and subnet mask for the local standalone NAT subnet.
                type: str
            key:
                description:
                    - WEP Key.
                type: str
            keyindex:
                description:
                    - WEP key index (1 - 4).
                type: int
            ldpc:
                description:
                    - VAP low-density parity-check (LDPC) coding configuration.
                type: str
                choices:
                    - disable
                    - rx
                    - tx
                    - rxtx
            local_authentication:
                description:
                    - Enable/disable AP local authentication.
                type: str
                choices:
                    - enable
                    - disable
            local_bridging:
                description:
                    - Enable/disable bridging of wireless and Ethernet interfaces on the FortiAP .
                type: str
                choices:
                    - enable
                    - disable
            local_lan:
                description:
                    - Allow/deny traffic destined for a Class A, B, or C private IP address .
                type: str
                choices:
                    - allow
                    - deny
            local_standalone:
                description:
                    - Enable/disable AP local standalone .
                type: str
                choices:
                    - enable
                    - disable
            local_standalone_nat:
                description:
                    - Enable/disable AP local standalone NAT mode.
                type: str
                choices:
                    - enable
                    - disable
            mac_auth_bypass:
                description:
                    - Enable/disable MAC authentication bypass.
                type: str
                choices:
                    - enable
                    - disable
            mac_filter:
                description:
                    - Enable/disable MAC filtering to block wireless clients by mac address.
                type: str
                choices:
                    - enable
                    - disable
            mac_filter_list:
                description:
                    - Create a list of MAC addresses for MAC address filtering.
                type: list
                suboptions:
                    id:
                        description:
                            - ID.
                        required: true
                        type: int
                    mac:
                        description:
                            - MAC address.
                        type: str
                    mac_filter_policy:
                        description:
                            - Deny or allow the client with this MAC address.
                        type: str
                        choices:
                            - allow
                            - deny
            mac_filter_policy_other:
                description:
                    - Allow or block clients with MAC addresses that are not in the filter list.
                type: str
                choices:
                    - allow
                    - deny
            max_clients:
                description:
                    - Maximum number of clients that can connect simultaneously to the VAP .
                type: int
            max_clients_ap:
                description:
                    - Maximum number of clients that can connect simultaneously to each radio .
                type: int
            me_disable_thresh:
                description:
                    - Disable multicast enhancement when this many clients are receiving multicast traffic.
                type: int
            mesh_backhaul:
                description:
                    - Enable/disable using this VAP as a WiFi mesh backhaul . This entry is only available when security is set to a WPA type or open.
                type: str
                choices:
                    - enable
                    - disable
            mpsk:
                description:
                    - Enable/disable multiple pre-shared keys (PSKs.)
                type: str
                choices:
                    - enable
                    - disable
            mpsk_concurrent_clients:
                description:
                    - Number of pre-shared keys (PSKs) to allow if multiple pre-shared keys are enabled.
                type: int
            mpsk_key:
                description:
                    - Pre-shared keys that can be used to connect to this virtual access point.
                type: list
                suboptions:
                    comment:
                        description:
                            - Comment.
                        type: str
                    concurrent_clients:
                        description:
                            - Number of clients that can connect using this pre-shared key.
                        type: str
                    key_name:
                        description:
                            - Pre-shared key name.
                        type: str
                    passphrase:
                        description:
                            - WPA Pre-shared key.
                        type: str
            multicast_enhance:
                description:
                    - Enable/disable converting multicast to unicast to improve performance .
                type: str
                choices:
                    - enable
                    - disable
            multicast_rate:
                description:
                    - Multicast rate (0, 6000, 12000, or 24000 kbps).
                type: str
                choices:
                    - 0
                    - 6000
                    - 12000
                    - 24000
            name:
                description:
                    - Virtual AP name.
                required: true
                type: str
            okc:
                description:
                    - Enable/disable Opportunistic Key Caching (OKC) .
                type: str
                choices:
                    - disable
                    - enable
            passphrase:
                description:
                    - WPA pre-shard key (PSK) to be used to authenticate WiFi users.
                type: str
            pmf:
                description:
                    - Protected Management Frames (PMF) support .
                type: str
                choices:
                    - disable
                    - enable
                    - optional
            pmf_assoc_comeback_timeout:
                description:
                    - Protected Management Frames (PMF) comeback maximum timeout (1-20 sec).
                type: int
            pmf_sa_query_retry_timeout:
                description:
                    - Protected Management Frames (PMF) SA query retry timeout interval (1 - 5 100s of msec).
                type: int
            portal_message_override_group:
                description:
                    - Replacement message group for this VAP (only available when security is set to a captive portal type).
                type: str
            portal_message_overrides:
                description:
                    - Individual message overrides.
                type: dict
                suboptions:
                    auth_disclaimer_page:
                        description:
                            - Override auth-disclaimer-page message with message from portal-message-overrides group.
                        type: str
                    auth_login_failed_page:
                        description:
                            - Override auth-login-failed-page message with message from portal-message-overrides group.
                        type: str
                    auth_login_page:
                        description:
                            - Override auth-login-page message with message from portal-message-overrides group.
                        type: str
                    auth_reject_page:
                        description:
                            - Override auth-reject-page message with message from portal-message-overrides group.
                        type: str
            portal_type:
                description:
                    - Captive portal functionality. Configure how the captive portal authenticates users and whether it includes a disclaimer.
                type: str
                choices:
                    - auth
                    - auth+disclaimer
                    - disclaimer
                    - email-collect
                    - cmcc
                    - cmcc-macauth
                    - auth-mac
            probe_resp_suppression:
                description:
                    - Enable/disable probe response suppression (to ignore weak signals) .
                type: str
                choices:
                    - enable
                    - disable
            probe_resp_threshold:
                description:
                    - Minimum signal level/threshold in dBm required for the AP response to probe requests (-95 to -20).
                type: str
            ptk_rekey:
                description:
                    - Enable/disable PTK rekey for WPA-Enterprise security.
                type: str
                choices:
                    - enable
                    - disable
            ptk_rekey_intv:
                description:
                    - PTK rekey interval (1800 - 864000 sec).
                type: int
            qos_profile:
                description:
                    - Quality of service profile name.
                type: str
            quarantine:
                description:
                    - Enable/disable station quarantine .
                type: str
                choices:
                    - enable
                    - disable
            radio_2g_threshold:
                description:
                    - Minimum signal level/threshold in dBm required for the AP response to receive a packet in 2.4G band (-95 to -20).
                type: str
            radio_5g_threshold:
                description:
                    - Minimum signal level/threshold in dBm required for the AP response to receive a packet in 5G band(-95 to -20).
                type: str
            radio_sensitivity:
                description:
                    - Enable/disable software radio sensitivity (to ignore weak signals) .
                type: str
                choices:
                    - enable
                    - disable
            radius_mac_auth:
                description:
                    - Enable/disable RADIUS-based MAC authentication of clients .
                type: str
                choices:
                    - enable
                    - disable
            radius_mac_auth_server:
                description:
                    - RADIUS-based MAC authentication server.
                type: str
            radius_mac_auth_usergroups:
                description:
                    - Selective user groups that are permitted for RADIUS mac authentication.
                type: list
                suboptions:
                    name:
                        description:
                            - User group name.
                        required: true
                        type: str
            radius_server:
                description:
                    - RADIUS server to be used to authenticate WiFi users.
                type: str
            rates_11a:
                description:
                    - Allowed data rates for 802.11a.
                type: str
                choices:
                    - 1
                    - 1-basic
                    - 2
                    - 2-basic
                    - 5.5
                    - 5.5-basic
                    - 11
                    - 11-basic
                    - 6
                    - 6-basic
                    - 9
                    - 9-basic
                    - 12
                    - 12-basic
                    - 18
                    - 18-basic
                    - 24
                    - 24-basic
                    - 36
                    - 36-basic
                    - 48
                    - 48-basic
                    - 54
                    - 54-basic
            rates_11ac_ss12:
                description:
                    - Allowed data rates for 802.11ac with 1 or 2 spatial streams.
                type: str
                choices:
                    - mcs0/1
                    - mcs1/1
                    - mcs2/1
                    - mcs3/1
                    - mcs4/1
                    - mcs5/1
                    - mcs6/1
                    - mcs7/1
                    - mcs8/1
                    - mcs9/1
                    - mcs10/1
                    - mcs11/1
                    - mcs0/2
                    - mcs1/2
                    - mcs2/2
                    - mcs3/2
                    - mcs4/2
                    - mcs5/2
                    - mcs6/2
                    - mcs7/2
                    - mcs8/2
                    - mcs9/2
                    - mcs10/2
                    - mcs11/2
            rates_11ac_ss34:
                description:
                    - Allowed data rates for 802.11ac with 3 or 4 spatial streams.
                type: str
                choices:
                    - mcs0/3
                    - mcs1/3
                    - mcs2/3
                    - mcs3/3
                    - mcs4/3
                    - mcs5/3
                    - mcs6/3
                    - mcs7/3
                    - mcs8/3
                    - mcs9/3
                    - mcs10/3
                    - mcs11/3
                    - mcs0/4
                    - mcs1/4
                    - mcs2/4
                    - mcs3/4
                    - mcs4/4
                    - mcs5/4
                    - mcs6/4
                    - mcs7/4
                    - mcs8/4
                    - mcs9/4
                    - mcs10/4
                    - mcs11/4
            rates_11bg:
                description:
                    - Allowed data rates for 802.11b/g.
                type: str
                choices:
                    - 1
                    - 1-basic
                    - 2
                    - 2-basic
                    - 5.5
                    - 5.5-basic
                    - 11
                    - 11-basic
                    - 6
                    - 6-basic
                    - 9
                    - 9-basic
                    - 12
                    - 12-basic
                    - 18
                    - 18-basic
                    - 24
                    - 24-basic
                    - 36
                    - 36-basic
                    - 48
                    - 48-basic
                    - 54
                    - 54-basic
            rates_11n_ss12:
                description:
                    - Allowed data rates for 802.11n with 1 or 2 spatial streams.
                type: str
                choices:
                    - mcs0/1
                    - mcs1/1
                    - mcs2/1
                    - mcs3/1
                    - mcs4/1
                    - mcs5/1
                    - mcs6/1
                    - mcs7/1
                    - mcs8/2
                    - mcs9/2
                    - mcs10/2
                    - mcs11/2
                    - mcs12/2
                    - mcs13/2
                    - mcs14/2
                    - mcs15/2
            rates_11n_ss34:
                description:
                    - Allowed data rates for 802.11n with 3 or 4 spatial streams.
                type: str
                choices:
                    - mcs16/3
                    - mcs17/3
                    - mcs18/3
                    - mcs19/3
                    - mcs20/3
                    - mcs21/3
                    - mcs22/3
                    - mcs23/3
                    - mcs24/4
                    - mcs25/4
                    - mcs26/4
                    - mcs27/4
                    - mcs28/4
                    - mcs29/4
                    - mcs30/4
                    - mcs31/4
            schedule:
                description:
                    - VAP schedule name.
                type: str
            security:
                description:
                    - Security mode for the wireless interface .
                type: str
                choices:
                    - open
                    - captive-portal
                    - wep64
                    - wep128
                    - wpa-personal
                    - wpa-personal+captive-portal
                    - wpa-enterprise
                    - wpa-only-personal
                    - wpa-only-personal+captive-portal
                    - wpa-only-enterprise
                    - wpa2-only-personal
                    - wpa2-only-personal+captive-portal
                    - wpa2-only-enterprise
                    - osen
            security_exempt_list:
                description:
                    - Optional security exempt list for captive portal authentication.
                type: str
            security_obsolete_option:
                description:
                    - Enable/disable obsolete security options.
                type: str
                choices:
                    - enable
                    - disable
            security_redirect_url:
                description:
                    - Optional URL for redirecting users after they pass captive portal authentication.
                type: str
            selected_usergroups:
                description:
                    - Selective user groups that are permitted to authenticate.
                type: list
                suboptions:
                    name:
                        description:
                            - User group name.
                        required: true
                        type: str
            split_tunneling:
                description:
                    - Enable/disable split tunneling .
                type: str
                choices:
                    - enable
                    - disable
            ssid:
                description:
                    - IEEE 802.11 service set identifier (SSID) for the wireless interface. Users who wish to use the wireless network must configure their
                       computers to access this SSID name.
                type: str
            tkip_counter_measure:
                description:
                    - Enable/disable TKIP counter measure.
                type: str
                choices:
                    - enable
                    - disable
            usergroup:
                description:
                    - Firewall user group to be used to authenticate WiFi users.
                type: list
                suboptions:
                    name:
                        description:
                            - User group name.
                        required: true
                        type: str
            utm_profile:
                description:
                    - UTM profile name.
                type: str
            vdom:
                description:
                    - Name of the VDOM that the Virtual AP has been added to. Source system.vdom.name.
                type: str
            vlan_auto:
                description:
                    - Enable/disable automatic management of SSID VLAN interface.
                type: str
                choices:
                    - enable
                    - disable
            vlan_pool:
                description:
                    - VLAN pool.
                type: list
                suboptions:
                    id:
                        description:
                            - ID.
                        required: true
                        type: int
                    wtp_group:
                        description:
                            - WTP group name.
                        type: str
            vlan_pooling:
                description:
                    - Enable/disable VLAN pooling, to allow grouping of multiple wireless controller VLANs into VLAN pools . When set to wtp-group, VLAN
                       pooling occurs with VLAN assignment by wtp-group.
                type: str
                choices:
                    - wtp-group
                    - round-robin
                    - hash
                    - disable
            vlanid:
                description:
                    - Optional VLAN ID.
                type: int
            voice_enterprise:
                description:
                    - Enable/disable 802.11k and 802.11v assisted Voice-Enterprise roaming .
                type: str
                choices:
                    - disable
                    - enable
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
  - name: Configure Virtual Access Points (VAPs).
    fortios_wireless_controller_vap:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      wireless_controller_vap:
        acct_interim_interval: "3"
        alias: "<your_own_value>"
        auth: "psk"
        broadcast_ssid: "enable"
        broadcast_suppression: "dhcp-up"
        captive_portal_ac_name: "<your_own_value>"
        captive_portal_macauth_radius_secret: "<your_own_value>"
        captive_portal_macauth_radius_server: "<your_own_value>"
        captive_portal_radius_secret: "<your_own_value>"
        captive_portal_radius_server: "<your_own_value>"
        captive_portal_session_timeout_interval: "13"
        dhcp_lease_time: "14"
        dhcp_option82_circuit_id_insertion: "style-1"
        dhcp_option82_insertion: "enable"
        dhcp_option82_remote_id_insertion: "style-1"
        dynamic_vlan: "enable"
        eap_reauth: "enable"
        eap_reauth_intv: "20"
        eapol_key_retries: "disable"
        encrypt: "TKIP"
        external_fast_roaming: "enable"
        external_logout: "<your_own_value>"
        external_web: "<your_own_value>"
        fast_bss_transition: "disable"
        fast_roaming: "enable"
        ft_mobility_domain: "28"
        ft_over_ds: "disable"
        ft_r0_key_lifetime: "30"
        gtk_rekey: "enable"
        gtk_rekey_intv: "32"
        hotspot20_profile: "<your_own_value>"
        intra_vap_privacy: "enable"
        ip: "<your_own_value>"
        key: "<your_own_value>"
        keyindex: "37"
        ldpc: "disable"
        local_authentication: "enable"
        local_bridging: "enable"
        local_lan: "allow"
        local_standalone: "enable"
        local_standalone_nat: "enable"
        mac_auth_bypass: "enable"
        mac_filter: "enable"
        mac_filter_list:
         -
            id:  "47"
            mac: "<your_own_value>"
            mac_filter_policy: "allow"
        mac_filter_policy_other: "allow"
        max_clients: "51"
        max_clients_ap: "52"
        me_disable_thresh: "53"
        mesh_backhaul: "enable"
        mpsk: "enable"
        mpsk_concurrent_clients: "56"
        mpsk_key:
         -
            comment: "Comment."
            concurrent_clients: "<your_own_value>"
            key_name: "<your_own_value>"
            passphrase: "<your_own_value>"
        multicast_enhance: "enable"
        multicast_rate: "0"
        name: "default_name_64"
        okc: "disable"
        passphrase: "<your_own_value>"
        pmf: "disable"
        pmf_assoc_comeback_timeout: "68"
        pmf_sa_query_retry_timeout: "69"
        portal_message_override_group: "<your_own_value>"
        portal_message_overrides:
            auth_disclaimer_page: "<your_own_value>"
            auth_login_failed_page: "<your_own_value>"
            auth_login_page: "<your_own_value>"
            auth_reject_page: "<your_own_value>"
        portal_type: "auth"
        probe_resp_suppression: "enable"
        probe_resp_threshold: "<your_own_value>"
        ptk_rekey: "enable"
        ptk_rekey_intv: "80"
        qos_profile: "<your_own_value>"
        quarantine: "enable"
        radio_2g_threshold: "<your_own_value>"
        radio_5g_threshold: "<your_own_value>"
        radio_sensitivity: "enable"
        radius_mac_auth: "enable"
        radius_mac_auth_server: "<your_own_value>"
        radius_mac_auth_usergroups:
         -
            name: "default_name_89"
        radius_server: "<your_own_value>"
        rates_11a: "1"
        rates_11ac_ss12: "mcs0/1"
        rates_11ac_ss34: "mcs0/3"
        rates_11bg: "1"
        rates_11n_ss12: "mcs0/1"
        rates_11n_ss34: "mcs16/3"
        schedule: "<your_own_value>"
        security: "open"
        security_exempt_list: "<your_own_value>"
        security_obsolete_option: "enable"
        security_redirect_url: "<your_own_value>"
        selected_usergroups:
         -
            name: "default_name_103"
        split_tunneling: "enable"
        ssid: "<your_own_value>"
        tkip_counter_measure: "enable"
        usergroup:
         -
            name: "default_name_108"
        utm_profile: "<your_own_value>"
        vdom: "<your_own_value> (source system.vdom.name)"
        vlan_auto: "enable"
        vlan_pool:
         -
            id:  "113"
            wtp_group: "<your_own_value>"
        vlan_pooling: "wtp-group"
        vlanid: "116"
        voice_enterprise: "disable"
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


def filter_wireless_controller_vap_data(json):
    option_list = ['acct_interim_interval', 'alias', 'auth',
                   'broadcast_ssid', 'broadcast_suppression', 'captive_portal_ac_name',
                   'captive_portal_macauth_radius_secret', 'captive_portal_macauth_radius_server', 'captive_portal_radius_secret',
                   'captive_portal_radius_server', 'captive_portal_session_timeout_interval', 'dhcp_lease_time',
                   'dhcp_option82_circuit_id_insertion', 'dhcp_option82_insertion', 'dhcp_option82_remote_id_insertion',
                   'dynamic_vlan', 'eap_reauth', 'eap_reauth_intv',
                   'eapol_key_retries', 'encrypt', 'external_fast_roaming',
                   'external_logout', 'external_web', 'fast_bss_transition',
                   'fast_roaming', 'ft_mobility_domain', 'ft_over_ds',
                   'ft_r0_key_lifetime', 'gtk_rekey', 'gtk_rekey_intv',
                   'hotspot20_profile', 'intra_vap_privacy', 'ip',
                   'key', 'keyindex', 'ldpc',
                   'local_authentication', 'local_bridging', 'local_lan',
                   'local_standalone', 'local_standalone_nat', 'mac_auth_bypass',
                   'mac_filter', 'mac_filter_list', 'mac_filter_policy_other',
                   'max_clients', 'max_clients_ap', 'me_disable_thresh',
                   'mesh_backhaul', 'mpsk', 'mpsk_concurrent_clients',
                   'mpsk_key', 'multicast_enhance', 'multicast_rate',
                   'name', 'okc', 'passphrase',
                   'pmf', 'pmf_assoc_comeback_timeout', 'pmf_sa_query_retry_timeout',
                   'portal_message_override_group', 'portal_message_overrides', 'portal_type',
                   'probe_resp_suppression', 'probe_resp_threshold', 'ptk_rekey',
                   'ptk_rekey_intv', 'qos_profile', 'quarantine',
                   'radio_2g_threshold', 'radio_5g_threshold', 'radio_sensitivity',
                   'radius_mac_auth', 'radius_mac_auth_server', 'radius_mac_auth_usergroups',
                   'radius_server', 'rates_11a', 'rates_11ac_ss12',
                   'rates_11ac_ss34', 'rates_11bg', 'rates_11n_ss12',
                   'rates_11n_ss34', 'schedule', 'security',
                   'security_exempt_list', 'security_obsolete_option', 'security_redirect_url',
                   'selected_usergroups', 'split_tunneling', 'ssid',
                   'tkip_counter_measure', 'usergroup', 'utm_profile',
                   'vdom', 'vlan_auto', 'vlan_pool',
                   'vlan_pooling', 'vlanid', 'voice_enterprise']
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


def wireless_controller_vap(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['wireless_controller_vap'] and data['wireless_controller_vap']:
        state = data['wireless_controller_vap']['state']
    else:
        state = True
    wireless_controller_vap_data = data['wireless_controller_vap']
    filtered_data = underscore_to_hyphen(filter_wireless_controller_vap_data(wireless_controller_vap_data))

    if state == "present":
        return fos.set('wireless-controller',
                       'vap',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('wireless-controller',
                          'vap',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_wireless_controller(data, fos):

    if data['wireless_controller_vap']:
        resp = wireless_controller_vap(data, fos)

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
        "state": {"required": False, "type": "str",
                  "choices": ["present", "absent"]},
        "wireless_controller_vap": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "acct_interim_interval": {"required": False, "type": "int"},
                "alias": {"required": False, "type": "str"},
                "auth": {"required": False, "type": "str",
                         "choices": ["psk", "radius", "usergroup"]},
                "broadcast_ssid": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "broadcast_suppression": {"required": False, "type": "str",
                                          "choices": ["dhcp-up", "dhcp-down", "dhcp-starvation",
                                                      "arp-known", "arp-unknown", "arp-reply",
                                                      "arp-poison", "arp-proxy", "netbios-ns",
                                                      "netbios-ds", "ipv6", "all-other-mc",
                                                      "all-other-bc"]},
                "captive_portal_ac_name": {"required": False, "type": "str"},
                "captive_portal_macauth_radius_secret": {"required": False, "type": "str"},
                "captive_portal_macauth_radius_server": {"required": False, "type": "str"},
                "captive_portal_radius_secret": {"required": False, "type": "str"},
                "captive_portal_radius_server": {"required": False, "type": "str"},
                "captive_portal_session_timeout_interval": {"required": False, "type": "int"},
                "dhcp_lease_time": {"required": False, "type": "int"},
                "dhcp_option82_circuit_id_insertion": {"required": False, "type": "str",
                                                       "choices": ["style-1", "style-2", "disable"]},
                "dhcp_option82_insertion": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                "dhcp_option82_remote_id_insertion": {"required": False, "type": "str",
                                                      "choices": ["style-1", "disable"]},
                "dynamic_vlan": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "eap_reauth": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "eap_reauth_intv": {"required": False, "type": "int"},
                "eapol_key_retries": {"required": False, "type": "str",
                                      "choices": ["disable", "enable"]},
                "encrypt": {"required": False, "type": "str",
                            "choices": ["TKIP", "AES", "TKIP-AES"]},
                "external_fast_roaming": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "external_logout": {"required": False, "type": "str"},
                "external_web": {"required": False, "type": "str"},
                "fast_bss_transition": {"required": False, "type": "str",
                                        "choices": ["disable", "enable"]},
                "fast_roaming": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "ft_mobility_domain": {"required": False, "type": "int"},
                "ft_over_ds": {"required": False, "type": "str",
                               "choices": ["disable", "enable"]},
                "ft_r0_key_lifetime": {"required": False, "type": "int"},
                "gtk_rekey": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "gtk_rekey_intv": {"required": False, "type": "int"},
                "hotspot20_profile": {"required": False, "type": "str"},
                "intra_vap_privacy": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "ip": {"required": False, "type": "str"},
                "key": {"required": False, "type": "str"},
                "keyindex": {"required": False, "type": "int"},
                "ldpc": {"required": False, "type": "str",
                         "choices": ["disable", "rx", "tx",
                                     "rxtx"]},
                "local_authentication": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "local_bridging": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "local_lan": {"required": False, "type": "str",
                              "choices": ["allow", "deny"]},
                "local_standalone": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "local_standalone_nat": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "mac_auth_bypass": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "mac_filter": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "mac_filter_list": {"required": False, "type": "list",
                                    "options": {
                                        "id": {"required": True, "type": "int"},
                                        "mac": {"required": False, "type": "str"},
                                        "mac_filter_policy": {"required": False, "type": "str",
                                                              "choices": ["allow", "deny"]}
                                    }},
                "mac_filter_policy_other": {"required": False, "type": "str",
                                            "choices": ["allow", "deny"]},
                "max_clients": {"required": False, "type": "int"},
                "max_clients_ap": {"required": False, "type": "int"},
                "me_disable_thresh": {"required": False, "type": "int"},
                "mesh_backhaul": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "mpsk": {"required": False, "type": "str",
                         "choices": ["enable", "disable"]},
                "mpsk_concurrent_clients": {"required": False, "type": "int"},
                "mpsk_key": {"required": False, "type": "list",
                             "options": {
                                 "comment": {"required": False, "type": "str"},
                                 "concurrent_clients": {"required": False, "type": "str"},
                                 "key_name": {"required": False, "type": "str"},
                                 "passphrase": {"required": False, "type": "str"}
                             }},
                "multicast_enhance": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "multicast_rate": {"required": False, "type": "str",
                                   "choices": ["0", "6000", "12000",
                                               "24000"]},
                "name": {"required": True, "type": "str"},
                "okc": {"required": False, "type": "str",
                        "choices": ["disable", "enable"]},
                "passphrase": {"required": False, "type": "str"},
                "pmf": {"required": False, "type": "str",
                        "choices": ["disable", "enable", "optional"]},
                "pmf_assoc_comeback_timeout": {"required": False, "type": "int"},
                "pmf_sa_query_retry_timeout": {"required": False, "type": "int"},
                "portal_message_override_group": {"required": False, "type": "str"},
                "portal_message_overrides": {"required": False, "type": "dict",
                                             "options": {
                                                 "auth_disclaimer_page": {"required": False, "type": "str"},
                                                 "auth_login_failed_page": {"required": False, "type": "str"},
                                                 "auth_login_page": {"required": False, "type": "str"},
                                                 "auth_reject_page": {"required": False, "type": "str"}
                                             }},
                "portal_type": {"required": False, "type": "str",
                                "choices": ["auth", "auth+disclaimer", "disclaimer",
                                            "email-collect", "cmcc", "cmcc-macauth",
                                            "auth-mac"]},
                "probe_resp_suppression": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "probe_resp_threshold": {"required": False, "type": "str"},
                "ptk_rekey": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "ptk_rekey_intv": {"required": False, "type": "int"},
                "qos_profile": {"required": False, "type": "str"},
                "quarantine": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "radio_2g_threshold": {"required": False, "type": "str"},
                "radio_5g_threshold": {"required": False, "type": "str"},
                "radio_sensitivity": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "radius_mac_auth": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "radius_mac_auth_server": {"required": False, "type": "str"},
                "radius_mac_auth_usergroups": {"required": False, "type": "list",
                                               "options": {
                                                   "name": {"required": True, "type": "str"}
                                               }},
                "radius_server": {"required": False, "type": "str"},
                "rates_11a": {"required": False, "type": "str",
                              "choices": ["1", "1-basic", "2",
                                          "2-basic", "5.5", "5.5-basic",
                                          "11", "11-basic", "6",
                                          "6-basic", "9", "9-basic",
                                          "12", "12-basic", "18",
                                          "18-basic", "24", "24-basic",
                                          "36", "36-basic", "48",
                                          "48-basic", "54", "54-basic"]},
                "rates_11ac_ss12": {"required": False, "type": "str",
                                    "choices": ["mcs0/1", "mcs1/1", "mcs2/1",
                                                "mcs3/1", "mcs4/1", "mcs5/1",
                                                "mcs6/1", "mcs7/1", "mcs8/1",
                                                "mcs9/1", "mcs10/1", "mcs11/1",
                                                "mcs0/2", "mcs1/2", "mcs2/2",
                                                "mcs3/2", "mcs4/2", "mcs5/2",
                                                "mcs6/2", "mcs7/2", "mcs8/2",
                                                "mcs9/2", "mcs10/2", "mcs11/2"]},
                "rates_11ac_ss34": {"required": False, "type": "str",
                                    "choices": ["mcs0/3", "mcs1/3", "mcs2/3",
                                                "mcs3/3", "mcs4/3", "mcs5/3",
                                                "mcs6/3", "mcs7/3", "mcs8/3",
                                                "mcs9/3", "mcs10/3", "mcs11/3",
                                                "mcs0/4", "mcs1/4", "mcs2/4",
                                                "mcs3/4", "mcs4/4", "mcs5/4",
                                                "mcs6/4", "mcs7/4", "mcs8/4",
                                                "mcs9/4", "mcs10/4", "mcs11/4"]},
                "rates_11bg": {"required": False, "type": "str",
                               "choices": ["1", "1-basic", "2",
                                           "2-basic", "5.5", "5.5-basic",
                                           "11", "11-basic", "6",
                                           "6-basic", "9", "9-basic",
                                           "12", "12-basic", "18",
                                           "18-basic", "24", "24-basic",
                                           "36", "36-basic", "48",
                                           "48-basic", "54", "54-basic"]},
                "rates_11n_ss12": {"required": False, "type": "str",
                                   "choices": ["mcs0/1", "mcs1/1", "mcs2/1",
                                               "mcs3/1", "mcs4/1", "mcs5/1",
                                               "mcs6/1", "mcs7/1", "mcs8/2",
                                               "mcs9/2", "mcs10/2", "mcs11/2",
                                               "mcs12/2", "mcs13/2", "mcs14/2",
                                               "mcs15/2"]},
                "rates_11n_ss34": {"required": False, "type": "str",
                                   "choices": ["mcs16/3", "mcs17/3", "mcs18/3",
                                               "mcs19/3", "mcs20/3", "mcs21/3",
                                               "mcs22/3", "mcs23/3", "mcs24/4",
                                               "mcs25/4", "mcs26/4", "mcs27/4",
                                               "mcs28/4", "mcs29/4", "mcs30/4",
                                               "mcs31/4"]},
                "schedule": {"required": False, "type": "str"},
                "security": {"required": False, "type": "str",
                             "choices": ["open", "captive-portal", "wep64",
                                         "wep128", "wpa-personal", "wpa-personal+captive-portal",
                                         "wpa-enterprise", "wpa-only-personal", "wpa-only-personal+captive-portal",
                                         "wpa-only-enterprise", "wpa2-only-personal", "wpa2-only-personal+captive-portal",
                                         "wpa2-only-enterprise", "osen"]},
                "security_exempt_list": {"required": False, "type": "str"},
                "security_obsolete_option": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                "security_redirect_url": {"required": False, "type": "str"},
                "selected_usergroups": {"required": False, "type": "list",
                                        "options": {
                                            "name": {"required": True, "type": "str"}
                                        }},
                "split_tunneling": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "ssid": {"required": False, "type": "str"},
                "tkip_counter_measure": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "usergroup": {"required": False, "type": "list",
                              "options": {
                                  "name": {"required": True, "type": "str"}
                              }},
                "utm_profile": {"required": False, "type": "str"},
                "vdom": {"required": False, "type": "str"},
                "vlan_auto": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "vlan_pool": {"required": False, "type": "list",
                              "options": {
                                  "id": {"required": True, "type": "int"},
                                  "wtp_group": {"required": False, "type": "str"}
                              }},
                "vlan_pooling": {"required": False, "type": "str",
                                 "choices": ["wtp-group", "round-robin", "hash",
                                             "disable"]},
                "vlanid": {"required": False, "type": "int"},
                "voice_enterprise": {"required": False, "type": "str",
                                     "choices": ["disable", "enable"]}

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

            is_error, has_changed, result = fortios_wireless_controller(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_wireless_controller(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
