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
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify wireless_controller feature and wtp_profile category.
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
    wireless_controller_wtp_profile:
        description:
            - Configure WTP profiles or FortiAP profiles that define radio settings for manageable FortiAP platforms.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            allowaccess:
                description:
                    - Control management access to the managed WTP, FortiAP, or AP. Separate entries with a space.
                choices:
                    - telnet
                    - http
                    - https
                    - ssh
            ap-country:
                description:
                    - Country in which this WTP, FortiAP or AP will operate (default = US).
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
            ble-profile:
                description:
                    - Bluetooth Low Energy profile name. Source wireless-controller.ble-profile.name.
            comment:
                description:
                    - Comment.
            control-message-offload:
                description:
                    - Enable/disable CAPWAP control message data channel offload.
                choices:
                    - ebp-frame
                    - aeroscout-tag
                    - ap-list
                    - sta-list
                    - sta-cap-list
                    - stats
                    - aeroscout-mu
            deny-mac-list:
                description:
                    - List of MAC addresses that are denied access to this WTP, FortiAP, or AP.
                suboptions:
                    id:
                        description:
                            - ID.
                        required: true
                    mac:
                        description:
                            - A WiFi device with this MAC address is denied access to this WTP, FortiAP or AP.
            dtls-in-kernel:
                description:
                    - Enable/disable data channel DTLS in kernel.
                choices:
                    - enable
                    - disable
            dtls-policy:
                description:
                    - WTP data channel DTLS policy (default = clear-text).
                choices:
                    - clear-text
                    - dtls-enabled
                    - ipsec-vpn
            energy-efficient-ethernet:
                description:
                    - Enable/disable use of energy efficient Ethernet on WTP.
                choices:
                    - enable
                    - disable
            ext-info-enable:
                description:
                    - Enable/disable station/VAP/radio extension information.
                choices:
                    - enable
                    - disable
            handoff-roaming:
                description:
                    - Enable/disable client load balancing during roaming to avoid roaming delay (default = disable).
                choices:
                    - enable
                    - disable
            handoff-rssi:
                description:
                    - Minimum received signal strength indicator (RSSI) value for handoff (20 - 30, default = 25).
            handoff-sta-thresh:
                description:
                    - Threshold value for AP handoff (5 - 35, default = 30).
            ip-fragment-preventing:
                description:
                    - Select how to prevent IP fragmentation for CAPWAP tunneled control and data packets (default = tcp-mss-adjust).
                choices:
                    - tcp-mss-adjust
                    - icmp-unreachable
            lan:
                description:
                    - WTP LAN port mapping.
                suboptions:
                    port-mode:
                        description:
                            - LAN port mode.
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port-ssid:
                        description:
                            - Bridge LAN port to SSID. Source wireless-controller.vap.name.
                    port1-mode:
                        description:
                            - LAN port 1 mode.
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port1-ssid:
                        description:
                            - Bridge LAN port 1 to SSID. Source wireless-controller.vap.name.
                    port2-mode:
                        description:
                            - LAN port 2 mode.
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port2-ssid:
                        description:
                            - Bridge LAN port 2 to SSID. Source wireless-controller.vap.name.
                    port3-mode:
                        description:
                            - LAN port 3 mode.
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port3-ssid:
                        description:
                            - Bridge LAN port 3 to SSID. Source wireless-controller.vap.name.
                    port4-mode:
                        description:
                            - LAN port 4 mode.
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port4-ssid:
                        description:
                            - Bridge LAN port 4 to SSID. Source wireless-controller.vap.name.
                    port5-mode:
                        description:
                            - LAN port 5 mode.
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port5-ssid:
                        description:
                            - Bridge LAN port 5 to SSID. Source wireless-controller.vap.name.
                    port6-mode:
                        description:
                            - LAN port 6 mode.
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port6-ssid:
                        description:
                            - Bridge LAN port 6 to SSID. Source wireless-controller.vap.name.
                    port7-mode:
                        description:
                            - LAN port 7 mode.
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port7-ssid:
                        description:
                            - Bridge LAN port 7 to SSID. Source wireless-controller.vap.name.
                    port8-mode:
                        description:
                            - LAN port 8 mode.
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port8-ssid:
                        description:
                            - Bridge LAN port 8 to SSID. Source wireless-controller.vap.name.
            lbs:
                description:
                    - Set various location based service (LBS) options.
                suboptions:
                    aeroscout:
                        description:
                            - Enable/disable AeroScout Real Time Location Service (RTLS) support.
                        choices:
                            - enable
                            - disable
                    aeroscout-ap-mac:
                        description:
                            - Use BSSID or board MAC address as AP MAC address in the Aeroscout AP message.
                        choices:
                            - bssid
                            - board-mac
                    aeroscout-mmu-report:
                        description:
                            - Enable/disable MU compounded report.
                        choices:
                            - enable
                            - disable
                    aeroscout-mu:
                        description:
                            - Enable/disable AeroScout support.
                        choices:
                            - enable
                            - disable
                    aeroscout-mu-factor:
                        description:
                            - AeroScout Mobile Unit (MU) mode dilution factor (default = 20).
                    aeroscout-mu-timeout:
                        description:
                            - AeroScout MU mode timeout (0 - 65535 sec, default = 5).
                    aeroscout-server-ip:
                        description:
                            - IP address of AeroScout server.
                    aeroscout-server-port:
                        description:
                            - AeroScout server UDP listening port.
                    ekahau-blink-mode:
                        description:
                            - Enable/disable Ekahua blink mode (also called AiRISTA Flow Blink Mode) to find the location of devices connected to a wireless
                               LAN (default = disable).
                        choices:
                            - enable
                            - disable
                    ekahau-tag:
                        description:
                            - WiFi frame MAC address or WiFi Tag.
                    erc-server-ip:
                        description:
                            - IP address of Ekahua RTLS Controller (ERC).
                    erc-server-port:
                        description:
                            - Ekahua RTLS Controller (ERC) UDP listening port.
                    fortipresence:
                        description:
                            - Enable/disable FortiPresence to monitor the location and activity of WiFi clients even if they don't connect to this WiFi
                               network (default = disable).
                        choices:
                            - foreign
                            - both
                            - disable
                    fortipresence-frequency:
                        description:
                            - FortiPresence report transmit frequency (5 - 65535 sec, default = 30).
                    fortipresence-port:
                        description:
                            - FortiPresence server UDP listening port (default = 3000).
                    fortipresence-project:
                        description:
                            - FortiPresence project name (max. 16 characters, default = fortipresence).
                    fortipresence-rogue:
                        description:
                            - Enable/disable FortiPresence finding and reporting rogue APs.
                        choices:
                            - enable
                            - disable
                    fortipresence-secret:
                        description:
                            - FortiPresence secret password (max. 16 characters).
                    fortipresence-server:
                        description:
                            - FortiPresence server IP address.
                    fortipresence-unassoc:
                        description:
                            - Enable/disable FortiPresence finding and reporting unassociated stations.
                        choices:
                            - enable
                            - disable
                    station-locate:
                        description:
                            - Enable/disable client station locating services for all clients, whether associated or not (default = disable).
                        choices:
                            - enable
                            - disable
            led-schedules:
                description:
                    - Recurring firewall schedules for illuminating LEDs on the FortiAP. If led-state is enabled, LEDs will be visible when at least one of
                       the schedules is valid. Separate multiple schedule names with a space.
                suboptions:
                    name:
                        description:
                            - LED schedule name. Source firewall.schedule.group.name firewall.schedule.recurring.name.
                        required: true
            led-state:
                description:
                    - Enable/disable use of LEDs on WTP (default = disable).
                choices:
                    - enable
                    - disable
            lldp:
                description:
                    - Enable/disable Link Layer Discovery Protocol (LLDP) for the WTP, FortiAP, or AP (default = disable).
                choices:
                    - enable
                    - disable
            login-passwd:
                description:
                    - Set the managed WTP, FortiAP, or AP's administrator password.
            login-passwd-change:
                description:
                    - Change or reset the administrator password of a managed WTP, FortiAP or AP (yes, default, or no, default = no).
                choices:
                    - yes
                    - default
                    - no
            max-clients:
                description:
                    - Maximum number of stations (STAs) supported by the WTP (default = 0, meaning no client limitation).
            name:
                description:
                    - WTP (or FortiAP or AP) profile name.
                required: true
            platform:
                description:
                    - WTP, FortiAP, or AP platform.
                suboptions:
                    type:
                        description:
                            - WTP, FortiAP or AP platform type. There are built-in WTP profiles for all supported FortiAP models. You can select a built-in
                               profile and customize it or create a new profile.
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
            poe-mode:
                description:
                    - Set the WTP, FortiAP, or AP's PoE mode.
                choices:
                    - auto
                    - 8023af
                    - 8023at
                    - power-adapter
            radio-1:
                description:
                    - Configuration options for radio 1.
                suboptions:
                    amsdu:
                        description:
                            - Enable/disable 802.11n AMSDU support. AMSDU can improve performance if supported by your WiFi clients (default = enable).
                        choices:
                            - enable
                            - disable
                    ap-handoff:
                        description:
                            - Enable/disable AP handoff of clients to other APs (default = disable).
                        choices:
                            - enable
                            - disable
                    ap-sniffer-addr:
                        description:
                            - MAC address to monitor.
                    ap-sniffer-bufsize:
                        description:
                            - Sniffer buffer size (1 - 32 MB, default = 16).
                    ap-sniffer-chan:
                        description:
                            - Channel on which to operate the sniffer (default = 6).
                    ap-sniffer-ctl:
                        description:
                            - Enable/disable sniffer on WiFi control frame (default = enable).
                        choices:
                            - enable
                            - disable
                    ap-sniffer-data:
                        description:
                            - Enable/disable sniffer on WiFi data frame (default = enable).
                        choices:
                            - enable
                            - disable
                    ap-sniffer-mgmt-beacon:
                        description:
                            - Enable/disable sniffer on WiFi management Beacon frames (default = enable).
                        choices:
                            - enable
                            - disable
                    ap-sniffer-mgmt-other:
                        description:
                            - Enable/disable sniffer on WiFi management other frames  (default = enable).
                        choices:
                            - enable
                            - disable
                    ap-sniffer-mgmt-probe:
                        description:
                            - Enable/disable sniffer on WiFi management probe frames (default = enable).
                        choices:
                            - enable
                            - disable
                    auto-power-high:
                        description:
                            - Automatic transmit power high limit in dBm (the actual range of transmit power depends on the AP platform type).
                    auto-power-level:
                        description:
                            - Enable/disable automatic power-level adjustment to prevent co-channel interference (default = disable).
                        choices:
                            - enable
                            - disable
                    auto-power-low:
                        description:
                            - Automatic transmission power low limit in dBm (the actual range of transmit power depends on the AP platform type).
                    band:
                        description:
                            - WiFi band that Radio 1 operates on.
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
                    bandwidth-admission-control:
                        description:
                            - Enable/disable WiFi multimedia (WMM) bandwidth admission control to optimize WiFi bandwidth use. A request to join the wireless
                               network is only allowed if the access point has enough bandwidth to support it.
                        choices:
                            - enable
                            - disable
                    bandwidth-capacity:
                        description:
                            - Maximum bandwidth capacity allowed (1 - 600000 Kbps, default = 2000).
                    beacon-interval:
                        description:
                            - Beacon interval. The time between beacon frames in msec (the actual range of beacon interval depends on the AP platform type,
                               default = 100).
                    call-admission-control:
                        description:
                            - Enable/disable WiFi multimedia (WMM) call admission control to optimize WiFi bandwidth use for VoIP calls. New VoIP calls are
                               only accepted if there is enough bandwidth available to support them.
                        choices:
                            - enable
                            - disable
                    call-capacity:
                        description:
                            - Maximum number of Voice over WLAN (VoWLAN) phones supported by the radio (0 - 60, default = 10).
                    channel:
                        description:
                            - Selected list of wireless radio channels.
                        suboptions:
                            chan:
                                description:
                                    - Channel number.
                                required: true
                    channel-bonding:
                        description:
                            - "Channel bandwidth: 80, 40, or 20MHz. Channels may use both 20 and 40 by enabling coexistence."
                        choices:
                            - 80MHz
                            - 40MHz
                            - 20MHz
                    channel-utilization:
                        description:
                            - Enable/disable measuring channel utilization.
                        choices:
                            - enable
                            - disable
                    coexistence:
                        description:
                            - Enable/disable allowing both HT20 and HT40 on the same radio (default = enable).
                        choices:
                            - enable
                            - disable
                    darrp:
                        description:
                            - Enable/disable Distributed Automatic Radio Resource Provisioning (DARRP) to make sure the radio is always using the most optimal
                               channel (default = disable).
                        choices:
                            - enable
                            - disable
                    dtim:
                        description:
                            - DTIM interval. The frequency to transmit Delivery Traffic Indication Message (or Map) (DTIM) messages (1 - 255, default = 1).
                               Set higher to save client battery life.
                    frag-threshold:
                        description:
                            - Maximum packet size that can be sent without fragmentation (800 - 2346 bytes, default = 2346).
                    frequency-handoff:
                        description:
                            - Enable/disable frequency handoff of clients to other channels (default = disable).
                        choices:
                            - enable
                            - disable
                    max-clients:
                        description:
                            - Maximum number of stations (STAs) or WiFi clients supported by the radio. Range depends on the hardware.
                    max-distance:
                        description:
                            - Maximum expected distance between the AP and clients (0 - 54000 m, default = 0).
                    mode:
                        description:
                            - Mode of radio 1. Radio 1 can be disabled, configured as an access point, a rogue AP monitor, or a sniffer.
                        choices:
                            - disabled
                            - ap
                            - monitor
                            - sniffer
                    power-level:
                        description:
                            - Radio power level as a percentage of the maximum transmit power (0 - 100, default = 100).
                    powersave-optimize:
                        description:
                            - Enable client power-saving features such as TIM, AC VO, and OBSS etc.
                        choices:
                            - tim
                            - ac-vo
                            - no-obss-scan
                            - no-11b-rate
                            - client-rate-follow
                    protection-mode:
                        description:
                            - Enable/disable 802.11g protection modes to support backwards compatibility with older clients (rtscts, ctsonly, disable).
                        choices:
                            - rtscts
                            - ctsonly
                            - disable
                    radio-id:
                        description:
                            - radio-id
                    rts-threshold:
                        description:
                            - Maximum packet size for RTS transmissions, specifying the maximum size of a data packet before RTS/CTS (256 - 2346 bytes,
                               default = 2346).
                    short-guard-interval:
                        description:
                            - Use either the short guard interval (Short GI) of 400 ns or the long guard interval (Long GI) of 800 ns.
                        choices:
                            - enable
                            - disable
                    spectrum-analysis:
                        description:
                            - Enable/disable spectrum analysis to find interference that would negatively impact wireless performance.
                        choices:
                            - enable
                            - disable
                    transmit-optimize:
                        description:
                            - Packet transmission optimization options including power saving, aggregation limiting, retry limiting, etc. All are enabled by
                               default.
                        choices:
                            - disable
                            - power-save
                            - aggr-limit
                            - retry-limit
                            - send-bar
                    vap-all:
                        description:
                            - Enable/disable the automatic inheritance of all Virtual Access Points (VAPs) (default = enable).
                        choices:
                            - enable
                            - disable
                    vaps:
                        description:
                            - Manually selected list of Virtual Access Points (VAPs).
                        suboptions:
                            name:
                                description:
                                    - Virtual Access Point (VAP) name. Source wireless-controller.vap-group.name wireless-controller.vap.name.
                                required: true
                    wids-profile:
                        description:
                            - Wireless Intrusion Detection System (WIDS) profile name to assign to the radio. Source wireless-controller.wids-profile.name.
            radio-2:
                description:
                    - Configuration options for radio 2.
                suboptions:
                    amsdu:
                        description:
                            - Enable/disable 802.11n AMSDU support. AMSDU can improve performance if supported by your WiFi clients (default = enable).
                        choices:
                            - enable
                            - disable
                    ap-handoff:
                        description:
                            - Enable/disable AP handoff of clients to other APs (default = disable).
                        choices:
                            - enable
                            - disable
                    ap-sniffer-addr:
                        description:
                            - MAC address to monitor.
                    ap-sniffer-bufsize:
                        description:
                            - Sniffer buffer size (1 - 32 MB, default = 16).
                    ap-sniffer-chan:
                        description:
                            - Channel on which to operate the sniffer (default = 6).
                    ap-sniffer-ctl:
                        description:
                            - Enable/disable sniffer on WiFi control frame (default = enable).
                        choices:
                            - enable
                            - disable
                    ap-sniffer-data:
                        description:
                            - Enable/disable sniffer on WiFi data frame (default = enable).
                        choices:
                            - enable
                            - disable
                    ap-sniffer-mgmt-beacon:
                        description:
                            - Enable/disable sniffer on WiFi management Beacon frames (default = enable).
                        choices:
                            - enable
                            - disable
                    ap-sniffer-mgmt-other:
                        description:
                            - Enable/disable sniffer on WiFi management other frames  (default = enable).
                        choices:
                            - enable
                            - disable
                    ap-sniffer-mgmt-probe:
                        description:
                            - Enable/disable sniffer on WiFi management probe frames (default = enable).
                        choices:
                            - enable
                            - disable
                    auto-power-high:
                        description:
                            - Automatic transmit power high limit in dBm (the actual range of transmit power depends on the AP platform type).
                    auto-power-level:
                        description:
                            - Enable/disable automatic power-level adjustment to prevent co-channel interference (default = disable).
                        choices:
                            - enable
                            - disable
                    auto-power-low:
                        description:
                            - Automatic transmission power low limit in dBm (the actual range of transmit power depends on the AP platform type).
                    band:
                        description:
                            - WiFi band that Radio 2 operates on.
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
                    bandwidth-admission-control:
                        description:
                            - Enable/disable WiFi multimedia (WMM) bandwidth admission control to optimize WiFi bandwidth use. A request to join the wireless
                               network is only allowed if the access point has enough bandwidth to support it.
                        choices:
                            - enable
                            - disable
                    bandwidth-capacity:
                        description:
                            - Maximum bandwidth capacity allowed (1 - 600000 Kbps, default = 2000).
                    beacon-interval:
                        description:
                            - Beacon interval. The time between beacon frames in msec (the actual range of beacon interval depends on the AP platform type,
                               default = 100).
                    call-admission-control:
                        description:
                            - Enable/disable WiFi multimedia (WMM) call admission control to optimize WiFi bandwidth use for VoIP calls. New VoIP calls are
                               only accepted if there is enough bandwidth available to support them.
                        choices:
                            - enable
                            - disable
                    call-capacity:
                        description:
                            - Maximum number of Voice over WLAN (VoWLAN) phones supported by the radio (0 - 60, default = 10).
                    channel:
                        description:
                            - Selected list of wireless radio channels.
                        suboptions:
                            chan:
                                description:
                                    - Channel number.
                                required: true
                    channel-bonding:
                        description:
                            - "Channel bandwidth: 80, 40, or 20MHz. Channels may use both 20 and 40 by enabling coexistence."
                        choices:
                            - 80MHz
                            - 40MHz
                            - 20MHz
                    channel-utilization:
                        description:
                            - Enable/disable measuring channel utilization.
                        choices:
                            - enable
                            - disable
                    coexistence:
                        description:
                            - Enable/disable allowing both HT20 and HT40 on the same radio (default = enable).
                        choices:
                            - enable
                            - disable
                    darrp:
                        description:
                            - Enable/disable Distributed Automatic Radio Resource Provisioning (DARRP) to make sure the radio is always using the most optimal
                               channel (default = disable).
                        choices:
                            - enable
                            - disable
                    dtim:
                        description:
                            - DTIM interval. The frequency to transmit Delivery Traffic Indication Message (or Map) (DTIM) messages (1 - 255, default = 1).
                               Set higher to save client battery life.
                    frag-threshold:
                        description:
                            - Maximum packet size that can be sent without fragmentation (800 - 2346 bytes, default = 2346).
                    frequency-handoff:
                        description:
                            - Enable/disable frequency handoff of clients to other channels (default = disable).
                        choices:
                            - enable
                            - disable
                    max-clients:
                        description:
                            - Maximum number of stations (STAs) or WiFi clients supported by the radio. Range depends on the hardware.
                    max-distance:
                        description:
                            - Maximum expected distance between the AP and clients (0 - 54000 m, default = 0).
                    mode:
                        description:
                            - Mode of radio 2. Radio 2 can be disabled, configured as an access point, a rogue AP monitor, or a sniffer.
                        choices:
                            - disabled
                            - ap
                            - monitor
                            - sniffer
                    power-level:
                        description:
                            - Radio power level as a percentage of the maximum transmit power (0 - 100, default = 100).
                    powersave-optimize:
                        description:
                            - Enable client power-saving features such as TIM, AC VO, and OBSS etc.
                        choices:
                            - tim
                            - ac-vo
                            - no-obss-scan
                            - no-11b-rate
                            - client-rate-follow
                    protection-mode:
                        description:
                            - Enable/disable 802.11g protection modes to support backwards compatibility with older clients (rtscts, ctsonly, disable).
                        choices:
                            - rtscts
                            - ctsonly
                            - disable
                    radio-id:
                        description:
                            - radio-id
                    rts-threshold:
                        description:
                            - Maximum packet size for RTS transmissions, specifying the maximum size of a data packet before RTS/CTS (256 - 2346 bytes,
                               default = 2346).
                    short-guard-interval:
                        description:
                            - Use either the short guard interval (Short GI) of 400 ns or the long guard interval (Long GI) of 800 ns.
                        choices:
                            - enable
                            - disable
                    spectrum-analysis:
                        description:
                            - Enable/disable spectrum analysis to find interference that would negatively impact wireless performance.
                        choices:
                            - enable
                            - disable
                    transmit-optimize:
                        description:
                            - Packet transmission optimization options including power saving, aggregation limiting, retry limiting, etc. All are enabled by
                               default.
                        choices:
                            - disable
                            - power-save
                            - aggr-limit
                            - retry-limit
                            - send-bar
                    vap-all:
                        description:
                            - Enable/disable the automatic inheritance of all Virtual Access Points (VAPs) (default = enable).
                        choices:
                            - enable
                            - disable
                    vaps:
                        description:
                            - Manually selected list of Virtual Access Points (VAPs).
                        suboptions:
                            name:
                                description:
                                    - Virtual Access Point (VAP) name. Source wireless-controller.vap-group.name wireless-controller.vap.name.
                                required: true
                    wids-profile:
                        description:
                            - Wireless Intrusion Detection System (WIDS) profile name to assign to the radio. Source wireless-controller.wids-profile.name.
            split-tunneling-acl:
                description:
                    - Split tunneling ACL filter list.
                suboptions:
                    dest-ip:
                        description:
                            - Destination IP and mask for the split-tunneling subnet.
                    id:
                        description:
                            - ID.
                        required: true
            split-tunneling-acl-local-ap-subnet:
                description:
                    - Enable/disable automatically adding local subnetwork of FortiAP to split-tunneling ACL (default = disable).
                choices:
                    - enable
                    - disable
            split-tunneling-acl-path:
                description:
                    - Split tunneling ACL path is local/tunnel.
                choices:
                    - tunnel
                    - local
            tun-mtu-downlink:
                description:
                    - Downlink CAPWAP tunnel MTU (0, 576, or 1500 bytes, default = 0).
            tun-mtu-uplink:
                description:
                    - Uplink CAPWAP tunnel MTU (0, 576, or 1500 bytes, default = 0).
            wan-port-mode:
                description:
                    - Enable/disable using a WAN port as a LAN port.
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
  tasks:
  - name: Configure WTP profiles or FortiAP profiles that define radio settings for manageable FortiAP platforms.
    fortios_wireless_controller_wtp_profile:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      wireless_controller_wtp_profile:
        state: "present"
        allowaccess: "telnet"
        ap-country: "NA"
        ble-profile: "<your_own_value> (source wireless-controller.ble-profile.name)"
        comment: "Comment."
        control-message-offload: "ebp-frame"
        deny-mac-list:
         -
            id:  "9"
            mac: "<your_own_value>"
        dtls-in-kernel: "enable"
        dtls-policy: "clear-text"
        energy-efficient-ethernet: "enable"
        ext-info-enable: "enable"
        handoff-roaming: "enable"
        handoff-rssi: "16"
        handoff-sta-thresh: "17"
        ip-fragment-preventing: "tcp-mss-adjust"
        lan:
            port-mode: "offline"
            port-ssid: "<your_own_value> (source wireless-controller.vap.name)"
            port1-mode: "offline"
            port1-ssid: "<your_own_value> (source wireless-controller.vap.name)"
            port2-mode: "offline"
            port2-ssid: "<your_own_value> (source wireless-controller.vap.name)"
            port3-mode: "offline"
            port3-ssid: "<your_own_value> (source wireless-controller.vap.name)"
            port4-mode: "offline"
            port4-ssid: "<your_own_value> (source wireless-controller.vap.name)"
            port5-mode: "offline"
            port5-ssid: "<your_own_value> (source wireless-controller.vap.name)"
            port6-mode: "offline"
            port6-ssid: "<your_own_value> (source wireless-controller.vap.name)"
            port7-mode: "offline"
            port7-ssid: "<your_own_value> (source wireless-controller.vap.name)"
            port8-mode: "offline"
            port8-ssid: "<your_own_value> (source wireless-controller.vap.name)"
        lbs:
            aeroscout: "enable"
            aeroscout-ap-mac: "bssid"
            aeroscout-mmu-report: "enable"
            aeroscout-mu: "enable"
            aeroscout-mu-factor: "43"
            aeroscout-mu-timeout: "44"
            aeroscout-server-ip: "<your_own_value>"
            aeroscout-server-port: "46"
            ekahau-blink-mode: "enable"
            ekahau-tag: "<your_own_value>"
            erc-server-ip: "<your_own_value>"
            erc-server-port: "50"
            fortipresence: "foreign"
            fortipresence-frequency: "52"
            fortipresence-port: "53"
            fortipresence-project: "<your_own_value>"
            fortipresence-rogue: "enable"
            fortipresence-secret: "<your_own_value>"
            fortipresence-server: "<your_own_value>"
            fortipresence-unassoc: "enable"
            station-locate: "enable"
        led-schedules:
         -
            name: "default_name_61 (source firewall.schedule.group.name firewall.schedule.recurring.name)"
        led-state: "enable"
        lldp: "enable"
        login-passwd: "<your_own_value>"
        login-passwd-change: "yes"
        max-clients: "66"
        name: "default_name_67"
        platform:
            type: "AP-11N"
        poe-mode: "auto"
        radio-1:
            amsdu: "enable"
            ap-handoff: "enable"
            ap-sniffer-addr: "<your_own_value>"
            ap-sniffer-bufsize: "75"
            ap-sniffer-chan: "76"
            ap-sniffer-ctl: "enable"
            ap-sniffer-data: "enable"
            ap-sniffer-mgmt-beacon: "enable"
            ap-sniffer-mgmt-other: "enable"
            ap-sniffer-mgmt-probe: "enable"
            auto-power-high: "82"
            auto-power-level: "enable"
            auto-power-low: "84"
            band: "802.11a"
            bandwidth-admission-control: "enable"
            bandwidth-capacity: "87"
            beacon-interval: "88"
            call-admission-control: "enable"
            call-capacity: "90"
            channel:
             -
                chan: "<your_own_value>"
            channel-bonding: "80MHz"
            channel-utilization: "enable"
            coexistence: "enable"
            darrp: "enable"
            dtim: "97"
            frag-threshold: "98"
            frequency-handoff: "enable"
            max-clients: "100"
            max-distance: "101"
            mode: "disabled"
            power-level: "103"
            powersave-optimize: "tim"
            protection-mode: "rtscts"
            radio-id: "106"
            rts-threshold: "107"
            short-guard-interval: "enable"
            spectrum-analysis: "enable"
            transmit-optimize: "disable"
            vap-all: "enable"
            vaps:
             -
                name: "default_name_113 (source wireless-controller.vap-group.name wireless-controller.vap.name)"
            wids-profile: "<your_own_value> (source wireless-controller.wids-profile.name)"
        radio-2:
            amsdu: "enable"
            ap-handoff: "enable"
            ap-sniffer-addr: "<your_own_value>"
            ap-sniffer-bufsize: "119"
            ap-sniffer-chan: "120"
            ap-sniffer-ctl: "enable"
            ap-sniffer-data: "enable"
            ap-sniffer-mgmt-beacon: "enable"
            ap-sniffer-mgmt-other: "enable"
            ap-sniffer-mgmt-probe: "enable"
            auto-power-high: "126"
            auto-power-level: "enable"
            auto-power-low: "128"
            band: "802.11a"
            bandwidth-admission-control: "enable"
            bandwidth-capacity: "131"
            beacon-interval: "132"
            call-admission-control: "enable"
            call-capacity: "134"
            channel:
             -
                chan: "<your_own_value>"
            channel-bonding: "80MHz"
            channel-utilization: "enable"
            coexistence: "enable"
            darrp: "enable"
            dtim: "141"
            frag-threshold: "142"
            frequency-handoff: "enable"
            max-clients: "144"
            max-distance: "145"
            mode: "disabled"
            power-level: "147"
            powersave-optimize: "tim"
            protection-mode: "rtscts"
            radio-id: "150"
            rts-threshold: "151"
            short-guard-interval: "enable"
            spectrum-analysis: "enable"
            transmit-optimize: "disable"
            vap-all: "enable"
            vaps:
             -
                name: "default_name_157 (source wireless-controller.vap-group.name wireless-controller.vap.name)"
            wids-profile: "<your_own_value> (source wireless-controller.wids-profile.name)"
        split-tunneling-acl:
         -
            dest-ip: "<your_own_value>"
            id:  "161"
        split-tunneling-acl-local-ap-subnet: "enable"
        split-tunneling-acl-path: "tunnel"
        tun-mtu-downlink: "164"
        tun-mtu-uplink: "165"
        wan-port-mode: "wan-lan"
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


def filter_wireless_controller_wtp_profile_data(json):
    option_list = ['allowaccess', 'ap-country', 'ble-profile',
                   'comment', 'control-message-offload', 'deny-mac-list',
                   'dtls-in-kernel', 'dtls-policy', 'energy-efficient-ethernet',
                   'ext-info-enable', 'handoff-roaming', 'handoff-rssi',
                   'handoff-sta-thresh', 'ip-fragment-preventing', 'lan',
                   'lbs', 'led-schedules', 'led-state',
                   'lldp', 'login-passwd', 'login-passwd-change',
                   'max-clients', 'name', 'platform',
                   'poe-mode', 'radio-1', 'radio-2',
                   'split-tunneling-acl', 'split-tunneling-acl-local-ap-subnet', 'split-tunneling-acl-path',
                   'tun-mtu-downlink', 'tun-mtu-uplink', 'wan-port-mode']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def wireless_controller_wtp_profile(data, fos):
    vdom = data['vdom']
    wireless_controller_wtp_profile_data = data['wireless_controller_wtp_profile']
    filtered_data = filter_wireless_controller_wtp_profile_data(wireless_controller_wtp_profile_data)

    if wireless_controller_wtp_profile_data['state'] == "present":
        return fos.set('wireless-controller',
                       'wtp-profile',
                       data=filtered_data,
                       vdom=vdom)

    elif wireless_controller_wtp_profile_data['state'] == "absent":
        return fos.delete('wireless-controller',
                          'wtp-profile',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_wireless_controller(data, fos):
    login(data, fos)

    if data['wireless_controller_wtp_profile']:
        resp = wireless_controller_wtp_profile(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "wireless_controller_wtp_profile": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "allowaccess": {"required": False, "type": "str",
                                "choices": ["telnet", "http", "https",
                                            "ssh"]},
                "ap-country": {"required": False, "type": "str",
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
                "ble-profile": {"required": False, "type": "str"},
                "comment": {"required": False, "type": "str"},
                "control-message-offload": {"required": False, "type": "str",
                                            "choices": ["ebp-frame", "aeroscout-tag", "ap-list",
                                                        "sta-list", "sta-cap-list", "stats",
                                                        "aeroscout-mu"]},
                "deny-mac-list": {"required": False, "type": "list",
                                  "options": {
                                      "id": {"required": True, "type": "int"},
                                      "mac": {"required": False, "type": "str"}
                                  }},
                "dtls-in-kernel": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "dtls-policy": {"required": False, "type": "str",
                                "choices": ["clear-text", "dtls-enabled", "ipsec-vpn"]},
                "energy-efficient-ethernet": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                "ext-info-enable": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "handoff-roaming": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "handoff-rssi": {"required": False, "type": "int"},
                "handoff-sta-thresh": {"required": False, "type": "int"},
                "ip-fragment-preventing": {"required": False, "type": "str",
                                           "choices": ["tcp-mss-adjust", "icmp-unreachable"]},
                "lan": {"required": False, "type": "dict",
                        "options": {
                            "port-mode": {"required": False, "type": "str",
                                          "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                      "bridge-to-ssid"]},
                            "port-ssid": {"required": False, "type": "str"},
                            "port1-mode": {"required": False, "type": "str",
                                           "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                       "bridge-to-ssid"]},
                            "port1-ssid": {"required": False, "type": "str"},
                            "port2-mode": {"required": False, "type": "str",
                                           "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                       "bridge-to-ssid"]},
                            "port2-ssid": {"required": False, "type": "str"},
                            "port3-mode": {"required": False, "type": "str",
                                           "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                       "bridge-to-ssid"]},
                            "port3-ssid": {"required": False, "type": "str"},
                            "port4-mode": {"required": False, "type": "str",
                                           "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                       "bridge-to-ssid"]},
                            "port4-ssid": {"required": False, "type": "str"},
                            "port5-mode": {"required": False, "type": "str",
                                           "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                       "bridge-to-ssid"]},
                            "port5-ssid": {"required": False, "type": "str"},
                            "port6-mode": {"required": False, "type": "str",
                                           "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                       "bridge-to-ssid"]},
                            "port6-ssid": {"required": False, "type": "str"},
                            "port7-mode": {"required": False, "type": "str",
                                           "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                       "bridge-to-ssid"]},
                            "port7-ssid": {"required": False, "type": "str"},
                            "port8-mode": {"required": False, "type": "str",
                                           "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                       "bridge-to-ssid"]},
                            "port8-ssid": {"required": False, "type": "str"}
                        }},
                "lbs": {"required": False, "type": "dict",
                        "options": {
                            "aeroscout": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                            "aeroscout-ap-mac": {"required": False, "type": "str",
                                                 "choices": ["bssid", "board-mac"]},
                            "aeroscout-mmu-report": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]},
                            "aeroscout-mu": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                            "aeroscout-mu-factor": {"required": False, "type": "int"},
                            "aeroscout-mu-timeout": {"required": False, "type": "int"},
                            "aeroscout-server-ip": {"required": False, "type": "str"},
                            "aeroscout-server-port": {"required": False, "type": "int"},
                            "ekahau-blink-mode": {"required": False, "type": "str",
                                                  "choices": ["enable", "disable"]},
                            "ekahau-tag": {"required": False, "type": "str"},
                            "erc-server-ip": {"required": False, "type": "str"},
                            "erc-server-port": {"required": False, "type": "int"},
                            "fortipresence": {"required": False, "type": "str",
                                              "choices": ["foreign", "both", "disable"]},
                            "fortipresence-frequency": {"required": False, "type": "int"},
                            "fortipresence-port": {"required": False, "type": "int"},
                            "fortipresence-project": {"required": False, "type": "str"},
                            "fortipresence-rogue": {"required": False, "type": "str",
                                                    "choices": ["enable", "disable"]},
                            "fortipresence-secret": {"required": False, "type": "str"},
                            "fortipresence-server": {"required": False, "type": "str"},
                            "fortipresence-unassoc": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                            "station-locate": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]}
                        }},
                "led-schedules": {"required": False, "type": "list",
                                  "options": {
                                      "name": {"required": True, "type": "str"}
                                  }},
                "led-state": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "lldp": {"required": False, "type": "str",
                         "choices": ["enable", "disable"]},
                "login-passwd": {"required": False, "type": "str"},
                "login-passwd-change": {"required": False, "type": "str",
                                        "choices": ["yes", "default", "no"]},
                "max-clients": {"required": False, "type": "int"},
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
                "poe-mode": {"required": False, "type": "str",
                             "choices": ["auto", "8023af", "8023at",
                                         "power-adapter"]},
                "radio-1": {"required": False, "type": "dict",
                            "options": {
                                "amsdu": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                                "ap-handoff": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                                "ap-sniffer-addr": {"required": False, "type": "str"},
                                "ap-sniffer-bufsize": {"required": False, "type": "int"},
                                "ap-sniffer-chan": {"required": False, "type": "int"},
                                "ap-sniffer-ctl": {"required": False, "type": "str",
                                                   "choices": ["enable", "disable"]},
                                "ap-sniffer-data": {"required": False, "type": "str",
                                                    "choices": ["enable", "disable"]},
                                "ap-sniffer-mgmt-beacon": {"required": False, "type": "str",
                                                           "choices": ["enable", "disable"]},
                                "ap-sniffer-mgmt-other": {"required": False, "type": "str",
                                                          "choices": ["enable", "disable"]},
                                "ap-sniffer-mgmt-probe": {"required": False, "type": "str",
                                                          "choices": ["enable", "disable"]},
                                "auto-power-high": {"required": False, "type": "int"},
                                "auto-power-level": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]},
                                "auto-power-low": {"required": False, "type": "int"},
                                "band": {"required": False, "type": "str",
                                         "choices": ["802.11a", "802.11b", "802.11g",
                                                     "802.11n", "802.11n-5G", "802.11ac",
                                                     "802.11n,g-only", "802.11g-only", "802.11n-only",
                                                     "802.11n-5G-only", "802.11ac,n-only", "802.11ac-only"]},
                                "bandwidth-admission-control": {"required": False, "type": "str",
                                                                "choices": ["enable", "disable"]},
                                "bandwidth-capacity": {"required": False, "type": "int"},
                                "beacon-interval": {"required": False, "type": "int"},
                                "call-admission-control": {"required": False, "type": "str",
                                                           "choices": ["enable", "disable"]},
                                "call-capacity": {"required": False, "type": "int"},
                                "channel": {"required": False, "type": "list",
                                            "options": {
                                                "chan": {"required": True, "type": "str"}
                                            }},
                                "channel-bonding": {"required": False, "type": "str",
                                                    "choices": ["80MHz", "40MHz", "20MHz"]},
                                "channel-utilization": {"required": False, "type": "str",
                                                        "choices": ["enable", "disable"]},
                                "coexistence": {"required": False, "type": "str",
                                                "choices": ["enable", "disable"]},
                                "darrp": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                                "dtim": {"required": False, "type": "int"},
                                "frag-threshold": {"required": False, "type": "int"},
                                "frequency-handoff": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                                "max-clients": {"required": False, "type": "int"},
                                "max-distance": {"required": False, "type": "int"},
                                "mode": {"required": False, "type": "str",
                                         "choices": ["disabled", "ap", "monitor",
                                                     "sniffer"]},
                                "power-level": {"required": False, "type": "int"},
                                "powersave-optimize": {"required": False, "type": "str",
                                                       "choices": ["tim", "ac-vo", "no-obss-scan",
                                                                   "no-11b-rate", "client-rate-follow"]},
                                "protection-mode": {"required": False, "type": "str",
                                                    "choices": ["rtscts", "ctsonly", "disable"]},
                                "radio-id": {"required": False, "type": "int"},
                                "rts-threshold": {"required": False, "type": "int"},
                                "short-guard-interval": {"required": False, "type": "str",
                                                         "choices": ["enable", "disable"]},
                                "spectrum-analysis": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                                "transmit-optimize": {"required": False, "type": "str",
                                                      "choices": ["disable", "power-save", "aggr-limit",
                                                                  "retry-limit", "send-bar"]},
                                "vap-all": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                                "vaps": {"required": False, "type": "list",
                                         "options": {
                                             "name": {"required": True, "type": "str"}
                                         }},
                                "wids-profile": {"required": False, "type": "str"}
                            }},
                "radio-2": {"required": False, "type": "dict",
                            "options": {
                                "amsdu": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                                "ap-handoff": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                                "ap-sniffer-addr": {"required": False, "type": "str"},
                                "ap-sniffer-bufsize": {"required": False, "type": "int"},
                                "ap-sniffer-chan": {"required": False, "type": "int"},
                                "ap-sniffer-ctl": {"required": False, "type": "str",
                                                   "choices": ["enable", "disable"]},
                                "ap-sniffer-data": {"required": False, "type": "str",
                                                    "choices": ["enable", "disable"]},
                                "ap-sniffer-mgmt-beacon": {"required": False, "type": "str",
                                                           "choices": ["enable", "disable"]},
                                "ap-sniffer-mgmt-other": {"required": False, "type": "str",
                                                          "choices": ["enable", "disable"]},
                                "ap-sniffer-mgmt-probe": {"required": False, "type": "str",
                                                          "choices": ["enable", "disable"]},
                                "auto-power-high": {"required": False, "type": "int"},
                                "auto-power-level": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]},
                                "auto-power-low": {"required": False, "type": "int"},
                                "band": {"required": False, "type": "str",
                                         "choices": ["802.11a", "802.11b", "802.11g",
                                                     "802.11n", "802.11n-5G", "802.11ac",
                                                     "802.11n,g-only", "802.11g-only", "802.11n-only",
                                                     "802.11n-5G-only", "802.11ac,n-only", "802.11ac-only"]},
                                "bandwidth-admission-control": {"required": False, "type": "str",
                                                                "choices": ["enable", "disable"]},
                                "bandwidth-capacity": {"required": False, "type": "int"},
                                "beacon-interval": {"required": False, "type": "int"},
                                "call-admission-control": {"required": False, "type": "str",
                                                           "choices": ["enable", "disable"]},
                                "call-capacity": {"required": False, "type": "int"},
                                "channel": {"required": False, "type": "list",
                                            "options": {
                                                "chan": {"required": True, "type": "str"}
                                            }},
                                "channel-bonding": {"required": False, "type": "str",
                                                    "choices": ["80MHz", "40MHz", "20MHz"]},
                                "channel-utilization": {"required": False, "type": "str",
                                                        "choices": ["enable", "disable"]},
                                "coexistence": {"required": False, "type": "str",
                                                "choices": ["enable", "disable"]},
                                "darrp": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                                "dtim": {"required": False, "type": "int"},
                                "frag-threshold": {"required": False, "type": "int"},
                                "frequency-handoff": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                                "max-clients": {"required": False, "type": "int"},
                                "max-distance": {"required": False, "type": "int"},
                                "mode": {"required": False, "type": "str",
                                         "choices": ["disabled", "ap", "monitor",
                                                     "sniffer"]},
                                "power-level": {"required": False, "type": "int"},
                                "powersave-optimize": {"required": False, "type": "str",
                                                       "choices": ["tim", "ac-vo", "no-obss-scan",
                                                                   "no-11b-rate", "client-rate-follow"]},
                                "protection-mode": {"required": False, "type": "str",
                                                    "choices": ["rtscts", "ctsonly", "disable"]},
                                "radio-id": {"required": False, "type": "int"},
                                "rts-threshold": {"required": False, "type": "int"},
                                "short-guard-interval": {"required": False, "type": "str",
                                                         "choices": ["enable", "disable"]},
                                "spectrum-analysis": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                                "transmit-optimize": {"required": False, "type": "str",
                                                      "choices": ["disable", "power-save", "aggr-limit",
                                                                  "retry-limit", "send-bar"]},
                                "vap-all": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                                "vaps": {"required": False, "type": "list",
                                         "options": {
                                             "name": {"required": True, "type": "str"}
                                         }},
                                "wids-profile": {"required": False, "type": "str"}
                            }},
                "split-tunneling-acl": {"required": False, "type": "list",
                                        "options": {
                                            "dest-ip": {"required": False, "type": "str"},
                                            "id": {"required": True, "type": "int"}
                                        }},
                "split-tunneling-acl-local-ap-subnet": {"required": False, "type": "str",
                                                        "choices": ["enable", "disable"]},
                "split-tunneling-acl-path": {"required": False, "type": "str",
                                             "choices": ["tunnel", "local"]},
                "tun-mtu-downlink": {"required": False, "type": "int"},
                "tun-mtu-uplink": {"required": False, "type": "int"},
                "wan-port-mode": {"required": False, "type": "str",
                                  "choices": ["wan-lan", "wan-only"]}

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
