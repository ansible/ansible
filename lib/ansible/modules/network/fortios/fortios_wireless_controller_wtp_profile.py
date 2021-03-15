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
module: fortios_wireless_controller_wtp_profile
short_description: Configure WTP profiles or FortiAP profiles that define radio settings for manageable FortiAP platforms in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify wireless_controller feature and wtp_profile category.
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
    wireless_controller_wtp_profile:
        description:
            - Configure WTP profiles or FortiAP profiles that define radio settings for manageable FortiAP platforms.
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
            allowaccess:
                description:
                    - Control management access to the managed WTP, FortiAP, or AP. Separate entries with a space.
                type: str
                choices:
                    - telnet
                    - http
                    - https
                    - ssh
            ap_country:
                description:
                    - Country in which this WTP, FortiAP or AP will operate .
                type: str
                choices:
                    - NA
                    - AL
                    - DZ
                    - AO
                    - AR
                    - AM
                    - AU
                    - AT
                    - AZ
                    - BH
                    - BD
                    - BB
                    - BY
                    - BE
                    - BZ
                    - BO
                    - BA
                    - BR
                    - BN
                    - BG
                    - KH
                    - CL
                    - CN
                    - CO
                    - CR
                    - HR
                    - CY
                    - CZ
                    - DK
                    - DO
                    - EC
                    - EG
                    - SV
                    - EE
                    - FI
                    - FR
                    - GE
                    - DE
                    - GR
                    - GL
                    - GD
                    - GU
                    - GT
                    - HT
                    - HN
                    - HK
                    - HU
                    - IS
                    - IN
                    - ID
                    - IR
                    - IE
                    - IL
                    - IT
                    - JM
                    - JO
                    - KZ
                    - KE
                    - KP
                    - KR
                    - KW
                    - LV
                    - LB
                    - LI
                    - LT
                    - LU
                    - MO
                    - MK
                    - MY
                    - MT
                    - MX
                    - MC
                    - MA
                    - MZ
                    - MM
                    - NP
                    - NL
                    - AN
                    - AW
                    - NZ
                    - NO
                    - OM
                    - PK
                    - PA
                    - PG
                    - PY
                    - PE
                    - PH
                    - PL
                    - PT
                    - PR
                    - QA
                    - RO
                    - RU
                    - RW
                    - SA
                    - RS
                    - ME
                    - SG
                    - SK
                    - SI
                    - ZA
                    - ES
                    - LK
                    - SE
                    - SD
                    - CH
                    - SY
                    - TW
                    - TZ
                    - TH
                    - TT
                    - TN
                    - TR
                    - AE
                    - UA
                    - GB
                    - US
                    - PS
                    - UY
                    - UZ
                    - VE
                    - VN
                    - YE
                    - ZB
                    - ZW
                    - JP
                    - CA
            ble_profile:
                description:
                    - Bluetooth Low Energy profile name. Source wireless-controller.ble-profile.name.
                type: str
            comment:
                description:
                    - Comment.
                type: str
            control_message_offload:
                description:
                    - Enable/disable CAPWAP control message data channel offload.
                type: str
                choices:
                    - ebp-frame
                    - aeroscout-tag
                    - ap-list
                    - sta-list
                    - sta-cap-list
                    - stats
                    - aeroscout-mu
            deny_mac_list:
                description:
                    - List of MAC addresses that are denied access to this WTP, FortiAP, or AP.
                type: list
                suboptions:
                    id:
                        description:
                            - ID.
                        required: true
                        type: int
                    mac:
                        description:
                            - A WiFi device with this MAC address is denied access to this WTP, FortiAP or AP.
                        type: str
            dtls_in_kernel:
                description:
                    - Enable/disable data channel DTLS in kernel.
                type: str
                choices:
                    - enable
                    - disable
            dtls_policy:
                description:
                    - WTP data channel DTLS policy .
                type: str
                choices:
                    - clear-text
                    - dtls-enabled
                    - ipsec-vpn
            energy_efficient_ethernet:
                description:
                    - Enable/disable use of energy efficient Ethernet on WTP.
                type: str
                choices:
                    - enable
                    - disable
            ext_info_enable:
                description:
                    - Enable/disable station/VAP/radio extension information.
                type: str
                choices:
                    - enable
                    - disable
            handoff_roaming:
                description:
                    - Enable/disable client load balancing during roaming to avoid roaming delay .
                type: str
                choices:
                    - enable
                    - disable
            handoff_rssi:
                description:
                    - Minimum received signal strength indicator (RSSI) value for handoff (20 - 30).
                type: int
            handoff_sta_thresh:
                description:
                    - Threshold value for AP handoff.
                type: int
            ip_fragment_preventing:
                description:
                    - Select how to prevent IP fragmentation for CAPWAP tunneled control and data packets .
                type: str
                choices:
                    - tcp-mss-adjust
                    - icmp-unreachable
            lan:
                description:
                    - WTP LAN port mapping.
                type: dict
                suboptions:
                    port_mode:
                        description:
                            - LAN port mode.
                        type: str
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port_ssid:
                        description:
                            - Bridge LAN port to SSID. Source wireless-controller.vap.name.
                        type: str
                    port1_mode:
                        description:
                            - LAN port 1 mode.
                        type: str
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port1_ssid:
                        description:
                            - Bridge LAN port 1 to SSID. Source wireless-controller.vap.name.
                        type: str
                    port2_mode:
                        description:
                            - LAN port 2 mode.
                        type: str
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port2_ssid:
                        description:
                            - Bridge LAN port 2 to SSID. Source wireless-controller.vap.name.
                        type: str
                    port3_mode:
                        description:
                            - LAN port 3 mode.
                        type: str
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port3_ssid:
                        description:
                            - Bridge LAN port 3 to SSID. Source wireless-controller.vap.name.
                        type: str
                    port4_mode:
                        description:
                            - LAN port 4 mode.
                        type: str
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port4_ssid:
                        description:
                            - Bridge LAN port 4 to SSID. Source wireless-controller.vap.name.
                        type: str
                    port5_mode:
                        description:
                            - LAN port 5 mode.
                        type: str
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port5_ssid:
                        description:
                            - Bridge LAN port 5 to SSID. Source wireless-controller.vap.name.
                        type: str
                    port6_mode:
                        description:
                            - LAN port 6 mode.
                        type: str
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port6_ssid:
                        description:
                            - Bridge LAN port 6 to SSID. Source wireless-controller.vap.name.
                        type: str
                    port7_mode:
                        description:
                            - LAN port 7 mode.
                        type: str
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port7_ssid:
                        description:
                            - Bridge LAN port 7 to SSID. Source wireless-controller.vap.name.
                        type: str
                    port8_mode:
                        description:
                            - LAN port 8 mode.
                        type: str
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port8_ssid:
                        description:
                            - Bridge LAN port 8 to SSID. Source wireless-controller.vap.name.
                        type: str
            lbs:
                description:
                    - Set various location based service (LBS) options.
                type: dict
                suboptions:
                    aeroscout:
                        description:
                            - Enable/disable AeroScout Real Time Location Service (RTLS) support .
                        type: str
                        choices:
                            - enable
                            - disable
                    aeroscout_ap_mac:
                        description:
                            - Use BSSID or board MAC address as AP MAC address in AeroScout AP messages .
                        type: str
                        choices:
                            - bssid
                            - board-mac
                    aeroscout_mmu_report:
                        description:
                            - Enable/disable compounded AeroScout tag and MU report .
                        type: str
                        choices:
                            - enable
                            - disable
                    aeroscout_mu:
                        description:
                            - Enable/disable AeroScout Mobile Unit (MU) support .
                        type: str
                        choices:
                            - enable
                            - disable
                    aeroscout_mu_factor:
                        description:
                            - AeroScout MU mode dilution factor .
                        type: int
                    aeroscout_mu_timeout:
                        description:
                            - AeroScout MU mode timeout (0 - 65535 sec).
                        type: int
                    aeroscout_server_ip:
                        description:
                            - IP address of AeroScout server.
                        type: str
                    aeroscout_server_port:
                        description:
                            - AeroScout server UDP listening port.
                        type: int
                    ekahau_blink_mode:
                        description:
                            - Enable/disable Ekahau blink mode (now known as AiRISTA Flow) to track and locate WiFi tags .
                        type: str
                        choices:
                            - enable
                            - disable
                    ekahau_tag:
                        description:
                            - WiFi frame MAC address or WiFi Tag.
                        type: str
                    erc_server_ip:
                        description:
                            - IP address of Ekahau RTLS Controller (ERC).
                        type: str
                    erc_server_port:
                        description:
                            - Ekahau RTLS Controller (ERC) UDP listening port.
                        type: int
                    fortipresence:
                        description:
                            - Enable/disable FortiPresence to monitor the location and activity of WiFi clients even if they don't connect to this WiFi
                               network .
                        type: str
                        choices:
                            - foreign
                            - both
                            - disable
                    fortipresence_frequency:
                        description:
                            - FortiPresence report transmit frequency (5 - 65535 sec).
                        type: int
                    fortipresence_port:
                        description:
                            - FortiPresence server UDP listening port .
                        type: int
                    fortipresence_project:
                        description:
                            - FortiPresence project name (max. 16 characters).
                        type: str
                    fortipresence_rogue:
                        description:
                            - Enable/disable FortiPresence finding and reporting rogue APs.
                        type: str
                        choices:
                            - enable
                            - disable
                    fortipresence_secret:
                        description:
                            - FortiPresence secret password (max. 16 characters).
                        type: str
                    fortipresence_server:
                        description:
                            - FortiPresence server IP address.
                        type: str
                    fortipresence_unassoc:
                        description:
                            - Enable/disable FortiPresence finding and reporting unassociated stations.
                        type: str
                        choices:
                            - enable
                            - disable
                    station_locate:
                        description:
                            - Enable/disable client station locating services for all clients, whether associated or not .
                        type: str
                        choices:
                            - enable
                            - disable
            led_schedules:
                description:
                    - Recurring firewall schedules for illuminating LEDs on the FortiAP. If led-state is enabled, LEDs will be visible when at least one of
                       the schedules is valid. Separate multiple schedule names with a space.
                type: list
                suboptions:
                    name:
                        description:
                            - LED schedule name. Source firewall.schedule.group.name firewall.schedule.recurring.name.
                        required: true
                        type: str
            led_state:
                description:
                    - Enable/disable use of LEDs on WTP .
                type: str
                choices:
                    - enable
                    - disable
            lldp:
                description:
                    - Enable/disable Link Layer Discovery Protocol (LLDP) for the WTP, FortiAP, or AP .
                type: str
                choices:
                    - enable
                    - disable
            login_passwd:
                description:
                    - Set the managed WTP, FortiAP, or AP's administrator password.
                type: str
            login_passwd_change:
                description:
                    - Change or reset the administrator password of a managed WTP, FortiAP or AP (yes, default, or no).
                type: str
                choices:
                    - yes
                    - default
                    - no
            max_clients:
                description:
                    - Maximum number of stations (STAs) supported by the WTP .
                type: int
            name:
                description:
                    - WTP (or FortiAP or AP) profile name.
                required: true
                type: str
            platform:
                description:
                    - WTP, FortiAP, or AP platform.
                type: dict
                suboptions:
                    type:
                        description:
                            - WTP, FortiAP or AP platform type. There are built-in WTP profiles for all supported FortiAP models. You can select a built-in
                               profile and customize it or create a new profile.
                        type: str
                        choices:
                            - AP-11N
                            - 220B
                            - 210B
                            - 222B
                            - 112B
                            - 320B
                            - 11C
                            - 14C
                            - 223B
                            - 28C
                            - 320C
                            - 221C
                            - 25D
                            - 222C
                            - 224D
                            - 214B
                            - 21D
                            - 24D
                            - 112D
                            - 223C
                            - 321C
                            - C220C
                            - C225C
                            - C23JD
                            - C24JE
                            - S321C
                            - S322C
                            - S323C
                            - S311C
                            - S313C
                            - S321CR
                            - S322CR
                            - S323CR
                            - S421E
                            - S422E
                            - S423E
                            - 421E
                            - 423E
                            - 221E
                            - 222E
                            - 223E
                            - 224E
                            - S221E
                            - S223E
                            - U421E
                            - U422EV
                            - U423E
                            - U221EV
                            - U223EV
                            - U24JEV
                            - U321EV
                            - U323EV
            poe_mode:
                description:
                    - Set the WTP, FortiAP, or AP's PoE mode.
                type: str
                choices:
                    - auto
                    - 8023af
                    - 8023at
                    - power-adapter
            radio_1:
                description:
                    - Configuration options for radio 1.
                type: dict
                suboptions:
                    amsdu:
                        description:
                            - Enable/disable 802.11n AMSDU support. AMSDU can improve performance if supported by your WiFi clients .
                        type: str
                        choices:
                            - enable
                            - disable
                    ap_handoff:
                        description:
                            - Enable/disable AP handoff of clients to other APs .
                        type: str
                        choices:
                            - enable
                            - disable
                    ap_sniffer_addr:
                        description:
                            - MAC address to monitor.
                        type: str
                    ap_sniffer_bufsize:
                        description:
                            - Sniffer buffer size (1 - 32 MB).
                        type: int
                    ap_sniffer_chan:
                        description:
                            - Channel on which to operate the sniffer .
                        type: int
                    ap_sniffer_ctl:
                        description:
                            - Enable/disable sniffer on WiFi control frame .
                        type: str
                        choices:
                            - enable
                            - disable
                    ap_sniffer_data:
                        description:
                            - Enable/disable sniffer on WiFi data frame .
                        type: str
                        choices:
                            - enable
                            - disable
                    ap_sniffer_mgmt_beacon:
                        description:
                            - Enable/disable sniffer on WiFi management Beacon frames .
                        type: str
                        choices:
                            - enable
                            - disable
                    ap_sniffer_mgmt_other:
                        description:
                            - Enable/disable sniffer on WiFi management other frames  .
                        type: str
                        choices:
                            - enable
                            - disable
                    ap_sniffer_mgmt_probe:
                        description:
                            - Enable/disable sniffer on WiFi management probe frames .
                        type: str
                        choices:
                            - enable
                            - disable
                    auto_power_high:
                        description:
                            - Automatic transmit power high limit in dBm (the actual range of transmit power depends on the AP platform type).
                        type: int
                    auto_power_level:
                        description:
                            - Enable/disable automatic power-level adjustment to prevent co-channel interference .
                        type: str
                        choices:
                            - enable
                            - disable
                    auto_power_low:
                        description:
                            - Automatic transmission power low limit in dBm (the actual range of transmit power depends on the AP platform type).
                        type: int
                    band:
                        description:
                            - WiFi band that Radio 1 operates on.
                        type: str
                        choices:
                            - 802.11a
                            - 802.11b
                            - 802.11g
                            - 802.11n
                            - 802.11n-5G
                            - 802.11ac
                            - 802.11n,g-only
                            - 802.11g-only
                            - 802.11n-only
                            - 802.11n-5G-only
                            - 802.11ac,n-only
                            - 802.11ac-only
                    bandwidth_admission_control:
                        description:
                            - Enable/disable WiFi multimedia (WMM) bandwidth admission control to optimize WiFi bandwidth use. A request to join the wireless
                               network is only allowed if the access point has enough bandwidth to support it.
                        type: str
                        choices:
                            - enable
                            - disable
                    bandwidth_capacity:
                        description:
                            - Maximum bandwidth capacity allowed (1 - 600000 Kbps).
                        type: int
                    beacon_interval:
                        description:
                            - Beacon interval. The time between beacon frames in msec (the actual range of beacon interval depends on the AP platform type).
                        type: int
                    call_admission_control:
                        description:
                            - Enable/disable WiFi multimedia (WMM) call admission control to optimize WiFi bandwidth use for VoIP calls. New VoIP calls are
                               only accepted if there is enough bandwidth available to support them.
                        type: str
                        choices:
                            - enable
                            - disable
                    call_capacity:
                        description:
                            - Maximum number of Voice over WLAN (VoWLAN) phones supported by the radio (0 - 60).
                        type: int
                    channel:
                        description:
                            - Selected list of wireless radio channels.
                        type: list
                        suboptions:
                            chan:
                                description:
                                    - Channel number.
                                required: true
                                type: str
                    channel_bonding:
                        description:
                            - "Channel bandwidth: 80, 40, or 20MHz. Channels may use both 20 and 40 by enabling coexistence."
                        type: str
                        choices:
                            - 80MHz
                            - 40MHz
                            - 20MHz
                    channel_utilization:
                        description:
                            - Enable/disable measuring channel utilization.
                        type: str
                        choices:
                            - enable
                            - disable
                    coexistence:
                        description:
                            - Enable/disable allowing both HT20 and HT40 on the same radio .
                        type: str
                        choices:
                            - enable
                            - disable
                    darrp:
                        description:
                            - Enable/disable Distributed Automatic Radio Resource Provisioning (DARRP) to make sure the radio is always using the most optimal
                               channel .
                        type: str
                        choices:
                            - enable
                            - disable
                    dtim:
                        description:
                            - DTIM interval. The frequency to transmit Delivery Traffic Indication Message (or Map) (DTIM) messages (1 - 255). Set higher to
                               save client battery life.
                        type: int
                    frag_threshold:
                        description:
                            - Maximum packet size that can be sent without fragmentation (800 - 2346 bytes).
                        type: int
                    frequency_handoff:
                        description:
                            - Enable/disable frequency handoff of clients to other channels .
                        type: str
                        choices:
                            - enable
                            - disable
                    max_clients:
                        description:
                            - Maximum number of stations (STAs) or WiFi clients supported by the radio. Range depends on the hardware.
                        type: int
                    max_distance:
                        description:
                            - Maximum expected distance between the AP and clients (0 - 54000 m).
                        type: int
                    mode:
                        description:
                            - Mode of radio 1. Radio 1 can be disabled, configured as an access point, a rogue AP monitor, or a sniffer.
                        type: str
                        choices:
                            - disabled
                            - ap
                            - monitor
                            - sniffer
                    power_level:
                        description:
                            - Radio power level as a percentage of the maximum transmit power (0 - 100).
                        type: int
                    powersave_optimize:
                        description:
                            - Enable client power-saving features such as TIM, AC VO, and OBSS etc.
                        type: str
                        choices:
                            - tim
                            - ac-vo
                            - no-obss-scan
                            - no-11b-rate
                            - client-rate-follow
                    protection_mode:
                        description:
                            - Enable/disable 802.11g protection modes to support backwards compatibility with older clients (rtscts, ctsonly, disable).
                        type: str
                        choices:
                            - rtscts
                            - ctsonly
                            - disable
                    radio_id:
                        description:
                            - radio-id
                        type: int
                    rts_threshold:
                        description:
                            - Maximum packet size for RTS transmissions, specifying the maximum size of a data packet before RTS/CTS (256 - 2346 bytes).
                        type: int
                    short_guard_interval:
                        description:
                            - Use either the short guard interval (Short GI) of 400 ns or the long guard interval (Long GI) of 800 ns.
                        type: str
                        choices:
                            - enable
                            - disable
                    spectrum_analysis:
                        description:
                            - Enable/disable spectrum analysis to find interference that would negatively impact wireless performance.
                        type: str
                        choices:
                            - enable
                            - disable
                    transmit_optimize:
                        description:
                            - Packet transmission optimization options including power saving, aggregation limiting, retry limiting, etc. All are enabled by
                               default.
                        type: str
                        choices:
                            - disable
                            - power-save
                            - aggr-limit
                            - retry-limit
                            - send-bar
                    vap_all:
                        description:
                            - Enable/disable the automatic inheritance of all Virtual Access Points (VAPs) .
                        type: str
                        choices:
                            - enable
                            - disable
                    vaps:
                        description:
                            - Manually selected list of Virtual Access Points (VAPs).
                        type: list
                        suboptions:
                            name:
                                description:
                                    - Virtual Access Point (VAP) name. Source wireless-controller.vap-group.name wireless-controller.vap.name.
                                required: true
                                type: str
                    wids_profile:
                        description:
                            - Wireless Intrusion Detection System (WIDS) profile name to assign to the radio. Source wireless-controller.wids-profile.name.
                        type: str
            radio_2:
                description:
                    - Configuration options for radio 2.
                type: dict
                suboptions:
                    amsdu:
                        description:
                            - Enable/disable 802.11n AMSDU support. AMSDU can improve performance if supported by your WiFi clients .
                        type: str
                        choices:
                            - enable
                            - disable
                    ap_handoff:
                        description:
                            - Enable/disable AP handoff of clients to other APs .
                        type: str
                        choices:
                            - enable
                            - disable
                    ap_sniffer_addr:
                        description:
                            - MAC address to monitor.
                        type: str
                    ap_sniffer_bufsize:
                        description:
                            - Sniffer buffer size (1 - 32 MB).
                        type: int
                    ap_sniffer_chan:
                        description:
                            - Channel on which to operate the sniffer .
                        type: int
                    ap_sniffer_ctl:
                        description:
                            - Enable/disable sniffer on WiFi control frame .
                        type: str
                        choices:
                            - enable
                            - disable
                    ap_sniffer_data:
                        description:
                            - Enable/disable sniffer on WiFi data frame .
                        type: str
                        choices:
                            - enable
                            - disable
                    ap_sniffer_mgmt_beacon:
                        description:
                            - Enable/disable sniffer on WiFi management Beacon frames .
                        type: str
                        choices:
                            - enable
                            - disable
                    ap_sniffer_mgmt_other:
                        description:
                            - Enable/disable sniffer on WiFi management other frames  .
                        type: str
                        choices:
                            - enable
                            - disable
                    ap_sniffer_mgmt_probe:
                        description:
                            - Enable/disable sniffer on WiFi management probe frames .
                        type: str
                        choices:
                            - enable
                            - disable
                    auto_power_high:
                        description:
                            - Automatic transmit power high limit in dBm (the actual range of transmit power depends on the AP platform type).
                        type: int
                    auto_power_level:
                        description:
                            - Enable/disable automatic power-level adjustment to prevent co-channel interference .
                        type: str
                        choices:
                            - enable
                            - disable
                    auto_power_low:
                        description:
                            - Automatic transmission power low limit in dBm (the actual range of transmit power depends on the AP platform type).
                        type: int
                    band:
                        description:
                            - WiFi band that Radio 2 operates on.
                        type: str
                        choices:
                            - 802.11a
                            - 802.11b
                            - 802.11g
                            - 802.11n
                            - 802.11n-5G
                            - 802.11ac
                            - 802.11n,g-only
                            - 802.11g-only
                            - 802.11n-only
                            - 802.11n-5G-only
                            - 802.11ac,n-only
                            - 802.11ac-only
                    bandwidth_admission_control:
                        description:
                            - Enable/disable WiFi multimedia (WMM) bandwidth admission control to optimize WiFi bandwidth use. A request to join the wireless
                               network is only allowed if the access point has enough bandwidth to support it.
                        type: str
                        choices:
                            - enable
                            - disable
                    bandwidth_capacity:
                        description:
                            - Maximum bandwidth capacity allowed (1 - 600000 Kbps).
                        type: int
                    beacon_interval:
                        description:
                            - Beacon interval. The time between beacon frames in msec (the actual range of beacon interval depends on the AP platform type).
                        type: int
                    call_admission_control:
                        description:
                            - Enable/disable WiFi multimedia (WMM) call admission control to optimize WiFi bandwidth use for VoIP calls. New VoIP calls are
                               only accepted if there is enough bandwidth available to support them.
                        type: str
                        choices:
                            - enable
                            - disable
                    call_capacity:
                        description:
                            - Maximum number of Voice over WLAN (VoWLAN) phones supported by the radio (0 - 60).
                        type: int
                    channel:
                        description:
                            - Selected list of wireless radio channels.
                        type: list
                        suboptions:
                            chan:
                                description:
                                    - Channel number.
                                required: true
                                type: str
                    channel_bonding:
                        description:
                            - "Channel bandwidth: 80, 40, or 20MHz. Channels may use both 20 and 40 by enabling coexistence."
                        type: str
                        choices:
                            - 80MHz
                            - 40MHz
                            - 20MHz
                    channel_utilization:
                        description:
                            - Enable/disable measuring channel utilization.
                        type: str
                        choices:
                            - enable
                            - disable
                    coexistence:
                        description:
                            - Enable/disable allowing both HT20 and HT40 on the same radio .
                        type: str
                        choices:
                            - enable
                            - disable
                    darrp:
                        description:
                            - Enable/disable Distributed Automatic Radio Resource Provisioning (DARRP) to make sure the radio is always using the most optimal
                               channel .
                        type: str
                        choices:
                            - enable
                            - disable
                    dtim:
                        description:
                            - DTIM interval. The frequency to transmit Delivery Traffic Indication Message (or Map) (DTIM) messages (1 - 255). Set higher to
                               save client battery life.
                        type: int
                    frag_threshold:
                        description:
                            - Maximum packet size that can be sent without fragmentation (800 - 2346 bytes).
                        type: int
                    frequency_handoff:
                        description:
                            - Enable/disable frequency handoff of clients to other channels .
                        type: str
                        choices:
                            - enable
                            - disable
                    max_clients:
                        description:
                            - Maximum number of stations (STAs) or WiFi clients supported by the radio. Range depends on the hardware.
                        type: int
                    max_distance:
                        description:
                            - Maximum expected distance between the AP and clients (0 - 54000 m).
                        type: int
                    mode:
                        description:
                            - Mode of radio 2. Radio 2 can be disabled, configured as an access point, a rogue AP monitor, or a sniffer.
                        type: str
                        choices:
                            - disabled
                            - ap
                            - monitor
                            - sniffer
                    power_level:
                        description:
                            - Radio power level as a percentage of the maximum transmit power (0 - 100).
                        type: int
                    powersave_optimize:
                        description:
                            - Enable client power-saving features such as TIM, AC VO, and OBSS etc.
                        type: str
                        choices:
                            - tim
                            - ac-vo
                            - no-obss-scan
                            - no-11b-rate
                            - client-rate-follow
                    protection_mode:
                        description:
                            - Enable/disable 802.11g protection modes to support backwards compatibility with older clients (rtscts, ctsonly, disable).
                        type: str
                        choices:
                            - rtscts
                            - ctsonly
                            - disable
                    radio_id:
                        description:
                            - radio-id
                        type: int
                    rts_threshold:
                        description:
                            - Maximum packet size for RTS transmissions, specifying the maximum size of a data packet before RTS/CTS (256 - 2346 bytes).
                        type: int
                    short_guard_interval:
                        description:
                            - Use either the short guard interval (Short GI) of 400 ns or the long guard interval (Long GI) of 800 ns.
                        type: str
                        choices:
                            - enable
                            - disable
                    spectrum_analysis:
                        description:
                            - Enable/disable spectrum analysis to find interference that would negatively impact wireless performance.
                        type: str
                        choices:
                            - enable
                            - disable
                    transmit_optimize:
                        description:
                            - Packet transmission optimization options including power saving, aggregation limiting, retry limiting, etc. All are enabled by
                               default.
                        type: str
                        choices:
                            - disable
                            - power-save
                            - aggr-limit
                            - retry-limit
                            - send-bar
                    vap_all:
                        description:
                            - Enable/disable the automatic inheritance of all Virtual Access Points (VAPs) .
                        type: str
                        choices:
                            - enable
                            - disable
                    vaps:
                        description:
                            - Manually selected list of Virtual Access Points (VAPs).
                        type: list
                        suboptions:
                            name:
                                description:
                                    - Virtual Access Point (VAP) name. Source wireless-controller.vap-group.name wireless-controller.vap.name.
                                required: true
                                type: str
                    wids_profile:
                        description:
                            - Wireless Intrusion Detection System (WIDS) profile name to assign to the radio. Source wireless-controller.wids-profile.name.
                        type: str
            split_tunneling_acl:
                description:
                    - Split tunneling ACL filter list.
                type: list
                suboptions:
                    dest_ip:
                        description:
                            - Destination IP and mask for the split-tunneling subnet.
                        type: str
                    id:
                        description:
                            - ID.
                        required: true
                        type: int
            split_tunneling_acl_local_ap_subnet:
                description:
                    - Enable/disable automatically adding local subnetwork of FortiAP to split-tunneling ACL .
                type: str
                choices:
                    - enable
                    - disable
            split_tunneling_acl_path:
                description:
                    - Split tunneling ACL path is local/tunnel.
                type: str
                choices:
                    - tunnel
                    - local
            tun_mtu_downlink:
                description:
                    - Downlink CAPWAP tunnel MTU (0, 576, or 1500 bytes).
                type: int
            tun_mtu_uplink:
                description:
                    - Uplink CAPWAP tunnel MTU (0, 576, or 1500 bytes).
                type: int
            wan_port_mode:
                description:
                    - Enable/disable using a WAN port as a LAN port.
                type: str
                choices:
                    - wan-lan
                    - wan-only
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
  - name: Configure WTP profiles or FortiAP profiles that define radio settings for manageable FortiAP platforms.
    fortios_wireless_controller_wtp_profile:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      wireless_controller_wtp_profile:
        allowaccess: "telnet"
        ap_country: "NA"
        ble_profile: "<your_own_value> (source wireless-controller.ble-profile.name)"
        comment: "Comment."
        control_message_offload: "ebp-frame"
        deny_mac_list:
         -
            id:  "9"
            mac: "<your_own_value>"
        dtls_in_kernel: "enable"
        dtls_policy: "clear-text"
        energy_efficient_ethernet: "enable"
        ext_info_enable: "enable"
        handoff_roaming: "enable"
        handoff_rssi: "16"
        handoff_sta_thresh: "17"
        ip_fragment_preventing: "tcp-mss-adjust"
        lan:
            port_mode: "offline"
            port_ssid: "<your_own_value> (source wireless-controller.vap.name)"
            port1_mode: "offline"
            port1_ssid: "<your_own_value> (source wireless-controller.vap.name)"
            port2_mode: "offline"
            port2_ssid: "<your_own_value> (source wireless-controller.vap.name)"
            port3_mode: "offline"
            port3_ssid: "<your_own_value> (source wireless-controller.vap.name)"
            port4_mode: "offline"
            port4_ssid: "<your_own_value> (source wireless-controller.vap.name)"
            port5_mode: "offline"
            port5_ssid: "<your_own_value> (source wireless-controller.vap.name)"
            port6_mode: "offline"
            port6_ssid: "<your_own_value> (source wireless-controller.vap.name)"
            port7_mode: "offline"
            port7_ssid: "<your_own_value> (source wireless-controller.vap.name)"
            port8_mode: "offline"
            port8_ssid: "<your_own_value> (source wireless-controller.vap.name)"
        lbs:
            aeroscout: "enable"
            aeroscout_ap_mac: "bssid"
            aeroscout_mmu_report: "enable"
            aeroscout_mu: "enable"
            aeroscout_mu_factor: "43"
            aeroscout_mu_timeout: "44"
            aeroscout_server_ip: "<your_own_value>"
            aeroscout_server_port: "46"
            ekahau_blink_mode: "enable"
            ekahau_tag: "<your_own_value>"
            erc_server_ip: "<your_own_value>"
            erc_server_port: "50"
            fortipresence: "foreign"
            fortipresence_frequency: "52"
            fortipresence_port: "53"
            fortipresence_project: "<your_own_value>"
            fortipresence_rogue: "enable"
            fortipresence_secret: "<your_own_value>"
            fortipresence_server: "<your_own_value>"
            fortipresence_unassoc: "enable"
            station_locate: "enable"
        led_schedules:
         -
            name: "default_name_61 (source firewall.schedule.group.name firewall.schedule.recurring.name)"
        led_state: "enable"
        lldp: "enable"
        login_passwd: "<your_own_value>"
        login_passwd_change: "yes"
        max_clients: "66"
        name: "default_name_67"
        platform:
            type: "AP-11N"
        poe_mode: "auto"
        radio_1:
            amsdu: "enable"
            ap_handoff: "enable"
            ap_sniffer_addr: "<your_own_value>"
            ap_sniffer_bufsize: "75"
            ap_sniffer_chan: "76"
            ap_sniffer_ctl: "enable"
            ap_sniffer_data: "enable"
            ap_sniffer_mgmt_beacon: "enable"
            ap_sniffer_mgmt_other: "enable"
            ap_sniffer_mgmt_probe: "enable"
            auto_power_high: "82"
            auto_power_level: "enable"
            auto_power_low: "84"
            band: "802.11a"
            bandwidth_admission_control: "enable"
            bandwidth_capacity: "87"
            beacon_interval: "88"
            call_admission_control: "enable"
            call_capacity: "90"
            channel:
             -
                chan: "<your_own_value>"
            channel_bonding: "80MHz"
            channel_utilization: "enable"
            coexistence: "enable"
            darrp: "enable"
            dtim: "97"
            frag_threshold: "98"
            frequency_handoff: "enable"
            max_clients: "100"
            max_distance: "101"
            mode: "disabled"
            power_level: "103"
            powersave_optimize: "tim"
            protection_mode: "rtscts"
            radio_id: "106"
            rts_threshold: "107"
            short_guard_interval: "enable"
            spectrum_analysis: "enable"
            transmit_optimize: "disable"
            vap_all: "enable"
            vaps:
             -
                name: "default_name_113 (source wireless-controller.vap-group.name wireless-controller.vap.name)"
            wids_profile: "<your_own_value> (source wireless-controller.wids-profile.name)"
        radio_2:
            amsdu: "enable"
            ap_handoff: "enable"
            ap_sniffer_addr: "<your_own_value>"
            ap_sniffer_bufsize: "119"
            ap_sniffer_chan: "120"
            ap_sniffer_ctl: "enable"
            ap_sniffer_data: "enable"
            ap_sniffer_mgmt_beacon: "enable"
            ap_sniffer_mgmt_other: "enable"
            ap_sniffer_mgmt_probe: "enable"
            auto_power_high: "126"
            auto_power_level: "enable"
            auto_power_low: "128"
            band: "802.11a"
            bandwidth_admission_control: "enable"
            bandwidth_capacity: "131"
            beacon_interval: "132"
            call_admission_control: "enable"
            call_capacity: "134"
            channel:
             -
                chan: "<your_own_value>"
            channel_bonding: "80MHz"
            channel_utilization: "enable"
            coexistence: "enable"
            darrp: "enable"
            dtim: "141"
            frag_threshold: "142"
            frequency_handoff: "enable"
            max_clients: "144"
            max_distance: "145"
            mode: "disabled"
            power_level: "147"
            powersave_optimize: "tim"
            protection_mode: "rtscts"
            radio_id: "150"
            rts_threshold: "151"
            short_guard_interval: "enable"
            spectrum_analysis: "enable"
            transmit_optimize: "disable"
            vap_all: "enable"
            vaps:
             -
                name: "default_name_157 (source wireless-controller.vap-group.name wireless-controller.vap.name)"
            wids_profile: "<your_own_value> (source wireless-controller.wids-profile.name)"
        split_tunneling_acl:
         -
            dest_ip: "<your_own_value>"
            id:  "161"
        split_tunneling_acl_local_ap_subnet: "enable"
        split_tunneling_acl_path: "tunnel"
        tun_mtu_downlink: "164"
        tun_mtu_uplink: "165"
        wan_port_mode: "wan-lan"
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


def filter_wireless_controller_wtp_profile_data(json):
    option_list = ['allowaccess', 'ap_country', 'ble_profile',
                   'comment', 'control_message_offload', 'deny_mac_list',
                   'dtls_in_kernel', 'dtls_policy', 'energy_efficient_ethernet',
                   'ext_info_enable', 'handoff_roaming', 'handoff_rssi',
                   'handoff_sta_thresh', 'ip_fragment_preventing', 'lan',
                   'lbs', 'led_schedules', 'led_state',
                   'lldp', 'login_passwd', 'login_passwd_change',
                   'max_clients', 'name', 'platform',
                   'poe_mode', 'radio_1', 'radio_2',
                   'split_tunneling_acl', 'split_tunneling_acl_local_ap_subnet', 'split_tunneling_acl_path',
                   'tun_mtu_downlink', 'tun_mtu_uplink', 'wan_port_mode']
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


def wireless_controller_wtp_profile(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['wireless_controller_wtp_profile'] and data['wireless_controller_wtp_profile']:
        state = data['wireless_controller_wtp_profile']['state']
    else:
        state = True
    wireless_controller_wtp_profile_data = data['wireless_controller_wtp_profile']
    filtered_data = underscore_to_hyphen(filter_wireless_controller_wtp_profile_data(wireless_controller_wtp_profile_data))

    if state == "present":
        return fos.set('wireless-controller',
                       'wtp-profile',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('wireless-controller',
                          'wtp-profile',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_wireless_controller(data, fos):

    if data['wireless_controller_wtp_profile']:
        resp = wireless_controller_wtp_profile(data, fos)

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
        "wireless_controller_wtp_profile": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "allowaccess": {"required": False, "type": "str",
                                "choices": ["telnet", "http", "https",
                                            "ssh"]},
                "ap_country": {"required": False, "type": "str",
                               "choices": ["NA", "AL", "DZ",
                                           "AO", "AR", "AM",
                                           "AU", "AT", "AZ",
                                           "BH", "BD", "BB",
                                           "BY", "BE", "BZ",
                                           "BO", "BA", "BR",
                                           "BN", "BG", "KH",
                                           "CL", "CN", "CO",
                                           "CR", "HR", "CY",
                                           "CZ", "DK", "DO",
                                           "EC", "EG", "SV",
                                           "EE", "FI", "FR",
                                           "GE", "DE", "GR",
                                           "GL", "GD", "GU",
                                           "GT", "HT", "HN",
                                           "HK", "HU", "IS",
                                           "IN", "ID", "IR",
                                           "IE", "IL", "IT",
                                           "JM", "JO", "KZ",
                                           "KE", "KP", "KR",
                                           "KW", "LV", "LB",
                                           "LI", "LT", "LU",
                                           "MO", "MK", "MY",
                                           "MT", "MX", "MC",
                                           "MA", "MZ", "MM",
                                           "NP", "NL", "AN",
                                           "AW", "NZ", "NO",
                                           "OM", "PK", "PA",
                                           "PG", "PY", "PE",
                                           "PH", "PL", "PT",
                                           "PR", "QA", "RO",
                                           "RU", "RW", "SA",
                                           "RS", "ME", "SG",
                                           "SK", "SI", "ZA",
                                           "ES", "LK", "SE",
                                           "SD", "CH", "SY",
                                           "TW", "TZ", "TH",
                                           "TT", "TN", "TR",
                                           "AE", "UA", "GB",
                                           "US", "PS", "UY",
                                           "UZ", "VE", "VN",
                                           "YE", "ZB", "ZW",
                                           "JP", "CA"]},
                "ble_profile": {"required": False, "type": "str"},
                "comment": {"required": False, "type": "str"},
                "control_message_offload": {"required": False, "type": "str",
                                            "choices": ["ebp-frame", "aeroscout-tag", "ap-list",
                                                        "sta-list", "sta-cap-list", "stats",
                                                        "aeroscout-mu"]},
                "deny_mac_list": {"required": False, "type": "list",
                                  "options": {
                                      "id": {"required": True, "type": "int"},
                                      "mac": {"required": False, "type": "str"}
                                  }},
                "dtls_in_kernel": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "dtls_policy": {"required": False, "type": "str",
                                "choices": ["clear-text", "dtls-enabled", "ipsec-vpn"]},
                "energy_efficient_ethernet": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                "ext_info_enable": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "handoff_roaming": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "handoff_rssi": {"required": False, "type": "int"},
                "handoff_sta_thresh": {"required": False, "type": "int"},
                "ip_fragment_preventing": {"required": False, "type": "str",
                                           "choices": ["tcp-mss-adjust", "icmp-unreachable"]},
                "lan": {"required": False, "type": "dict",
                        "options": {
                            "port_mode": {"required": False, "type": "str",
                                          "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                      "bridge-to-ssid"]},
                            "port_ssid": {"required": False, "type": "str"},
                            "port1_mode": {"required": False, "type": "str",
                                           "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                       "bridge-to-ssid"]},
                            "port1_ssid": {"required": False, "type": "str"},
                            "port2_mode": {"required": False, "type": "str",
                                           "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                       "bridge-to-ssid"]},
                            "port2_ssid": {"required": False, "type": "str"},
                            "port3_mode": {"required": False, "type": "str",
                                           "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                       "bridge-to-ssid"]},
                            "port3_ssid": {"required": False, "type": "str"},
                            "port4_mode": {"required": False, "type": "str",
                                           "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                       "bridge-to-ssid"]},
                            "port4_ssid": {"required": False, "type": "str"},
                            "port5_mode": {"required": False, "type": "str",
                                           "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                       "bridge-to-ssid"]},
                            "port5_ssid": {"required": False, "type": "str"},
                            "port6_mode": {"required": False, "type": "str",
                                           "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                       "bridge-to-ssid"]},
                            "port6_ssid": {"required": False, "type": "str"},
                            "port7_mode": {"required": False, "type": "str",
                                           "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                       "bridge-to-ssid"]},
                            "port7_ssid": {"required": False, "type": "str"},
                            "port8_mode": {"required": False, "type": "str",
                                           "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                       "bridge-to-ssid"]},
                            "port8_ssid": {"required": False, "type": "str"}
                        }},
                "lbs": {"required": False, "type": "dict",
                        "options": {
                            "aeroscout": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                            "aeroscout_ap_mac": {"required": False, "type": "str",
                                                 "choices": ["bssid", "board-mac"]},
                            "aeroscout_mmu_report": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]},
                            "aeroscout_mu": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                            "aeroscout_mu_factor": {"required": False, "type": "int"},
                            "aeroscout_mu_timeout": {"required": False, "type": "int"},
                            "aeroscout_server_ip": {"required": False, "type": "str"},
                            "aeroscout_server_port": {"required": False, "type": "int"},
                            "ekahau_blink_mode": {"required": False, "type": "str",
                                                  "choices": ["enable", "disable"]},
                            "ekahau_tag": {"required": False, "type": "str"},
                            "erc_server_ip": {"required": False, "type": "str"},
                            "erc_server_port": {"required": False, "type": "int"},
                            "fortipresence": {"required": False, "type": "str",
                                              "choices": ["foreign", "both", "disable"]},
                            "fortipresence_frequency": {"required": False, "type": "int"},
                            "fortipresence_port": {"required": False, "type": "int"},
                            "fortipresence_project": {"required": False, "type": "str"},
                            "fortipresence_rogue": {"required": False, "type": "str",
                                                    "choices": ["enable", "disable"]},
                            "fortipresence_secret": {"required": False, "type": "str", "no_log": True},
                            "fortipresence_server": {"required": False, "type": "str"},
                            "fortipresence_unassoc": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                            "station_locate": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]}
                        }},
                "led_schedules": {"required": False, "type": "list",
                                  "options": {
                                      "name": {"required": True, "type": "str"}
                                  }},
                "led_state": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "lldp": {"required": False, "type": "str",
                         "choices": ["enable", "disable"]},
                "login_passwd": {"required": False, "type": "str", "no_log": True},
                "login_passwd_change": {"required": False, "type": "str",
                                        "choices": ["yes", "default", "no"]},
                "max_clients": {"required": False, "type": "int"},
                "name": {"required": True, "type": "str"},
                "platform": {"required": False, "type": "dict",
                             "options": {
                                 "type": {"required": False, "type": "str",
                                          "choices": ["AP-11N", "220B", "210B",
                                                      "222B", "112B", "320B",
                                                      "11C", "14C", "223B",
                                                      "28C", "320C", "221C",
                                                      "25D", "222C", "224D",
                                                      "214B", "21D", "24D",
                                                      "112D", "223C", "321C",
                                                      "C220C", "C225C", "C23JD",
                                                      "C24JE", "S321C", "S322C",
                                                      "S323C", "S311C", "S313C",
                                                      "S321CR", "S322CR", "S323CR",
                                                      "S421E", "S422E", "S423E",
                                                      "421E", "423E", "221E",
                                                      "222E", "223E", "224E",
                                                      "S221E", "S223E", "U421E",
                                                      "U422EV", "U423E", "U221EV",
                                                      "U223EV", "U24JEV", "U321EV",
                                                      "U323EV"]}
                             }},
                "poe_mode": {"required": False, "type": "str",
                             "choices": ["auto", "8023af", "8023at",
                                         "power-adapter"]},
                "radio_1": {"required": False, "type": "dict",
                            "options": {
                                "amsdu": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                                "ap_handoff": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                                "ap_sniffer_addr": {"required": False, "type": "str"},
                                "ap_sniffer_bufsize": {"required": False, "type": "int"},
                                "ap_sniffer_chan": {"required": False, "type": "int"},
                                "ap_sniffer_ctl": {"required": False, "type": "str",
                                                   "choices": ["enable", "disable"]},
                                "ap_sniffer_data": {"required": False, "type": "str",
                                                    "choices": ["enable", "disable"]},
                                "ap_sniffer_mgmt_beacon": {"required": False, "type": "str",
                                                           "choices": ["enable", "disable"]},
                                "ap_sniffer_mgmt_other": {"required": False, "type": "str",
                                                          "choices": ["enable", "disable"]},
                                "ap_sniffer_mgmt_probe": {"required": False, "type": "str",
                                                          "choices": ["enable", "disable"]},
                                "auto_power_high": {"required": False, "type": "int"},
                                "auto_power_level": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]},
                                "auto_power_low": {"required": False, "type": "int"},
                                "band": {"required": False, "type": "str",
                                         "choices": ["802.11a", "802.11b", "802.11g",
                                                     "802.11n", "802.11n-5G", "802.11ac",
                                                     "802.11n,g-only", "802.11g-only", "802.11n-only",
                                                     "802.11n-5G-only", "802.11ac,n-only", "802.11ac-only"]},
                                "bandwidth_admission_control": {"required": False, "type": "str",
                                                                "choices": ["enable", "disable"]},
                                "bandwidth_capacity": {"required": False, "type": "int"},
                                "beacon_interval": {"required": False, "type": "int"},
                                "call_admission_control": {"required": False, "type": "str",
                                                           "choices": ["enable", "disable"]},
                                "call_capacity": {"required": False, "type": "int"},
                                "channel": {"required": False, "type": "list",
                                            "options": {
                                                "chan": {"required": True, "type": "str"}
                                            }},
                                "channel_bonding": {"required": False, "type": "str",
                                                    "choices": ["80MHz", "40MHz", "20MHz"]},
                                "channel_utilization": {"required": False, "type": "str",
                                                        "choices": ["enable", "disable"]},
                                "coexistence": {"required": False, "type": "str",
                                                "choices": ["enable", "disable"]},
                                "darrp": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                                "dtim": {"required": False, "type": "int"},
                                "frag_threshold": {"required": False, "type": "int"},
                                "frequency_handoff": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                                "max_clients": {"required": False, "type": "int"},
                                "max_distance": {"required": False, "type": "int"},
                                "mode": {"required": False, "type": "str",
                                         "choices": ["disabled", "ap", "monitor",
                                                     "sniffer"]},
                                "power_level": {"required": False, "type": "int"},
                                "powersave_optimize": {"required": False, "type": "str",
                                                       "choices": ["tim", "ac-vo", "no-obss-scan",
                                                                   "no-11b-rate", "client-rate-follow"]},
                                "protection_mode": {"required": False, "type": "str",
                                                    "choices": ["rtscts", "ctsonly", "disable"]},
                                "radio_id": {"required": False, "type": "int"},
                                "rts_threshold": {"required": False, "type": "int"},
                                "short_guard_interval": {"required": False, "type": "str",
                                                         "choices": ["enable", "disable"]},
                                "spectrum_analysis": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                                "transmit_optimize": {"required": False, "type": "str",
                                                      "choices": ["disable", "power-save", "aggr-limit",
                                                                  "retry-limit", "send-bar"]},
                                "vap_all": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                                "vaps": {"required": False, "type": "list",
                                         "options": {
                                             "name": {"required": True, "type": "str"}
                                         }},
                                "wids_profile": {"required": False, "type": "str"}
                            }},
                "radio_2": {"required": False, "type": "dict",
                            "options": {
                                "amsdu": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                                "ap_handoff": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                                "ap_sniffer_addr": {"required": False, "type": "str"},
                                "ap_sniffer_bufsize": {"required": False, "type": "int"},
                                "ap_sniffer_chan": {"required": False, "type": "int"},
                                "ap_sniffer_ctl": {"required": False, "type": "str",
                                                   "choices": ["enable", "disable"]},
                                "ap_sniffer_data": {"required": False, "type": "str",
                                                    "choices": ["enable", "disable"]},
                                "ap_sniffer_mgmt_beacon": {"required": False, "type": "str",
                                                           "choices": ["enable", "disable"]},
                                "ap_sniffer_mgmt_other": {"required": False, "type": "str",
                                                          "choices": ["enable", "disable"]},
                                "ap_sniffer_mgmt_probe": {"required": False, "type": "str",
                                                          "choices": ["enable", "disable"]},
                                "auto_power_high": {"required": False, "type": "int"},
                                "auto_power_level": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]},
                                "auto_power_low": {"required": False, "type": "int"},
                                "band": {"required": False, "type": "str",
                                         "choices": ["802.11a", "802.11b", "802.11g",
                                                     "802.11n", "802.11n-5G", "802.11ac",
                                                     "802.11n,g-only", "802.11g-only", "802.11n-only",
                                                     "802.11n-5G-only", "802.11ac,n-only", "802.11ac-only"]},
                                "bandwidth_admission_control": {"required": False, "type": "str",
                                                                "choices": ["enable", "disable"]},
                                "bandwidth_capacity": {"required": False, "type": "int"},
                                "beacon_interval": {"required": False, "type": "int"},
                                "call_admission_control": {"required": False, "type": "str",
                                                           "choices": ["enable", "disable"]},
                                "call_capacity": {"required": False, "type": "int"},
                                "channel": {"required": False, "type": "list",
                                            "options": {
                                                "chan": {"required": True, "type": "str"}
                                            }},
                                "channel_bonding": {"required": False, "type": "str",
                                                    "choices": ["80MHz", "40MHz", "20MHz"]},
                                "channel_utilization": {"required": False, "type": "str",
                                                        "choices": ["enable", "disable"]},
                                "coexistence": {"required": False, "type": "str",
                                                "choices": ["enable", "disable"]},
                                "darrp": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                                "dtim": {"required": False, "type": "int"},
                                "frag_threshold": {"required": False, "type": "int"},
                                "frequency_handoff": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                                "max_clients": {"required": False, "type": "int"},
                                "max_distance": {"required": False, "type": "int"},
                                "mode": {"required": False, "type": "str",
                                         "choices": ["disabled", "ap", "monitor",
                                                     "sniffer"]},
                                "power_level": {"required": False, "type": "int"},
                                "powersave_optimize": {"required": False, "type": "str",
                                                       "choices": ["tim", "ac-vo", "no-obss-scan",
                                                                   "no-11b-rate", "client-rate-follow"]},
                                "protection_mode": {"required": False, "type": "str",
                                                    "choices": ["rtscts", "ctsonly", "disable"]},
                                "radio_id": {"required": False, "type": "int"},
                                "rts_threshold": {"required": False, "type": "int"},
                                "short_guard_interval": {"required": False, "type": "str",
                                                         "choices": ["enable", "disable"]},
                                "spectrum_analysis": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                                "transmit_optimize": {"required": False, "type": "str",
                                                      "choices": ["disable", "power-save", "aggr-limit",
                                                                  "retry-limit", "send-bar"]},
                                "vap_all": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                                "vaps": {"required": False, "type": "list",
                                         "options": {
                                             "name": {"required": True, "type": "str"}
                                         }},
                                "wids_profile": {"required": False, "type": "str"}
                            }},
                "split_tunneling_acl": {"required": False, "type": "list",
                                        "options": {
                                            "dest_ip": {"required": False, "type": "str"},
                                            "id": {"required": True, "type": "int"}
                                        }},
                "split_tunneling_acl_local_ap_subnet": {"required": False, "type": "str",
                                                        "choices": ["enable", "disable"]},
                "split_tunneling_acl_path": {"required": False, "type": "str",
                                             "choices": ["tunnel", "local"]},
                "tun_mtu_downlink": {"required": False, "type": "int"},
                "tun_mtu_uplink": {"required": False, "type": "int"},
                "wan_port_mode": {"required": False, "type": "str",
                                  "choices": ["wan-lan", "wan-only"]}

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
