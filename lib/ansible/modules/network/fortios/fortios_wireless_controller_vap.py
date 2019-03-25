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
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify wireless_controller feature and vap category.
      Examples include all parameters and values need to be adjusted to datasources before usage.
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
            - FortiOS or FortiGate ip address.
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
    wireless_controller_vap:
        description:
            - Configure Virtual Access Points (VAPs).
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            acct-interim-interval:
                description:
                    - WiFi RADIUS accounting interim interval (60 - 86400 sec, default = 0).
            alias:
                description:
                    - Alias.
            auth:
                description:
                    - Authentication protocol.
                choices:
                    - psk
                    - radius
                    - usergroup
            broadcast-ssid:
                description:
                    - Enable/disable broadcasting the SSID (default = enable).
                choices:
                    - enable
                    - disable
            broadcast-suppression:
                description:
                    - Optional suppression of broadcast messages. For example, you can keep DHCP messages, ARP broadcasts, and so on off of the wireless
                       network.
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
            captive-portal-ac-name:
                description:
                    - Local-bridging captive portal ac-name.
            captive-portal-macauth-radius-secret:
                description:
                    - Secret key to access the macauth RADIUS server.
            captive-portal-macauth-radius-server:
                description:
                    - Captive portal external RADIUS server domain name or IP address.
            captive-portal-radius-secret:
                description:
                    - Secret key to access the RADIUS server.
            captive-portal-radius-server:
                description:
                    - Captive portal RADIUS server domain name or IP address.
            captive-portal-session-timeout-interval:
                description:
                    - Session timeout interval (0 - 864000 sec, default = 0).
            dhcp-lease-time:
                description:
                    - DHCP lease time in seconds for NAT IP address.
            dhcp-option82-circuit-id-insertion:
                description:
                    - Enable/disable DHCP option 82 circuit-id insert (default = disable).
                choices:
                    - style-1
                    - style-2
                    - disable
            dhcp-option82-insertion:
                description:
                    - Enable/disable DHCP option 82 insert (default = disable).
                choices:
                    - enable
                    - disable
            dhcp-option82-remote-id-insertion:
                description:
                    - Enable/disable DHCP option 82 remote-id insert (default = disable).
                choices:
                    - style-1
                    - disable
            dynamic-vlan:
                description:
                    - Enable/disable dynamic VLAN assignment.
                choices:
                    - enable
                    - disable
            eap-reauth:
                description:
                    - Enable/disable EAP re-authentication for WPA-Enterprise security.
                choices:
                    - enable
                    - disable
            eap-reauth-intv:
                description:
                    - EAP re-authentication interval (1800 - 864000 sec, default = 86400).
            eapol-key-retries:
                description:
                    - Enable/disable retransmission of EAPOL-Key frames (message 3/4 and group message 1/2) (default = enable).
                choices:
                    - disable
                    - enable
            encrypt:
                description:
                    - Encryption protocol to use (only available when security is set to a WPA type).
                choices:
                    - TKIP
                    - AES
                    - TKIP-AES
            external-fast-roaming:
                description:
                    - Enable/disable fast roaming or pre-authentication with external APs not managed by the FortiGate (default = disable).
                choices:
                    - enable
                    - disable
            external-logout:
                description:
                    - URL of external authentication logout server.
            external-web:
                description:
                    - URL of external authentication web server.
            fast-bss-transition:
                description:
                    - Enable/disable 802.11r Fast BSS Transition (FT) (default = disable).
                choices:
                    - disable
                    - enable
            fast-roaming:
                description:
                    - Enable/disable fast-roaming, or pre-authentication, where supported by clients (default = disable).
                choices:
                    - enable
                    - disable
            ft-mobility-domain:
                description:
                    - Mobility domain identifier in FT (1 - 65535, default = 1000).
            ft-over-ds:
                description:
                    - Enable/disable FT over the Distribution System (DS).
                choices:
                    - disable
                    - enable
            ft-r0-key-lifetime:
                description:
                    - Lifetime of the PMK-R0 key in FT, 1-65535 minutes.
            gtk-rekey:
                description:
                    - Enable/disable GTK rekey for WPA security.
                choices:
                    - enable
                    - disable
            gtk-rekey-intv:
                description:
                    - GTK rekey interval (1800 - 864000 sec, default = 86400).
            hotspot20-profile:
                description:
                    - Hotspot 2.0 profile name.
            intra-vap-privacy:
                description:
                    - Enable/disable blocking communication between clients on the same SSID (called intra-SSID privacy) (default = disable).
                choices:
                    - enable
                    - disable
            ip:
                description:
                    - IP address and subnet mask for the local standalone NAT subnet.
            key:
                description:
                    - WEP Key.
            keyindex:
                description:
                    - WEP key index (1 - 4).
            ldpc:
                description:
                    - VAP low-density parity-check (LDPC) coding configuration.
                choices:
                    - disable
                    - rx
                    - tx
                    - rxtx
            local-authentication:
                description:
                    - Enable/disable AP local authentication.
                choices:
                    - enable
                    - disable
            local-bridging:
                description:
                    - Enable/disable bridging of wireless and Ethernet interfaces on the FortiAP (default = disable).
                choices:
                    - enable
                    - disable
            local-lan:
                description:
                    - Allow/deny traffic destined for a Class A, B, or C private IP address (default = allow).
                choices:
                    - allow
                    - deny
            local-standalone:
                description:
                    - Enable/disable AP local standalone (default = disable).
                choices:
                    - enable
                    - disable
            local-standalone-nat:
                description:
                    - Enable/disable AP local standalone NAT mode.
                choices:
                    - enable
                    - disable
            mac-auth-bypass:
                description:
                    - Enable/disable MAC authentication bypass.
                choices:
                    - enable
                    - disable
            mac-filter:
                description:
                    - Enable/disable MAC filtering to block wireless clients by mac address.
                choices:
                    - enable
                    - disable
            mac-filter-list:
                description:
                    - Create a list of MAC addresses for MAC address filtering.
                suboptions:
                    id:
                        description:
                            - ID.
                        required: true
                    mac:
                        description:
                            - MAC address.
                    mac-filter-policy:
                        description:
                            - Deny or allow the client with this MAC address.
                        choices:
                            - allow
                            - deny
            mac-filter-policy-other:
                description:
                    - Allow or block clients with MAC addresses that are not in the filter list.
                choices:
                    - allow
                    - deny
            max-clients:
                description:
                    - Maximum number of clients that can connect simultaneously to the VAP (default = 0, meaning no limitation).
            max-clients-ap:
                description:
                    - Maximum number of clients that can connect simultaneously to each radio (default = 0, meaning no limitation).
            me-disable-thresh:
                description:
                    - Disable multicast enhancement when this many clients are receiving multicast traffic.
            mesh-backhaul:
                description:
                    - Enable/disable using this VAP as a WiFi mesh backhaul (default = disable). This entry is only available when security is set to a WPA
                       type or open.
                choices:
                    - enable
                    - disable
            mpsk:
                description:
                    - Enable/disable multiple pre-shared keys (PSKs.)
                choices:
                    - enable
                    - disable
            mpsk-concurrent-clients:
                description:
                    - Number of pre-shared keys (PSKs) to allow if multiple pre-shared keys are enabled.
            mpsk-key:
                description:
                    - Pre-shared keys that can be used to connect to this virtual access point.
                suboptions:
                    comment:
                        description:
                            - Comment.
                    concurrent-clients:
                        description:
                            - Number of clients that can connect using this pre-shared key.
                    key-name:
                        description:
                            - Pre-shared key name.
                        required: true
                    passphrase:
                        description:
                            - WPA Pre-shared key.
            multicast-enhance:
                description:
                    - Enable/disable converting multicast to unicast to improve performance (default = disable).
                choices:
                    - enable
                    - disable
            multicast-rate:
                description:
                    - Multicast rate (0, 6000, 12000, or 24000 kbps, default = 0).
                choices:
                    - 0
                    - 6000
                    - 12000
                    - 24000
            name:
                description:
                    - Virtual AP name.
                required: true
            okc:
                description:
                    - Enable/disable Opportunistic Key Caching (OKC) (default = enable).
                choices:
                    - disable
                    - enable
            passphrase:
                description:
                    - WPA pre-shard key (PSK) to be used to authenticate WiFi users.
            pmf:
                description:
                    - Protected Management Frames (PMF) support (default = disable).
                choices:
                    - disable
                    - enable
                    - optional
            pmf-assoc-comeback-timeout:
                description:
                    - Protected Management Frames (PMF) comeback maximum timeout (1-20 sec).
            pmf-sa-query-retry-timeout:
                description:
                    - Protected Management Frames (PMF) SA query retry timeout interval (1 - 5 100s of msec).
            portal-message-override-group:
                description:
                    - Replacement message group for this VAP (only available when security is set to a captive portal type).
            portal-message-overrides:
                description:
                    - Individual message overrides.
                suboptions:
                    auth-disclaimer-page:
                        description:
                            - Override auth-disclaimer-page message with message from portal-message-overrides group.
                    auth-login-failed-page:
                        description:
                            - Override auth-login-failed-page message with message from portal-message-overrides group.
                    auth-login-page:
                        description:
                            - Override auth-login-page message with message from portal-message-overrides group.
                    auth-reject-page:
                        description:
                            - Override auth-reject-page message with message from portal-message-overrides group.
            portal-type:
                description:
                    - Captive portal functionality. Configure how the captive portal authenticates users and whether it includes a disclaimer.
                choices:
                    - auth
                    - auth+disclaimer
                    - disclaimer
                    - email-collect
                    - cmcc
                    - cmcc-macauth
                    - auth-mac
            probe-resp-suppression:
                description:
                    - Enable/disable probe response suppression (to ignore weak signals) (default = disable).
                choices:
                    - enable
                    - disable
            probe-resp-threshold:
                description:
                    - Minimum signal level/threshold in dBm required for the AP response to probe requests (-95 to -20, default = -80).
            ptk-rekey:
                description:
                    - Enable/disable PTK rekey for WPA-Enterprise security.
                choices:
                    - enable
                    - disable
            ptk-rekey-intv:
                description:
                    - PTK rekey interval (1800 - 864000 sec, default = 86400).
            qos-profile:
                description:
                    - Quality of service profile name.
            quarantine:
                description:
                    - Enable/disable station quarantine (default = enable).
                choices:
                    - enable
                    - disable
            radio-2g-threshold:
                description:
                    - Minimum signal level/threshold in dBm required for the AP response to receive a packet in 2.4G band (-95 to -20, default = -79).
            radio-5g-threshold:
                description:
                    - Minimum signal level/threshold in dBm required for the AP response to receive a packet in 5G band(-95 to -20, default = -76).
            radio-sensitivity:
                description:
                    - Enable/disable software radio sensitivity (to ignore weak signals) (default = disable).
                choices:
                    - enable
                    - disable
            radius-mac-auth:
                description:
                    - Enable/disable RADIUS-based MAC authentication of clients (default = disable).
                choices:
                    - enable
                    - disable
            radius-mac-auth-server:
                description:
                    - RADIUS-based MAC authentication server.
            radius-mac-auth-usergroups:
                description:
                    - Selective user groups that are permitted for RADIUS mac authentication.
                suboptions:
                    name:
                        description:
                            - User group name.
                        required: true
            radius-server:
                description:
                    - RADIUS server to be used to authenticate WiFi users.
            rates-11a:
                description:
                    - Allowed data rates for 802.11a.
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
            rates-11ac-ss12:
                description:
                    - Allowed data rates for 802.11ac with 1 or 2 spatial streams.
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
            rates-11ac-ss34:
                description:
                    - Allowed data rates for 802.11ac with 3 or 4 spatial streams.
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
            rates-11bg:
                description:
                    - Allowed data rates for 802.11b/g.
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
            rates-11n-ss12:
                description:
                    - Allowed data rates for 802.11n with 1 or 2 spatial streams.
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
            rates-11n-ss34:
                description:
                    - Allowed data rates for 802.11n with 3 or 4 spatial streams.
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
            security:
                description:
                    - Security mode for the wireless interface (default = wpa2-only-personal).
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
            security-exempt-list:
                description:
                    - Optional security exempt list for captive portal authentication.
            security-obsolete-option:
                description:
                    - Enable/disable obsolete security options.
                choices:
                    - enable
                    - disable
            security-redirect-url:
                description:
                    - Optional URL for redirecting users after they pass captive portal authentication.
            selected-usergroups:
                description:
                    - Selective user groups that are permitted to authenticate.
                suboptions:
                    name:
                        description:
                            - User group name.
                        required: true
            split-tunneling:
                description:
                    - Enable/disable split tunneling (default = disable).
                choices:
                    - enable
                    - disable
            ssid:
                description:
                    - IEEE 802.11 service set identifier (SSID) for the wireless interface. Users who wish to use the wireless network must configure their
                       computers to access this SSID name.
            tkip-counter-measure:
                description:
                    - Enable/disable TKIP counter measure.
                choices:
                    - enable
                    - disable
            usergroup:
                description:
                    - Firewall user group to be used to authenticate WiFi users.
                suboptions:
                    name:
                        description:
                            - User group name.
                        required: true
            utm-profile:
                description:
                    - UTM profile name.
            vdom:
                description:
                    - Name of the VDOM that the Virtual AP has been added to. Source system.vdom.name.
            vlan-auto:
                description:
                    - Enable/disable automatic management of SSID VLAN interface.
                choices:
                    - enable
                    - disable
            vlan-pool:
                description:
                    - VLAN pool.
                suboptions:
                    id:
                        description:
                            - ID.
                        required: true
                    wtp-group:
                        description:
                            - WTP group name.
            vlan-pooling:
                description:
                    - Enable/disable VLAN pooling, to allow grouping of multiple wireless controller VLANs into VLAN pools (default = disable). When set to
                       wtp-group, VLAN pooling occurs with VLAN assignment by wtp-group.
                choices:
                    - wtp-group
                    - round-robin
                    - hash
                    - disable
            vlanid:
                description:
                    - Optional VLAN ID.
            voice-enterprise:
                description:
                    - Enable/disable 802.11k and 802.11v assisted Voice-Enterprise roaming (default = disable).
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
  tasks:
  - name: Configure Virtual Access Points (VAPs).
    fortios_wireless_controller_vap:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      wireless_controller_vap:
        state: "present"
        acct-interim-interval: "3"
        alias: "<your_own_value>"
        auth: "psk"
        broadcast-ssid: "enable"
        broadcast-suppression: "dhcp-up"
        captive-portal-ac-name: "<your_own_value>"
        captive-portal-macauth-radius-secret: "<your_own_value>"
        captive-portal-macauth-radius-server: "<your_own_value>"
        captive-portal-radius-secret: "<your_own_value>"
        captive-portal-radius-server: "<your_own_value>"
        captive-portal-session-timeout-interval: "13"
        dhcp-lease-time: "14"
        dhcp-option82-circuit-id-insertion: "style-1"
        dhcp-option82-insertion: "enable"
        dhcp-option82-remote-id-insertion: "style-1"
        dynamic-vlan: "enable"
        eap-reauth: "enable"
        eap-reauth-intv: "20"
        eapol-key-retries: "disable"
        encrypt: "TKIP"
        external-fast-roaming: "enable"
        external-logout: "<your_own_value>"
        external-web: "<your_own_value>"
        fast-bss-transition: "disable"
        fast-roaming: "enable"
        ft-mobility-domain: "28"
        ft-over-ds: "disable"
        ft-r0-key-lifetime: "30"
        gtk-rekey: "enable"
        gtk-rekey-intv: "32"
        hotspot20-profile: "<your_own_value>"
        intra-vap-privacy: "enable"
        ip: "<your_own_value>"
        key: "<your_own_value>"
        keyindex: "37"
        ldpc: "disable"
        local-authentication: "enable"
        local-bridging: "enable"
        local-lan: "allow"
        local-standalone: "enable"
        local-standalone-nat: "enable"
        mac-auth-bypass: "enable"
        mac-filter: "enable"
        mac-filter-list:
         -
            id:  "47"
            mac: "<your_own_value>"
            mac-filter-policy: "allow"
        mac-filter-policy-other: "allow"
        max-clients: "51"
        max-clients-ap: "52"
        me-disable-thresh: "53"
        mesh-backhaul: "enable"
        mpsk: "enable"
        mpsk-concurrent-clients: "56"
        mpsk-key:
         -
            comment: "Comment."
            concurrent-clients: "<your_own_value>"
            key-name: "<your_own_value>"
            passphrase: "<your_own_value>"
        multicast-enhance: "enable"
        multicast-rate: "0"
        name: "default_name_64"
        okc: "disable"
        passphrase: "<your_own_value>"
        pmf: "disable"
        pmf-assoc-comeback-timeout: "68"
        pmf-sa-query-retry-timeout: "69"
        portal-message-override-group: "<your_own_value>"
        portal-message-overrides:
            auth-disclaimer-page: "<your_own_value>"
            auth-login-failed-page: "<your_own_value>"
            auth-login-page: "<your_own_value>"
            auth-reject-page: "<your_own_value>"
        portal-type: "auth"
        probe-resp-suppression: "enable"
        probe-resp-threshold: "<your_own_value>"
        ptk-rekey: "enable"
        ptk-rekey-intv: "80"
        qos-profile: "<your_own_value>"
        quarantine: "enable"
        radio-2g-threshold: "<your_own_value>"
        radio-5g-threshold: "<your_own_value>"
        radio-sensitivity: "enable"
        radius-mac-auth: "enable"
        radius-mac-auth-server: "<your_own_value>"
        radius-mac-auth-usergroups:
         -
            name: "default_name_89"
        radius-server: "<your_own_value>"
        rates-11a: "1"
        rates-11ac-ss12: "mcs0/1"
        rates-11ac-ss34: "mcs0/3"
        rates-11bg: "1"
        rates-11n-ss12: "mcs0/1"
        rates-11n-ss34: "mcs16/3"
        schedule: "<your_own_value>"
        security: "open"
        security-exempt-list: "<your_own_value>"
        security-obsolete-option: "enable"
        security-redirect-url: "<your_own_value>"
        selected-usergroups:
         -
            name: "default_name_103"
        split-tunneling: "enable"
        ssid: "<your_own_value>"
        tkip-counter-measure: "enable"
        usergroup:
         -
            name: "default_name_108"
        utm-profile: "<your_own_value>"
        vdom: "<your_own_value> (source system.vdom.name)"
        vlan-auto: "enable"
        vlan-pool:
         -
            id:  "113"
            wtp-group: "<your_own_value>"
        vlan-pooling: "wtp-group"
        vlanid: "116"
        voice-enterprise: "disable"
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


def login(data, fos):
    host = data['host']
    username = data['username']
    password = data['password']

    fos.debug('on')
    if 'https' in data and not data['https']:
        fos.https('off')
    else:
        fos.https('on')

    fos.login(host, username, password)


def filter_wireless_controller_vap_data(json):
    option_list = ['acct-interim-interval', 'alias', 'auth',
                   'broadcast-ssid', 'broadcast-suppression', 'captive-portal-ac-name',
                   'captive-portal-macauth-radius-secret', 'captive-portal-macauth-radius-server', 'captive-portal-radius-secret',
                   'captive-portal-radius-server', 'captive-portal-session-timeout-interval', 'dhcp-lease-time',
                   'dhcp-option82-circuit-id-insertion', 'dhcp-option82-insertion', 'dhcp-option82-remote-id-insertion',
                   'dynamic-vlan', 'eap-reauth', 'eap-reauth-intv',
                   'eapol-key-retries', 'encrypt', 'external-fast-roaming',
                   'external-logout', 'external-web', 'fast-bss-transition',
                   'fast-roaming', 'ft-mobility-domain', 'ft-over-ds',
                   'ft-r0-key-lifetime', 'gtk-rekey', 'gtk-rekey-intv',
                   'hotspot20-profile', 'intra-vap-privacy', 'ip',
                   'key', 'keyindex', 'ldpc',
                   'local-authentication', 'local-bridging', 'local-lan',
                   'local-standalone', 'local-standalone-nat', 'mac-auth-bypass',
                   'mac-filter', 'mac-filter-list', 'mac-filter-policy-other',
                   'max-clients', 'max-clients-ap', 'me-disable-thresh',
                   'mesh-backhaul', 'mpsk', 'mpsk-concurrent-clients',
                   'mpsk-key', 'multicast-enhance', 'multicast-rate',
                   'name', 'okc', 'passphrase',
                   'pmf', 'pmf-assoc-comeback-timeout', 'pmf-sa-query-retry-timeout',
                   'portal-message-override-group', 'portal-message-overrides', 'portal-type',
                   'probe-resp-suppression', 'probe-resp-threshold', 'ptk-rekey',
                   'ptk-rekey-intv', 'qos-profile', 'quarantine',
                   'radio-2g-threshold', 'radio-5g-threshold', 'radio-sensitivity',
                   'radius-mac-auth', 'radius-mac-auth-server', 'radius-mac-auth-usergroups',
                   'radius-server', 'rates-11a', 'rates-11ac-ss12',
                   'rates-11ac-ss34', 'rates-11bg', 'rates-11n-ss12',
                   'rates-11n-ss34', 'schedule', 'security',
                   'security-exempt-list', 'security-obsolete-option', 'security-redirect-url',
                   'selected-usergroups', 'split-tunneling', 'ssid',
                   'tkip-counter-measure', 'usergroup', 'utm-profile',
                   'vdom', 'vlan-auto', 'vlan-pool',
                   'vlan-pooling', 'vlanid', 'voice-enterprise']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def flatten_multilists_attributes(data):
    multilist_attrs = []

    for attr in multilist_attrs:
        try:
            path = "data['" + "']['".join(elem for elem in attr) + "']"
            current_val = eval(path)
            flattened_val = ' '.join(elem for elem in current_val)
            exec(path + '= flattened_val')
        except BaseException:
            pass

    return data


def wireless_controller_vap(data, fos):
    vdom = data['vdom']
    wireless_controller_vap_data = data['wireless_controller_vap']
    flattened_data = flatten_multilists_attributes(wireless_controller_vap_data)
    filtered_data = filter_wireless_controller_vap_data(flattened_data)
    if wireless_controller_vap_data['state'] == "present":
        return fos.set('wireless-controller',
                       'vap',
                       data=filtered_data,
                       vdom=vdom)

    elif wireless_controller_vap_data['state'] == "absent":
        return fos.delete('wireless-controller',
                          'vap',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_wireless_controller(data, fos):
    login(data, fos)

    if data['wireless_controller_vap']:
        resp = wireless_controller_vap(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "wireless_controller_vap": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "acct-interim-interval": {"required": False, "type": "int"},
                "alias": {"required": False, "type": "str"},
                "auth": {"required": False, "type": "str",
                         "choices": ["psk", "radius", "usergroup"]},
                "broadcast-ssid": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "broadcast-suppression": {"required": False, "type": "str",
                                          "choices": ["dhcp-up", "dhcp-down", "dhcp-starvation",
                                                      "arp-known", "arp-unknown", "arp-reply",
                                                      "arp-poison", "arp-proxy", "netbios-ns",
                                                      "netbios-ds", "ipv6", "all-other-mc",
                                                      "all-other-bc"]},
                "captive-portal-ac-name": {"required": False, "type": "str"},
                "captive-portal-macauth-radius-secret": {"required": False, "type": "str"},
                "captive-portal-macauth-radius-server": {"required": False, "type": "str"},
                "captive-portal-radius-secret": {"required": False, "type": "str"},
                "captive-portal-radius-server": {"required": False, "type": "str"},
                "captive-portal-session-timeout-interval": {"required": False, "type": "int"},
                "dhcp-lease-time": {"required": False, "type": "int"},
                "dhcp-option82-circuit-id-insertion": {"required": False, "type": "str",
                                                       "choices": ["style-1", "style-2", "disable"]},
                "dhcp-option82-insertion": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                "dhcp-option82-remote-id-insertion": {"required": False, "type": "str",
                                                      "choices": ["style-1", "disable"]},
                "dynamic-vlan": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "eap-reauth": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "eap-reauth-intv": {"required": False, "type": "int"},
                "eapol-key-retries": {"required": False, "type": "str",
                                      "choices": ["disable", "enable"]},
                "encrypt": {"required": False, "type": "str",
                            "choices": ["TKIP", "AES", "TKIP-AES"]},
                "external-fast-roaming": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "external-logout": {"required": False, "type": "str"},
                "external-web": {"required": False, "type": "str"},
                "fast-bss-transition": {"required": False, "type": "str",
                                        "choices": ["disable", "enable"]},
                "fast-roaming": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "ft-mobility-domain": {"required": False, "type": "int"},
                "ft-over-ds": {"required": False, "type": "str",
                               "choices": ["disable", "enable"]},
                "ft-r0-key-lifetime": {"required": False, "type": "int"},
                "gtk-rekey": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "gtk-rekey-intv": {"required": False, "type": "int"},
                "hotspot20-profile": {"required": False, "type": "str"},
                "intra-vap-privacy": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "ip": {"required": False, "type": "str"},
                "key": {"required": False, "type": "str"},
                "keyindex": {"required": False, "type": "int"},
                "ldpc": {"required": False, "type": "str",
                         "choices": ["disable", "rx", "tx",
                                     "rxtx"]},
                "local-authentication": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "local-bridging": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "local-lan": {"required": False, "type": "str",
                              "choices": ["allow", "deny"]},
                "local-standalone": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "local-standalone-nat": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "mac-auth-bypass": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "mac-filter": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "mac-filter-list": {"required": False, "type": "list",
                                    "options": {
                                        "id": {"required": True, "type": "int"},
                                        "mac": {"required": False, "type": "str"},
                                        "mac-filter-policy": {"required": False, "type": "str",
                                                              "choices": ["allow", "deny"]}
                                    }},
                "mac-filter-policy-other": {"required": False, "type": "str",
                                            "choices": ["allow", "deny"]},
                "max-clients": {"required": False, "type": "int"},
                "max-clients-ap": {"required": False, "type": "int"},
                "me-disable-thresh": {"required": False, "type": "int"},
                "mesh-backhaul": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "mpsk": {"required": False, "type": "str",
                         "choices": ["enable", "disable"]},
                "mpsk-concurrent-clients": {"required": False, "type": "int"},
                "mpsk-key": {"required": False, "type": "list",
                             "options": {
                                 "comment": {"required": False, "type": "str"},
                                 "concurrent-clients": {"required": False, "type": "str"},
                                 "key-name": {"required": True, "type": "str"},
                                 "passphrase": {"required": False, "type": "str"}
                             }},
                "multicast-enhance": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "multicast-rate": {"required": False, "type": "str",
                                   "choices": ["0", "6000", "12000",
                                               "24000"]},
                "name": {"required": True, "type": "str"},
                "okc": {"required": False, "type": "str",
                        "choices": ["disable", "enable"]},
                "passphrase": {"required": False, "type": "str"},
                "pmf": {"required": False, "type": "str",
                        "choices": ["disable", "enable", "optional"]},
                "pmf-assoc-comeback-timeout": {"required": False, "type": "int"},
                "pmf-sa-query-retry-timeout": {"required": False, "type": "int"},
                "portal-message-override-group": {"required": False, "type": "str"},
                "portal-message-overrides": {"required": False, "type": "dict",
                                             "options": {
                                                 "auth-disclaimer-page": {"required": False, "type": "str"},
                                                 "auth-login-failed-page": {"required": False, "type": "str"},
                                                 "auth-login-page": {"required": False, "type": "str"},
                                                 "auth-reject-page": {"required": False, "type": "str"}
                                             }},
                "portal-type": {"required": False, "type": "str",
                                "choices": ["auth", "auth+disclaimer", "disclaimer",
                                            "email-collect", "cmcc", "cmcc-macauth",
                                            "auth-mac"]},
                "probe-resp-suppression": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "probe-resp-threshold": {"required": False, "type": "str"},
                "ptk-rekey": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "ptk-rekey-intv": {"required": False, "type": "int"},
                "qos-profile": {"required": False, "type": "str"},
                "quarantine": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "radio-2g-threshold": {"required": False, "type": "str"},
                "radio-5g-threshold": {"required": False, "type": "str"},
                "radio-sensitivity": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "radius-mac-auth": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "radius-mac-auth-server": {"required": False, "type": "str"},
                "radius-mac-auth-usergroups": {"required": False, "type": "list",
                                               "options": {
                                                   "name": {"required": True, "type": "str"}
                                               }},
                "radius-server": {"required": False, "type": "str"},
                "rates-11a": {"required": False, "type": "str",
                              "choices": ["1", "1-basic", "2",
                                          "2-basic", "5.5", "5.5-basic",
                                          "11", "11-basic", "6",
                                          "6-basic", "9", "9-basic",
                                          "12", "12-basic", "18",
                                          "18-basic", "24", "24-basic",
                                          "36", "36-basic", "48",
                                          "48-basic", "54", "54-basic"]},
                "rates-11ac-ss12": {"required": False, "type": "str",
                                    "choices": ["mcs0/1", "mcs1/1", "mcs2/1",
                                                "mcs3/1", "mcs4/1", "mcs5/1",
                                                "mcs6/1", "mcs7/1", "mcs8/1",
                                                "mcs9/1", "mcs10/1", "mcs11/1",
                                                "mcs0/2", "mcs1/2", "mcs2/2",
                                                "mcs3/2", "mcs4/2", "mcs5/2",
                                                "mcs6/2", "mcs7/2", "mcs8/2",
                                                "mcs9/2", "mcs10/2", "mcs11/2"]},
                "rates-11ac-ss34": {"required": False, "type": "str",
                                    "choices": ["mcs0/3", "mcs1/3", "mcs2/3",
                                                "mcs3/3", "mcs4/3", "mcs5/3",
                                                "mcs6/3", "mcs7/3", "mcs8/3",
                                                "mcs9/3", "mcs10/3", "mcs11/3",
                                                "mcs0/4", "mcs1/4", "mcs2/4",
                                                "mcs3/4", "mcs4/4", "mcs5/4",
                                                "mcs6/4", "mcs7/4", "mcs8/4",
                                                "mcs9/4", "mcs10/4", "mcs11/4"]},
                "rates-11bg": {"required": False, "type": "str",
                               "choices": ["1", "1-basic", "2",
                                           "2-basic", "5.5", "5.5-basic",
                                           "11", "11-basic", "6",
                                           "6-basic", "9", "9-basic",
                                           "12", "12-basic", "18",
                                           "18-basic", "24", "24-basic",
                                           "36", "36-basic", "48",
                                           "48-basic", "54", "54-basic"]},
                "rates-11n-ss12": {"required": False, "type": "str",
                                   "choices": ["mcs0/1", "mcs1/1", "mcs2/1",
                                               "mcs3/1", "mcs4/1", "mcs5/1",
                                               "mcs6/1", "mcs7/1", "mcs8/2",
                                               "mcs9/2", "mcs10/2", "mcs11/2",
                                               "mcs12/2", "mcs13/2", "mcs14/2",
                                               "mcs15/2"]},
                "rates-11n-ss34": {"required": False, "type": "str",
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
                "security-exempt-list": {"required": False, "type": "str"},
                "security-obsolete-option": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                "security-redirect-url": {"required": False, "type": "str"},
                "selected-usergroups": {"required": False, "type": "list",
                                        "options": {
                                            "name": {"required": True, "type": "str"}
                                        }},
                "split-tunneling": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "ssid": {"required": False, "type": "str"},
                "tkip-counter-measure": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "usergroup": {"required": False, "type": "list",
                              "options": {
                                  "name": {"required": True, "type": "str"}
                              }},
                "utm-profile": {"required": False, "type": "str"},
                "vdom": {"required": False, "type": "str"},
                "vlan-auto": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "vlan-pool": {"required": False, "type": "list",
                              "options": {
                                  "id": {"required": True, "type": "int"},
                                  "wtp-group": {"required": False, "type": "str"}
                              }},
                "vlan-pooling": {"required": False, "type": "str",
                                 "choices": ["wtp-group", "round-robin", "hash",
                                             "disable"]},
                "vlanid": {"required": False, "type": "int"},
                "voice-enterprise": {"required": False, "type": "str",
                                     "choices": ["disable", "enable"]}

            }
        }
    }

    module = AnsibleModule(argument_spec=fields,
                           supports_check_mode=False)
    try:
        from fortiosapi import FortiOSAPI
    except ImportError:
        module.fail_json(msg="fortiosapi module is required")

    fos = FortiOSAPI()

    is_error, has_changed, result = fortios_wireless_controller(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
