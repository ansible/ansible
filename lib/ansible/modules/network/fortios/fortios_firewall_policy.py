#!/usr/bin/python
from __future__ import (absolute_import, division, print_function)
# Copyright 2018 Fortinet, Inc.
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
module: fortios_firewall_policy
short_description: Configure IPv4 policies.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure firewall feature and policy category.
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
        default: false
    firewall_policy:
        description:
            - Configure IPv4 policies.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            action:
                description:
                    - Policy action (allow/deny/ipsec).
                choices:
                    - accept
                    - deny
                    - ipsec
            app-category:
                description:
                    - Application category ID list.
                suboptions:
                    id:
                        description:
                            - Category IDs.
                        required: true
            app-group:
                description:
                    - Application group names.
                suboptions:
                    name:
                        description:
                            - Application group names. Source application.group.name.
                        required: true
            application:
                description:
                    - Application ID list.
                suboptions:
                    id:
                        description:
                            - Application IDs.
                        required: true
            application-list:
                description:
                    - Name of an existing Application list. Source application.list.name.
            auth-cert:
                description:
                    - HTTPS server certificate for policy authentication. Source vpn.certificate.local.name.
            auth-path:
                description:
                    - Enable/disable authentication-based routing.
                choices:
                    - enable
                    - disable
            auth-redirect-addr:
                description:
                    - HTTP-to-HTTPS redirect address for firewall authentication.
            av-profile:
                description:
                    - Name of an existing Antivirus profile. Source antivirus.profile.name.
            block-notification:
                description:
                    - Enable/disable block notification.
                choices:
                    - enable
                    - disable
            captive-portal-exempt:
                description:
                    - Enable to exempt some users from the captive portal.
                choices:
                    - enable
                    - disable
            capture-packet:
                description:
                    - Enable/disable capture packets.
                choices:
                    - enable
                    - disable
            comments:
                description:
                    - Comment.
            custom-log-fields:
                description:
                    - Custom fields to append to log messages for this policy.
                suboptions:
                    field-id:
                        description:
                            - Custom log field. Source log.custom-field.id.
                        required: true
            delay-tcp-npu-session:
                description:
                    - Enable TCP NPU session delay to guarantee packet order of 3-way handshake.
                choices:
                    - enable
                    - disable
            devices:
                description:
                    - Names of devices or device groups that can be matched by the policy.
                suboptions:
                    name:
                        description:
                            - Device or group name. Source user.device.alias user.device-group.name user.device-category.name.
                        required: true
            diffserv-forward:
                description:
                    - Enable to change packet's DiffServ values to the specified diffservcode-forward value.
                choices:
                    - enable
                    - disable
            diffserv-reverse:
                description:
                    - Enable to change packet's reverse (reply) DiffServ values to the specified diffservcode-rev value.
                choices:
                    - enable
                    - disable
            diffservcode-forward:
                description:
                    - Change packet's DiffServ to this value.
            diffservcode-rev:
                description:
                    - Change packet's reverse (reply) DiffServ to this value.
            disclaimer:
                description:
                    - Enable/disable user authentication disclaimer.
                choices:
                    - enable
                    - disable
            dlp-sensor:
                description:
                    - Name of an existing DLP sensor. Source dlp.sensor.name.
            dnsfilter-profile:
                description:
                    - Name of an existing DNS filter profile. Source dnsfilter.profile.name.
            dscp-match:
                description:
                    - Enable DSCP check.
                choices:
                    - enable
                    - disable
            dscp-negate:
                description:
                    - Enable negated DSCP match.
                choices:
                    - enable
                    - disable
            dscp-value:
                description:
                    - DSCP value.
            dsri:
                description:
                    - Enable DSRI to ignore HTTP server responses.
                choices:
                    - enable
                    - disable
            dstaddr:
                description:
                    - Destination address and address group names.
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address.name firewall.addrgrp.name firewall.vip.name firewall.vipgrp.name.
                        required: true
            dstaddr-negate:
                description:
                    - When enabled dstaddr specifies what the destination address must NOT be.
                choices:
                    - enable
                    - disable
            dstintf:
                description:
                    - Outgoing (egress) interface.
                suboptions:
                    name:
                        description:
                            - Interface name. Source system.interface.name system.zone.name.
                        required: true
            firewall-session-dirty:
                description:
                    - How to handle sessions if the configuration of this firewall policy changes.
                choices:
                    - check-all
                    - check-new
            fixedport:
                description:
                    - Enable to prevent source NAT from changing a session's source port.
                choices:
                    - enable
                    - disable
            fsso:
                description:
                    - Enable/disable Fortinet Single Sign-On.
                choices:
                    - enable
                    - disable
            fsso-agent-for-ntlm:
                description:
                    - FSSO agent to use for NTLM authentication. Source user.fsso.name.
            global-label:
                description:
                    - Label for the policy that appears when the GUI is in Global View mode.
            groups:
                description:
                    - Names of user groups that can authenticate with this policy.
                suboptions:
                    name:
                        description:
                            - Group name. Source user.group.name.
                        required: true
            icap-profile:
                description:
                    - Name of an existing ICAP profile. Source icap.profile.name.
            identity-based-route:
                description:
                    - Name of identity-based routing rule. Source firewall.identity-based-route.name.
            inbound:
                description:
                    - "Policy-based IPsec VPN: only traffic from the remote network can initiate a VPN."
                choices:
                    - enable
                    - disable
            internet-service:
                description:
                    - Enable/disable use of Internet Services for this policy. If enabled, destination address and service are not used.
                choices:
                    - enable
                    - disable
            internet-service-custom:
                description:
                    - Custom Internet Service name.
                suboptions:
                    name:
                        description:
                            - Custom Internet Service name. Source firewall.internet-service-custom.name.
                        required: true
            internet-service-id:
                description:
                    - Internet Service ID.
                suboptions:
                    id:
                        description:
                            - Internet Service ID. Source firewall.internet-service.id.
                        required: true
            internet-service-negate:
                description:
                    - When enabled internet-service specifies what the service must NOT be.
                choices:
                    - enable
                    - disable
            internet-service-src:
                description:
                    - Enable/disable use of Internet Services in source for this policy. If enabled, source address is not used.
                choices:
                    - enable
                    - disable
            internet-service-src-custom:
                description:
                    - Custom Internet Service source name.
                suboptions:
                    name:
                        description:
                            - Custom Internet Service name. Source firewall.internet-service-custom.name.
                        required: true
            internet-service-src-id:
                description:
                    - Internet Service source ID.
                suboptions:
                    id:
                        description:
                            - Internet Service ID. Source firewall.internet-service.id.
                        required: true
            internet-service-src-negate:
                description:
                    - When enabled internet-service-src specifies what the service must NOT be.
                choices:
                    - enable
                    - disable
            ippool:
                description:
                    - Enable to use IP Pools for source NAT.
                choices:
                    - enable
                    - disable
            ips-sensor:
                description:
                    - Name of an existing IPS sensor. Source ips.sensor.name.
            label:
                description:
                    - Label for the policy that appears when the GUI is in Section View mode.
            learning-mode:
                description:
                    - Enable to allow everything, but log all of the meaningful data for security information gathering. A learning report will be generated.
                choices:
                    - enable
                    - disable
            logtraffic:
                description:
                    - Enable or disable logging. Log all sessions or security profile sessions.
                choices:
                    - all
                    - utm
                    - disable
            logtraffic-start:
                description:
                    - Record logs when a session starts and ends.
                choices:
                    - enable
                    - disable
            match-vip:
                description:
                    - Enable to match packets that have had their destination addresses changed by a VIP.
                choices:
                    - enable
                    - disable
            name:
                description:
                    - Policy name.
            nat:
                description:
                    - Enable/disable source NAT.
                choices:
                    - enable
                    - disable
            natinbound:
                description:
                    - "Policy-based IPsec VPN: apply destination NAT to inbound traffic."
                choices:
                    - enable
                    - disable
            natip:
                description:
                    - "Policy-based IPsec VPN: source NAT IP address for outgoing traffic."
            natoutbound:
                description:
                    - "Policy-based IPsec VPN: apply source NAT to outbound traffic."
                choices:
                    - enable
                    - disable
            ntlm:
                description:
                    - Enable/disable NTLM authentication.
                choices:
                    - enable
                    - disable
            ntlm-enabled-browsers:
                description:
                    - HTTP-User-Agent value of supported browsers.
                suboptions:
                    user-agent-string:
                        description:
                            - User agent string.
                        required: true
            ntlm-guest:
                description:
                    - Enable/disable NTLM guest user access.
                choices:
                    - enable
                    - disable
            outbound:
                description:
                    - "Policy-based IPsec VPN: only traffic from the internal network can initiate a VPN."
                choices:
                    - enable
                    - disable
            per-ip-shaper:
                description:
                    - Per-IP traffic shaper. Source firewall.shaper.per-ip-shaper.name.
            permit-any-host:
                description:
                    - Accept UDP packets from any host.
                choices:
                    - enable
                    - disable
            permit-stun-host:
                description:
                    - Accept UDP packets from any Session Traversal Utilities for NAT (STUN) host.
                choices:
                    - enable
                    - disable
            policyid:
                description:
                    - Policy ID.
                required: true
            poolname:
                description:
                    - IP Pool names.
                suboptions:
                    name:
                        description:
                            - IP pool name. Source firewall.ippool.name.
                        required: true
            profile-group:
                description:
                    - Name of profile group. Source firewall.profile-group.name.
            profile-protocol-options:
                description:
                    - Name of an existing Protocol options profile. Source firewall.profile-protocol-options.name.
            profile-type:
                description:
                    - Determine whether the firewall policy allows security profile groups or single profiles only.
                choices:
                    - single
                    - group
            radius-mac-auth-bypass:
                description:
                    - Enable MAC authentication bypass. The bypassed MAC address must be received from RADIUS server.
                choices:
                    - enable
                    - disable
            redirect-url:
                description:
                    - URL users are directed to after seeing and accepting the disclaimer or authenticating.
            replacemsg-override-group:
                description:
                    - Override the default replacement message group for this policy. Source system.replacemsg-group.name.
            rsso:
                description:
                    - Enable/disable RADIUS single sign-on (RSSO).
                choices:
                    - enable
                    - disable
            rtp-addr:
                description:
                    - Address names if this is an RTP NAT policy.
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address.name firewall.addrgrp.name.
                        required: true
            rtp-nat:
                description:
                    - Enable Real Time Protocol (RTP) NAT.
                choices:
                    - disable
                    - enable
            scan-botnet-connections:
                description:
                    - Block or monitor connections to Botnet servers or disable Botnet scanning.
                choices:
                    - disable
                    - block
                    - monitor
            schedule:
                description:
                    - Schedule name. Source firewall.schedule.onetime.name firewall.schedule.recurring.name firewall.schedule.group.name.
            schedule-timeout:
                description:
                    - Enable to force current sessions to end when the schedule object times out. Disable allows them to end from inactivity.
                choices:
                    - enable
                    - disable
            send-deny-packet:
                description:
                    - Enable to send a reply when a session is denied or blocked by a firewall policy.
                choices:
                    - disable
                    - enable
            service:
                description:
                    - Service and service group names.
                suboptions:
                    name:
                        description:
                            - Service and service group names. Source firewall.service.custom.name firewall.service.group.name.
                        required: true
            service-negate:
                description:
                    - When enabled service specifies what the service must NOT be.
                choices:
                    - enable
                    - disable
            session-ttl:
                description:
                    - TTL in seconds for sessions accepted by this policy (0 means use the system default session TTL).
            spamfilter-profile:
                description:
                    - Name of an existing Spam filter profile. Source spamfilter.profile.name.
            srcaddr:
                description:
                    - Source address and address group names.
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address.name firewall.addrgrp.name.
                        required: true
            srcaddr-negate:
                description:
                    - When enabled srcaddr specifies what the source address must NOT be.
                choices:
                    - enable
                    - disable
            srcintf:
                description:
                    - Incoming (ingress) interface.
                suboptions:
                    name:
                        description:
                            - Interface name. Source system.interface.name system.zone.name.
                        required: true
            ssh-filter-profile:
                description:
                    - Name of an existing SSH filter profile. Source ssh-filter.profile.name.
            ssl-mirror:
                description:
                    - Enable to copy decrypted SSL traffic to a FortiGate interface (called SSL mirroring).
                choices:
                    - enable
                    - disable
            ssl-mirror-intf:
                description:
                    - SSL mirror interface name.
                suboptions:
                    name:
                        description:
                            - Mirror Interface name. Source system.interface.name system.zone.name.
                        required: true
            ssl-ssh-profile:
                description:
                    - Name of an existing SSL SSH profile. Source firewall.ssl-ssh-profile.name.
            status:
                description:
                    - Enable or disable this policy.
                choices:
                    - enable
                    - disable
            tcp-mss-receiver:
                description:
                    - Receiver TCP maximum segment size (MSS).
            tcp-mss-sender:
                description:
                    - Sender TCP maximum segment size (MSS).
            tcp-session-without-syn:
                description:
                    - Enable/disable creation of TCP session without SYN flag.
                choices:
                    - all
                    - data-only
                    - disable
            timeout-send-rst:
                description:
                    - Enable/disable sending RST packets when TCP sessions expire.
                choices:
                    - enable
                    - disable
            traffic-shaper:
                description:
                    - Traffic shaper. Source firewall.shaper.traffic-shaper.name.
            traffic-shaper-reverse:
                description:
                    - Reverse traffic shaper. Source firewall.shaper.traffic-shaper.name.
            url-category:
                description:
                    - URL category ID list.
                suboptions:
                    id:
                        description:
                            - URL category ID.
                        required: true
            users:
                description:
                    - Names of individual users that can authenticate with this policy.
                suboptions:
                    name:
                        description:
                            - Names of individual users that can authenticate with this policy. Source user.local.name.
                        required: true
            utm-status:
                description:
                    - Enable to add one or more security profiles (AV, IPS, etc.) to the firewall policy.
                choices:
                    - enable
                    - disable
            uuid:
                description:
                    - Universally Unique Identifier (UUID; automatically assigned but can be manually reset).
            vlan-cos-fwd:
                description:
                    - "VLAN forward direction user priority: 255 passthrough, 0 lowest, 7 highest."
            vlan-cos-rev:
                description:
                    - "VLAN reverse direction user priority: 255 passthrough, 0 lowest, 7 highest.."
            vlan-filter:
                description:
                    - Set VLAN filters.
            voip-profile:
                description:
                    - Name of an existing VoIP profile. Source voip.profile.name.
            vpntunnel:
                description:
                    - "Policy-based IPsec VPN: name of the IPsec VPN Phase 1. Source vpn.ipsec.phase1.name vpn.ipsec.manualkey.name."
            waf-profile:
                description:
                    - Name of an existing Web application firewall profile. Source waf.profile.name.
            wanopt:
                description:
                    - Enable/disable WAN optimization.
                choices:
                    - enable
                    - disable
            wanopt-detection:
                description:
                    - WAN optimization auto-detection mode.
                choices:
                    - active
                    - passive
                    - off
            wanopt-passive-opt:
                description:
                    - WAN optimization passive mode options. This option decides what IP address will be used to connect server.
                choices:
                    - default
                    - transparent
                    - non-transparent
            wanopt-peer:
                description:
                    - WAN optimization peer. Source wanopt.peer.peer-host-id.
            wanopt-profile:
                description:
                    - WAN optimization profile. Source wanopt.profile.name.
            wccp:
                description:
                    - Enable/disable forwarding traffic matching this policy to a configured WCCP server.
                choices:
                    - enable
                    - disable
            webcache:
                description:
                    - Enable/disable web cache.
                choices:
                    - enable
                    - disable
            webcache-https:
                description:
                    - Enable/disable web cache for HTTPS.
                choices:
                    - disable
                    - enable
            webfilter-profile:
                description:
                    - Name of an existing Web filter profile. Source webfilter.profile.name.
            wsso:
                description:
                    - Enable/disable WiFi Single Sign On (WSSO).
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
  - name: Configure IPv4 policies.
    fortios_firewall_policy:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      firewall_policy:
        state: "present"
        action: "accept"
        app-category:
         -
            id:  "5"
        app-group:
         -
            name: "default_name_7 (source application.group.name)"
        application:
         -
            id:  "9"
        application-list: "<your_own_value> (source application.list.name)"
        auth-cert: "<your_own_value> (source vpn.certificate.local.name)"
        auth-path: "enable"
        auth-redirect-addr: "<your_own_value>"
        av-profile: "<your_own_value> (source antivirus.profile.name)"
        block-notification: "enable"
        captive-portal-exempt: "enable"
        capture-packet: "enable"
        comments: "<your_own_value>"
        custom-log-fields:
         -
            field-id: "<your_own_value> (source log.custom-field.id)"
        delay-tcp-npu-session: "enable"
        devices:
         -
            name: "default_name_23 (source user.device.alias user.device-group.name user.device-category.name)"
        diffserv-forward: "enable"
        diffserv-reverse: "enable"
        diffservcode-forward: "<your_own_value>"
        diffservcode-rev: "<your_own_value>"
        disclaimer: "enable"
        dlp-sensor: "<your_own_value> (source dlp.sensor.name)"
        dnsfilter-profile: "<your_own_value> (source dnsfilter.profile.name)"
        dscp-match: "enable"
        dscp-negate: "enable"
        dscp-value: "<your_own_value>"
        dsri: "enable"
        dstaddr:
         -
            name: "default_name_36 (source firewall.address.name firewall.addrgrp.name firewall.vip.name firewall.vipgrp.name)"
        dstaddr-negate: "enable"
        dstintf:
         -
            name: "default_name_39 (source system.interface.name system.zone.name)"
        firewall-session-dirty: "check-all"
        fixedport: "enable"
        fsso: "enable"
        fsso-agent-for-ntlm: "<your_own_value> (source user.fsso.name)"
        global-label: "<your_own_value>"
        groups:
         -
            name: "default_name_46 (source user.group.name)"
        icap-profile: "<your_own_value> (source icap.profile.name)"
        identity-based-route: "<your_own_value> (source firewall.identity-based-route.name)"
        inbound: "enable"
        internet-service: "enable"
        internet-service-custom:
         -
            name: "default_name_52 (source firewall.internet-service-custom.name)"
        internet-service-id:
         -
            id:  "54 (source firewall.internet-service.id)"
        internet-service-negate: "enable"
        internet-service-src: "enable"
        internet-service-src-custom:
         -
            name: "default_name_58 (source firewall.internet-service-custom.name)"
        internet-service-src-id:
         -
            id:  "60 (source firewall.internet-service.id)"
        internet-service-src-negate: "enable"
        ippool: "enable"
        ips-sensor: "<your_own_value> (source ips.sensor.name)"
        label: "<your_own_value>"
        learning-mode: "enable"
        logtraffic: "all"
        logtraffic-start: "enable"
        match-vip: "enable"
        name: "default_name_69"
        nat: "enable"
        natinbound: "enable"
        natip: "<your_own_value>"
        natoutbound: "enable"
        ntlm: "enable"
        ntlm-enabled-browsers:
         -
            user-agent-string: "<your_own_value>"
        ntlm-guest: "enable"
        outbound: "enable"
        per-ip-shaper: "<your_own_value> (source firewall.shaper.per-ip-shaper.name)"
        permit-any-host: "enable"
        permit-stun-host: "enable"
        policyid: "82"
        poolname:
         -
            name: "default_name_84 (source firewall.ippool.name)"
        profile-group: "<your_own_value> (source firewall.profile-group.name)"
        profile-protocol-options: "<your_own_value> (source firewall.profile-protocol-options.name)"
        profile-type: "single"
        radius-mac-auth-bypass: "enable"
        redirect-url: "<your_own_value>"
        replacemsg-override-group: "<your_own_value> (source system.replacemsg-group.name)"
        rsso: "enable"
        rtp-addr:
         -
            name: "default_name_93 (source firewall.address.name firewall.addrgrp.name)"
        rtp-nat: "disable"
        scan-botnet-connections: "disable"
        schedule: "<your_own_value> (source firewall.schedule.onetime.name firewall.schedule.recurring.name firewall.schedule.group.name)"
        schedule-timeout: "enable"
        send-deny-packet: "disable"
        service:
         -
            name: "default_name_100 (source firewall.service.custom.name firewall.service.group.name)"
        service-negate: "enable"
        session-ttl: "102"
        spamfilter-profile: "<your_own_value> (source spamfilter.profile.name)"
        srcaddr:
         -
            name: "default_name_105 (source firewall.address.name firewall.addrgrp.name)"
        srcaddr-negate: "enable"
        srcintf:
         -
            name: "default_name_108 (source system.interface.name system.zone.name)"
        ssh-filter-profile: "<your_own_value> (source ssh-filter.profile.name)"
        ssl-mirror: "enable"
        ssl-mirror-intf:
         -
            name: "default_name_112 (source system.interface.name system.zone.name)"
        ssl-ssh-profile: "<your_own_value> (source firewall.ssl-ssh-profile.name)"
        status: "enable"
        tcp-mss-receiver: "115"
        tcp-mss-sender: "116"
        tcp-session-without-syn: "all"
        timeout-send-rst: "enable"
        traffic-shaper: "<your_own_value> (source firewall.shaper.traffic-shaper.name)"
        traffic-shaper-reverse: "<your_own_value> (source firewall.shaper.traffic-shaper.name)"
        url-category:
         -
            id:  "122"
        users:
         -
            name: "default_name_124 (source user.local.name)"
        utm-status: "enable"
        uuid: "<your_own_value>"
        vlan-cos-fwd: "127"
        vlan-cos-rev: "128"
        vlan-filter: "<your_own_value>"
        voip-profile: "<your_own_value> (source voip.profile.name)"
        vpntunnel: "<your_own_value> (source vpn.ipsec.phase1.name vpn.ipsec.manualkey.name)"
        waf-profile: "<your_own_value> (source waf.profile.name)"
        wanopt: "enable"
        wanopt-detection: "active"
        wanopt-passive-opt: "default"
        wanopt-peer: "<your_own_value> (source wanopt.peer.peer-host-id)"
        wanopt-profile: "<your_own_value> (source wanopt.profile.name)"
        wccp: "enable"
        webcache: "enable"
        webcache-https: "disable"
        webfilter-profile: "<your_own_value> (source webfilter.profile.name)"
        wsso: "enable"
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
  sample: "key1"
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


def filter_firewall_policy_data(json):
    option_list = ['action', 'app-category', 'app-group',
                   'application', 'application-list', 'auth-cert',
                   'auth-path', 'auth-redirect-addr', 'av-profile',
                   'block-notification', 'captive-portal-exempt', 'capture-packet',
                   'comments', 'custom-log-fields', 'delay-tcp-npu-session',
                   'devices', 'diffserv-forward', 'diffserv-reverse',
                   'diffservcode-forward', 'diffservcode-rev', 'disclaimer',
                   'dlp-sensor', 'dnsfilter-profile', 'dscp-match',
                   'dscp-negate', 'dscp-value', 'dsri',
                   'dstaddr', 'dstaddr-negate', 'dstintf',
                   'firewall-session-dirty', 'fixedport', 'fsso',
                   'fsso-agent-for-ntlm', 'global-label', 'groups',
                   'icap-profile', 'identity-based-route', 'inbound',
                   'internet-service', 'internet-service-custom', 'internet-service-id',
                   'internet-service-negate', 'internet-service-src', 'internet-service-src-custom',
                   'internet-service-src-id', 'internet-service-src-negate', 'ippool',
                   'ips-sensor', 'label', 'learning-mode',
                   'logtraffic', 'logtraffic-start', 'match-vip',
                   'name', 'nat', 'natinbound',
                   'natip', 'natoutbound', 'ntlm',
                   'ntlm-enabled-browsers', 'ntlm-guest', 'outbound',
                   'per-ip-shaper', 'permit-any-host', 'permit-stun-host',
                   'policyid', 'poolname', 'profile-group',
                   'profile-protocol-options', 'profile-type', 'radius-mac-auth-bypass',
                   'redirect-url', 'replacemsg-override-group', 'rsso',
                   'rtp-addr', 'rtp-nat', 'scan-botnet-connections',
                   'schedule', 'schedule-timeout', 'send-deny-packet',
                   'service', 'service-negate', 'session-ttl',
                   'spamfilter-profile', 'srcaddr', 'srcaddr-negate',
                   'srcintf', 'ssh-filter-profile', 'ssl-mirror',
                   'ssl-mirror-intf', 'ssl-ssh-profile', 'status',
                   'tcp-mss-receiver', 'tcp-mss-sender', 'tcp-session-without-syn',
                   'timeout-send-rst', 'traffic-shaper', 'traffic-shaper-reverse',
                   'url-category', 'users', 'utm-status',
                   'uuid', 'vlan-cos-fwd', 'vlan-cos-rev',
                   'vlan-filter', 'voip-profile', 'vpntunnel',
                   'waf-profile', 'wanopt', 'wanopt-detection',
                   'wanopt-passive-opt', 'wanopt-peer', 'wanopt-profile',
                   'wccp', 'webcache', 'webcache-https',
                   'webfilter-profile', 'wsso']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def firewall_policy(data, fos):
    vdom = data['vdom']
    firewall_policy_data = data['firewall_policy']
    filtered_data = filter_firewall_policy_data(firewall_policy_data)
    if firewall_policy_data['state'] == "present":
        return fos.set('firewall',
                       'policy',
                       data=filtered_data,
                       vdom=vdom)

    elif firewall_policy_data['state'] == "absent":
        return fos.delete('firewall',
                          'policy',
                          mkey=filtered_data['policyid'],
                          vdom=vdom)


def fortios_firewall(data, fos):
    login(data)

    methodlist = ['firewall_policy']
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
        "https": {"required": False, "type": "bool", "default": "False"},
        "firewall_policy": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "action": {"required": False, "type": "str",
                           "choices": ["accept", "deny", "ipsec"]},
                "app-category": {"required": False, "type": "list",
                                 "options": {
                                     "id": {"required": True, "type": "int"}
                                 }},
                "app-group": {"required": False, "type": "list",
                              "options": {
                                  "name": {"required": True, "type": "str"}
                              }},
                "application": {"required": False, "type": "list",
                                "options": {
                                    "id": {"required": True, "type": "int"}
                                }},
                "application-list": {"required": False, "type": "str"},
                "auth-cert": {"required": False, "type": "str"},
                "auth-path": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "auth-redirect-addr": {"required": False, "type": "str"},
                "av-profile": {"required": False, "type": "str"},
                "block-notification": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "captive-portal-exempt": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "capture-packet": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "comments": {"required": False, "type": "str"},
                "custom-log-fields": {"required": False, "type": "list",
                                      "options": {
                                          "field-id": {"required": True, "type": "str"}
                                      }},
                "delay-tcp-npu-session": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "devices": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "diffserv-forward": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "diffserv-reverse": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "diffservcode-forward": {"required": False, "type": "str"},
                "diffservcode-rev": {"required": False, "type": "str"},
                "disclaimer": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "dlp-sensor": {"required": False, "type": "str"},
                "dnsfilter-profile": {"required": False, "type": "str"},
                "dscp-match": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "dscp-negate": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "dscp-value": {"required": False, "type": "str"},
                "dsri": {"required": False, "type": "str",
                         "choices": ["enable", "disable"]},
                "dstaddr": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "dstaddr-negate": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "dstintf": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "firewall-session-dirty": {"required": False, "type": "str",
                                           "choices": ["check-all", "check-new"]},
                "fixedport": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "fsso": {"required": False, "type": "str",
                         "choices": ["enable", "disable"]},
                "fsso-agent-for-ntlm": {"required": False, "type": "str"},
                "global-label": {"required": False, "type": "str"},
                "groups": {"required": False, "type": "list",
                           "options": {
                               "name": {"required": True, "type": "str"}
                           }},
                "icap-profile": {"required": False, "type": "str"},
                "identity-based-route": {"required": False, "type": "str"},
                "inbound": {"required": False, "type": "str",
                            "choices": ["enable", "disable"]},
                "internet-service": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "internet-service-custom": {"required": False, "type": "list",
                                            "options": {
                                                "name": {"required": True, "type": "str"}
                                            }},
                "internet-service-id": {"required": False, "type": "list",
                                        "options": {
                                            "id": {"required": True, "type": "int"}
                                        }},
                "internet-service-negate": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                "internet-service-src": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "internet-service-src-custom": {"required": False, "type": "list",
                                                "options": {
                                                    "name": {"required": True, "type": "str"}
                                                }},
                "internet-service-src-id": {"required": False, "type": "list",
                                            "options": {
                                                "id": {"required": True, "type": "int"}
                                            }},
                "internet-service-src-negate": {"required": False, "type": "str",
                                                "choices": ["enable", "disable"]},
                "ippool": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "ips-sensor": {"required": False, "type": "str"},
                "label": {"required": False, "type": "str"},
                "learning-mode": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "logtraffic": {"required": False, "type": "str",
                               "choices": ["all", "utm", "disable"]},
                "logtraffic-start": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "match-vip": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "name": {"required": False, "type": "str"},
                "nat": {"required": False, "type": "str",
                        "choices": ["enable", "disable"]},
                "natinbound": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "natip": {"required": False, "type": "str"},
                "natoutbound": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "ntlm": {"required": False, "type": "str",
                         "choices": ["enable", "disable"]},
                "ntlm-enabled-browsers": {"required": False, "type": "list",
                                          "options": {
                                              "user-agent-string": {"required": True, "type": "str"}
                                          }},
                "ntlm-guest": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "outbound": {"required": False, "type": "str",
                             "choices": ["enable", "disable"]},
                "per-ip-shaper": {"required": False, "type": "str"},
                "permit-any-host": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "permit-stun-host": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "policyid": {"required": True, "type": "int"},
                "poolname": {"required": False, "type": "list",
                             "options": {
                                 "name": {"required": True, "type": "str"}
                             }},
                "profile-group": {"required": False, "type": "str"},
                "profile-protocol-options": {"required": False, "type": "str"},
                "profile-type": {"required": False, "type": "str",
                                 "choices": ["single", "group"]},
                "radius-mac-auth-bypass": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "redirect-url": {"required": False, "type": "str"},
                "replacemsg-override-group": {"required": False, "type": "str"},
                "rsso": {"required": False, "type": "str",
                         "choices": ["enable", "disable"]},
                "rtp-addr": {"required": False, "type": "list",
                             "options": {
                                 "name": {"required": True, "type": "str"}
                             }},
                "rtp-nat": {"required": False, "type": "str",
                            "choices": ["disable", "enable"]},
                "scan-botnet-connections": {"required": False, "type": "str",
                                            "choices": ["disable", "block", "monitor"]},
                "schedule": {"required": False, "type": "str"},
                "schedule-timeout": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "send-deny-packet": {"required": False, "type": "str",
                                     "choices": ["disable", "enable"]},
                "service": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "service-negate": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "session-ttl": {"required": False, "type": "int"},
                "spamfilter-profile": {"required": False, "type": "str"},
                "srcaddr": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "srcaddr-negate": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "srcintf": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "ssh-filter-profile": {"required": False, "type": "str"},
                "ssl-mirror": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "ssl-mirror-intf": {"required": False, "type": "list",
                                    "options": {
                                        "name": {"required": True, "type": "str"}
                                    }},
                "ssl-ssh-profile": {"required": False, "type": "str"},
                "status": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "tcp-mss-receiver": {"required": False, "type": "int"},
                "tcp-mss-sender": {"required": False, "type": "int"},
                "tcp-session-without-syn": {"required": False, "type": "str",
                                            "choices": ["all", "data-only", "disable"]},
                "timeout-send-rst": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "traffic-shaper": {"required": False, "type": "str"},
                "traffic-shaper-reverse": {"required": False, "type": "str"},
                "url-category": {"required": False, "type": "list",
                                 "options": {
                                     "id": {"required": True, "type": "int"}
                                 }},
                "users": {"required": False, "type": "list",
                          "options": {
                              "name": {"required": True, "type": "str"}
                          }},
                "utm-status": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "uuid": {"required": False, "type": "str"},
                "vlan-cos-fwd": {"required": False, "type": "int"},
                "vlan-cos-rev": {"required": False, "type": "int"},
                "vlan-filter": {"required": False, "type": "str"},
                "voip-profile": {"required": False, "type": "str"},
                "vpntunnel": {"required": False, "type": "str"},
                "waf-profile": {"required": False, "type": "str"},
                "wanopt": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "wanopt-detection": {"required": False, "type": "str",
                                     "choices": ["active", "passive", "off"]},
                "wanopt-passive-opt": {"required": False, "type": "str",
                                       "choices": ["default", "transparent", "non-transparent"]},
                "wanopt-peer": {"required": False, "type": "str"},
                "wanopt-profile": {"required": False, "type": "str"},
                "wccp": {"required": False, "type": "str",
                         "choices": ["enable", "disable"]},
                "webcache": {"required": False, "type": "str",
                             "choices": ["enable", "disable"]},
                "webcache-https": {"required": False, "type": "str",
                                   "choices": ["disable", "enable"]},
                "webfilter-profile": {"required": False, "type": "str"},
                "wsso": {"required": False, "type": "str",
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

    is_error, has_changed, result = fortios_firewall(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
