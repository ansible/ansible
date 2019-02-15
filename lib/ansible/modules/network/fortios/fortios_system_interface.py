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
module: fortios_system_interface
short_description: Configure interfaces in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify system feature and interface category.
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
    system_interface:
        description:
            - Configure interfaces.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            ac-name:
                description:
                    - PPPoE server name.
            aggregate:
                description:
                    - Aggregate interface.
            algorithm:
                description:
                    - Frame distribution algorithm.
                choices:
                    - L2
                    - L3
                    - L4
            alias:
                description:
                    - Alias will be displayed with the interface name to make it easier to distinguish.
            allowaccess:
                description:
                    - Permitted types of management access to this interface.
                choices:
                    - ping
                    - https
                    - ssh
                    - snmp
                    - http
                    - telnet
                    - fgfm
                    - radius-acct
                    - probe-response
                    - capwap
                    - ftm
            ap-discover:
                description:
                    - Enable/disable automatic registration of unknown FortiAP devices.
                choices:
                    - enable
                    - disable
            arpforward:
                description:
                    - Enable/disable ARP forwarding.
                choices:
                    - enable
                    - disable
            auth-type:
                description:
                    - PPP authentication type to use.
                choices:
                    - auto
                    - pap
                    - chap
                    - mschapv1
                    - mschapv2
            auto-auth-extension-device:
                description:
                    - Enable/disable automatic authorization of dedicated Fortinet extension device on this interface.
                choices:
                    - enable
                    - disable
            bfd:
                description:
                    - Bidirectional Forwarding Detection (BFD) settings.
                choices:
                    - global
                    - enable
                    - disable
            bfd-desired-min-tx:
                description:
                    - BFD desired minimal transmit interval.
            bfd-detect-mult:
                description:
                    - BFD detection multiplier.
            bfd-required-min-rx:
                description:
                    - BFD required minimal receive interval.
            broadcast-forticlient-discovery:
                description:
                    - Enable/disable broadcasting FortiClient discovery messages.
                choices:
                    - enable
                    - disable
            broadcast-forward:
                description:
                    - Enable/disable broadcast forwarding.
                choices:
                    - enable
                    - disable
            captive-portal:
                description:
                    - Enable/disable captive portal.
            cli-conn-status:
                description:
                    - CLI connection status.
            color:
                description:
                    - Color of icon on the GUI.
            dedicated-to:
                description:
                    - Configure interface for single purpose.
                choices:
                    - none
                    - management
            defaultgw:
                description:
                    - Enable to get the gateway IP from the DHCP or PPPoE server.
                choices:
                    - enable
                    - disable
            description:
                description:
                    - Description.
            detected-peer-mtu:
                description:
                    - MTU of detected peer (0 - 4294967295).
            detectprotocol:
                description:
                    - Protocols used to detect the server.
                choices:
                    - ping
                    - tcp-echo
                    - udp-echo
            detectserver:
                description:
                    - Gateway's ping server for this IP.
            device-access-list:
                description:
                    - Device access list.
            device-identification:
                description:
                    - Enable/disable passively gathering of device identity information about the devices on the network connected to this interface.
                choices:
                    - enable
                    - disable
            device-identification-active-scan:
                description:
                    - Enable/disable active gathering of device identity information about the devices on the network connected to this interface.
                choices:
                    - enable
                    - disable
            device-netscan:
                description:
                    - Enable/disable inclusion of devices detected on this interface in network vulnerability scans.
                choices:
                    - disable
                    - enable
            device-user-identification:
                description:
                    - Enable/disable passive gathering of user identity information about users on this interface.
                choices:
                    - enable
                    - disable
            devindex:
                description:
                    - Device Index.
            dhcp-client-identifier:
                description:
                    - DHCP client identifier.
            dhcp-relay-agent-option:
                description:
                    - Enable/disable DHCP relay agent option.
                choices:
                    - enable
                    - disable
            dhcp-relay-ip:
                description:
                    - DHCP relay IP address.
            dhcp-relay-service:
                description:
                    - Enable/disable allowing this interface to act as a DHCP relay.
                choices:
                    - disable
                    - enable
            dhcp-relay-type:
                description:
                    - DHCP relay type (regular or IPsec).
                choices:
                    - regular
                    - ipsec
            dhcp-renew-time:
                description:
                    - DHCP renew time in seconds (300-604800), 0 means use the renew time provided by the server.
            disc-retry-timeout:
                description:
                    - Time in seconds to wait before retrying to start a PPPoE discovery, 0 means no timeout.
            disconnect-threshold:
                description:
                    - Time in milliseconds to wait before sending a notification that this interface is down or disconnected.
            distance:
                description:
                    - Distance for routes learned through PPPoE or DHCP, lower distance indicates preferred route.
            dns-server-override:
                description:
                    - Enable/disable use DNS acquired by DHCP or PPPoE.
                choices:
                    - enable
                    - disable
            drop-fragment:
                description:
                    - Enable/disable drop fragment packets.
                choices:
                    - enable
                    - disable
            drop-overlapped-fragment:
                description:
                    - Enable/disable drop overlapped fragment packets.
                choices:
                    - enable
                    - disable
            egress-shaping-profile:
                description:
                    - Outgoing traffic shaping profile.
            endpoint-compliance:
                description:
                    - Enable/disable endpoint compliance enforcement.
                choices:
                    - enable
                    - disable
            estimated-downstream-bandwidth:
                description:
                    - Estimated maximum downstream bandwidth (kbps). Used to estimate link utilization.
            estimated-upstream-bandwidth:
                description:
                    - Estimated maximum upstream bandwidth (kbps). Used to estimate link utilization.
            explicit-ftp-proxy:
                description:
                    - Enable/disable the explicit FTP proxy on this interface.
                choices:
                    - enable
                    - disable
            explicit-web-proxy:
                description:
                    - Enable/disable the explicit web proxy on this interface.
                choices:
                    - enable
                    - disable
            external:
                description:
                    - Enable/disable identifying the interface as an external interface (which usually means it's connected to the Internet).
                choices:
                    - enable
                    - disable
            fail-action-on-extender:
                description:
                    - Action on extender when interface fail .
                choices:
                    - soft-restart
                    - hard-restart
                    - reboot
            fail-alert-interfaces:
                description:
                    - Names of the FortiGate interfaces from which the link failure alert is sent for this interface.
                suboptions:
                    name:
                        description:
                            - Names of the physical interfaces belonging to the aggregate or redundant interface. Source system.interface.name.
                        required: true
            fail-alert-method:
                description:
                    - Select link-failed-signal or link-down method to alert about a failed link.
                choices:
                    - link-failed-signal
                    - link-down
            fail-detect:
                description:
                    - Enable/disable fail detection features for this interface.
                choices:
                    - enable
                    - disable
            fail-detect-option:
                description:
                    - Options for detecting that this interface has failed.
                choices:
                    - detectserver
                    - link-down
            fortiheartbeat:
                description:
                    - Enable/disable FortiHeartBeat (FortiTelemetry on GUI).
                choices:
                    - enable
                    - disable
            fortilink:
                description:
                    - Enable FortiLink to dedicate this interface to manage other Fortinet devices.
                choices:
                    - enable
                    - disable
            fortilink-backup-link:
                description:
                    - fortilink split interface backup link.
            fortilink-split-interface:
                description:
                    - Enable/disable FortiLink split interface to connect member link to different FortiSwitch in stack for uplink redundancy (maximum 2
                       interfaces in the "members" command).
                choices:
                    - enable
                    - disable
            fortilink-stacking:
                description:
                    - Enable/disable FortiLink switch-stacking on this interface.
                choices:
                    - enable
                    - disable
            forward-domain:
                description:
                    - Transparent mode forward domain.
            gwdetect:
                description:
                    - Enable/disable detect gateway alive for first.
                choices:
                    - enable
                    - disable
            ha-priority:
                description:
                    - HA election priority for the PING server.
            icmp-accept-redirect:
                description:
                    - Enable/disable ICMP accept redirect.
                choices:
                    - enable
                    - disable
            icmp-send-redirect:
                description:
                    - Enable/disable ICMP send redirect.
                choices:
                    - enable
                    - disable
            ident-accept:
                description:
                    - Enable/disable authentication for this interface.
                choices:
                    - enable
                    - disable
            idle-timeout:
                description:
                    - PPPoE auto disconnect after idle timeout seconds, 0 means no timeout.
            inbandwidth:
                description:
                    - Bandwidth limit for incoming traffic (0 - 16776000 kbps), 0 means unlimited.
            ingress-spillover-threshold:
                description:
                    - Ingress Spillover threshold (0 - 16776000 kbps).
            interface:
                description:
                    - Interface name. Source system.interface.name.
            internal:
                description:
                    - Implicitly created.
            ip:
                description:
                    - "Interface IPv4 address and subnet mask, syntax: X.X.X.X/24."
            ipmac:
                description:
                    - Enable/disable IP/MAC binding.
                choices:
                    - enable
                    - disable
            ips-sniffer-mode:
                description:
                    - Enable/disable the use of this interface as a one-armed sniffer.
                choices:
                    - enable
                    - disable
            ipunnumbered:
                description:
                    - Unnumbered IP used for PPPoE interfaces for which no unique local address is provided.
            ipv6:
                description:
                    - IPv6 of interface.
                suboptions:
                    autoconf:
                        description:
                            - Enable/disable address auto config.
                        choices:
                            - enable
                            - disable
                    dhcp6-client-options:
                        description:
                            - DHCPv6 client options.
                        choices:
                            - rapid
                            - iapd
                            - iana
                    dhcp6-information-request:
                        description:
                            - Enable/disable DHCPv6 information request.
                        choices:
                            - enable
                            - disable
                    dhcp6-prefix-delegation:
                        description:
                            - Enable/disable DHCPv6 prefix delegation.
                        choices:
                            - enable
                            - disable
                    dhcp6-prefix-hint:
                        description:
                            - DHCPv6 prefix that will be used as a hint to the upstream DHCPv6 server.
                    dhcp6-prefix-hint-plt:
                        description:
                            - DHCPv6 prefix hint preferred life time (sec), 0 means unlimited lease time.
                    dhcp6-prefix-hint-vlt:
                        description:
                            - DHCPv6 prefix hint valid life time (sec).
                    dhcp6-relay-ip:
                        description:
                            - DHCPv6 relay IP address.
                    dhcp6-relay-service:
                        description:
                            - Enable/disable DHCPv6 relay.
                        choices:
                            - disable
                            - enable
                    dhcp6-relay-type:
                        description:
                            - DHCPv6 relay type.
                        choices:
                            - regular
                    ip6-address:
                        description:
                            - "Primary IPv6 address prefix, syntax: xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx/xxx"
                    ip6-allowaccess:
                        description:
                            - Allow management access to the interface.
                        choices:
                            - ping
                            - https
                            - ssh
                            - snmp
                            - http
                            - telnet
                            - fgfm
                            - capwap
                    ip6-default-life:
                        description:
                            - Default life (sec).
                    ip6-delegated-prefix-list:
                        description:
                            - Advertised IPv6 delegated prefix list.
                        suboptions:
                            autonomous-flag:
                                description:
                                    - Enable/disable the autonomous flag.
                                choices:
                                    - enable
                                    - disable
                            onlink-flag:
                                description:
                                    - Enable/disable the onlink flag.
                                choices:
                                    - enable
                                    - disable
                            prefix-id:
                                description:
                                    - Prefix ID.
                                required: true
                            rdnss:
                                description:
                                    - Recursive DNS server option.
                            rdnss-service:
                                description:
                                    - Recursive DNS service option.
                                choices:
                                    - delegated
                                    - default
                                    - specify
                            subnet:
                                description:
                                    -  Add subnet ID to routing prefix.
                            upstream-interface:
                                description:
                                    - Name of the interface that provides delegated information. Source system.interface.name.
                    ip6-dns-server-override:
                        description:
                            - Enable/disable using the DNS server acquired by DHCP.
                        choices:
                            - enable
                            - disable
                    ip6-extra-addr:
                        description:
                            - Extra IPv6 address prefixes of interface.
                        suboptions:
                            prefix:
                                description:
                                    - IPv6 address prefix.
                                required: true
                    ip6-hop-limit:
                        description:
                            - Hop limit (0 means unspecified).
                    ip6-link-mtu:
                        description:
                            - IPv6 link MTU.
                    ip6-manage-flag:
                        description:
                            - Enable/disable the managed flag.
                        choices:
                            - enable
                            - disable
                    ip6-max-interval:
                        description:
                            - IPv6 maximum interval (4 to 1800 sec).
                    ip6-min-interval:
                        description:
                            - IPv6 minimum interval (3 to 1350 sec).
                    ip6-mode:
                        description:
                            - Addressing mode (static, DHCP, delegated).
                        choices:
                            - static
                            - dhcp
                            - pppoe
                            - delegated
                    ip6-other-flag:
                        description:
                            - Enable/disable the other IPv6 flag.
                        choices:
                            - enable
                            - disable
                    ip6-prefix-list:
                        description:
                            - Advertised prefix list.
                        suboptions:
                            autonomous-flag:
                                description:
                                    - Enable/disable the autonomous flag.
                                choices:
                                    - enable
                                    - disable
                            dnssl:
                                description:
                                    - DNS search list option.
                                suboptions:
                                    domain:
                                        description:
                                            - Domain name.
                                        required: true
                            onlink-flag:
                                description:
                                    - Enable/disable the onlink flag.
                                choices:
                                    - enable
                                    - disable
                            preferred-life-time:
                                description:
                                    - Preferred life time (sec).
                            prefix:
                                description:
                                    - IPv6 prefix.
                                required: true
                            rdnss:
                                description:
                                    - Recursive DNS server option.
                            valid-life-time:
                                description:
                                    - Valid life time (sec).
                    ip6-reachable-time:
                        description:
                            - IPv6 reachable time (milliseconds; 0 means unspecified).
                    ip6-retrans-time:
                        description:
                            - IPv6 retransmit time (milliseconds; 0 means unspecified).
                    ip6-send-adv:
                        description:
                            - Enable/disable sending advertisements about the interface.
                        choices:
                            - enable
                            - disable
                    ip6-subnet:
                        description:
                            - " Subnet to routing prefix, syntax: xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx/xxx"
                    ip6-upstream-interface:
                        description:
                            - Interface name providing delegated information. Source system.interface.name.
                    nd-cert:
                        description:
                            - Neighbor discovery certificate. Source certificate.local.name.
                    nd-cga-modifier:
                        description:
                            - Neighbor discovery CGA modifier.
                    nd-mode:
                        description:
                            - Neighbor discovery mode.
                        choices:
                            - basic
                            - SEND-compatible
                    nd-security-level:
                        description:
                            - Neighbor discovery security level (0 - 7; 0 = least secure, default = 0).
                    nd-timestamp-delta:
                        description:
                            - Neighbor discovery timestamp delta value (1 - 3600 sec; default = 300).
                    nd-timestamp-fuzz:
                        description:
                            - Neighbor discovery timestamp fuzz factor (1 - 60 sec; default = 1).
                    vrip6_link_local:
                        description:
                            - Link-local IPv6 address of virtual router.
                    vrrp-virtual-mac6:
                        description:
                            - Enable/disable virtual MAC for VRRP.
                        choices:
                            - enable
                            - disable
                    vrrp6:
                        description:
                            - IPv6 VRRP configuration.
                        suboptions:
                            accept-mode:
                                description:
                                    - Enable/disable accept mode.
                                choices:
                                    - enable
                                    - disable
                            adv-interval:
                                description:
                                    - Advertisement interval (1 - 255 seconds).
                            preempt:
                                description:
                                    - Enable/disable preempt mode.
                                choices:
                                    - enable
                                    - disable
                            priority:
                                description:
                                    - Priority of the virtual router (1 - 255).
                            start-time:
                                description:
                                    - Startup time (1 - 255 seconds).
                            status:
                                description:
                                    - Enable/disable VRRP.
                                choices:
                                    - enable
                                    - disable
                            vrdst6:
                                description:
                                    - Monitor the route to this destination.
                            vrgrp:
                                description:
                                    - VRRP group ID (1 - 65535).
                            vrid:
                                description:
                                    - Virtual router identifier (1 - 255).
                                required: true
                            vrip6:
                                description:
                                    - IPv6 address of the virtual router.
            l2forward:
                description:
                    - Enable/disable l2 forwarding.
                choices:
                    - enable
                    - disable
            lacp-ha-slave:
                description:
                    - LACP HA slave.
                choices:
                    - enable
                    - disable
            lacp-mode:
                description:
                    - LACP mode.
                choices:
                    - static
                    - passive
                    - active
            lacp-speed:
                description:
                    - How often the interface sends LACP messages.
                choices:
                    - slow
                    - fast
            lcp-echo-interval:
                description:
                    - Time in seconds between PPPoE Link Control Protocol (LCP) echo requests.
            lcp-max-echo-fails:
                description:
                    - Maximum missed LCP echo messages before disconnect.
            link-up-delay:
                description:
                    - Number of milliseconds to wait before considering a link is up.
            lldp-transmission:
                description:
                    - Enable/disable Link Layer Discovery Protocol (LLDP) transmission.
                choices:
                    - enable
                    - disable
                    - vdom
            macaddr:
                description:
                    - Change the interface's MAC address.
            managed-device:
                description:
                    - Available when FortiLink is enabled, used for managed devices through FortiLink interface.
                suboptions:
                    name:
                        description:
                            - Managed dev identifier.
                        required: true
            management-ip:
                description:
                    - High Availability in-band management IP address of this interface.
            member:
                description:
                    - Physical interfaces that belong to the aggregate or redundant interface.
                suboptions:
                    interface-name:
                        description:
                            - Physical interface name. Source system.interface.name.
                        required: true
            min-links:
                description:
                    - Minimum number of aggregated ports that must be up.
            min-links-down:
                description:
                    - Action to take when less than the configured minimum number of links are active.
                choices:
                    - operational
                    - administrative
            mode:
                description:
                    - Addressing mode (static, DHCP, PPPoE).
                choices:
                    - static
                    - dhcp
                    - pppoe
            mtu:
                description:
                    - MTU value for this interface.
            mtu-override:
                description:
                    - Enable to set a custom MTU for this interface.
                choices:
                    - enable
                    - disable
            name:
                description:
                    - Name.
                required: true
            ndiscforward:
                description:
                    - Enable/disable NDISC forwarding.
                choices:
                    - enable
                    - disable
            netbios-forward:
                description:
                    - Enable/disable NETBIOS forwarding.
                choices:
                    - disable
                    - enable
            netflow-sampler:
                description:
                    - Enable/disable NetFlow on this interface and set the data that NetFlow collects (rx, tx, or both).
                choices:
                    - disable
                    - tx
                    - rx
                    - both
            outbandwidth:
                description:
                    - Bandwidth limit for outgoing traffic (0 - 16776000 kbps).
            padt-retry-timeout:
                description:
                    - PPPoE Active Discovery Terminate (PADT) used to terminate sessions after an idle time.
            password:
                description:
                    - PPPoE account's password.
            ping-serv-status:
                description:
                    - PING server status.
            polling-interval:
                description:
                    - sFlow polling interval (1 - 255 sec).
            pppoe-unnumbered-negotiate:
                description:
                    - Enable/disable PPPoE unnumbered negotiation.
                choices:
                    - enable
                    - disable
            pptp-auth-type:
                description:
                    - PPTP authentication type.
                choices:
                    - auto
                    - pap
                    - chap
                    - mschapv1
                    - mschapv2
            pptp-client:
                description:
                    - Enable/disable PPTP client.
                choices:
                    - enable
                    - disable
            pptp-password:
                description:
                    - PPTP password.
            pptp-server-ip:
                description:
                    - PPTP server IP address.
            pptp-timeout:
                description:
                    - Idle timer in minutes (0 for disabled).
            pptp-user:
                description:
                    - PPTP user name.
            preserve-session-route:
                description:
                    - Enable/disable preservation of session route when dirty.
                choices:
                    - enable
                    - disable
            priority:
                description:
                    - Priority of learned routes.
            priority-override:
                description:
                    - Enable/disable fail back to higher priority port once recovered.
                choices:
                    - enable
                    - disable
            proxy-captive-portal:
                description:
                    - Enable/disable proxy captive portal on this interface.
                choices:
                    - enable
                    - disable
            redundant-interface:
                description:
                    - Redundant interface.
            remote-ip:
                description:
                    - Remote IP address of tunnel.
            replacemsg-override-group:
                description:
                    - Replacement message override group.
            role:
                description:
                    - Interface role.
                choices:
                    - lan
                    - wan
                    - dmz
                    - undefined
            sample-direction:
                description:
                    - Data that NetFlow collects (rx, tx, or both).
                choices:
                    - tx
                    - rx
                    - both
            sample-rate:
                description:
                    - sFlow sample rate (10 - 99999).
            scan-botnet-connections:
                description:
                    - Enable monitoring or blocking connections to Botnet servers through this interface.
                choices:
                    - disable
                    - block
                    - monitor
            secondary-IP:
                description:
                    - Enable/disable adding a secondary IP to this interface.
                choices:
                    - enable
                    - disable
            secondaryip:
                description:
                    - Second IP address of interface.
                suboptions:
                    allowaccess:
                        description:
                            - Management access settings for the secondary IP address.
                        choices:
                            - ping
                            - https
                            - ssh
                            - snmp
                            - http
                            - telnet
                            - fgfm
                            - radius-acct
                            - probe-response
                            - capwap
                            - ftm
                    detectprotocol:
                        description:
                            - Protocols used to detect the server.
                        choices:
                            - ping
                            - tcp-echo
                            - udp-echo
                    detectserver:
                        description:
                            - Gateway's ping server for this IP.
                    gwdetect:
                        description:
                            - Enable/disable detect gateway alive for first.
                        choices:
                            - enable
                            - disable
                    ha-priority:
                        description:
                            - HA election priority for the PING server.
                    id:
                        description:
                            - ID.
                        required: true
                    ip:
                        description:
                            - Secondary IP address of the interface.
                    ping-serv-status:
                        description:
                            - PING server status.
            security-exempt-list:
                description:
                    - Name of security-exempt-list.
            security-external-logout:
                description:
                    - URL of external authentication logout server.
            security-external-web:
                description:
                    - URL of external authentication web server.
            security-groups:
                description:
                    - User groups that can authenticate with the captive portal.
                suboptions:
                    name:
                        description:
                            - Names of user groups that can authenticate with the captive portal.
                        required: true
            security-mac-auth-bypass:
                description:
                    - Enable/disable MAC authentication bypass.
                choices:
                    - enable
                    - disable
            security-mode:
                description:
                    - Turn on captive portal authentication for this interface.
                choices:
                    - none
                    - captive-portal
                    - 802.1X
            security-redirect-url:
                description:
                    - URL redirection after disclaimer/authentication.
            service-name:
                description:
                    - PPPoE service name.
            sflow-sampler:
                description:
                    - Enable/disable sFlow on this interface.
                choices:
                    - enable
                    - disable
            snmp-index:
                description:
                    - Permanent SNMP Index of the interface.
            speed:
                description:
                    - Interface speed. The default setting and the options available depend on the interface hardware.
                choices:
                    - auto
                    - 10full
                    - 10half
                    - 100full
                    - 100half
                    - 1000full
                    - 1000half
                    - 1000auto
            spillover-threshold:
                description:
                    - Egress Spillover threshold (0 - 16776000 kbps), 0 means unlimited.
            src-check:
                description:
                    - Enable/disable source IP check.
                choices:
                    - enable
                    - disable
            status:
                description:
                    - Bring the interface up or shut the interface down.
                choices:
                    - up
                    - down
            stpforward:
                description:
                    - Enable/disable STP forwarding.
                choices:
                    - enable
                    - disable
            stpforward-mode:
                description:
                    - Configure STP forwarding mode.
                choices:
                    - rpl-all-ext-id
                    - rpl-bridge-ext-id
                    - rpl-nothing
            subst:
                description:
                    - Enable to always send packets from this interface to a destination MAC address.
                choices:
                    - enable
                    - disable
            substitute-dst-mac:
                description:
                    - Destination MAC address that all packets are sent to from this interface.
            switch:
                description:
                    - Contained in switch.
            switch-controller-access-vlan:
                description:
                    - Block FortiSwitch port-to-port traffic.
                choices:
                    - enable
                    - disable
            switch-controller-arp-inspection:
                description:
                    - Enable/disable FortiSwitch ARP inspection.
                choices:
                    - enable
                    - disable
            switch-controller-dhcp-snooping:
                description:
                    - Switch controller DHCP snooping.
                choices:
                    - enable
                    - disable
            switch-controller-dhcp-snooping-option82:
                description:
                    - Switch controller DHCP snooping option82.
                choices:
                    - enable
                    - disable
            switch-controller-dhcp-snooping-verify-mac:
                description:
                    - Switch controller DHCP snooping verify MAC.
                choices:
                    - enable
                    - disable
            switch-controller-igmp-snooping:
                description:
                    - Switch controller IGMP snooping.
                choices:
                    - enable
                    - disable
            switch-controller-learning-limit:
                description:
                    - Limit the number of dynamic MAC addresses on this VLAN (1 - 128, 0 = no limit, default).
            tagging:
                description:
                    - Config object tagging.
                suboptions:
                    category:
                        description:
                            - Tag category. Source system.object-tagging.category.
                    name:
                        description:
                            - Tagging entry name.
                        required: true
                    tags:
                        description:
                            - Tags.
                        suboptions:
                            name:
                                description:
                                    - Tag name. Source system.object-tagging.tags.name.
                                required: true
            tcp-mss:
                description:
                    - TCP maximum segment size. 0 means do not change segment size.
            trust-ip-1:
                description:
                    - Trusted host for dedicated management traffic (0.0.0.0/24 for all hosts).
            trust-ip-2:
                description:
                    - Trusted host for dedicated management traffic (0.0.0.0/24 for all hosts).
            trust-ip-3:
                description:
                    - Trusted host for dedicated management traffic (0.0.0.0/24 for all hosts).
            trust-ip6-1:
                description:
                    - "Trusted IPv6 host for dedicated management traffic (::/0 for all hosts)."
            trust-ip6-2:
                description:
                    - "Trusted IPv6 host for dedicated management traffic (::/0 for all hosts)."
            trust-ip6-3:
                description:
                    - "Trusted IPv6 host for dedicated management traffic (::/0 for all hosts)."
            type:
                description:
                    - Interface type.
                choices:
                    - physical
                    - vlan
                    - aggregate
                    - redundant
                    - tunnel
                    - vdom-link
                    - loopback
                    - switch
                    - hard-switch
                    - vap-switch
                    - wl-mesh
                    - fext-wan
                    - vxlan
                    - hdlc
                    - switch-vlan
            username:
                description:
                    - Username of the PPPoE account, provided by your ISP.
            vdom:
                description:
                    - Interface is in this virtual domain (VDOM). Source system.vdom.name.
            vindex:
                description:
                    - Switch control interface VLAN ID.
            vlanforward:
                description:
                    - Enable/disable traffic forwarding between VLANs on this interface.
                choices:
                    - enable
                    - disable
            vlanid:
                description:
                    - VLAN ID (1 - 4094).
            vrf:
                description:
                    - Virtual Routing Forwarding ID.
            vrrp:
                description:
                    - VRRP configuration.
                suboptions:
                    accept-mode:
                        description:
                            - Enable/disable accept mode.
                        choices:
                            - enable
                            - disable
                    adv-interval:
                        description:
                            - Advertisement interval (1 - 255 seconds).
                    preempt:
                        description:
                            - Enable/disable preempt mode.
                        choices:
                            - enable
                            - disable
                    priority:
                        description:
                            - Priority of the virtual router (1 - 255).
                    proxy-arp:
                        description:
                            - VRRP Proxy ARP configuration.
                        suboptions:
                            id:
                                description:
                                    - ID.
                                required: true
                            ip:
                                description:
                                    - Set IP addresses of proxy ARP.
                    start-time:
                        description:
                            - Startup time (1 - 255 seconds).
                    status:
                        description:
                            - Enable/disable this VRRP configuration.
                        choices:
                            - enable
                            - disable
                    version:
                        description:
                            - VRRP version.
                        choices:
                            - 2
                            - 3
                    vrdst:
                        description:
                            - Monitor the route to this destination.
                    vrdst-priority:
                        description:
                            - Priority of the virtual router when the virtual router destination becomes unreachable (0 - 254).
                    vrgrp:
                        description:
                            - VRRP group ID (1 - 65535).
                    vrid:
                        description:
                            - Virtual router identifier (1 - 255).
                        required: true
                    vrip:
                        description:
                            - IP address of the virtual router.
            vrrp-virtual-mac:
                description:
                    - Enable/disable use of virtual MAC for VRRP.
                choices:
                    - enable
                    - disable
            wccp:
                description:
                    - Enable/disable WCCP on this interface. Used for encapsulated WCCP communication between WCCP clients and servers.
                choices:
                    - enable
                    - disable
            weight:
                description:
                    - Default weight for static routes (if route has no weight configured).
            wins-ip:
                description:
                    - WINS server IP.
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure interfaces.
    fortios_system_interface:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      system_interface:
        state: "present"
        ac-name: "<your_own_value>"
        aggregate: "<your_own_value>"
        algorithm: "L2"
        alias: "<your_own_value>"
        allowaccess: "ping"
        ap-discover: "enable"
        arpforward: "enable"
        auth-type: "auto"
        auto-auth-extension-device: "enable"
        bfd: "global"
        bfd-desired-min-tx: "13"
        bfd-detect-mult: "14"
        bfd-required-min-rx: "15"
        broadcast-forticlient-discovery: "enable"
        broadcast-forward: "enable"
        captive-portal: "18"
        cli-conn-status: "19"
        color: "20"
        dedicated-to: "none"
        defaultgw: "enable"
        description: "<your_own_value>"
        detected-peer-mtu: "24"
        detectprotocol: "ping"
        detectserver: "<your_own_value>"
        device-access-list: "<your_own_value>"
        device-identification: "enable"
        device-identification-active-scan: "enable"
        device-netscan: "disable"
        device-user-identification: "enable"
        devindex: "32"
        dhcp-client-identifier:  "myId_33"
        dhcp-relay-agent-option: "enable"
        dhcp-relay-ip: "<your_own_value>"
        dhcp-relay-service: "disable"
        dhcp-relay-type: "regular"
        dhcp-renew-time: "38"
        disc-retry-timeout: "39"
        disconnect-threshold: "40"
        distance: "41"
        dns-server-override: "enable"
        drop-fragment: "enable"
        drop-overlapped-fragment: "enable"
        egress-shaping-profile: "<your_own_value>"
        endpoint-compliance: "enable"
        estimated-downstream-bandwidth: "47"
        estimated-upstream-bandwidth: "48"
        explicit-ftp-proxy: "enable"
        explicit-web-proxy: "enable"
        external: "enable"
        fail-action-on-extender: "soft-restart"
        fail-alert-interfaces:
         -
            name: "default_name_54 (source system.interface.name)"
        fail-alert-method: "link-failed-signal"
        fail-detect: "enable"
        fail-detect-option: "detectserver"
        fortiheartbeat: "enable"
        fortilink: "enable"
        fortilink-backup-link: "60"
        fortilink-split-interface: "enable"
        fortilink-stacking: "enable"
        forward-domain: "63"
        gwdetect: "enable"
        ha-priority: "65"
        icmp-accept-redirect: "enable"
        icmp-send-redirect: "enable"
        ident-accept: "enable"
        idle-timeout: "69"
        inbandwidth: "70"
        ingress-spillover-threshold: "71"
        interface: "<your_own_value> (source system.interface.name)"
        internal: "73"
        ip: "<your_own_value>"
        ipmac: "enable"
        ips-sniffer-mode: "enable"
        ipunnumbered: "<your_own_value>"
        ipv6:
            autoconf: "enable"
            dhcp6-client-options: "rapid"
            dhcp6-information-request: "enable"
            dhcp6-prefix-delegation: "enable"
            dhcp6-prefix-hint: "<your_own_value>"
            dhcp6-prefix-hint-plt: "84"
            dhcp6-prefix-hint-vlt: "85"
            dhcp6-relay-ip: "<your_own_value>"
            dhcp6-relay-service: "disable"
            dhcp6-relay-type: "regular"
            ip6-address: "<your_own_value>"
            ip6-allowaccess: "ping"
            ip6-default-life: "91"
            ip6-delegated-prefix-list:
             -
                autonomous-flag: "enable"
                onlink-flag: "enable"
                prefix-id: "95"
                rdnss: "<your_own_value>"
                rdnss-service: "delegated"
                subnet: "<your_own_value>"
                upstream-interface: "<your_own_value> (source system.interface.name)"
            ip6-dns-server-override: "enable"
            ip6-extra-addr:
             -
                prefix: "<your_own_value>"
            ip6-hop-limit: "103"
            ip6-link-mtu: "104"
            ip6-manage-flag: "enable"
            ip6-max-interval: "106"
            ip6-min-interval: "107"
            ip6-mode: "static"
            ip6-other-flag: "enable"
            ip6-prefix-list:
             -
                autonomous-flag: "enable"
                dnssl:
                 -
                    domain: "<your_own_value>"
                onlink-flag: "enable"
                preferred-life-time: "115"
                prefix: "<your_own_value>"
                rdnss: "<your_own_value>"
                valid-life-time: "118"
            ip6-reachable-time: "119"
            ip6-retrans-time: "120"
            ip6-send-adv: "enable"
            ip6-subnet: "<your_own_value>"
            ip6-upstream-interface: "<your_own_value> (source system.interface.name)"
            nd-cert: "<your_own_value> (source certificate.local.name)"
            nd-cga-modifier: "<your_own_value>"
            nd-mode: "basic"
            nd-security-level: "127"
            nd-timestamp-delta: "128"
            nd-timestamp-fuzz: "129"
            vrip6_link_local: "<your_own_value>"
            vrrp-virtual-mac6: "enable"
            vrrp6:
             -
                accept-mode: "enable"
                adv-interval: "134"
                preempt: "enable"
                priority: "136"
                start-time: "137"
                status: "enable"
                vrdst6: "<your_own_value>"
                vrgrp: "140"
                vrid: "141"
                vrip6: "<your_own_value>"
        l2forward: "enable"
        lacp-ha-slave: "enable"
        lacp-mode: "static"
        lacp-speed: "slow"
        lcp-echo-interval: "147"
        lcp-max-echo-fails: "148"
        link-up-delay: "149"
        lldp-transmission: "enable"
        macaddr: "<your_own_value>"
        managed-device:
         -
            name: "default_name_153"
        management-ip: "<your_own_value>"
        member:
         -
            interface-name: "<your_own_value> (source system.interface.name)"
        min-links: "157"
        min-links-down: "operational"
        mode: "static"
        mtu: "160"
        mtu-override: "enable"
        name: "default_name_162"
        ndiscforward: "enable"
        netbios-forward: "disable"
        netflow-sampler: "disable"
        outbandwidth: "166"
        padt-retry-timeout: "167"
        password: "<your_own_value>"
        ping-serv-status: "169"
        polling-interval: "170"
        pppoe-unnumbered-negotiate: "enable"
        pptp-auth-type: "auto"
        pptp-client: "enable"
        pptp-password: "<your_own_value>"
        pptp-server-ip: "<your_own_value>"
        pptp-timeout: "176"
        pptp-user: "<your_own_value>"
        preserve-session-route: "enable"
        priority: "179"
        priority-override: "enable"
        proxy-captive-portal: "enable"
        redundant-interface: "<your_own_value>"
        remote-ip: "<your_own_value>"
        replacemsg-override-group: "<your_own_value>"
        role: "lan"
        sample-direction: "tx"
        sample-rate: "187"
        scan-botnet-connections: "disable"
        secondary-IP: "enable"
        secondaryip:
         -
            allowaccess: "ping"
            detectprotocol: "ping"
            detectserver: "<your_own_value>"
            gwdetect: "enable"
            ha-priority: "195"
            id:  "196"
            ip: "<your_own_value>"
            ping-serv-status: "198"
        security-exempt-list: "<your_own_value>"
        security-external-logout: "<your_own_value>"
        security-external-web: "<your_own_value>"
        security-groups:
         -
            name: "default_name_203"
        security-mac-auth-bypass: "enable"
        security-mode: "none"
        security-redirect-url: "<your_own_value>"
        service-name: "<your_own_value>"
        sflow-sampler: "enable"
        snmp-index: "209"
        speed: "auto"
        spillover-threshold: "211"
        src-check: "enable"
        status: "up"
        stpforward: "enable"
        stpforward-mode: "rpl-all-ext-id"
        subst: "enable"
        substitute-dst-mac: "<your_own_value>"
        switch: "<your_own_value>"
        switch-controller-access-vlan: "enable"
        switch-controller-arp-inspection: "enable"
        switch-controller-dhcp-snooping: "enable"
        switch-controller-dhcp-snooping-option82: "enable"
        switch-controller-dhcp-snooping-verify-mac: "enable"
        switch-controller-igmp-snooping: "enable"
        switch-controller-learning-limit: "225"
        tagging:
         -
            category: "<your_own_value> (source system.object-tagging.category)"
            name: "default_name_228"
            tags:
             -
                name: "default_name_230 (source system.object-tagging.tags.name)"
        tcp-mss: "231"
        trust-ip-1: "<your_own_value>"
        trust-ip-2: "<your_own_value>"
        trust-ip-3: "<your_own_value>"
        trust-ip6-1: "<your_own_value>"
        trust-ip6-2: "<your_own_value>"
        trust-ip6-3: "<your_own_value>"
        type: "physical"
        username: "<your_own_value>"
        vdom: "<your_own_value> (source system.vdom.name)"
        vindex: "241"
        vlanforward: "enable"
        vlanid: "243"
        vrf: "244"
        vrrp:
         -
            accept-mode: "enable"
            adv-interval: "247"
            preempt: "enable"
            priority: "249"
            proxy-arp:
             -
                id:  "251"
                ip: "<your_own_value>"
            start-time: "253"
            status: "enable"
            version: "2"
            vrdst: "<your_own_value>"
            vrdst-priority: "257"
            vrgrp: "258"
            vrid: "259"
            vrip: "<your_own_value>"
        vrrp-virtual-mac: "enable"
        wccp: "enable"
        weight: "263"
        wins-ip: "<your_own_value>"
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


def filter_system_interface_data(json):
    option_list = ['ac-name', 'aggregate', 'algorithm',
                   'alias', 'allowaccess', 'ap-discover',
                   'arpforward', 'auth-type', 'auto-auth-extension-device',
                   'bfd', 'bfd-desired-min-tx', 'bfd-detect-mult',
                   'bfd-required-min-rx', 'broadcast-forticlient-discovery', 'broadcast-forward',
                   'captive-portal', 'cli-conn-status', 'color',
                   'dedicated-to', 'defaultgw', 'description',
                   'detected-peer-mtu', 'detectprotocol', 'detectserver',
                   'device-access-list', 'device-identification', 'device-identification-active-scan',
                   'device-netscan', 'device-user-identification', 'devindex',
                   'dhcp-client-identifier', 'dhcp-relay-agent-option', 'dhcp-relay-ip',
                   'dhcp-relay-service', 'dhcp-relay-type', 'dhcp-renew-time',
                   'disc-retry-timeout', 'disconnect-threshold', 'distance',
                   'dns-server-override', 'drop-fragment', 'drop-overlapped-fragment',
                   'egress-shaping-profile', 'endpoint-compliance', 'estimated-downstream-bandwidth',
                   'estimated-upstream-bandwidth', 'explicit-ftp-proxy', 'explicit-web-proxy',
                   'external', 'fail-action-on-extender', 'fail-alert-interfaces',
                   'fail-alert-method', 'fail-detect', 'fail-detect-option',
                   'fortiheartbeat', 'fortilink', 'fortilink-backup-link',
                   'fortilink-split-interface', 'fortilink-stacking', 'forward-domain',
                   'gwdetect', 'ha-priority', 'icmp-accept-redirect',
                   'icmp-send-redirect', 'ident-accept', 'idle-timeout',
                   'inbandwidth', 'ingress-spillover-threshold', 'interface',
                   'internal', 'ip', 'ipmac',
                   'ips-sniffer-mode', 'ipunnumbered', 'ipv6',
                   'l2forward', 'lacp-ha-slave', 'lacp-mode',
                   'lacp-speed', 'lcp-echo-interval', 'lcp-max-echo-fails',
                   'link-up-delay', 'lldp-transmission', 'macaddr',
                   'managed-device', 'management-ip', 'member',
                   'min-links', 'min-links-down', 'mode',
                   'mtu', 'mtu-override', 'name',
                   'ndiscforward', 'netbios-forward', 'netflow-sampler',
                   'outbandwidth', 'padt-retry-timeout', 'password',
                   'ping-serv-status', 'polling-interval', 'pppoe-unnumbered-negotiate',
                   'pptp-auth-type', 'pptp-client', 'pptp-password',
                   'pptp-server-ip', 'pptp-timeout', 'pptp-user',
                   'preserve-session-route', 'priority', 'priority-override',
                   'proxy-captive-portal', 'redundant-interface', 'remote-ip',
                   'replacemsg-override-group', 'role', 'sample-direction',
                   'sample-rate', 'scan-botnet-connections', 'secondary-IP',
                   'secondaryip', 'security-exempt-list', 'security-external-logout',
                   'security-external-web', 'security-groups', 'security-mac-auth-bypass',
                   'security-mode', 'security-redirect-url', 'service-name',
                   'sflow-sampler', 'snmp-index', 'speed',
                   'spillover-threshold', 'src-check', 'status',
                   'stpforward', 'stpforward-mode', 'subst',
                   'substitute-dst-mac', 'switch', 'switch-controller-access-vlan',
                   'switch-controller-arp-inspection', 'switch-controller-dhcp-snooping', 'switch-controller-dhcp-snooping-option82',
                   'switch-controller-dhcp-snooping-verify-mac', 'switch-controller-igmp-snooping', 'switch-controller-learning-limit',
                   'tagging', 'tcp-mss', 'trust-ip-1',
                   'trust-ip-2', 'trust-ip-3', 'trust-ip6-1',
                   'trust-ip6-2', 'trust-ip6-3', 'type',
                   'username', 'vdom', 'vindex',
                   'vlanforward', 'vlanid', 'vrf',
                   'vrrp', 'vrrp-virtual-mac', 'wccp',
                   'weight', 'wins-ip']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def flatten_multilists_attributes(data):
    multilist_attrs = [[u'allowaccess'], [u'ipv6', u'ip6-allowaccess']]

    for attr in multilist_attrs:
        try:
            path = "data['" + "']['".join(elem for elem in attr) + "']"
            current_val = eval(path)
            flattened_val = ' '.join(elem for elem in current_val)
            exec(path + '= flattened_val')
        except BaseException:
            pass

    return data


def system_interface(data, fos):
    vdom = data['vdom']
    system_interface_data = data['system_interface']
    flattened_data = flatten_multilists_attributes(system_interface_data)
    filtered_data = filter_system_interface_data(flattened_data)
    if system_interface_data['state'] == "present":
        return fos.set('system',
                       'interface',
                       data=filtered_data,
                       vdom=vdom)

    elif system_interface_data['state'] == "absent":
        return fos.delete('system',
                          'interface',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_system(data, fos):
    login(data)

    if data['system_interface']:
        resp = system_interface(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "system_interface": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "ac-name": {"required": False, "type": "str"},
                "aggregate": {"required": False, "type": "str"},
                "algorithm": {"required": False, "type": "str",
                              "choices": ["L2", "L3", "L4"]},
                "alias": {"required": False, "type": "str"},
                "allowaccess": {"required": False, "type": "list",
                                "choices": ["ping", "https", "ssh",
                                            "snmp", "http", "telnet",
                                            "fgfm", "radius-acct", "probe-response",
                                            "capwap", "ftm"]},
                "ap-discover": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "arpforward": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "auth-type": {"required": False, "type": "str",
                              "choices": ["auto", "pap", "chap",
                                          "mschapv1", "mschapv2"]},
                "auto-auth-extension-device": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                "bfd": {"required": False, "type": "str",
                        "choices": ["global", "enable", "disable"]},
                "bfd-desired-min-tx": {"required": False, "type": "int"},
                "bfd-detect-mult": {"required": False, "type": "int"},
                "bfd-required-min-rx": {"required": False, "type": "int"},
                "broadcast-forticlient-discovery": {"required": False, "type": "str",
                                                    "choices": ["enable", "disable"]},
                "broadcast-forward": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "captive-portal": {"required": False, "type": "int"},
                "cli-conn-status": {"required": False, "type": "int"},
                "color": {"required": False, "type": "int"},
                "dedicated-to": {"required": False, "type": "str",
                                 "choices": ["none", "management"]},
                "defaultgw": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "description": {"required": False, "type": "str"},
                "detected-peer-mtu": {"required": False, "type": "int"},
                "detectprotocol": {"required": False, "type": "str",
                                   "choices": ["ping", "tcp-echo", "udp-echo"]},
                "detectserver": {"required": False, "type": "str"},
                "device-access-list": {"required": False, "type": "str"},
                "device-identification": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "device-identification-active-scan": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                "device-netscan": {"required": False, "type": "str",
                                   "choices": ["disable", "enable"]},
                "device-user-identification": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                "devindex": {"required": False, "type": "int"},
                "dhcp-client-identifier": {"required": False, "type": "str"},
                "dhcp-relay-agent-option": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                "dhcp-relay-ip": {"required": False, "type": "str"},
                "dhcp-relay-service": {"required": False, "type": "str",
                                       "choices": ["disable", "enable"]},
                "dhcp-relay-type": {"required": False, "type": "str",
                                    "choices": ["regular", "ipsec"]},
                "dhcp-renew-time": {"required": False, "type": "int"},
                "disc-retry-timeout": {"required": False, "type": "int"},
                "disconnect-threshold": {"required": False, "type": "int"},
                "distance": {"required": False, "type": "int"},
                "dns-server-override": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "drop-fragment": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "drop-overlapped-fragment": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                "egress-shaping-profile": {"required": False, "type": "str"},
                "endpoint-compliance": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "estimated-downstream-bandwidth": {"required": False, "type": "int"},
                "estimated-upstream-bandwidth": {"required": False, "type": "int"},
                "explicit-ftp-proxy": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "explicit-web-proxy": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "external": {"required": False, "type": "str",
                             "choices": ["enable", "disable"]},
                "fail-action-on-extender": {"required": False, "type": "str",
                                            "choices": ["soft-restart", "hard-restart", "reboot"]},
                "fail-alert-interfaces": {"required": False, "type": "list",
                                          "options": {
                                              "name": {"required": True, "type": "str"}
                                          }},
                "fail-alert-method": {"required": False, "type": "str",
                                      "choices": ["link-failed-signal", "link-down"]},
                "fail-detect": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "fail-detect-option": {"required": False, "type": "str",
                                       "choices": ["detectserver", "link-down"]},
                "fortiheartbeat": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "fortilink": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "fortilink-backup-link": {"required": False, "type": "int"},
                "fortilink-split-interface": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                "fortilink-stacking": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "forward-domain": {"required": False, "type": "int"},
                "gwdetect": {"required": False, "type": "str",
                             "choices": ["enable", "disable"]},
                "ha-priority": {"required": False, "type": "int"},
                "icmp-accept-redirect": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "icmp-send-redirect": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "ident-accept": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "idle-timeout": {"required": False, "type": "int"},
                "inbandwidth": {"required": False, "type": "int"},
                "ingress-spillover-threshold": {"required": False, "type": "int"},
                "interface": {"required": False, "type": "str"},
                "internal": {"required": False, "type": "int"},
                "ip": {"required": False, "type": "str"},
                "ipmac": {"required": False, "type": "str",
                          "choices": ["enable", "disable"]},
                "ips-sniffer-mode": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "ipunnumbered": {"required": False, "type": "str"},
                "ipv6": {"required": False, "type": "dict",
                         "options": {
                             "autoconf": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                             "dhcp6-client-options": {"required": False, "type": "str",
                                                      "choices": ["rapid", "iapd", "iana"]},
                             "dhcp6-information-request": {"required": False, "type": "str",
                                                           "choices": ["enable", "disable"]},
                             "dhcp6-prefix-delegation": {"required": False, "type": "str",
                                                         "choices": ["enable", "disable"]},
                             "dhcp6-prefix-hint": {"required": False, "type": "str"},
                             "dhcp6-prefix-hint-plt": {"required": False, "type": "int"},
                             "dhcp6-prefix-hint-vlt": {"required": False, "type": "int"},
                             "dhcp6-relay-ip": {"required": False, "type": "str"},
                             "dhcp6-relay-service": {"required": False, "type": "str",
                                                     "choices": ["disable", "enable"]},
                             "dhcp6-relay-type": {"required": False, "type": "str",
                                                  "choices": ["regular"]},
                             "ip6-address": {"required": False, "type": "str"},
                             "ip6-allowaccess": {"required": False, "type": "list",
                                                 "choices": ["ping", "https", "ssh",
                                                             "snmp", "http", "telnet",
                                                             "fgfm", "capwap"]},
                             "ip6-default-life": {"required": False, "type": "int"},
                             "ip6-delegated-prefix-list": {"required": False, "type": "list",
                                                           "options": {
                                                               "autonomous-flag": {"required": False, "type": "str",
                                                                                   "choices": ["enable", "disable"]},
                                                               "onlink-flag": {"required": False, "type": "str",
                                                                               "choices": ["enable", "disable"]},
                                                               "prefix-id": {"required": True, "type": "int"},
                                                               "rdnss": {"required": False, "type": "str"},
                                                               "rdnss-service": {"required": False, "type": "str",
                                                                                 "choices": ["delegated", "default", "specify"]},
                                                               "subnet": {"required": False, "type": "str"},
                                                               "upstream-interface": {"required": False, "type": "str"}
                                                           }},
                             "ip6-dns-server-override": {"required": False, "type": "str",
                                                         "choices": ["enable", "disable"]},
                             "ip6-extra-addr": {"required": False, "type": "list",
                                                "options": {
                                                    "prefix": {"required": True, "type": "str"}
                                                }},
                             "ip6-hop-limit": {"required": False, "type": "int"},
                             "ip6-link-mtu": {"required": False, "type": "int"},
                             "ip6-manage-flag": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]},
                             "ip6-max-interval": {"required": False, "type": "int"},
                             "ip6-min-interval": {"required": False, "type": "int"},
                             "ip6-mode": {"required": False, "type": "str",
                                          "choices": ["static", "dhcp", "pppoe",
                                                      "delegated"]},
                             "ip6-other-flag": {"required": False, "type": "str",
                                                "choices": ["enable", "disable"]},
                             "ip6-prefix-list": {"required": False, "type": "list",
                                                 "options": {
                                                     "autonomous-flag": {"required": False, "type": "str",
                                                                         "choices": ["enable", "disable"]},
                                                     "dnssl": {"required": False, "type": "list",
                                                               "options": {
                                                                   "domain": {"required": True, "type": "str"}
                                                               }},
                                                     "onlink-flag": {"required": False, "type": "str",
                                                                     "choices": ["enable", "disable"]},
                                                     "preferred-life-time": {"required": False, "type": "int"},
                                                     "prefix": {"required": True, "type": "str"},
                                                     "rdnss": {"required": False, "type": "str"},
                                                     "valid-life-time": {"required": False, "type": "int"}
                                                 }},
                             "ip6-reachable-time": {"required": False, "type": "int"},
                             "ip6-retrans-time": {"required": False, "type": "int"},
                             "ip6-send-adv": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                             "ip6-subnet": {"required": False, "type": "str"},
                             "ip6-upstream-interface": {"required": False, "type": "str"},
                             "nd-cert": {"required": False, "type": "str"},
                             "nd-cga-modifier": {"required": False, "type": "str"},
                             "nd-mode": {"required": False, "type": "str",
                                         "choices": ["basic", "SEND-compatible"]},
                             "nd-security-level": {"required": False, "type": "int"},
                             "nd-timestamp-delta": {"required": False, "type": "int"},
                             "nd-timestamp-fuzz": {"required": False, "type": "int"},
                             "vrip6_link_local": {"required": False, "type": "str"},
                             "vrrp-virtual-mac6": {"required": False, "type": "str",
                                                   "choices": ["enable", "disable"]},
                             "vrrp6": {"required": False, "type": "list",
                                       "options": {
                                           "accept-mode": {"required": False, "type": "str",
                                                           "choices": ["enable", "disable"]},
                                           "adv-interval": {"required": False, "type": "int"},
                                           "preempt": {"required": False, "type": "str",
                                                       "choices": ["enable", "disable"]},
                                           "priority": {"required": False, "type": "int"},
                                           "start-time": {"required": False, "type": "int"},
                                           "status": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                                           "vrdst6": {"required": False, "type": "str"},
                                           "vrgrp": {"required": False, "type": "int"},
                                           "vrid": {"required": True, "type": "int"},
                                           "vrip6": {"required": False, "type": "str"}
                                       }}
                         }},
                "l2forward": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "lacp-ha-slave": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "lacp-mode": {"required": False, "type": "str",
                              "choices": ["static", "passive", "active"]},
                "lacp-speed": {"required": False, "type": "str",
                               "choices": ["slow", "fast"]},
                "lcp-echo-interval": {"required": False, "type": "int"},
                "lcp-max-echo-fails": {"required": False, "type": "int"},
                "link-up-delay": {"required": False, "type": "int"},
                "lldp-transmission": {"required": False, "type": "str",
                                      "choices": ["enable", "disable", "vdom"]},
                "macaddr": {"required": False, "type": "str"},
                "managed-device": {"required": False, "type": "list",
                                   "options": {
                                       "name": {"required": True, "type": "str"}
                                   }},
                "management-ip": {"required": False, "type": "str"},
                "member": {"required": False, "type": "list",
                           "options": {
                               "interface-name": {"required": True, "type": "str"}
                           }},
                "min-links": {"required": False, "type": "int"},
                "min-links-down": {"required": False, "type": "str",
                                   "choices": ["operational", "administrative"]},
                "mode": {"required": False, "type": "str",
                         "choices": ["static", "dhcp", "pppoe"]},
                "mtu": {"required": False, "type": "int"},
                "mtu-override": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "name": {"required": True, "type": "str"},
                "ndiscforward": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "netbios-forward": {"required": False, "type": "str",
                                    "choices": ["disable", "enable"]},
                "netflow-sampler": {"required": False, "type": "str",
                                    "choices": ["disable", "tx", "rx",
                                                "both"]},
                "outbandwidth": {"required": False, "type": "int"},
                "padt-retry-timeout": {"required": False, "type": "int"},
                "password": {"required": False, "type": "str"},
                "ping-serv-status": {"required": False, "type": "int"},
                "polling-interval": {"required": False, "type": "int"},
                "pppoe-unnumbered-negotiate": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                "pptp-auth-type": {"required": False, "type": "str",
                                   "choices": ["auto", "pap", "chap",
                                               "mschapv1", "mschapv2"]},
                "pptp-client": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "pptp-password": {"required": False, "type": "str"},
                "pptp-server-ip": {"required": False, "type": "str"},
                "pptp-timeout": {"required": False, "type": "int"},
                "pptp-user": {"required": False, "type": "str"},
                "preserve-session-route": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "priority": {"required": False, "type": "int"},
                "priority-override": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "proxy-captive-portal": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "redundant-interface": {"required": False, "type": "str"},
                "remote-ip": {"required": False, "type": "str"},
                "replacemsg-override-group": {"required": False, "type": "str"},
                "role": {"required": False, "type": "str",
                         "choices": ["lan", "wan", "dmz",
                                     "undefined"]},
                "sample-direction": {"required": False, "type": "str",
                                     "choices": ["tx", "rx", "both"]},
                "sample-rate": {"required": False, "type": "int"},
                "scan-botnet-connections": {"required": False, "type": "str",
                                            "choices": ["disable", "block", "monitor"]},
                "secondary-IP": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "secondaryip": {"required": False, "type": "list",
                                "options": {
                                    "allowaccess": {"required": False, "type": "str",
                                                    "choices": ["ping", "https", "ssh",
                                                                "snmp", "http", "telnet",
                                                                "fgfm", "radius-acct", "probe-response",
                                                                "capwap", "ftm"]},
                                    "detectprotocol": {"required": False, "type": "str",
                                                       "choices": ["ping", "tcp-echo", "udp-echo"]},
                                    "detectserver": {"required": False, "type": "str"},
                                    "gwdetect": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]},
                                    "ha-priority": {"required": False, "type": "int"},
                                    "id": {"required": True, "type": "int"},
                                    "ip": {"required": False, "type": "str"},
                                    "ping-serv-status": {"required": False, "type": "int"}
                                }},
                "security-exempt-list": {"required": False, "type": "str"},
                "security-external-logout": {"required": False, "type": "str"},
                "security-external-web": {"required": False, "type": "str"},
                "security-groups": {"required": False, "type": "list",
                                    "options": {
                                        "name": {"required": True, "type": "str"}
                                    }},
                "security-mac-auth-bypass": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                "security-mode": {"required": False, "type": "str",
                                  "choices": ["none", "captive-portal", "802.1X"]},
                "security-redirect-url": {"required": False, "type": "str"},
                "service-name": {"required": False, "type": "str"},
                "sflow-sampler": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "snmp-index": {"required": False, "type": "int"},
                "speed": {"required": False, "type": "str",
                          "choices": ["auto", "10full", "10half",
                                      "100full", "100half", "1000full",
                                      "1000half", "1000auto"]},
                "spillover-threshold": {"required": False, "type": "int"},
                "src-check": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "status": {"required": False, "type": "str",
                           "choices": ["up", "down"]},
                "stpforward": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "stpforward-mode": {"required": False, "type": "str",
                                    "choices": ["rpl-all-ext-id", "rpl-bridge-ext-id", "rpl-nothing"]},
                "subst": {"required": False, "type": "str",
                          "choices": ["enable", "disable"]},
                "substitute-dst-mac": {"required": False, "type": "str"},
                "switch": {"required": False, "type": "str"},
                "switch-controller-access-vlan": {"required": False, "type": "str",
                                                  "choices": ["enable", "disable"]},
                "switch-controller-arp-inspection": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]},
                "switch-controller-dhcp-snooping": {"required": False, "type": "str",
                                                    "choices": ["enable", "disable"]},
                "switch-controller-dhcp-snooping-option82": {"required": False, "type": "str",
                                                             "choices": ["enable", "disable"]},
                "switch-controller-dhcp-snooping-verify-mac": {"required": False, "type": "str",
                                                               "choices": ["enable", "disable"]},
                "switch-controller-igmp-snooping": {"required": False, "type": "str",
                                                    "choices": ["enable", "disable"]},
                "switch-controller-learning-limit": {"required": False, "type": "int"},
                "tagging": {"required": False, "type": "list",
                            "options": {
                                "category": {"required": False, "type": "str"},
                                "name": {"required": True, "type": "str"},
                                "tags": {"required": False, "type": "list",
                                         "options": {
                                             "name": {"required": True, "type": "str"}
                                         }}
                            }},
                "tcp-mss": {"required": False, "type": "int"},
                "trust-ip-1": {"required": False, "type": "str"},
                "trust-ip-2": {"required": False, "type": "str"},
                "trust-ip-3": {"required": False, "type": "str"},
                "trust-ip6-1": {"required": False, "type": "str"},
                "trust-ip6-2": {"required": False, "type": "str"},
                "trust-ip6-3": {"required": False, "type": "str"},
                "type": {"required": False, "type": "str",
                         "choices": ["physical", "vlan", "aggregate",
                                     "redundant", "tunnel", "vdom-link",
                                     "loopback", "switch", "hard-switch",
                                     "vap-switch", "wl-mesh", "fext-wan",
                                     "vxlan", "hdlc", "switch-vlan"]},
                "username": {"required": False, "type": "str"},
                "vdom": {"required": False, "type": "str"},
                "vindex": {"required": False, "type": "int"},
                "vlanforward": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "vlanid": {"required": False, "type": "int"},
                "vrf": {"required": False, "type": "int"},
                "vrrp": {"required": False, "type": "list",
                         "options": {
                             "accept-mode": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                             "adv-interval": {"required": False, "type": "int"},
                             "preempt": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                             "priority": {"required": False, "type": "int"},
                             "proxy-arp": {"required": False, "type": "list",
                                           "options": {
                                               "id": {"required": True, "type": "int"},
                                               "ip": {"required": False, "type": "str"}
                                           }},
                             "start-time": {"required": False, "type": "int"},
                             "status": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                             "version": {"required": False, "type": "str",
                                         "choices": ["2", "3"]},
                             "vrdst": {"required": False, "type": "str"},
                             "vrdst-priority": {"required": False, "type": "int"},
                             "vrgrp": {"required": False, "type": "int"},
                             "vrid": {"required": True, "type": "int"},
                             "vrip": {"required": False, "type": "str"}
                         }},
                "vrrp-virtual-mac": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "wccp": {"required": False, "type": "str",
                         "choices": ["enable", "disable"]},
                "weight": {"required": False, "type": "int"},
                "wins-ip": {"required": False, "type": "str"}

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
